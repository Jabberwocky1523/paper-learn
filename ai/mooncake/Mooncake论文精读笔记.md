# Mooncake 论文精读笔记

## 论文信息

- **题目**：*Mooncake: Trading More Storage for Less Computation — A KVCache-centric Architecture for Serving LLM Chatbot*
- **会议**：23rd USENIX Conference on File and Storage Technologies（FAST 2025）
- **作者单位**：Moonshot AI、清华大学
- **论文文件**：[fast25-qin.pdf](./fast25-qin.pdf)
- **系统定位**：Kimi 的大规模 LLM 在线推理平台
- **关键词**：LLM Serving、KVCache、Prefill/Decode Disaggregation、Prefix Caching、RDMA、Scheduling

---

## 1. 一句话总结

Mooncake 将集群中的 CPU、DRAM、SSD 和 RDMA 网络组织成一个全局 KVCache 池，用缓存复用和高速传输代替重复的 GPU prefill 计算，并通过 KVCache-aware 调度在满足 TTFT、TBT SLO 的前提下提高有效吞吐量。

其核心思想可以概括为：

> Trading more storage for less computation：用更多存储和网络资源，换取更少的 GPU 计算。

---

## 2. 研究背景

### 2.1 LLM 推理的两个阶段

一次生成式 LLM 请求通常分为：

1. **Prefill 阶段**
   - 一次性处理全部输入 token。
   - 计算 Attention 和 MLP，并生成首个输出 token。
   - 同时产生后续解码所需的 KVCache。
   - 并行度高，通常属于计算密集型任务。

2. **Decode 阶段**
   - 以自回归方式逐个生成 token。
   - 每轮需要读取模型权重和已有 KVCache。
   - 通常受显存容量、显存带宽和 batch 大小限制。

Prefill 和 Decode 的资源特征不同。如果它们共享同一批 GPU，长输入的 prefill 可能阻塞 decode，使用户观察到输出 token 停顿。

### 2.2 关键服务指标

- **TTFT（Time To First Token）**：请求到达后，生成第一个 token 所需的时间。
- **TBT（Time Between Tokens）**：相邻输出 token 之间的时间。
- **SLO（Service Level Objective）**：服务承诺的延迟目标。
- **Goodput / 有效吞吐量**：能够同时满足 TTFT 和 TBT SLO 的请求吞吐量。

Mooncake 的目标不是单纯最大化系统接收的请求数，而是在满足延迟约束的情况下最大化有效请求容量。

---

## 3. 论文要解决的问题

传统 LLM serving 系统主要存在以下问题：

1. **Prefill 与 Decode 相互干扰**：长上下文 prefill 会影响 decode 的稳定性。
2. **相同前缀被反复计算**：多轮对话和 Agent system prompt 中存在大量重复内容。
3. **本地缓存容量有限**：单机 HBM 或 DRAM 无法容纳足够多的 KVCache。
4. **缓存命中与负载均衡冲突**：缓存最多的节点可能也是队列最长的节点。
5. **高速网络未被充分利用**：GPU 服务器通常配备多块高速 NIC，但一般推理系统没有充分使用这些资源。

论文的核心研究问题是：

> 能否把整个集群的存储和网络资源组织起来，通过全局 KVCache 复用减少 GPU 计算，同时满足严格的 TTFT 和 TBT SLO？

---

## 4. 为什么传输 KVCache 可能比重新计算更划算

### 4.1 Prefill 计算量

对于输入长度为 \(n\) 的请求，论文将 prefill FLOPs 近似为：

$$
C(n)=l(an^2d+bnd^2)
$$

其中：

- \(l\)：Transformer 层数；
- \(d\)：模型隐藏维度；
- \(an^2d\)：Attention 相关计算；
- \(bnd^2\)：MLP 和线性投影相关计算。

如果长度为 \(p\) 的输入前缀已经生成过 KVCache，那么复用它可以近似节省：

$$
\Delta C \approx l(ap^2d+bpd^2)
$$

### 4.2 KVCache 传输量

长度为 \(p\) 的前缀对应的 KVCache 大小约为：

$$
S_{KV}=p\times l\times\frac{2d}{gqa}\times s
$$

其中：

