---
tags:
  - papers/llm-serving
  - papers/systems
  - papers/kv-cache
  - papers/disaggregated-architecture
aliases:
  - MOONCAKE
  - KVCache-centric LLM Serving
date: 2025-02-25
venue: "FAST '25"
paper_type: AI_method
---

# Mooncake: Trading More Storage for Less Computation — A KVCache-centric Architecture for Serving LLM Chatbot

## 核心信息

- 标题: Mooncake: Trading More Storage for Less Computation — A KVCache-centric Architecture for Serving LLM Chatbot
- 标题翻译: Mooncake：以更多存储换取更少计算 —— 面向 LLM 聊天机器人服务的 KVCache 中心化架构
- 作者: Ruoyu Qin (Moonshot AI & 清华大学), Zheming Li, Weiran He, Jialei Cui (Moonshot AI), Feng Ren, Mingxing Zhang, Yongwei Wu, Weimin Zheng (清华大学), Xinran Xu (Moonshot AI)
- 机构: Moonshot AI（月之暗面）、清华大学
- 发表时间: 2025年2月25-27日
- 发表渠道: 23rd USENIX Conference on File and Storage Technologies (FAST '25)
- 论文链接: https://www.usenix.org/conference/fast25/presentation/qin
- 代码 / 项目: https://github.com/kvcache-ai/Mooncake
- 论文类型: 系统架构 / AI 推理基础设施

## 原文摘要翻译

MOONCAKE 是 Kimi 的在线推理服务平台，Kimi 是由月之暗面（Moonshot AI）开发的 LLM 聊天机器人服务。该平台采用以 KVCache 为中心的解耦架构，不仅分离了 prefill 和 decoding 集群，还高效利用了 GPU 集群中未被充分利用的 CPU、DRAM、SSD 和 NIC 资源，构建了一个解耦的分布式 KVCache。MOONCAKE 的核心是其以 KVCache 为中心的全局缓存和调度器，旨在在满足严格的延迟相关服务等级目标（SLO）的前提下最大化吞吐量。实验表明，MOONCAKE 在涉及长上下文输入的场景中表现卓越。在使用真实 trace 的测试中，MOONCAKE 在满足 SLO 的同时，相比基线方法将有效请求容量提升了 59% 至 498%。目前，MOONCAKE 已在数千个节点上运行，token 每日处理量超过 1000 亿。在实际部署中，MOONCAKE 的创新架构使 Kimi 在 NVIDIA A800 和 H800 集群上分别比此前系统多处理 115% 和 107% 的请求。

## 创新点

1. **以 KVCache 为中心的分布式全局缓存（MOONCAKE Store）**：将 GPU 集群中未被充分利用的 CPU DRAM、SSD 和 RDMA NIC 资源池化，构建一个跨节点的分布式 KVCache，使缓存容量从单节点 ~3M token 扩展到 ~50M token 级别。这是首个在大规模部署中展示跨会话、跨查询共享 KVCache 显著收益的系统。

2. **KVCache 感知的全局调度算法（Conductor）**：提出了综合考虑前缀缓存命中长度、实例负载和传输时间的 prefill 调度策略，配合基于启发式的热点自动迁移机制，无需精确预测未来 KVCache 使用模式即可实现缓存负载均衡。实验表明全局缓存感知调度相比局部缓存感知调度可额外降低 14% 的平均 TTFT。

3. **Chunked Pipeline Parallelism (CPP) 用于长上下文 prefill**：首次将流水线并行应用于推理阶段的长上下文 prefill，相比序列并行（SP）方案减少了跨节点通信开销，且天然适配短上下文场景，无需频繁弹性扩缩。

4. **多 RDMA NIC 拓扑感知传输引擎**：设计了零拷贝、拓扑感知路径选择、端点池化和故障处理的高性能 KVCache 传输引擎，在 8×400 Gbps 配置下达到 190 GB/s 的传输带宽，相比 TCP 方案快 4.6 倍。

## 一句话总结

MOONCAKE 通过将 GPU 集群中闲置的 CPU DRAM/SSD/NIC 资源构建为分布式 KVCache 全局缓存，配合缓存感知的全局调度，以存储换计算，在满足严格延迟 SLO 的前提下将 LLM 在线推理的有效请求容量提升 59%–498%，已在 Kimi 的大规模生产环境中验证。

## 研究问题

MaaS（Model as a Service）提供商的核心优化问题是：在满足 TTFT（time to first token）和 TBT（time between tokens）等延迟 SLO 的前提下，最大化整体有效吞吐量（goodput）。现有 LLM 在线推理系统面临两个主要瓶颈：

- **缓存容量不足**：现有 prefix caching 方案（如 vLLM 的 prefix caching）局限于单节点 HBM/DRAM，缓存容量仅支持约 3M token，在多样化工作负载下命中率不到理论最大值的 50%。
- **prefill 与 decoding 资源冲突**：prefill 阶段是计算密集型，decoding 阶段是内存密集型，二者耦合在同一节点上会导致长上下文 prefill 严重干扰 decoding 的 TBT SLO。

MOONCAKE 的核心命题是：能否通过构建一个跨节点的分布式 KVCache 全局缓存，以更多存储资源换取更少冗余计算，同时在解耦架构下实现 KVCache 感知的全局调度？

## 数据与任务定义

### 工作负载

论文使用三类工作负载进行评估（统计见表 2）：

| 工作负载     | 平均输入长度 | 平均输出长度 | 缓存命中率 | 请求到达模式 | 请求数 |
| ------------ | ------------ | ------------ | ---------- | ------------ | ------ |
| Conversation | 12,035       | 343          | 40%        | 时间戳回放   | 12,031 |
| Tool & Agent | 8,596        | 182          | 59%        | 时间戳回放   | 23,608 |
| Synthetic    | 15,325       | 149          | 66%        | Poisson 过程 | 3,993  |

- Conversation 和 Tool & Agent 均采样自 Kimi 线上推理集群的 1 小时 trace。
- Synthetic 工作负载由 ShareGPT、Leval（长上下文 benchmark）和 LooGLE（长文本 QA/摘要数据集）按 1:1:1 比例混合构建。

### SLO 指标

- TTFT 阈值：30 s
- TBT 阈值：100 ms / 200 ms / 300 ms（按场景分三档）
- 有效请求：同时满足 TTFT 和 TBT 阈值的请求
- 有效请求容量：有效请求占总请求的比例

### 实验硬件

- 每节点：8 × NVIDIA A800-SXM4-80GB GPU + 4 × 200 Gbps RDMA NIC
- 测试规模：16 节点（端到端实验）
- 基准模型：LLaMA3-70B dummy model（复用 LLaMA3-70B 架构参数）

### 基线系统

- vLLM v0.5.1
- vLLM + prefix caching
- vLLM + chunked prefill

## 方法主线

### 总览

MOONCAKE 采用三层解耦架构：

1. **P/D 解耦**：将 prefill 节点和 decoding 节点分离为两个独立资源池
2. **KVCache 解耦**：将 CPU DRAM、SSD 和 RDMA NIC 池化为分布式 KVCache 存储层（MOONCAKE Store）
3. **调度解耦**：全局调度器 Conductor 以 KVCache 为中心进行请求分发

### 机制流程

![MOONCAKE 整体架构：KVCache 中心的 Conductor 调度器连接 Prefill Pool、Decoding Pool 和 Mooncake Store 三层解耦组件](images/page_003_fig_figure_2.png)
*Figure 2: MOONCAKE Architecture.*

一条推理请求在 MOONCAKE 中的完整处理流程（见 Figure 3）分为以下四步：

**Step 1 — KVCache 复用（KVCache Reuse）**

- 输入：请求的原始输入token、可复用的前缀缓存块标识（block key）、为该请求分配的完整缓存块标识
- 操作：Conductor 选择一对 prefill 节点组和 decoding 节点后，prefill 节点根据前缀缓存块标识将对应的 KVCache 从远程 CPU 内存加载到 GPU HBM
- 输出：prefill 节点的 GPU HBM 中已加载可复用的前缀 KVCache，准备好启动增量 prefill
- 若无前缀缓存命中则跳过此步骤。节点选择需同时平衡三个目标：最大化缓存复用、均衡 prefill 节点负载、满足 TTFT SLO。

**Step 2 — 增量 Prefill（Incremental Prefill）**

- 输入：已加载的前缀 KVCache + 原始输入中未缓存的部分
- 操作：prefill 节点利用前缀缓存完成 prefill 阶段，仅对尚未命中缓存的token进行增量计算；若未命中缓存的token数量超过阈值（通常 >1000），则将 prefill 切分为多个 chunk，以 chunked pipeline parallelism (CPP) 方式跨多节点流水线执行。新生成的增量 KVCache 逐层回存至 CPU 内存。
- 输出：完整的请求 KVCache（前缀 + 增量），异步流向 decoding 节点

**Step 3 — KVCache 传输（KVCache Transfer）**

- 输入：prefill 节点 CPU 内存中的增量 KVCache（逐层产生）
- 操作：MOONCAKE Store 的传输引擎通过 RDMA 将每层产生的 KVCache 异步传输至目标 decoding 节点的 CPU 内存。内部按 16 KB 粒度切片，利用拓扑感知路径选择和多个 RDMA NIC 并行传输。
- 输出：decoding 节点 CPU 内存中的完整 KVCache
- 此步骤与 Step 2 的增量 prefill 重叠执行，以流式传输方式减少等待时间。

**Step 4 — Decoding**

- 输入：decoding 节点 CPU 内存中的完整 KVCache
- 操作：KVCache 从 CPU 内存加载至 GPU HBM 后，请求加入 continuous batching 的下一批次，自回归生成输出token
- 输出：模型生成的输出token 序列
- Decoding 节点由 Conductor 根据当前负载预选，确保不违反 TBT SLO。

![推理实例工作流：KVCache 复用 → 增量 Prefill → KVCache 传输 → Decoding 四个阶段](images/page_005_fig_figure_3.png)
*Figure 3: Workflow of inference instances.*

### MOONCAKE Store：分布式 KVCache 存储

**缓存管理**：所有 KVCache 以分页块（paged block）形式存储在分布式缓存池中。块大小由模型规模和最优网络传输大小决定，通常为 16–512 token。每个块附带由自身哈希和前缀共同决定的哈希 key 以支持去重。同一哈希 key 可在不同节点上有多副本以缓解热点访问延迟。缓存池满时采用 LRU 策略淘汰（正在被访问的块除外）。

**传输引擎核心设计**：

- **拓扑感知路径选择**：每个服务器生成拓扑矩阵，将 NIC 分为"首选"和"备选"列表。首选同 NUMA 节点或同 PCIe Switch 下的 NIC，避免跨 UPI/PCIe Switch 的带宽瓶颈。
- **多切片并行传输**：单个请求的传输内部以 16 KB 切片粒度划分，不同切片可使用不同路径，多个 RDMA NIC 协同工作。
- **端点池化**：采用 SIEVE 算法管理连接驱逐，限制活跃连接数上限。
- **故障处理**：自动检测不可用连接并切换到备选可达路径，支持 RDMA context 和 completion queue 的临时故障规避。

### Prefill Pool：Chunked Pipeline Parallelism

MOONCAKE 选择维持 prefill 节点与 decoding 节点的分离，而非采用 chunked prefill 将二者合并在同一节点，原因有二：(1) 在线服务有更严格的 SLO，chunked prefill 虽减少了解码干扰但难以同时最大化 prefill 阶段的 MFU 和满足 decoding 阶段的 TBT SLO；(2) 长上下文场景下，输入token 可达输出token 的 10–100 倍，需跨节点并行加速 prefill。

MOONCAKE 采用 CPP 方案：将 prefill 集群中每 X 个节点组成一个流水线 prefill 节点组，每个请求的输入token 按 prefill_chunk 切分，不同 chunk 可同时在不同节点上处理。相比序列并行（SP），CPP 仅在流水线阶段边界需要跨节点通信（可与计算重叠），MFU 更高且与 KVCache 传输的网络资源竞争更少。CPP 此前仅在训练系统中被探索，这是首次在推理阶段应用。

### 调度算法

**Prefill 全局调度（Algorithm 1）**：

核心逻辑：对每个新请求，将其 prompt 中各个token对应的缓存块键（block key）与每个 prefill 实例的缓存键逐一比较，找到前缀匹配长度（prefix_len）。然后基于请求长度和 prefix_len 用离线多项式回归模型估计预填充执行时间，加上该实例上当前排队的预估等待时间，得到该实例上的预估 TTFT。将请求分配给预估 TTFT 最短的实例。如果预估算出的最优情况仍无法满足 SLO，直接返回 HTTP 429。

**缓存负载均衡**：

论文提出一个启发式热点自动迁移方案：当请求因实例负载过高而未路由到前缀匹配最长的实例时，Conductor 将缓存位置和请求转发给备用实例（如果估算的额外 prefill 时间小于传输时间），备用实例主动从缓存持有者拉取 KVCache 并本地存储。更重要的是，当最佳远端前缀匹配长度不超过当前本地可复用前缀乘以一个阈值时，倾向于直接计算而非远程传输。这两种策略在降低 prefill 时间的同时，自动实现了热点缓存的复制和扩散。实验表明，全局缓存感知调度（含缓存负载均衡）相比局部缓存感知调度平均 TTFT 再降低 14%。

## 关键结果

### 数学分析：存储换计算的条件

论文给出了 KVCache 复用收益的数学条件。prefill 阶段 FLOPS 为：

$$flops(n) = l \times (a n^2 d + b n d^2)$$

复用长度为 $p$ 的前缀 KVCache 后，大约节省 $l \times (a p^2 d + b p d^2)$ 的计算量。但需要传输大小为 $p \times l \times (2 \times d / gqa) \times s$ 的缓存数据。KVCache 复用在 TTFT 上有利的条件是：

$$G > \frac{2 d s}{gqa \times (a p d + b d^2)}$$

其中 $G$ 为平均计算吞吐量。对 LLaMA3-70B + 8×A800 配置，假设前缀长度 8192，所需最小带宽 $B$ 约为 6 GB/s（A800）/ 19 GB/s（H800）。在实际部署中，单张 100 Gbps NIC 即可满足需求。

### 端到端有效请求容量

使用 16 节点集群，在三类工作负载不同 TBT SLO 阈值下的有效请求容量提升（相比 vLLM）：

| 工作负载     | TBT 100ms | TBT 200ms | TBT 300ms |
| ------------ | --------- | --------- | --------- |
| Conversation | +498%     | +157%     | +59%      |
| Tool & Agent | +64%      | +42%      | +22%      |
| Synthetic    | +62%      | +40%      | +28%      |

- 在 Conversation 负载下 MOONCAKE 优势最大，因为输入长度变化大、输出较长，vLLM 的 prefill/decoding 耦合导致严重的 TBT 波动。
- Synthetic 负载下约 20% 的 vLLM 请求 TBT 超过 300 ms，而 MOONCAKE 大多数请求维持 TBT < 100 ms。

### Prefill GPU 时间节省

相比 vLLM，MOONCAKE 的 prefill GPU 时间在 Conversation、Tool & Agent、Synthetic 三种负载下分别降低 36%、53%、64%。相比 vLLM + prefix caching 也有 1.40×–2.59× 的优势，原因在于局部缓存容量不足（HBM 中只能存少量 KVCache）且无法跨节点共享。

### 全局缓存 vs 局部缓存

- 局部缓存（单节点 3M token 容量）在多数场景下达不到理论最大命中率的 50%。
- 达到接近 100% 理论最大化命中率需要约 50M token 容量，至少需汇聚约 20 个节点的 DRAM。
- 实际工作负载实验中，全局缓存相比局部缓存的缓存命中率最高提升 136%（2.36×），prefill 计算时间最多降低 48%。

### 传输引擎性能

- 传输 40 GB 数据（LLaMA3-70B 128k token 对应的 KVCache 大小）：4×200 Gbps 配置下达 87 GB/s，8×400 Gbps 配置下达 190 GB/s。
- 相较 TCP 方案分别快约 2.4× 和 4.6×，相较 Gloo 方案快 7.5× 和 16.2×。
- 带宽需求实验表明，当总通信带宽超过 100 Gbps 时，系统平均 TTFT 保持在 2 s 以下，显著低于重计算的基线。

### P/D 节点配比

固定 16 节点总数，变换 prefill/decoding 节点配比。实验表明 P/D 配比约 1:1（8P8D）时达到最高有效请求容量，prefill 和 decoding 集群负载相对均衡。在实际部署中，线上流量的统计特征通常稳定，因此选择固定配比并持续监控负载，仅在大幅波动时切换节点角色。

## 深度分析

### 为什么全局缓存有效？

全局缓存的核心优势来自两个层面：

1. **容量放大**：单节点即使预留 1 TB DRAM 也只能存约 3M token 的 KVCache，而跨节点汇聚后可线性扩展至数十 M token。缓存命中率与容量直接相关（Figure 9 展示了随容量增长命中率提升的趋势曲线）。
2. **热点分散**：在多租户多会话场景下，不同请求的前缀热点分布在不同的 prefill 节点上。通过缓存负载均衡机制，热点 KVCache 自动扩散复制到更多节点（Figure 11 展示了 top-100 热点 key 在系统稳定后的高副本数），减少了单点访问拥塞。

### 为什么 P/D 分离优于 chunked prefill？

争议点在于 Sarathi-Serve 等工作认为 chunked prefill 已经能缓解 prefill 对 decoding 的干扰，P/D 分离带来的额外通信开销可能不值得。MOONCAKE 的反驳论据：

- chunked prefill 仍然在同一节点上交替执行 prefill chunk 和 decoding batch，难以同时最大化 prefill MFU 和满足 TBT SLO。
- 通过高性能传输引擎（190 GB/s），P/D 分离的通信开销可以被有效隐藏（与 prefill 重叠执行）。
- 长上下文场景下，prefill 需要跨节点并行（CPP），P/D 合并的节点架构灵活性不足。

### CPP vs SP 的选择

CPP 相比 SP 的核心优势：(1) 仅在流水线阶段边界需要跨节点通信，且可与计算重叠，MFU 损失更小；(2) 无需弹性扩缩，对短上下文自动退化为单节点 TP，避免了频繁的节点重配置。但论文未给出 CPP 与 SP 的直接性能对比数据，这是一个遗憾。

### 生产部署验证

论文声称 MOONCAKE 已在 Kimi 的线上集群运行，使 A800 和 H800 集群分别多处理 115% 和 107% 的请求。这是系统论文中最强的证据类型——来自真实生产环境的统计数据。但需注意，这些数字来自与前代 vLLM 系统的对比，且基数不透明（论文未说明"前代系统"的具体配置和调优程度）。

## 局限

1. **单模型验证**：所有实验基于 LLaMA3-70B 的 dummy model，未在其他模型架构（如 MoE、非 LLaMA 系列）上验证。不同模型的 KVCache 大小、prefill/decoding 计算比差异可能影响结论的普适性。

2. **KVCache 压缩未被纳入**：论文在 Related Work 中提到 KVCache 压缩技术（quantization、cross-layer attention 等）是正交优化方向，但未评估这些技术在 MOONCAKE 架构下的叠加效果。压缩后更小的 KVCache 可能弱化全局缓存的容量优势。

3. **P/D 固定配比的局限**：虽然实验表明 1:1 配比在当前负载下最优，但工作负载特征变化（如输出长度分布变化）可能导致最优配比漂移，文中提到了节点角色切换但未给出自动调整的具体机制和切换开销。

4. **未与 DistServe 等同期工作直接对比**：DistServe (OSDI '24) 等同期 P/D 解耦系统与 MOONCAKE 有相似的架构动机，但实验部分未进行直接的苹果到苹果对比。论文在 Related Work 中提及了这些工作但未给出对比数据。

5. **预热和缓存建立过程未充分讨论**：全局缓存的优势依赖缓存命中率，而命中率的建立需要时间。论文在 steady-state 条件下评估，但冷启动场景（新集群上线、缓存清空后）下的性能退化未量化。

6. **成本分析缺失**：论文未对 MOONCAKE Store 所需的额外 DRAM/SSD 资源做成本效益分析。"存储换计算"在经济层面的 trade-off（更多 DRAM 的成本 vs 更多 GPU 空闲时间的成本）未被量化。

## 我的笔记

### 论文定位

MOONCAKE 是一篇典型的工业系统论文，属于 FAST——存储系统顶会。核心理念（disaggregated KVCache + P/D separation）在推理系统领域已有不少同期工作（Splitwise、DistServe、CachedAttention 等），MOONCAKE 的独特性在于：(1) 将分布式缓存做到生产级规模（PB 级、千节点）；(2) 实现了完整的高性能 RDMA 传输引擎；(3) 在真实大规模部署中验证了效果。

### 对推理系统设计的启示

- **存储与计算的权衡在推理场景中需要重新审视**：传统观点认为分布式缓存会因传输带宽瓶颈而不可行，但论文用数学分析和实验证明了在当今 GPU 集群网络配置下（100+ Gbps NIC per GPU），全局缓存的收益可以远超传输成本。
- **调度器的设计复杂度从"负载均衡"升级为"缓存+负载联合优化"**：MOONCAKE 的 Conductor 需要同时考虑缓存命中、节点负载、传输延迟和 SLO 约束，这比传统 load-balancing 调度器复杂得多。
- **RDMA 在推理基础设施中的重要性上升**：随着模型和上下文的增大，KVCache 传输成为新的瓶颈。MOONCAKE 的传输引擎设计（拓扑感知、多切片并行）为类似系统提供了参考实现。

### 可复用的工程思路

1. CPU DRAM 作为 KVCache 存储介质的可行性在 100+ Gbps NIC 条件下得到验证，可以作为自建推理集群的参考架构。
2. 启发式热点复制策略（不在最长命中的实例上执行 → 由备用实例拉取 → 本地保留副本）是一种简洁有效的热点管理方式，避免了复杂的预测模型。
3. CPP 用于长上下文 prefill 是一个被低估的方向，尤其在 128k+ 上下文的场景下，相比 SP 在通信效率上有天然优势。

### 值得关注的后续问题

- MOONCAKE 的架构在 MoE 模型上的表现如何？MoE 模型每次推理激活的参数量不同，KVCache 的生成和存储模式可能有较大差异。
- KVCache 压缩技术（如 KVQuant、KIVI）与 MOONCAKE 的全局缓存叠加能产生多大的复合收益？
- 在实际部署中，P/D 配比的自动动态调整（而非当前的手动固定）能带来多大的额外增益？

## 引用

1. Ruoyu Qin, Zheming Li, Weiran He, Jialei Cui, Feng Ren, Mingxing Zhang, Yongwei Wu, Weimin Zheng, and Xinran Xu. **Mooncake: Trading More Storage for Less Computation — A KVCache-centric Architecture for Serving LLM Chatbot.** In *Proceedings of the 23rd USENIX Conference on File and Storage Technologies (FAST '25)*, Santa Clara, CA, USA, pages 155–170, February 2025. USENIX Association.

- 论文链接: <https://www.usenix.org/conference/fast25/presentation/qin>
- 代码仓库: <https://github.com/kvcache-ai/Mooncake>

```bibtex
@inproceedings{qin2025mooncake,
  title     = {Mooncake: Trading More Storage for Less Computation -- A KVCache-centric Architecture for Serving LLM Chatbot},
  author    = {Qin, Ruoyu and Li, Zheming and He, Weiran and Cui, Jialei and Ren, Feng and Zhang, Mingxing and Wu, Yongwei and Zheng, Weimin and Xu, Xinran},
  booktitle = {23rd USENIX Conference on File and Storage Technologies (FAST '25)},
  year      = {2025},
  url       = {https://www.usenix.org/conference/fast25/presentation/qin}
}
```