- \(gqa\)：Query head 数与 KV head 数之比；
- \(s\)：每个张量元素占用的字节数；
- 系数 2 表示 Key 和 Value。

论文推导出传输优于重新计算的条件：

$$
\frac{B}{G}>
\frac{2ds}{gqa(apd+bd^2)}
$$

其中 \(B\) 是有效 KVCache 加载带宽，\(G\) 是 GPU 计算吞吐量。

### 4.3 直觉解释

- 模型越大，重新计算的代价越高。
- 前缀越长，可节省的 prefill 计算越多。
- GQA/MQA 减小了 KVCache 大小，使传输更加划算。
- 网络越快，远端缓存复用越有价值。

以 LLaMA3-70B 和 8192 token 前缀为例，论文估算最低有效带宽约为：

- 8×A800：6 GB/s；
- 8×H800：19 GB/s。

因此，Mooncake 的收益依赖高速 RDMA 网络以及足够高的前缀复用率。

---

## 5. Mooncake 总体架构

Mooncake 进行了两层资源解耦：

```text
用户请求
   │
   ▼
Conductor：全局调度器
   │
   ├── Prefill Pool：处理输入并产生 KVCache
   │
   ├── Mooncake Store：保存、查找、迁移和复制 KVCache
   │
   └── Decode Pool：加载完整 KVCache 并持续生成 token
```

主要组件包括：

### 5.1 Conductor

全局调度器，负责：

- 查找请求能够复用的前缀 KVCache；
- 估算缓存传输、排队和 prefill 执行时间；
- 选择 prefill 节点；
- 根据负载和 TBT 选择 decode 节点；
- 调度 KVCache 的迁移与热点副本；
- 在预计无法满足 SLO 时拒绝请求。

### 5.2 Prefill Pool

- 专门执行 prompt 的 prefill。
- 从本地或远端读取已有前缀 KVCache。
- 只计算没有命中的输入部分。
- 将新产生的 KVCache 按层异步传给 decode 节点。

### 5.3 Decode Pool

- 专门进行逐 token 解码。
- 接收 prefill 阶段产生的完整 KVCache。
- 使用 continuous batching 提高 GPU 利用率。
- 调度时重点保证 TBT，同时考虑显存能够容纳的 KVCache 总量。

### 5.4 Mooncake Store

将各节点的 DRAM、SSD、VRAM 和 RDMA 网络整合为全局 KVCache 系统，是 Mooncake 的核心组件。

---

## 6. 单个请求的执行流程

1. 请求完成 tokenization 后，Conductor 对 prompt 分块并计算 block key。
2. Conductor 查找可复用的最长前缀 KVCache。
3. 综合缓存命中、排队时间和节点负载，选择 prefill 与 decode 节点。
4. 将已命中的前缀 KVCache 加载到 prefill GPU。
5. GPU 只计算未缓存的增量输入。
6. 每生成一层新的 KVCache，就将其异步传至 decode 节点的 CPU 内存。
7. decode 节点把 KVCache 从 DRAM 加载到 HBM。
8. 请求加入 continuous batching，开始逐 token 输出。

关键优化是**逐层流式传输**：新 KVCache 的传输可以与后续层的 prefill 计算重叠，从而隐藏部分通信延迟。

---

## 7. Mooncake Store 的关键设计

### 7.1 分页 KVCache

- KVCache 被划分为固定大小的 block。
- 一个 block 通常对应 16～512 个 token。
- 实验中采用 256 token/block。
- 分页设计能够减少空间碎片，并支持按块查找、迁移和淘汰。

### 7.2 前缀寻址与去重

每个 block 的 key 同时依赖：

- 当前 block 的 token 内容；
- 之前的前缀状态。

这样只有完全相同的前缀才能复用对应 KVCache，避免把相同局部文本但不同上下文的状态混淆。

### 7.3 缓存淘汰

- 缓存池满时使用 LRU 淘汰。
- 正在被请求访问的 block 不会被淘汰。
- 热门 block 可以在多个节点保存副本，以分散访问压力。

### 7.4 高性能传输引擎

传输引擎支持 DRAM 和 GPU VRAM，可在合适时使用 GPU Direct RDMA。其主要设计包括：

- 根据 NUMA、PCIe 和 NIC 拓扑选择传输路径；
- 将单次传输切成约 16 KB 的 slice，分配给多块 NIC；
- 使用 endpoint pool 控制 RDMA 连接数量；
- 使用 SIEVE 管理连接淘汰；
- NIC 或连接故障时切换到备用路径并重试。

这部分的目标不仅是峰值带宽，还包括动态集群中的可用性和故障恢复。

---

## 8. Chunked Pipeline Parallelism（CPP）

超长输入可能无法在单个节点上满足 TTFT。Mooncake 因此将 prompt 切分为多个 chunk，让同一个请求的不同 chunk 在多个 prefill 节点上流水执行。

相比跨节点 Tensor Parallelism 或 Sequence Parallelism，CPP 的设计目标是：

- 跨节点通信主要发生在流水线边界；
- 通信更容易与计算重叠；
- 减少频繁 All-Reduce；
- 避免和 KVCache 传输争抢网络；
- 短输入不会承受明显的跨节点并行开销；
- 长输入可以使用更多节点降低 TTFT。

---

## 9. KVCache-aware 调度

### 9.1 Prefill 节点选择

对每个候选 prefill 节点，Conductor 估算：

$$
TTFT_{estimate}=
T_{transfer}+T_{queue}+T_{prefill}
$$

- \(T_{transfer}\)：把远端缓存迁入该节点的时间；
- \(T_{queue}\)：节点上现有请求的预计排队时间；
- \(T_{prefill}\)：根据输入长度和缓存命中长度预测的执行时间。

Prefill 时间通过离线数据拟合的多项式回归模型预测。最终选择预计 TTFT 最短的节点，而不一定选择缓存命中最长的节点。

### 9.2 Decode 节点选择

Decode 调度重点考虑：

- 当前 continuous batch 的负载；
- 预计 TBT；
- GPU 显存能否容纳请求的 KVCache。

如果预计 TTFT 或 TBT 超过 SLO，系统返回 HTTP 429，避免过载进一步影响已有请求。

### 9.3 热点缓存自动复制

当拥有最佳缓存的节点过载时，请求可能被调度到较空闲的节点。若传输比重新计算更划算，目标节点会拉取 KVCache，并将其保留为副本。

```text
热门前缀被频繁访问
        ↓
原缓存节点逐渐过载
        ↓
请求被调度到其他节点
        ↓
KVCache 随请求迁移并被保留
        ↓
热门缓存形成更多副本
```

该机制利用真实请求流量完成热点迁移，不需要准确预测未来访问热度。

在论文实验中，不同 prefill 调度方式的平均 TTFT 为：

| 调度方式 | 平均 TTFT |
|---|---:|
| 全局 Cache-aware | 3.07 s |
| 本地 Cache-aware | 3.58 s |
| 负载均衡 | 5.27 s |
| 随机调度 | 19.65 s |

全局缓存感知调度比本地缓存感知调度进一步降低约 14% 的平均 TTFT。

---

## 10. 实验设置

### 10.1 测试集群

- 16 台服务器；
- 每台服务器配备 8×NVIDIA A800-SXM4-80GB；
- 每台服务器配备 4×200 Gbps RDMA NIC；
- 使用模拟 LLaMA3-70B 结构的 dummy model；
- KVCache block size 为 256 token；
- 基线系统为 vLLM 0.5.1。

### 10.2 工作负载

| 工作负载 | 平均输入长度 | 平均输出长度 | 前缀缓存比例 | 请求数 | 到达方式 |
|---|---:|---:|---:|---:|---|
| Conversation | 12,035 | 343 | 40% | 12,031 | 真实时间戳 |
| Tool & Agent | 8,596 | 182 | 59% | 23,608 | 真实时间戳 |
| Synthetic | 15,325 | 149 | 66% | 3,993 | Poisson |

Synthetic workload 由 ShareGPT、LEval 和 LooGLE 以 1:1:1 混合构造。另外两类来自 Kimi 的真实流量轨迹。

### 10.3 指标

- TTFT 门限通常设为 30 秒；
- TBT 门限根据场景设为 100、200 或 300 ms；
- TBT 定义为一个请求中最长 10% token 间隔的平均值；
- 同时满足 TTFT 和 TBT 门限的请求被视为有效请求。

---

## 11. 主要实验结果

### 11.1 有效请求容量

真实 Conversation workload 中，Mooncake 相比基线在不同 TBT SLO 下将有效请求容量提高约 **59%～498%**。SLO 越严格，Prefill/Decode 隔离的价值越明显。

- Tool & Agent workload：提高约 22%～64%；
- Synthetic workload：提高约 28%～62%；
- Synthetic workload 在 200 ms TBT 门限下提高约 40%。

### 11.2 Prefill GPU 时间

相比普通 vLLM，Mooncake 的平均 prefill GPU 时间下降：

| 工作负载 | GPU 时间下降比例 |
|---|---:|
| Conversation | 36% |
| Tool & Agent | 53% |
| Synthetic | 64% |

在缓存热点较为分散的 Synthetic workload 中，vLLM prefix caching 的 prefill GPU 时间约为 Mooncake 的 2.59 倍。

### 11.3 全局缓存效果

对于 LLaMA3-70B：

- 每个 token 的 KVCache 约为 320 KB；
- 单机约 1 TB DRAM 只能保存约 300 万 token；
- 在多数 workload 中，300 万 token 容量达不到理论最大命中率的 50%；
- 约 5000 万 token 才接近理论最大命中率，需要聚合至少 20 台机器的 DRAM。

相比本地缓存，全局缓存：

- 缓存命中率最多提高 136%，即达到约 2.36 倍；
- Prefill GPU 计算时间最多减少 48%。

### 11.4 KVCache 传输性能

传输约 40 GB KVCache 时：

| 网络配置 | 实际传输带宽 | 相比 TCP |
|---|---:|---:|
| 4×200 Gbps | 87 GB/s | 约 2.4× |
| 8×400 Gbps | 190 GB/s | 约 4.6× |

当总网络带宽低于约 100 Gbps 时，TTFT 和网络拥塞明显恶化，因此论文建议至少使用 100 Gbps 网络。

### 11.5 端到端延迟

在 128K 输入、95% 前缀命中的情况下：

- Prefill 时间减少 92%；
- 计入调度、传输和缓存加载开销后，TTFT 仍减少 86%。

### 11.6 Prefill/Decode 节点比例

- 增加 prefill 节点通常降低 TTFT，但可能增加 TBT；
- 增加 decode 节点通常降低 TBT，但可能增加 TTFT；
- 在论文的 synthetic workload 中，约 1:1 的 P/D 比取得最高有效请求容量。

生产系统主要采用固定比例，并持续监控负载；只有流量特征发生显著变化时才切换节点角色。

### 11.7 生产部署

作者报告 Mooncake 已部署在数千个节点上，每天处理超过 1000 亿 token。相比此前基于 vLLM 的系统：

- A800 集群请求处理能力提高 115%；
- H800 集群请求处理能力提高 107%。

---

## 12. 论文的主要贡献

按重要性归纳如下：

1. 将 KVCache 从单机显存对象提升为全局、可调度的集群资源。
2. 在同一调度决策中联合考虑缓存位置、Prefill 负载、Decode 负载和延迟 SLO。
3. 证明在高速网络和长上下文场景中，传输 KVCache 可以比重新计算更高效。
4. 实现面向 DRAM/VRAM 的高性能多 NIC RDMA 传输引擎。
5. 通过请求驱动的缓存迁移自动形成热点副本。
6. 将 P/D 分离和长上下文 CPP 用于真实的大规模生产系统。

单项技术如 P/D 分离、prefix caching、分页缓存、LRU 和 RDMA 并非全部由本文首次提出。论文的主要价值在于将这些机制围绕 KVCache 整合为经过生产验证的系统架构。

---

## 13. 局限与批判性评价

### 13.1 基线不够全面

论文使用 vLLM 0.5.1。由于当时的实现限制，vLLM 的 prefix caching 和 chunked prefill 被分别测试，没有测试两者结合后的最强配置。

Mooncake 的最终收益同时来自：

- P/D 分离；
- 全局缓存容量；
- 高速 RDMA；
- Cache-aware 调度；
- CPP；
- 请求准入控制。

因此，仅凭端到端结果很难准确判断每个组件分别贡献了多少，论文还可以提供更完整的消融实验。

### 13.2 依赖高端基础设施

Mooncake 最适合以下条件同时成立的场景：

- 模型较大；
- 输入上下文较长；
- 前缀复用率较高；
- 拥有高速 RDMA 网络；
- 集群规模足以形成大容量共享缓存。

在短 prompt、低复用率或普通以太网环境中，缓存查找、迁移和系统复杂度可能得不偿失。

### 13.3 模型和硬件覆盖有限

可复现实验主要基于 LLaMA3-70B 结构、A800 和 16 节点集群，缺少以下场景：

- 小模型；
- MoE 模型；
- 不同 GQA/MQA 配置；
- 普通网络环境；
- 更大规模集群的控制面压力。

### 13.4 生产提升数据不够透明

生产环境中 115% 和 107% 的提升很有价值，但论文没有完整公开：

- 流量前后是否完全一致；
- 模型和软件配置；
- 请求拒绝率；
- 成本、能耗和网络开销；
- 集群资源利用率；
- 前后系统版本差异。

因此，这些数字更适合作为工业部署经验，而不是完全可复现的因果结论。

### 13.5 控制面与多租户问题讨论不足

Conductor 需要维护全局缓存元数据和节点负载，但论文没有深入评估：

- 调度器吞吐上限；
- 元数据规模；
- 多 Conductor 的一致性；
- 控制面故障恢复；
- 多租户缓存隔离；
- KVCache 隐私与安全；
- 恶意或异常请求造成的缓存污染。

此外，缓存平衡阈值仍需人工调整，P/D 比例也主要依赖流量统计的稳定性。

### 13.6 指标解释需要谨慎

系统会拒绝预计不能满足 SLO 的请求，因此“有效请求容量”同时受以下因素影响：

- 推理性能；
- 调度预测准确度；
- 准入控制策略；
- SLO 门限的选择。

该指标很贴近生产服务，但不应简单等同于纯粹的模型吞吐量。

---

## 14. 适用与不适用场景

### 适合

- 长上下文聊天；
- 多轮对话；
- 具有固定长 system prompt 的 Agent；
- 长文档重复问答；
- 大模型推理；
- 配备高速 RDMA 的大规模 GPU 集群。

### 收益可能有限

- 短输入、一次性请求；
- 前缀重复率很低；
- 小模型；
- 低带宽网络；
- 缓存规模无法跨节点扩展；
- 数据安全策略禁止跨租户复用 KVCache。

---

## 15. 阅读结论

Mooncake 的核心逻辑可以压缩成四句话：

1. **P/D 分离解决 Prefill 对 Decode 的干扰。**
2. **全局 KVCache 减少重复的 Prefill 计算。**
3. **KVCache-aware 调度协调缓存命中与节点负载。**
4. **高速 RDMA 保证传输 KVCache 比重新计算更划算。**

最准确的结论是：

> Mooncake 并未证明分布式 KVCache 在所有环境中都更优；它证明了在大模型、长上下文、高前缀复用率和高速网络同时成立时，用存储和通信换取 GPU 计算能够显著提高 goodput。

---

## 16. 快速复习卡片

### Q1：Mooncake 的核心优化对象是什么？

KVCache。系统围绕 KVCache 的保存、复用、传输、复制和调度重新组织推理集群。

### Q2：为什么要分离 Prefill 和 Decode？

两者资源特征不同。Prefill 偏计算密集，Decode 偏显存带宽密集；混合运行时，长 Prefill 会破坏 Decode 的 TBT。

### Q3：为什么需要全局缓存？

单机 HBM/DRAM 容量不足，无法覆盖分散的长上下文缓存热点。聚合集群 DRAM 能显著提高命中率。

### Q4：为什么不总是把请求发到缓存命中最长的节点？

该节点可能排队严重。Mooncake 综合考虑传输、排队和增量计算时间，选择预计 TTFT 最短的节点。

### Q5：Mooncake 最重要的硬件前提是什么？

高速 RDMA 网络。论文建议总带宽至少达到约 100 Gbps。

### Q6：论文最值得保留的实验结果是什么？

全局缓存相对本地缓存可将命中率提高到约 2.36 倍，并最多减少 48% 的 prefill GPU 时间；真实对话 workload 中有效请求容量提高 59%～498%。

### Q7：论文最明显的局限是什么？

基线和消融实验不够完整，而且结果依赖长上下文、高复用率和昂贵的高速网络环境。

