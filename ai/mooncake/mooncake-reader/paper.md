# Mooncake: Trading More Storage for Less Computation — A KVCache-centric Architecture for Serving LLM Chatbot

**Authors:** Ruoyu Qin (Moonshot AI & Tsinghua), Zheming Li, Weiran He, Jialei Cui, Feng Ren, Mingxing Zhang, Yongwei Wu, Weimin Zheng, Xinran Xu
**Venue:** 23rd USENIX Conference on File and Storage Technologies (FAST '25), Feb 25–27, 2025, Santa Clara, CA
**DOI/URL:** https://www.usenix.org/conference/fast25/presentation/qin

---

## 术语表 / Terminology Ledger

| 规范术语 | 首次定义 | 中文翻译 | 论文中变体 |
|---|---|---|---|
| KVCache | Key-Value Cache | 键值缓存 | KV Cache, KV cache |
| MOONCAKE | — | 系统名称（不翻译） | Mooncake |
| SLO | Service Level Objective | 服务水平目标 | SLOs |
| TTFT | Time to First Token | 首 token 延迟 | — |
| TBT | Time Between Tokens | token 间延迟 | — |
| MFU | Model FLOPs Utilization | 模型 FLOPs 利用率 | — |
| Prefill | Prefill stage | 预填充阶段 | prefill stage |
| Decoding | Decoding stage | 解码阶段 | decoding stage |
| P/D Disaggregation | Prefill/Decoding Disaggregation | 预填充/解码分离架构 | P/D disaggregation |
| Conductor | Global Scheduler | 全局调度器 | — |
| RDMA | Remote Direct Memory Access | 远程直接内存访问 | — |
| CPP | Chunked Pipeline Parallelism | 分块流水线并行 | — |
| SP | Sequence Parallelism | 序列并行 | — |
| TP | Tensor Parallelism | 张量并行 | — |
| HBM | High Bandwidth Memory | 高带宽显存 | VRAM, GPU memory |
| Goodput | Good throughput | 有效吞吐量 | effective request capacity |

---

## 页面索引 / Page Index

| 页码 | 内容 |
|---|---|
| 1 | 标题、摘要 |
| 1–2 | §1 Introduction（引言） |
| 2–3 | §2 Preliminary and Problem Definition（预备知识与问题定义，含 Table 1） |
| 3–5 | §3 Design of MOONCAKE（系统设计，含 §3.2.3 Network Setup & Failure Handling） |
| 5–6 | §4 Scheduling（调度策略，含 Algorithm 1） |
| 6–12 | §5 Evaluation（实验评估，含 §5.3.3 Cache Replica） |
| 12 | §6 Related Work（相关工作） |
| 12 | §7 Conclusion（结论） |
| 12 | Acknowledgments（致谢） |
| 12–14 | References（参考文献 [1]–[43]） |

---

## §0 Abstract / 摘要

<a id="S001"></a>
**Source:** p.1, Abstract

**Original:**
MOONCAKE is the serving platform for Kimi, an LLM chatbot service developed by Moonshot AI. This platform features a KVCache-centric disaggregated architecture that not only separates prefill and decoding clusters but also efficiently utilizes the underexploited CPU, DRAM, SSD and NIC resources of the GPU cluster to establish a disaggregated KVCache. At the core of MOONCAKE is its KVCache-centric global cache and a scheduler designed to maximize throughput while adhering to stringent latency-related Service Level Objectives (SLOs). Our experiments demonstrate that MOONCAKE excels in scenarios involving long-context inputs. In tests using real traces, MOONCAKE increases the effective request capacity by 59%–498% when compared to baseline methods, all while complying with SLOs. Currently, MOONCAKE is operational across thousands of nodes, processing over 100 billion tokens daily. In practical deployments, MOONCAKE's innovative architecture enables Kimi to handle 115% and 107% more requests on NVIDIA A800 and H800 clusters, respectively, compared to previous systems.

**中文:**
MOONCAKE 是 Kimi（月之暗面开发的 LLM 聊天机器人服务）的推理服务平台。该平台采用以 KVCache 为中心的解耦架构，不仅将 prefill 集群与 decoding 集群分离，还高效利用 GPU 集群中未被充分利用的 CPU、DRAM、SSD 和网卡资源，构建了一个分散式 KVCache 存储层。MOONCAKE 的核心是其以 KVCache 为中心的全局缓存，以及一个在满足严格延迟 SLO 的前提下最大化吞吐量的调度器。实验表明，MOONCAKE 在长上下文输入场景中表现突出。在基于真实请求轨迹的测试中，相比于基线方法，MOONCAKE 在满足 SLO 的前提下将有效请求容量提升了 **59%–498%**。目前，MOONCAKE 已在数千个节点上运行，每天处理超过 **1000 亿个 token**。在实际部署中，MOONCAKE 的创新架构使 Kimi 在 A800 和 H800 集群上分别能多处理 **115%** 和 **107%** 的请求。

---

<a id="S002"></a>
**Source:** p.1, Figure 1 caption

**Original:**
Figure 1: The experiment of the effective request capacity of MOONCAKE under the real-world conversation workload and different TBT SLOs. In this experiment, MOONCAKE and three baseline systems utilize 16 8×A800 nodes each.

**中文:**
图 1：在真实对话工作负载和不同 TBT SLO 下，MOONCAKE 的有效请求容量实验。本实验中，MOONCAKE 和三个基线系统各使用 16 个 8×A800 节点。

> **Figure 1 关键发现:** 在 TBT=100ms 时，MOONCAKE 有效请求容量比 vLLM 高约 5 倍；随着 TBT SLO 放宽至 1s，优势仍保持在 +59%。

---

## §1 Introduction / 引言

<a id="S003"></a>
**Source:** p.1, §1 ¶1

**Original:**
With the rapid adoption of large language models (LLMs) in various scenarios, the workloads for LLM serving have become significantly diversified. These workloads differ in input/output length, distribution of arrival, and, most importantly, demand different kinds of Service Level Objectives (SLOs). As a Model as a Service (MaaS) provider, one of the primary goals of Kimi is to solve an optimization problem with multiple complex constraints. The optimization goal is to maximize overall effective throughput, which directly impacts revenue, while the constraints reflect varying levels of SLOs. These SLOs typically involve meeting latency-related requirements, mainly the time to first token (TTFT) and the time between tokens (TBT).

**中文:**
随着大语言模型在各种场景中的快速普及，LLM 推理服务的工作负载变得越来越多样化。这些工作负载在输入/输出长度、请求到达分布以及（最重要的）对服务水平目标（SLO）的需求上各不相同。作为模型即服务（MaaS）提供商，Kimi 的核心目标之一是求解一个带多重复杂约束的优化问题：优化目标是最大化整体有效吞吐量（直接影响营收），约束条件则反映了不同级别的 SLO。这些 SLO 主要包括延迟相关指标：首 token 时间（TTFT）和 token 间延迟（TBT）。

---

<a id="S004"></a>
**Source:** p.1, §1 ¶2

**Original:**
To achieve this goal, a prerequisite is to make the best use of the various kinds of resources available in the GPU cluster. Specifically, although GPU servers are currently provided as highly integrated nodes (e.g., DGX/HGX supercomputers), it is necessary to decouple and restructure them into several disaggregated resource pools, each optimized for different but collaborative goals. For example, many other researchers have suggested separating prefill servers from decoding servers, because these two stages of LLM serving have very different computational characteristics.

**中文:**
实现这一目标的前提是充分利用 GPU 集群中各种可用资源。具体来说，虽然 GPU 服务器目前以高度集成的节点形式提供（如 DGX/HGX 超级计算机），但有必要将其解耦重组为多个分散式资源池，每个池针对不同但协作的目标进行优化。例如，此前已有研究者提出将 prefill 服务器与 decoding 服务器分离，因为这两个阶段的 LLM 推理具有截然不同的计算特性。

---

<a id="S005"></a>
**Source:** p.1, §1 ¶3

**Original:**
Further advancing this disaggregation strategy, we have engineered a disaggregated KVCache by pooling CPU, DRAM, SSD and RDMA resources of the GPU cluster, referred to as MOONCAKE Store. This novel architecture harnesses underutilized resources to enable efficient near-GPU prefix caching, significantly enhancing the global cache capacity and internode transfer bandwidth. The resultant distributed KVCache system embodies the principle of **trading more storage for less computation**. Thus, as demonstrated in Figure 1, it substantially boosts Kimi's maximum throughput capacity in meeting the required SLOs for many important real-world scenarios.

**中文:**
在此解耦策略的基础上，我们进一步工程化了一个分散式 KVCache——将 GPU 集群的 CPU、DRAM、SSD 和 RDMA 资源池化，称为 **MOONCAKE Store**。这一新颖的架构利用未充分利用的资源来实现高效的近 GPU 前缀缓存，显著提升了全局缓存容量和节点间传输带宽。由此构建的分散式 KVCache 系统体现了「**用更多存储换取更少计算**」的原则。如图 1 所示，在许多重要的真实场景中，它大幅提升了 Kimi 在满足 SLO 前提下的最大吞吐能力。

---

<a id="S006"></a>
**Source:** p.1–2, §1 ¶4

**Original:**
Later in this paper, we will first delve into a mathematical analysis of this strategy's benefits for LLM serving and empirically assess its efficacy using real-world data (§2.2). Then, we will detail the design choices made in implementing this petabyte-level disaggregated cache, which is interconnected via an RDMA network up to 8×400 Gbps (§3.2).

**中文:**
本文后续将首先从数学上分析该策略对 LLM 推理服务的好处，并结合真实数据评估其有效性（§2.2）。然后，我们将详细介绍实现这一由 RDMA 网络互联（带宽最高 8×400 Gbps）的 PB 级分散式缓存所做的设计选择（§3.2）。

---

<a id="S007"></a>
**Source:** p.2, §1 ¶5

**Original:**
Building on this idea, we also found that the scheduling of KVCache is central to LLM serving, and hence propose a corresponding disaggregated architecture. Figure 2 presents our current KVCache-centric disaggregated architecture for LLM serving, named MOONCAKE. For each request, the global scheduler (Conductor) will select a pair of prefill and decoding instances and schedule the request in the following steps: 1) transfer as much reusable KVCache as possible to the selected prefill instance; 2) complete the prefill stage in chunks/layers and continuously stream the output KVCache to the corresponding decoding instance; 3) load the KVCache and add the request to the continuous batching process at the decoding instance for generating request outputs.

**中文:**
基于这一思路，我们还发现 KVCache 的调度是 LLM 推理服务的核心，因此提出了相应的解耦架构。图 2 展示了我们当前以 KVCache 为中心的 LLM 推理分离式架构——**MOONCAKE**。对每个请求，全局调度器（Conductor）会选择一个 prefill 实例和一个 decoding 实例，并按照以下步骤调度请求：1) 将尽可能多的可复用 KVCache 传输到选定的 prefill 实例；2) 以分块/分层方式完成 prefill 阶段，并将输出 KVCache 持续流式传输到对应的 decoding 实例；3) 加载 KVCache 并将请求加入 decoding 实例的连续批处理（continuous batching）流程中生成输出。

---

<a id="S008"></a>
**Source:** p.2, §1 ¶6

**Original:**
Although this process seems straightforward, the selection policy is complex due to many restrictions. In the prefill stage, the main objective is to reuse the KVCache as much as possible to avoid redundant computation. However, the distributed KVCache pool faces challenges in terms of both capacity and access latency. Thus Conductor is responsible for scheduling requests with KVCache-awareness and executing scheduling operations such as swapping and replication accordingly. The hottest blocks should be replicated to multiple nodes to avoid fetching congestion, while the coldest ones should be swapped out to reduce reserving costs. In contrast, the decoding stage has different optimization goals and constraints. The aim is to aggregate as many tokens as possible in a decoding batch to improve the Model FLOPs Utilization (MFU). However, this objective is restricted not only by the TBT SLO but also by the total size of aggregated KVCache that can be contained in the VRAM.

**中文:**
尽管这个流程看似简单，但由于存在诸多约束，选择策略实际上非常复杂。在 prefill 阶段，主要目标是尽可能多地复用 KVCache 以避免冗余计算。然而，分散式 KVCache 池同时面临容量和访问延迟两方面的挑战。因此，Conductor 需要以 KVCache 感知的方式调度请求，并相应执行交换（swap）和复制（replication）等调度操作：最热的 block 应该复制到多个节点以避免获取拥塞，最冷的 block 则应换出以降低保留成本。相比之下，decoding 阶段有不同的优化目标和约束：其目标是在一个 decoding batch 中聚合尽可能多的 token 以提高模型 FLOPs 利用率（MFU），但该目标不仅受 TBT SLO 限制，还受 VRAM 中可容纳的聚合 KVCache 总大小的限制。

---

<a id="S009"></a>
**Source:** p.2, §1 ¶7

**Original:**
In §4, we will detail our KVCache-centric request scheduling algorithm, which balances instance loads and user experience as measured by TTFT and TBT SLOs. This includes a heuristic-based automated hotspot migration scheme that replicates hot KVCache blocks without requiring precise predictions of future KVCache usage. Experimental results show that our KVCache-centric scheduling can significantly lower TTFT in real-world scenarios.

**中文:**
在 §4 中，我们将详细阐述以 KVCache 为中心的请求调度算法，该算法在实例负载和以 TTFT/TBT SLO 衡量的用户体验之间取得平衡。其中包括一个基于启发式的自动热点迁移方案——无需精确预测未来的 KVCache 使用情况即可复制热 KVCache block。实验结果表明，以 KVCache 为中心的调度能在真实场景中显著降低 TTFT。

---

<a id="S010"></a>
**Source:** p.2, §1 ¶8

**Original:**
We will also describe the main design choices made during its implementation, especially those not covered in current research. For example, regarding P/D disaggregation, there are currently debates on its feasibility in large-scale practice due to bandwidth requirements and trade-offs associated with chunked prefill (e.g., Sarathi-Serve). We demonstrate, through comparison with vLLM, that with a highly optimized transfer engine, the communication challenges can be managed, and P/D disaggregation is preferable for scenarios with stringent SLO limits (§5.2). Additionally, we discuss how to implement a separate prefill node pool that seamlessly handles the dynamic distribution of context length. We employ a chunked pipeline parallelism (CPP) mechanism to scale the processing of a single request across multiple nodes, which is necessary for reducing the TTFT of long-context inputs. Compared to traditional sequence parallelism (SP) based solutions, CPP reduces network consumption and simplifies the reliance on frequent elastic scaling (§3.3).

**中文:**
我们还将描述实现过程中的主要设计选择，特别是当前研究中尚未涉及的部分。例如，关于 P/D 解耦，目前对其在大规模实践中的可行性存在争议——主要质疑来自带宽需求以及与分块 prefill（如 Sarathi-Serve）之间的权衡。我们通过与 vLLM 的对比实验证明：借助高度优化的传输引擎，通信挑战可以克服，且 P/D 解耦在 SLO 要求严格的场景下更优（§5.2）。此外，我们讨论了如何实现一个能无缝处理上下文长度动态分布的独立 prefill 节点池——采用分块流水线并行（CPP）机制将单个请求的处理跨多节点扩展，这对降低长上下文输入的 TTFT 至关重要。与传统的序列并行（SP）方案相比，CPP 减少了网络消耗并简化了对频繁弹性扩缩的需求（§3.3）。

---

<a id="S011"></a>
**Source:** p.2, §1 ¶9

**Original:**
MOONCAKE is currently the serving platform of Kimi and has successfully handled exponential workload growth (more than 100 billion tokens a day). According to our historical statistics, the innovative architecture of MOONCAKE enables Kimi to handle 115% and 107% more requests on the A800 and H800 clusters, respectively, compared to previous systems.

**中文:**
MOONCAKE 目前是 Kimi 的推理服务平台，已成功应对指数级增长的工作负载（每日超过 1000 亿 token）。根据历史统计，MOONCAKE 的创新架构使 Kimi 在 A800 和 H800 集群上分别能多处理 115% 和 107% 的请求，相比之前的系统。

---

<a id="S012"></a>
**Source:** p.2, §1 ¶10 (开源承诺)

**Original:**
To ensure the reproducibility of our results while safeguarding proprietary information, we also provide detailed experimental outcomes using a dummy model mirroring the architecture of LLaMA3-70B, based on replayed traces of actual workloads. These traces, along with the KVCache transfer infrastructure of MOONCAKE, are open-sourced at https://github.com/kvcache-ai/Mooncake.

**中文:**
为确保结果可复现同时保护专有信息，我们还提供了使用与 LLaMA3-70B 架构相同的虚拟模型、基于实际工作负载重放轨迹的详细实验结果。这些 trace 数据以及 MOONCAKE 的 KVCache 传输基础设施已在 https://github.com/kvcache-ai/Mooncake 开源。

---

## §2 Preliminary and Problem Definition / 预备知识与问题定义

### §2.1 Service Level Objectives of LLM Serving

<a id="S013"></a>
**Source:** p.2, §2.1 ¶1

**Original:**
Modern large language models (LLMs) are based on the Transformer architecture, which utilizes attention mechanisms and multilayer perceptrons (MLP) to process input. Popular Transformer-based models, such as GPT and LLaMA, employ a decoder-only structure. Each inference request is logically divided into two stages: the prefill stage and the decoding stage. During the prefill stage, all input tokens are processed in parallel, and hence it is typically computationally intensive. This stage generates the first output token while storing intermediate results of computed keys and values, referred to as the KVCache. The decoding stage then uses this KVCache to autoregressively generate new tokens. It processes only one token at a time per batch due to the limitation of autoregressive generation, which makes it memory-constrained and causes computation time to increase sublinearly with batch size. Thus, a widely used optimization in the decoding stage is continuous batching.

**中文:**
现代大语言模型基于 Transformer 架构，利用注意力机制和多层感知机（MLP）处理输入。流行的 Transformer 模型（如 GPT、LLaMA）采用 decoder-only 结构。每次推理请求在逻辑上分为两个阶段：**prefill 阶段**和 **decoding 阶段**。prefill 阶段中，所有输入 token 并行处理，因此通常是计算密集型的，该阶段生成第一个输出 token 并存储中间计算结果（键和值），称为 KVCache。decoding 阶段则利用该 KVCache 自回归地生成新 token——受限于自回归生成的特性，每个 batch 每次只能处理一个 token，使其成为内存密集型阶段，且计算时间随 batch size 亚线性增长。因此，decoding 阶段广泛使用的一种优化是 **continuous batching**。

---

<a id="S014"></a>
**Source:** p.2-3, §2.1 ¶2

**Original:**
Due to the distinct characteristics of the prefill and decoding stages, MaaS providers set different metrics to measure their corresponding Service Level Objectives (SLOs). Specifically, the prefill stage is mainly concerned with the latency between the request arrival and the generation of the first token, known as the time to first token (TTFT). On the other hand, the decoding stage focuses on the latency between successive token generations for the same request, referred to as the time between tokens (TBT).

**中文:**
由于 prefill 和 decoding 阶段具有截然不同的特性，MaaS 提供商设定了不同的指标来衡量对应的 SLO。具体而言：prefill 阶段主要关注请求到达到首 token 生成的延迟——TTFT；decoding 阶段则关注同一请求中连续 token 生成之间的延迟——TBT。

---

<a id="S015"></a>
**Source:** p.3, §2.1 ¶3

**Original:**
In real deployments, if the monitor detects unmet SLOs, we need to either add inference resources or reject some incoming requests. However, due to the current contingent supply of GPUs, elastically scaling out the inference cluster is typically unfeasible. Therefore, we proactively reject requests that are predicted not to meet the SLOs to alleviate the cluster's load. Our main objective is to maximize overall throughput while adhering to SLOs, a concept referred to as goodput in other research.

**中文:**
在实际部署中，如果监控检测到 SLO 未达标，我们需要要么增加推理资源，要么拒绝部分新请求。然而，鉴于当前 GPU 供应的不确定性，弹性扩展推理集群通常不可行。因此，我们主动拒绝预测无法满足 SLO 的请求以缓解集群负载。我们的主要目标是：**在满足 SLO 的前提下最大化整体吞吐量**——这一概念在其他研究中也称为 goodput（有效吞吐量）。

---

### §2.2 More Storage for Less Computation / 更多存储换更少计算

<a id="S016"></a>
**Source:** p.3, §2.2 ¶1

**Original:**
To meet the stringent SLOs described above, a commonly adopted solution is to cache previously generated KVCache and reuse it upon finding a prefix match. However, existing approaches typically restrict caching to local HBM and DRAM, assuming that the transfer bandwidth required for global scheduling would be prohibitively high. But, as we will described later in §5.3, the capacity of local DRAM supports only up to 50% of the theoretical cache hit rate, making the design of a global cache essential. In this section, we present a mathematical analysis of the actual bandwidth necessary to benefit from this strategy, explaining why distributed caching is advantageous, especially for larger models like LLaMA3-70B.

**中文:**
为满足上述严格的 SLO，一种常见的解决方案是缓存先前生成的 KVCache 并在发现前缀匹配时复用。然而，现有方法通常将缓存限制在本地 HBM 和 DRAM 中，认为全局调度所需的传输带宽过高。但正如我们将在 §5.3 中展示的，本地 DRAM 的容量仅能支持理论缓存命中率的不到 50%，使得全局缓存设计必不可少。本节我们将从数学上分析该策略所需的实际带宽，解释为什么分散式缓存是有利的，特别是对于 LLaMA3-70B 这样的大模型。

---

<a id="E001"></a>
**Source:** p.3, Equation (1) — Prefill FLOPS

$$ \text{flops}(n) = l \cdot (a n^2 d + b n d^2) $$

> **说明:** 其中 $l$ 为层数，$n$ 为输入长度，$d$ 为模型维度，$a, b$ 为常量系数。该公式刻画了 Transformer prefill 阶段的计算量与输入长度 $n$ 的二次方关系。

---

<a id="E002"></a>
**Source:** p.3, Equation (2) — KVCache 复用收益不等式

$$ \frac{B}{G} > \frac{2ds}{\text{gqa} \cdot (apd + bd^2)} $$

> **说明:** 当满足该不等式时，复用 KVCache 不仅在 TTFT 上更优，还能节省 GPU 计算时间和成本。$B$ 为 KVCache 加载带宽，$G$ 为 GPU 计算吞吐量，$p$ 为共享前缀长度，$s$ 为张量元素大小，$\text{gqa}$ 为 grouped-query attention 中 query head 数与 kv head 数之比。

---

<a id="S017"></a>
**Source:** p.3, §2.2 ¶2

**Original:**
In such scenarios, reusing the KVCache not only reduces GPU time and costs but also enhances the user experience by improving TTFT. The criteria for bandwidth B relative to computation throughput G are more readily met with larger values of d, which is proportional to the model size. For example, when running LLaMA3-70B on a machine with 8×A800 GPUs and assuming a prefix length of 8192, Equation 2 yields a minimum required B of 6 GB/s. The requirement for B will be enlarged to 19 GB/s for an 8×H800 machine. Moreover, in practical scenarios, because the transfer stages cannot be perfectly overlapped with each other, the actual bandwidth requirement is even higher. However, as we will demonstrate in §5.4.2, a fully utilized 100 Gbps NIC per NVIDIA A800 HGX network is sufficient to meet these criteria.

**中文:**
在这些场景中，复用 KVCache 不仅能减少 GPU 计算时间和成本，还能通过降低 TTFT 来改善用户体验。带宽 $B$ 相对计算吞吐量 $G$ 的标准在模型维度 $d$ 更大时更容易满足——$d$ 与模型大小成正比。例如，在 8×A800 机器上运行 LLaMA3-70B，假设前缀长度为 8192，公式 (2) 给出的最小所需 $B$ 为 **6 GB/s**；在 8×H800 机器上则提升至 **19 GB/s**。在实际场景中，由于传输阶段无法完美相互重叠，实际带宽需求更高。但如 §5.4.2 所示，每台 A800 HGX 节点充分利用一条 100 Gbps NIC 即可满足该条件。

---

<a id="T001"></a>
**Source:** p.3, Table 1 — Notations and Parameters

| Notation | Description | Value (LLaMA3-70B, 8×A800) |
|---|---|---|
| $l$ | Number of layers | 80 |
| $d$ | Model dimension | 8192 |
| $a, b$ | Constant coefficients in Equation (1) | 4, 22 |
| $\text{gqa}$ | Num query heads / Num key-value heads | 8 |
| $s$ | Tensor element size | 2 B (BFloat16) |
| $G$ | GPU computation throughput | 8×312 TFLOPS |
| $B_{h2d}$ | Host-to-device bandwidth | 128 GB/s |
| $B_{nic}$ | NIC bandwidth | 800 Gbps |
| $n, p$ | Prompt length and matched prefix length, respectively | — |

> **中文说明:** 表 1：符号与参数。模型和机器参数按 LLaMA3-70B 和 8×A800 设置。其中 $n$ 为 prompt 长度，$p$ 为匹配的前缀长度。

---

## §3 Design of MOONCAKE / 系统设计

### §3.1 Overview / 总体架构

<a id="S018"></a>
**Source:** p.3, §3.1 ¶1

**Original:**
As depicted in Figure 2, MOONCAKE employs a disaggregated architecture that not only separates prefill from decoding nodes but also groups the CPU, DRAM, SSD, and RDMA resources of the GPU cluster to implement a disaggregated KVCache. To schedule all these disaggregated components, at its center, MOONCAKE implements a global scheduler named Conductor. Conductor is responsible for dispatching requests based on the current distribution of the KVCache and workload characteristics. MOONCAKE Store, detailed in §3.2, manages the storage and transfer of these KVCache blocks.

**中文:**
如图 2 所示，MOONCAKE 采用解耦架构——不仅将 prefill 节点与 decoding 节点分离，还将 GPU 集群的 CPU、DRAM、SSD 和 RDMA 资源整合为一个分散式 KVCache。为了调度这些解耦的组件，MOONCAKE 在中心实现了一个名为 **Conductor** 的全局调度器。Conductor 负责根据 KVCache 的当前分布和工作负载特征调度请求。MOONCAKE Store（详见 §3.2）管理这些 KVCache block 的存储和传输。

---

<a id="S019"></a>
**Source:** p.3–4, §3.1 ¶2 (四步工作流)

**Original:**
Specifically, Figure 3 demonstrates the typical workflow of a request. Once tokenizing is finished, the conductor selects a pair of prefill nodes and a decoding node, and starts a workflow comprising four steps:
1) **KVCache Reuse:** The selected prefill node receives a request that includes the raw input, the block keys of the prefix cache that can be reused, and the block keys of the full cache allocated to the request. It loads the prefix cache from remote CPU memory into GPU memory based on the prefix cache block keys to bootstrap the request.
2) **Incremental Prefill:** The prefill node completes the prefill stage using prefix cache and stores the newly generated incremental KVCache back into CPU memory. If the number of uncached input tokens exceeds a certain threshold, the prefill stage is split into multiple chunks and executed in a pipeline manner.
3) **KVCache Transfer:** MOONCAKE Store is deployed in each node to manage and transfer these caches. This step is asynchronously executed and overlapped with the above incremental prefill step, streaming the KVCache generated by each model layer to the destination decoding node's CPU memory to reduce waiting time.
4) **Decoding:** After all the KVCache is received in the CPU memory of the decoding node, the request joins the next batch in a continuous batching manner.

**中文:**
图 3 展示了一个请求的典型处理流程。完成分词后，Conductor 选择一对 prefill 节点和一个 decoding 节点，启动包含四个步骤的工作流：
1. **KVCache 复用:** 选定的 prefill 节点接收请求（含原始输入、可复用的前缀缓存 block key、分配给该请求的全量缓存 block key），从远程 CPU 内存将前缀缓存加载到 GPU 显存，启动该请求。
2. **增量 Prefill:** prefill 节点利用前缀缓存完成 prefill 阶段，将新生成的增量 KVCache 存回 CPU 内存。如果未缓存的输入 token 数超过阈值，prefill 将被拆分为多个 chunk 以流水线方式执行。
3. **KVCache 传输:** MOONCAKE Store 部署在每个节点上，异步执行此步骤并与增量 prefill 重叠，将每层的 KVCache 流式传输到目标 decoding 节点的 CPU 内存以缩短等待时间。
4. **Decoding:** decoding 节点在 CPU 内存中收到全部 KVCache 后，请求以连续批处理方式加入下一批次。

---

### §3.2 MOONCAKE Store: Cache of KVCache / KVCache 缓存系统

<a id="S020"></a>
**Source:** p.4, §3.2 ¶1

**Original:**
Central to MOONCAKE is its efficient implementation of a distributed global cache of KVCache, referred to as MOONCAKE Store. As described in §2.2, reusing cached KVCache not only cuts computation costs but also improves user experience by reducing the TTFT, particularly when the aggregated bandwidth is fully utilized. However, achieving full utilization is challenging because the bandwidth can reach up to 8×400 Gbps, comparable to DRAM bandwidth.

**中文:**
MOONCAKE 的核心是其高效的分散式全局 KVCache 实现——**MOONCAKE Store**。如 §2.2 所述，复用缓存 KVCache 不仅能降低计算成本，还能通过减少 TTFT 改善用户体验——特别是在聚合带宽被充分利用时。但实现带宽的充分利用率本身就是一个挑战，因为总带宽可达 8×400 Gbps，相当于 DRAM 带宽级别。

---

#### §3.2.1 KVCache Management / 缓存管理

<a id="S021"></a>
**Source:** p.4, §3.2.1

**Original:**
In MOONCAKE Store, all KVCache is stored as paged blocks within a distributed cache pool. The block size, i.e., the number of tokens contained in each block, is determined by the model size and the optimal network transmission size, typically ranging from 16 to 512 tokens. Each block is attached with a hash key determined by both its own hash and its prefix for deduplication. The same hash key may have multiple replicas across different nodes to mitigate hot-cache access latency, controlled by our cache-load-balancing policy described in §4.2. MOONCAKE Store allocates space for each cache block in the cache pool and logs metadata such as the block key and its address. When the cache pool is full, MOONCAKE Store employs a LRU (Least Recently Used) strategy to evict an existing cache block--unless the block is currently being accessed by an ongoing request--and overwrites the evicted block's space with the new block.

**中文:**
在 MOONCAKE Store 中，所有 KVCache 以分页 block 形式存储在分散式缓存池中。block 大小（即每个 block 包含的 token 数）由模型大小和最优网络传输大小决定，通常在 16 到 512 个 token 之间。每个 block 附有一个 hash key，由自身哈希值与其前缀共同确定以实现去重。同一 hash key 可在不同节点上有多个副本，以减轻热缓存访问延迟——这由 §4.2 中描述的缓存负载均衡策略控制。当缓存池满时，MOONCAKE Store 使用 **LRU（最近最少使用）** 策略淘汰现有缓存 block（除非该 block 正在被活跃请求访问），并用新 block 覆盖被淘汰 block 的空间。

---

#### §3.2.2 Interface / 接口

<a id="S022"></a>
**Source:** p.4, §3.2.2

**Original:**
At the higher layer, MOONCAKE Store offers object-based APIs such as put, get, and change_replica. These facilitate the caching of KVCache in a disaggregated manner, organizing mini blocks of KVCache as memory objects and enabling Conductor to adjust the number of replicas for each KVCache block to achieve higher bandwidth aggregation. These functions are supported by a set of synchronous batch transfer APIs. Transfer operations are available for both DRAM and GPU VRAM and will utilize GPU Direct RDMA when optimal, provided that the specified memory region has been pre-registered. The completion of these operations can be monitored asynchronously via the getTransferStatus API.

**中文:**
在上层，MOONCAKE Store 提供面向对象的 API，如 `put`、`get` 和 `change_replica`。这些 API 以分散式方式缓存 KVCache——将 KVCache mini block 组织为内存对象，并使 Conductor 能够调整每个 KVCache block 的副本数以实现更高的聚合带宽。这些功能由一组同步的批量传输 API 支撑。传输操作同时支持 DRAM 和 GPU VRAM，在满足最优条件（内存区域已预注册）时会使用 GPU Direct RDMA。操作完成情况可通过 `getTransferStatus` API 异步监控。

---

#### §3.2.3 Transfer Engine / 传输引擎

<a id="S023"></a>
**Source:** p.4–5, §3.2.3 ¶1

**Original:**
To efficiently implement the above APIs, a transfer engine is designed to achieve several key objectives: 1) Effectively distribute transfer tasks across multiple RDMA NIC devices; 2) Abstract the complexities of RDMA connection management from the APIs; and 3) Appropriately handle temporary network failures. This transfer engine has been meticulously engineered to fulfill each of these goals.

**中文:**
为高效实现上述 API，传输引擎的设计追求三个关键目标：1) 在多 RDMA 网卡间有效分配传输任务；2) 从 API 层抽象 RDMA 连接管理的复杂性；3) 妥善处理临时网络故障。传输引擎经过了精心的工程打磨以实现每一个目标。

---

<a id="S024"></a>
**Source:** p.5, §3.2.3 — Topology-aware path selection

**Original:**
Before processing requests, each server generates a topology matrix and broadcasts it across the cluster. This matrix categorizes network interface cards (NICs) into "preferred" and "secondary" lists for various types of memory, which types are specified during memory registration. Under normal conditions, a NIC from the preferred list is selected for transfers, facilitating RDMA operations within the local NUMA or GPU Direct RDMA through the local PCIe switch only. In case of failures, NICs from both lists may be utilized. The process involves identifying the appropriate local and target NICs based on the memory addresses, establishing a connection, and executing the data transfer. To further maximize bandwidth utilization, a single request's transfer is internally divided into multiple slices at a granularity of 16 KB. Each slice might use a different path, enabling collaborative work among all RDMA NICs.

**中文:**
在处理请求前，每台服务器生成一个**拓扑矩阵**并在集群中广播。该矩阵将网卡按各类内存（内存注册时指定类型）分为「首选」和「备选」列表。正常情况下，从首选列表中选择 NIC 进行传输，确保 RDMA 操作仅在本地 NUMA 或本地 PCIe Switch 内进行（GPU Direct RDMA）。故障时则可能同时使用两类 NIC。流程包括：根据内存地址识别合适的本地和目标 NIC → 建立连接 → 执行数据传输。为进一步最大化带宽利用率，单个请求的传输被内部分割为多个 **16 KB 粒度的 slice**，每个 slice 可使用不同路径，使所有 RDMA 网卡协同工作。

---

<a id="S025"></a>
**Source:** p.5, §3.2.3 — Endpoint management

**Original:**
MOONCAKE Store employs a pair of endpoints to represent the connection between a local RDMA NIC and a remote RDMA NIC. In practice, each endpoint includes one or more RDMA queue pair objects. Connections in MOONCAKE Store are established in an on demand manner; endpoints remain unpaired until the first request is made. To prevent a large number of endpoints from slowing down request processing, MOONCAKE Store employs endpoint pooling, which caps the maximum number of active connections. We use the SIEVE algorithm to manage endpoint eviction. If a connection fails due to link errors, it is removed from the endpoint pools on both sides and re-established during the next data transfer attempt.

**中文:**
MOONCAKE Store 使用一对 endpoint 表示本地和远程 RDMA NIC 之间的连接。每个 endpoint 包含一个或多个 RDMA queue pair 对象。连接以按需方式建立——endpoint 在首次请求前保持未配对状态。为防止大量 endpoint 拖慢请求处理，MOONCAKE Store 使用 **endpoint pooling** 限制最大活跃连接数，并用 **SIEVE** 算法管理 endpoint 淘汰。如果连接因链路错误失败，将被从两端的 endpoint pool 中移除，下次传输尝试时重建。

---

<a id="S025a"></a>
**Source:** p.5, §3.2.3 — Network Setup

**Original:**
The benefits of MOONCAKE rely on a high-bandwidth network interconnect. Currently, we use standard HGX machines where each A800 GPU is paired with a 100/200 Gbps NIC, and each H800 GPU is paired with a 200/400 Gbps NIC, which is comparable to memory bandwidth and existing libraries (other than NCCL) fail to fully utilize this capacity. As for NCCL, it cannot gracefully handle dynamic topology changes due to the addition or removal of nodes/NICs and does not support DRAM-to-DRAM paths. In contrast, the transfer engine endeavors to find alternative paths upon failure. To address congestion, the network utilizes RoCEv2 tuned by cloud providers. In the scheduler, we mitigate congestion by increasing the number of replicas for hot KVCaches (§4.2).

**中文:**
MOONCAKE 的优势依赖于高带宽网络互联。目前使用标准 HGX 机器（每张 A800 GPU 配 100/200 Gbps NIC，每张 H800 GPU 配 200/400 Gbps NIC），其网络带宽与内存带宽相当，而除 NCCL 外的现有库无法充分利用此容量。NCCL 无法优雅处理由于节点/NIC 增删导致的动态拓扑变化，且不支持 DRAM 到 DRAM 路径。相比之下，传输引擎会在故障时寻找替代路径。为应对拥塞，网络层面使用了经云提供商调优的 RoCEv2；在调度层面，我们通过增加热 KVCache 的副本数来缓解拥塞（§4.2）。

---

<a id="S025b"></a>
**Source:** p.5, §3.2.3 — Failure Handling

**Original:**
In a multi-NIC environment, one common failure scenario is the temporary unavailability of a specific NIC, while other routes may still connect two nodes. MOONCAKE Store is designed to adeptly manage such temporary failures effectively. If a connection is identified as unavailable, MOONCAKE Store automatically identifies an alternative, reachable path and resubmits the request to a different RDMA NIC device. Furthermore, MOONCAKE Store is capable of detecting problems with other RDMA resources, including RDMA contexts and completion queues. It temporarily avoids using these resources until the issue, such as a downed link, is resolved.

**中文:**
在多 NIC 环境中，常见故障场景是某个特定 NIC 暂时不可用，而其他路由仍可连接两个节点。MOONCAKE Store 被设计为能有效管理此类临时故障。如果某个连接被识别为不可用，MOONCAKE Store 会自动识别一条替代的可达路径，并将请求重新提交到不同的 RDMA NIC 设备。此外，MOONCAKE Store 能检测其他 RDMA 资源（包括 RDMA 上下文和完成队列）的问题，并暂时避免使用这些资源，直到问题（如链路断开）得到解决。

---

### §3.3 MOONCAKE's Prefill Pool / Prefill 节点池设计

<a id="S026a"></a>
**Source:** p.5–6, §3.3 ¶1 — 为何维持解耦架构

**Original:**
Unlike the inviolable decoding nodes, the necessity and best practices for designing a separate and elastic prefill pool remain under debate. For example, although many researchers share our intuition to use a disaggregated architecture, it is worth discussing whether this separation is still necessary with the introduction of chunked prefill. However, after careful consideration, we decided to maintain MOONCAKE's disaggregated architecture. This decision is primarily driven by the fact that online services typically have more stringent SLOs. While chunked prefill reduces decoding interference, it remains challenging to simultaneously maximize MFU during the prefill stage and meet the TBT SLO during the decoding stage. We will demonstrate this in the end-to-end experiments in §5.2.

**中文:**
与不可侵犯的 decoding 节点不同，是否需要设计一个独立的弹性 prefill 节点池及其最佳实践仍存在争议。例如，尽管许多研究者与我们一样倾向于解耦架构，但引入 chunked prefill 后这种分离是否仍然必要值得讨论。但经过仔细考量，我们决定维持 MOONCAKE 的解耦架构。主要原因是在线服务通常具有更严格的 SLO——虽然 chunked prefill 能减少对 decoding 的干扰，但同时最大化 prefill 阶段的 MFU 并满足 decoding 阶段的 TBT SLO 仍然困难。我们将在 §5.2 的端到端实验中证明这一点。

---

<a id="S026b"></a>
**Source:** p.5–6, §3.3 ¶2 — TP 跨节点的问题

**Original:**
Another important reason is that we think prefill nodes require different cross-node parallelism settings to handle long contexts as the available context length of recent LLMs is increasing rapidly, from 8k to 128k and even up to 1 million tokens. Typically, for such long context requests, the input tokens can be 10 to 100 times larger than the output tokens, making optimizing the TTFT crucial. Due to the abundant parallelism in long context prefill, using more than a single 8×GPU node to process them in parallel is desirable. However, extending tensor parallelism (TP) across more than one node requires two expensive RDMA-based all-reduce operations per layer, significantly reducing the MFU of prefill nodes.

**中文:**
另一个重要原因是：随着 LLM 上下文长度从 8k 快速增长至 128k 甚至 100 万 token，prefill 节点需要不同的跨节点并行设置来处理长上下文。对于此类长上下文请求，输入 token 可达输出 token 的 10–100 倍，使得 TTFT 优化至关重要。由于长上下文 prefill 中存在丰富的并行性，使用超过单个 8×GPU 节点并行处理是可取的。然而，将张量并行（TP）扩展到多个节点需要在每层进行两次昂贵的基于 RDMA 的 all-reduce 操作，严重降低 prefill 节点的 MFU。

---

<a id="S026c"></a>
**Source:** p.6, §3.3 ¶3 — SP 的局限性

**Original:**
Recently, many works have proposed sequence parallelism (SP). SP partitions the input sequences of requests across different nodes to achieve acceleration, allowing even long requests to meet the TTFT SLO. However, when applied to shorter input requests, SP results in a lower MFU compared to using single-node TP only. Recent research proposes elastic sequence parallelism to dynamically scale up or down the SP group. Although possible, this adds complexity to our architecture. Additionally, SP still requires frequent cross-node communication, which lowers the MFU and competes with network resources for transferring KVCache across nodes.

**中文:**
近期许多工作提出了序列并行（SP）。SP 将请求的输入序列划分到不同节点以实现加速，使长请求也能满足 TTFT SLO。然而，当应用于短输入请求时，SP 的 MFU 低于仅使用单节点 TP。最近有研究提出弹性序列并行以动态扩缩 SP 组——虽然可行，但这为我们的架构增加了复杂性。此外，SP 仍需频繁的跨节点通信，降低了 MFU 并与跨节点 KVCache 传输竞争网络资源。

---

<a id="S026d"></a>
**Source:** p.6, §3.3 ¶4 — CPP 设计与优势

**Original:**
To address this, MOONCAKE leverages the autoregressive property of decoder-only transformers and implements chunked pipeline parallelism (CPP) for long context prefill. We group every X nodes in the prefill cluster into a pipelined prefill node group. For each request, its input tokens are partitioned into chunks, each no longer than the prefill_chunk. Different chunks of the same request can be processed simultaneously by different nodes, thus parallelizing the processing and reducing TTFT. CPP offers two main benefits: 1) Similar to pipeline parallelism in training, it requires cross-node communication only at the boundaries of each pipeline stage, which can be easily overlapped with computation. This leads to better MFU and less network resource contention with KVCache transfer. 2) It naturally fits both short and long contexts, bringing no significant overhead for short context prefill and avoiding frequent dynamic adjustment of node partitioning. This pipeline-based acceleration method has been explored in training systems, but to our knowledge, this is the first application in the inference stage, as long context inference has only recently emerged.

**中文:**
为此，MOONCAKE 利用 decoder-only Transformer 的自回归特性，实现了用于长上下文 prefill 的**分块流水线并行（CPP）**。我们将 prefill 集群中每 X 个节点编组为一个流水线 prefill 节点组。对每个请求，输入 token 被划分为若干 chunk，每个 chunk 不超过 `prefill_chunk` 阈值。同一请求的不同 chunk 可由不同节点同时处理，从而并行化处理并降低 TTFT。CPP 有两个主要优势：(1) 与训练中的流水线并行类似，跨节点通信仅发生在每个流水线阶段的边界，可与计算轻松重叠，从而带来更高的 MFU 和更少的与 KVCache 传输的网络资源竞争；(2) 它天然适配短上下文和长上下文——对短上下文 prefill 不引入额外开销，同时避免了频繁的节点划分动态调整。这种基于流水线的加速方法在训练系统中已有探索，但据我们所知，这是推理阶段的首次应用——因为长上下文推理直到最近才出现。

---

## §4 Scheduling / 调度策略

### §4.1 Prefill Global Scheduling / Prefill 全局调度

<a id="S027"></a>
**Source:** p.6, §4.1 ¶1–2

**Original:**
Previous research on LLM serving typically uses a load-balancing strategy that evaluates the load on each instance based on the number of assigned requests. In MOONCAKE, however, the selection of prefill instances considers additional factors--not just load but also the prefix cache hit length and the distribution of reusable KVCache blocks. [...] To address these complexities, we propose a cache-aware global scheduling algorithm that accounts for both the prefill time due to the prefix cache and the local queuing time. [...] Conductor assigns the request to the instance with the shortest TTFT and updates the cache and queue times for that instance accordingly. If the SLO is not achievable, Conductor directly returns the HTTP 429 Too Many Requests response status code to the upper layers.

**中文:**
此前 LLM 推理系统的研究通常采用基于请求数量的负载均衡策略。但在 MOONCAKE 中，prefill 实例的选择还需考虑额外因素——不仅是负载，还有**前缀缓存命中长度**和**可复用 KVCache block 的分布**。为此，我们提出了一种缓存感知的全局调度算法，同时考虑前缀缓存带来的 prefill 时间以及本地排队时间。Conductor 将请求分配给能达成最短 TTFT 的实例，并相应更新该实例的缓存和排队时间。如果 SLO 无法达成，Conductor 直接向上层返回 **HTTP 429 Too Many Requests** 状态码。

---

<a id="A001"></a>
**Source:** p.6, Algorithm 1 — KVCache-centric Scheduling Algorithm

```
Algorithm 1: KVCache-centric Scheduling Algorithm
Input:  prefill instance pool P, decoding instance pool D,
        request R, cache block size B
Output: the prefill and decoding instances (p, d) to process R

 1: block_keys ← PrefixHash(R.prompt_tokens, B)
 2: TTFT, p ← inf, 0/
 3: best_len, best_instance ← FindBestPrefixMatch(P, block_keys)
 4: for instance ∈ P do
 5:   if instance.prefix_len > kvcache_balancing_threshold then
 6:     prefix_len ← best_len
 7:     transfer_len ← best_len - instance.prefix_len
 8:     T_transfer ← EstimateKVCacheTransferTime(transfer_len)
 9:   else
10:     prefix_len ← instance.prefix_len
11:     T_transfer ← 0
12:   T_queue ← EstimatePrefillQueueTime(instance)
13:   T_prefill ← EstimatePrefillExecutionTime(
                    len(R.prompt_tokens), prefix_len)
14:   if TTFT > T_transfer + T_queue + T_prefill then
15:     TTFT ← T_transfer + T_queue + T_prefill
16:     p ← instance
17: d, TBT ← SelectDecodingInstance(D)
18: if TTFT > TTFT_SLO or TBT > TBT_SLO then
19:   reject R; return
20: if p.prefix_len > kvcache_balancing_threshold then
21:   TransferKVCache(best_instance, p)
22: return (p, d)
```

> **算法说明:** 对于每个新请求，先将 prompt token 哈希为 block key，然后在所有 prefill 实例中寻找最佳前缀匹配。若某实例的本地前缀匹配长度超过 `kvcache_balancing_threshold` 阈值，则计算从最佳匹配实例传输 KVCache 的时间；否则直接使用本地缓存。Conductor 估算总 TTFT（传输时间 + 排队时间 + prefill 执行时间），选择 TTFT 最短的实例。若 SLO 无法满足则拒绝请求（HTTP 429）；否则将请求调度到选中实例，并在需要时触发 KVCache 传输。

---

<a id="S027a"></a>
**Source:** p.6, §4.1 ¶2 — 调度框架的工程复杂性

**Original:**
The backbone of this scheduling framework is straightforward, but complexities are hidden in the engineering implementation of various components. For example, to predict the computation time of the prefill stage for a request, we employ a predictive model derived from offline test data. This model estimates the prefill duration based on the request's length and prefix cache hit length. Thanks to the regular computation pattern of Transformers, the error bound of this prediction is small as long as enough offline data is available. The queuing time for a request is calculated by aggregating the prefill times of all queued requests. In practical implementations, TTFTs are computed in parallel, rendering the processing time negligible compared to the inference time. More difficulty lies in predicting the transfer time because it is determined not only by the size of the transferred data but also by the current network status, especially whether the sending node is under congestion. This also necessitates the replication of hot KVCache blocks, which will be discussed in §4.2.

**中文:**
该调度框架的主干逻辑简洁明了，但复杂性隐藏在各组件的工程实现中。例如，为预测请求的 prefill 阶段计算时间，我们采用了基于离线测试数据的预测模型——该模型根据请求长度和前缀缓存命中长度估算 prefill 耗时。得益于 Transformer 规则的计算模式，只要有足够的离线数据，预测误差很小。请求排队时间通过聚合所有排队请求的 prefill 时间来计算——在实际实现中，TTFT 是并行计算的，因此处理时间相比推理时间可忽略不计。更具挑战性的是传输时间的预测，因为它不仅取决于传输数据大小，还取决于当前网络状态（特别是发送节点是否拥塞）。这也解释了为什么需要对热 KVCache block 进行复制（详见 §4.2）。

---

### §4.2 Cache Load Balancing / 缓存负载均衡

<a id="S028"></a>
**Source:** p.6, §4.2 ¶1–3

**Original:**
In MOONCAKE, each prefill instance has its own set of local prefix caches. The usage frequency of these caches varies significantly. For example, system prompts are accessed by almost every request, whereas caches storing content from a local long document may be used by only one user. [...] A straw-man solution to this KVCache scheduling problem could be collecting the global usages of each block, using a prediction model to forecast their future usages, and making scheduling decisions accordingly. However, unlike the estimation of prefill time, workloads are highly dynamic and change significantly over time. Especially for a MaaS provider experiencing rapid growth in its user base, it is impossible to accurately predict future usages. Thus, we propose a heuristic-based automated hotspot migration scheme to enhance cache load balancing.

**中文:**
在 MOONCAKE 中，每个 prefill 实例有自己的一套本地前缀缓存。这些缓存的使用频率差异很大——例如，系统提示词几乎每个请求都会访问，而存储某个本地长文档的缓存可能只有一个用户使用。一个朴素方案是收集每个 block 的全局使用量、使用预测模型预估未来使用量并据此做出调度决策。然而，与 prefill 时间估算不同，工作负载高度动态且随时间变化显著——尤其对于用户量快速增长的 MaaS 提供商而言，精确预测未来使用量是不可能的。因此，我们提出了**基于启发式的自动热点迁移方案**来增强缓存负载均衡。

---

<a id="S029"></a>
**Source:** p.6–7, §4.2 — Figure 5 实验

**Original:**
The experimental results, depicted in Figure 5, demonstrate that our KVCache-centric scheduling algorithms outperform random and load-balancing scheduling. By incorporating cache load balancing, the global cache-aware algorithm reduces the average TTFT by an additional 14% compared to the local cache-aware algorithm.

**中文:**
图 5 的实验结果表明，我们以 KVCache 为中心的调度算法优于随机调度和负载均衡调度。通过引入缓存负载均衡，全局缓存感知算法相比本地缓存感知算法额外将平均 TTFT **降低了 14%**。

---

## §5 Evaluation / 实验评估

### §5.1 Setup / 实验设置

<a id="S030"></a>
**Source:** p.7, §5.1

**Original:**
**Testbed.** Each node in the cluster is configured with eight NVIDIA-A800-SXM4-80GB GPUs and four 200 Gbps RDMA NICs. The KVCache block size in MOONCAKE Store is set to 256. **Metric.** We measure the TTFT and TBT of each request, where the TBT is calculated as the average of the longest 10% of the token arrival intervals. The threshold for TTFT is set to 30 s, and TBT thresholds are set to 100 ms, 200 ms, and 300 ms, depending on the scenario. We consider requests with both TTFT and TBT below their respective thresholds as effective requests. **Baseline.** We employ vLLM, one of the state-of-the-art open-source LLM serving systems. Recent updates to vLLM have integrated features like prefix caching and chunked prefill, which we also compare. We utilize vLLM v0.5.1. Due to limitations in the current implementation, we test the prefix cache and chunked prefill features separately.

**中文:**
**测试环境:** 每个节点配置 8 张 A800-SXM4-80GB GPU 和 4 个 200 Gbps RDMA 网卡。KVCache block 大小为 256。
**指标:** 测量每个请求的 TTFT 和 TBT（TBT 取最长的 10% token 到达间隔的平均值）。TTFT 阈值设为 30s，TBT 阈值根据场景设为 100ms/200ms/300ms。TTFT 和 TBT 均低于阈值的请求视为有效请求。
**基线:** vLLM v0.5.1（最先进的开源 LLM 推理系统之一），同时比较其前缀缓存和 chunked prefill 特性（因当前实现限制，两个特性分别测试）。

---

### §5.2 End-to-end Performance / 端到端性能

<a id="S031"></a>
**Source:** p.7–8, §5.2.1 — 三种工作负载

**Original:**
We employ three types of workloads in our tests: two real-world traces sampled from Kimi that represent online conversations and tool&agent interactions, respectively, and a synthetic workload to cover different inference scenarios. [...] Conversation workload: average ~12k tokens input, ~40% prefix caching ratio from multi-turn conversations. Tool&Agent workload: high proportion of prefix caching (~59%), with shorter input and output lengths. Synthetic workload: longest average input length (~15k), highest prefix cache ratio (~66%), but dispersed cache hotspots.

**中文:**
我们使用三种工作负载进行测试：

**Conversation workload（对话工作负载）:** 聊天机器人是 LLM 最普遍的应用之一。该工作负载包含大量长上下文请求——最长可达 128k token，平均约 12k token，与当前长上下文数据集的数据长度相当。由于多轮对话带来约 40% 的前缀缓存率。我们从线上推理集群中采样了 1 小时的对话 trace，每条记录包含输入/输出长度及到达时间戳。

**Tool&Agent workload（工具与智能体工作负载）:** LLM 作为工具或智能体执行任务的研究日益增多。这些任务通常包含预设计的、完全重复的冗长系统提示词。我们从线上同样采样了 1 小时的 trace。该工作负载展现出高比例的前缀缓存（~59%），且输入和输出长度较短。

**Synthetic workload（合成工作负载）:** 由公开数据集（ShareGPT、Leval、LooGLE）组合构建。ShareGPT 为短输入的多轮对话；Leval 是长上下文模型性能评估基准，模拟工具/智能体场景中冗长系统提示词的请求；LooGLE 针对长上下文 QA 和摘要任务（输入最长 100k token）。三者按 1:1:1 混合，保留多轮对话的序列关系但随机打乱。由于数据集不含到达时间，使用泊松过程模拟真实到达模式。该工作负载平均输入最长、前缀缓存比例最高（66%），但缓存热点最为分散。

| 负载 | 平均输入长度 | 平均输出长度 | 缓存率 | 来源 | 请求数 | 到达模式 |
|---|---|---|---|---|---|---|
| Conversation | 12,035 | 343 | 40% | Kimi 线上 trace | 12,031 | 时间戳 |
| Tool&Agent | 8,596 | 182 | 59% | Kimi 线上 trace | 23,608 | 时间戳 |
| Synthetic | 15,325 | 149 | 66% | ShareGPT+Leval+LooGLE | 3,993 | 泊松过程 |

---

<a id="S032"></a>
**Source:** p.8, §5.2.2 — 有效请求容量结果

**Original:**
**Conversation workload.** Compared to vLLM, MOONCAKE achieves a very significant increase in effective request capacity. **Tool&Agent workload.** MOONCAKE uses a global cache pool to significantly increase caching capacity and optimize cache utilization through internode transfers [...] enhances effective caching capacity by 42% compared to vLLM with prefix caching under the 200 ms threshold. **Synthetic workload.** Compared to vLLM, MOONCAKE increases effective request capacity by 40% under the 200 ms threshold.

**中文:**
- **Conversation:** MOONCAKE 相比 vLLM 在有效请求容量上有极大提升（TBT=100ms 时 +498%，即约 5 倍）。
- **Tool&Agent:** 在 200ms TBT 阈值下，MOONCAKE 比 vLLM+Prefix Caching 提升 **42%**。
- **Synthetic:** 在 200ms 阈值下，MOONCAKE 比 vLLM 提升 **40%**。

---

<a id="S033"></a>
**Source:** p.8–9, §5.2.3 — Prefill GPU 时间

**Original:**
Across different systems, MOONCAKE significantly reduces GPU time by fully utilizing global cache for prefix caching, achieving reductions of 36%, 53%, and 64% for conversation, tool&agent, and synthetic workloads, respectively, compared to vLLM.

**中文:**
MOONCAKE 通过充分利用全局缓存进行前缀缓存，显著减少了 GPU 计算时间。相比 vLLM，在 Conversation、Tool&Agent 和 Synthetic 三种工作负载下，prefill GPU 时间分别降低了 **36%**、**53%** 和 **64%**。

---

### §5.3 MOONCAKE Store / 缓存效果分析

<a id="S034"></a>
**Source:** p.9–10, §5.3.1 — 缓存容量定量分析

**Original:**
Figure 9 displays theoretical cache hit rates under various workloads and their combinations. The findings indicate that a local cache with a 3M token capacity does not achieve 50% of the theoretical maximum hit rate in most scenarios. We also determine that, in these workloads, a cache capacity of 50M tokens nearly reaches the theoretical maximum hit rate of 100%, which require to pool at least 20 nodes' DRAM.

**中文:**
图 9 展示了不同工作负载下的理论缓存命中率。结果表明：**300 万 token 容量的本地缓存在大多数场景下无法达到理论最大命中率的 50%**。而在这些工作负载中，**5000 万 token 的缓存容量**才能接近 100% 的理论最大命中率——这需要池化至少 20 个节点的 DRAM。这充分说明了全局缓存的必要性。

---

<a id="S035"></a>
**Source:** p.10, §5.3.2 — 全局 vs 本地缓存实验

**Original:**
Compared to the local cache, the global cache exhibits a maximum increase of 136% in cache hit rate and a reduction of up to 48% in prefill computation time.

**中文:**
相比本地缓存，全局缓存实现了**缓存命中率最高提升 136%（即 2.36 倍）**，prefill 计算时间**最多降低 48%**。

---

#### §5.3.3 Cache Replica / 缓存副本

<a id="S035a"></a>
**Source:** p.10, §5.3.3

**Original:**
Building upon the cache load balancing scheduling strategy discussed in §4.2, the cache keys in MOONCAKE Store may have replicas distributed across different machines, thereby reducing access latency for hot caches. To further investigate the system's dynamic behavior, we count the number of cache replicas for keys across three workloads, as shown in Figure 11. It can be observed that in the conversation and tool&agent workloads, there are highly concentrated hot caches (e.g., the top 100 keys), which, after the system stabilizes, have replicas on almost every instance in the prefill pool. In contrast, the synthetic workload has fewer shared prefix caches, resulting in fewer replicas and potential fluctuations, even for the top 10 blocks. This demonstrates that our scheduling strategy in §4.2 effectively provides replicas for hot caches, particularly in scenarios with highly concentrated prefix caches.

**中文:**
基于 §4.2 中讨论的缓存负载均衡调度策略，MOONCAKE Store 中的缓存 key 可在不同机器上分布多个副本，从而降低热缓存的访问延迟。为进一步研究系统的动态行为，我们统计了三种工作负载下缓存 key 的副本数量，如图 11 所示。可以观察到，在 Conversation 和 Tool&Agent 工作负载中存在高度集中的热缓存（如 top 100 key），系统稳定后这些 key 几乎在 prefill 池的每个实例上都有副本。相比之下，Synthetic 工作负载的共享前缀缓存较少，即便 top 10 block 的副本数也较少且存在波动。这表明 §4.2 的调度策略能有效地为热缓存提供副本，特别是在前缀缓存高度集中的场景中。

---

### §5.4 KVCache Transfer Performance / 传输性能

<a id="S036"></a>
**Source:** p.10–11, §5.4.1 — 传输引擎性能

**Original:**
As depicted in Figure 12, the transfer engine consistently exhibits significantly lower latency than the alternative methods. In the scenario of transferring 40 GB of data, corresponding to the cache size for LLaMA3-70B with 128k tokens, the transfer engine achieves bandwidth of 87 GB/s and 190 GB/s under network configurations of 4×200 Gbps and 8×400 Gbps, respectively. These rates are approximately 2.4× and 4.6× faster than those achieved using the TCP protocol.

**中文:**
如图 12 所示，传输引擎的延迟始终显著低于对比方案。在传输 40 GB 数据（LLaMA3-70B 128k token 的 KVCache 大小）的场景中，传输引擎在 4×200 Gbps 和 8×400 Gbps 网络配置下分别达到了 **87 GB/s** 和 **190 GB/s** 的带宽，分别是 TCP 协议的 **2.4 倍**和 **4.6 倍**。

---

<a id="S037"></a>
**Source:** p.11, §5.4.2 — 最小带宽需求

**Original:**
MOONCAKE's global cache pool relies on efficient inter-node cache transfers to hide cache transfer times within GPU computation times. We evaluate the impact of network bandwidth on the system's performance by simulating a range of bandwidths from 24 Gbps to 400 Gbps and measuring the transfer time and TTFT under the synthetic workload described in §5.2.1. Figure 13a shows that the average TTFT of requests decreases as bandwidth increases. When the total communication bandwidth exceeds 100 Gbps, the average TTFT remains below 2 s, significantly less than the TTFT of the recomputation baseline. However, when bandwidth falls below 100 Gbps, system performance is significantly compromised. This is marked by a sharp increase in TTFT and evident network congestion, as demonstrated by the substantial divergence between actual and theoretical transfer times illustrated in Figure 13b. Consequently, we recommend a minimum network bandwidth of 100 Gbps to ensure optimal system performance.

**中文:**
MOONCAKE 的全局缓存池依赖高效的节点间缓存传输，以将传输时间隐藏在 GPU 计算时间内。我们通过模拟从 24 Gbps 到 400 Gbps 的带宽范围，在合成工作负载下测量传输时间和 TTFT。图 13a 显示，请求的平均 TTFT 随带宽增加而降低。当总通信带宽超过 **100 Gbps** 时，平均 TTFT 保持在 2s 以下，显著低于重新计算的基线。然而，当带宽低于 100 Gbps 时，系统性能急剧恶化——TTFT 急剧上升，且如图 13b 所示，实际传输时间与理论传输时间之间出现显著偏离，表明出现网络拥塞。因此，推荐最低网络带宽为 **100 Gbps** 以确保系统最佳性能。

---

<a id="S038"></a>
**Source:** p.11, §5.4.3 — E2E 延迟分解

**Original:**
The latency of a single inference request in MOONCAKE can be decomposed into five components: 1) scheduling and queuing time; 2) layer-wise prefill time; 3) cache transfer time; 4) time required for the decoding node to load cache from DRAM to HBM; and 5) decoding time. We experimentally analyze the proportion of these five components under settings with prefix cache ratios of 0% and 95%, as shown in Figure 14. First, it is evident from the figure that the introduction of prefix caching significantly reduces the prefill time. Specifically, with an input length of 128k tokens, prefix caching reduces the prefill time by 92%. Furthermore, the overhead introduced by MOONCAKE has minimal impact on the system's performance. The Schedule, Transfer, and Load Cache components can proceed asynchronously with model inference and therefore do not affect MOONCAKE's throughput. Moreover, the increase in TTFT due to these overheads is smaller than the reduction achieved by prefix caching. Even when accounting for the overhead, prefix caching in MOONCAKE can reduce TTFT by 86% with an input length of 128k tokens.

**中文:**
MOONCAKE 中单个推理请求的延迟可分解为五个组成部分：1) 调度与排队时间；2) 逐层 prefill 时间；3) 缓存传输时间；4) decoding 节点将缓存从 DRAM 加载至 HBM 的时间；5) decoding 时间。我们实验分析了前缀缓存率为 0% 和 95% 两种设置下这五个部分的比例（图 14）。首先，前缀缓存的引入显著降低了 prefill 时间——在 128k token 输入长度下，前缀缓存将 prefill 时间降低了 **92%**。此外，MOONCAKE 引入的开销对系统性能影响极小：Schedule、Transfer 和 Load Cache 组件可与模型推理异步执行，因此不影响吞吐量；这些开销导致的 TTFT 增加幅度小于前缀缓存带来的减少幅度。即使计入全部开销，MOONCAKE 的前缀缓存仍可将 128k token 输入的 TTFT 降低 **86%**。

---

### §5.5 P/D Ratio / Prefill/Decoding 节点比例

<a id="S039"></a>
**Source:** p.11–12, §5.5

**Original:**
Figure 15a demonstrates that when the P/D ratio is approximately 1:1, MOONCAKE achieves its highest effective request capacity, indicating that the loads on the prefill and decoding clusters are relatively balanced. We also note that some prior work has proposed dynamically switching the roles of nodes between prefill and decoding. However, in practical deployments, we find that the statistical characteristics of online traffic are generally stable. Therefore, we choose to fix the P/D ratio while continuously monitoring the loads of the prefill and decoding clusters, only switching node roles when significant load fluctuations occur.

**中文:**
实验表明，当 P/D 比例约为 **1:1** 时，MOONCAKE 达到了最高的有效请求容量——此时 prefill 和 decoding 集群的负载相对平衡。此外，我们注意到此前有工作提出在 prefill 和 decoding 之间动态切换节点角色。但在实际部署中，线上流量的统计特征通常是稳定的，因此我们选择固定 P/D 比例，持续监控两个集群的负载，仅在发生显著负载波动时才切换节点角色。

---

## §6 Related Work / 相关工作

<a id="S040"></a>
**Source:** p.12, §6

**Original:**
Significant efforts have been dedicated to enhancing the efficiency of LLM serving systems through scheduling, memory management, and resource disaggregation. Production-grade systems like FasterTransformer, TensorRT-LLM, and DeepSpeed Inference are designed to significantly boost throughput. Orca employs iteration-level scheduling to facilitate concurrent processing at various stages, while vLLM leverages dynamic KVCache management to optimize memory. FlexGen, Sarathi-Serve, and FastServe incorporate innovative scheduling and swapping strategies to distribute workloads effectively across limited hardware, often complementing each other's optimizations. Further optimizations lead to the separation of prefill and decoding stages, leading to the disaggregated architecture of MOONCAKE. Our design builds on these developments, particularly drawing from the open-source community of vLLM, for which we are deeply appreciative.

Prefix caching is also widely adopted to enable the reuse of KVCache across multiple requests, reducing computational overhead in LLM inference systems. Prompt Cache precomputes and stores frequently used text KVCache on inference servers, facilitating their reuse and significantly reducing inference latency. SGLang leverages RadixAttention, which uses a least recently used (LRU) cache within a radix tree structure to efficiently enable automatic sharing across various reuse patterns.

Among these approaches, CachedAttention, a concurrent work with us, proposes a hierarchical KV caching system that utilizes cost-effective memory and storage media to accommodate KVCache for all requests. The architecture of MOONCAKE shares many design choices with CachedAttention. However, in long-context inference, the KVCache becomes extremely large, requiring high capacity and efficient data transfer along with KVCache-centric global scheduling. Additionally, MOONCAKE is not a standalone cache service, it incorporates both a memory-efficient cache storage mechanism and a cache-aware scheduling strategy, further improving prefix caching efficiency. The benefits of a distributed KVCache pool depend on the cache hit rate, which increases as the per-token cache size decreases under a fixed capacity. Consequently, orthogonal techniques such as KVCache compression (CacheGen, KVQuant, KIVI) and KVCache-friendly attention architectures (DeepSeek-V2, Cross-Layer Attention) can further enhance our approach.

**中文:**
LLM 推理系统效率的提升吸引了大量研究工作，涵盖调度、内存管理和资源解耦三大方向。

**生产级系统:** FasterTransformer、TensorRT-LLM、DeepSpeed Inference 大幅提升了吞吐量。Orca 采用迭代级调度实现多阶段并发处理，vLLM 利用动态 KVCache 管理优化内存，FlexGen、Sarathi-Serve 和 FastServe 通过创新的调度和交换策略在有限硬件上有效分配工作负载。这些优化相互补充，最终引向了 prefill/decoding 阶段的分离——即 MOONCAKE 的解耦架构。MOONCAKE 的设计建立在上述工作的基础上，尤其受益于 vLLM 开源社区。

**前缀缓存:** Prompt Cache 预计算并存储常用文本的 KVCache，显著降低推理延迟。SGLang 的 RadixAttention 在基数树结构中使用 LRU 缓存，自动实现多种复用模式下的高效共享。

**并发工作 CachedAttention:** 提出分层 KV 缓存系统，与 MOONCAKE 共享许多设计选择。但 MOONCAKE 的独特之处在于：(1) 面向长上下文推理场景的极高 KVCache 容量和数据传输需求；(2) 不仅仅是独立的缓存服务，还整合了缓存感知的调度策略。此外，分散式 KVCache 池的收益依赖于缓存命中率，KVCache 压缩（CacheGen、KVQuant、KIVI）和缓存友好的注意力架构（DeepSeek-V2、跨层注意力）等正交技术可进一步增强本方法。

---

## §7 Conclusion / 结论

<a id="S041"></a>
**Source:** p.12, §7

**Original:**
This paper presents MOONCAKE, a KVCache-centric disaggregated architecture designed for efficiently serving LLMs, particularly in long-context scenarios. We discuss the necessity, challenges, and design choices involved in balancing the goal of maximizing overall effective throughput while meeting latency-related SLO requirements.

**中文:**
本文提出了 MOONCAKE——一种以 KVCache 为中心的解耦架构，用于高效地服务 LLM 推理，特别是在长上下文场景中。我们讨论了在最大化整体有效吞吐量和满足延迟 SLO 要求之间取得平衡的过程中所涉及的必要性、挑战和设计选择。

---

## Acknowledgments / 致谢

<a id="S042"></a>
**Source:** p.12, Acknowledgments

**Original:**
We thank the anonymous reviewers and our shepherd, Mr. Kan Wu, for their valuable feedback. The authors affiliated with Tsinghua University are all in the Department of Computer Science and Technology, Beijing National Research Center for Information Science and Technology (BNRist), Tsinghua University, China. This work is supported by National Key Research & Development Program of China (2022YFB4502004), Natural Science Foundation of China (62141216) and Tsinghua University Initiative Scientific Research Program, Young Elite Scientists Sponsorship Program by CAST (2022QNRC001), and Beijing HaiZhi XingTu Technology Co., Ltd.

**中文:**
我们感谢匿名审稿人和 shepherd Kan Wu 先生的宝贵反馈。清华大学作者均来自清华大学计算机科学与技术系、北京信息科学与技术国家研究中心（BNRist）。本工作受国家重点研发计划（2022YFB4502004）、国家自然科学基金（62141216）、清华大学自主科研计划、中国科协青年人才托举工程（2022QNRC001）以及北京海智星图科技有限公司的支持。

---

## References / 参考文献

<a id="REF"></a>
**Source:** p.12–14, References [1]–[43]

[1] OpenAI. Introducing chatgpt. https://openai.com/blog/chatgpt, 2022.

[2] Hugo Touvron, et al. Llama 2: Open foundation and fine-tuned chat models. arXiv:2307.09288, 2023.

[3] Mark Chen, et al. Evaluating large language models trained on code. arXiv:2107.03374, 2021.

[4] Charles Packer, et al. Memgpt: Towards llms as operating systems. arXiv:2310.08560, 2023.

[5] Moonshot AI. Kimi. https://kimi.moonshot.cn, 2023.

[6] NVIDIA. Nvidia h100 tensor core gpu architecture. https://resources.nvidia.com/en-us-tensor-core, 2022.

[7] Pratyush Patel, et al. Splitwise: Efficient generative llm inference using phase splitting. ISCA 2024.

[8] Yinmin Zhong, et al. Distserve: Disaggregating prefill and decoding for goodput-optimized large language model serving. OSDI 2024.

[9] Cunchen Hu, et al. Inference without interference: Disaggregate llm inference for mixed downstream workloads. arXiv:2401.11181, 2024.

[10] Amey Agrawal, et al. Taming throughput-latency tradeoff in llm inference with sarathi-serve. OSDI 2024.

[11] Alec Radford, et al. Language models are unsupervised multitask learners. OpenAI blog, 2019.

[12] Hugo Touvron, et al. Llama: Open and efficient foundation language models. arXiv:2302.13971, 2023.

[13] Gyeong-In Yu, et al. Orca: A distributed serving system for transformer-based generative models. OSDI 2022.

[14] Woosuk Kwon, et al. Efficient memory management for large language model serving with pagedattention. SOSP 2023.

[15] Bingyang Wu, et al. Loongserve: Efficiently serving long-context large language models with elastic sequence parallelism. SOSP 2024.

[16] In Gim, et al. Prompt cache: Modular attention reuse for low-latency inference. MLSys 2024.

[17] Lianmin Zheng, et al. Efficiently programming large language models using sglang. arXiv:2312.07104, 2023.

[18] Vikranth Srivatsa, et al. Preble: Efficient distributed prompt scheduling for llm serving. 2024.

[19] Yazhuo Zhang, et al. Sieve is simpler than lru: an efficient turn-key eviction algorithm for web caches. NSDI 2024.

[20] Google. Our next-generation model: Gemini 1.5. https://blog.google/technology/ai/, 2024.

[21] Sam Ade Jacobs, et al. Deepspeed ulysses: System optimizations for enabling training of extreme long sequence transformer models. arXiv:2309.14509, 2023.

[22] Hao Liu, et al. Ring attention with blockwise transformers for near-infinite context. NeurIPS 2023 Workshop.

[23] William Brandon, et al. Striped attention: Faster ring attention for causal transformers. arXiv:2311.09431, 2023.

[24] Dacheng Li, et al. Lightseq: Sequence level parallelism for distributed training of long context transformers. WANT@NeurIPS 2023.

[25] Vijay Anand Korthikanti, et al. Reducing activation recomputation in large transformer models. MLSys 2023.

[26] Shenggui Li, et al. Sequence parallelism: Long sequence training from system perspective. ACL 2023.

[27] Jiarui Fang and Shangchun Zhao. Usp: A unified sequence parallelism approach for long context generative ai. arXiv:2405.07719, 2024.

[28] Zhuohan Li, et al. Terapipe: Token-level pipeline parallelism for training large-scale language models. ICML 2021.

[29] Chenxin An, et al. L-eval: Instituting standardized evaluation for long context language models. arXiv:2307.11088, 2023.

[30] Jiaqi Li, et al. Loogle: Can long-context language models understand long contexts? arXiv:2311.04939, 2023.

[31] Joon Sung Park, et al. Generative agents: Interactive simulacra of human behavior. UIST 2023.

[32] ShareGPT teams. https://sharegpt.com/.

[33] NVIDIA Corporation. Fastertransformer. https://github.com/NVIDIA/FasterTransformer, 2019.

[34] NVIDIA Corporation. Tensorrt-llm. https://github.com/NVIDIA/TensorRT-LLM, 2023.

[35] Reza Yazdani Aminabadi, et al. Deepspeed-inference: enabling efficient inference of transformer models at unprecedented scale. SC 2022.

[36] Ying Sheng, et al. Flexgen: High-throughput generative inference of large language models with a single gpu. ICML 2023.

[37] Bingyang Wu, et al. Fast distributed inference serving for large language models. arXiv:2305.05920, 2023.

[38] Bin Gao, et al. Cost-efficient large language model serving for multi-turn conversations with cachedattention. USENIX ATC 2024.

[39] Yuhan Liu, et al. Cachegen: Kv cache compression and streaming for fast large language model serving. SIGCOMM 2024.

[40] Coleman Hooper, et al. Kvquant: Towards 10 million context length llm inference with kv cache quantization. arXiv:2401.18079, 2024.

[41] Zirui Liu, et al. Kivi: A tuning-free asymmetric 2bit quantization for kv cache. arXiv:2402.02750, 2024.

[42] Aixin Liu, et al. Deepseek-v2: A strong, economical, and efficient mixture-of-experts language model. arXiv:2405.04434, 2024.

[43] William Brandon, et al. Reducing transformer key-value cache size with cross-layer attention. arXiv:2405.12981, 2024.

---

## 阅读提示 / Critical Reading Notes

1. **核心贡献:** MOONCAKE 是第一个在大规模生产环境中（Kimi）验证了「用分散式 KVCache 池化集群闲置资源」可行性的系统。它不是纯研究原型，而是已部署在生产环境、每天处理千亿 token 的工业级系统。

2. **与其他工作的关键差异:** 与 CachedAttention（并发工作）相比，MOONCAKE 的独特之处在于其 KVCache 感知的全局调度器（Conductor）和缓存负载均衡策略——并非被动的缓存服务，而是主动调度请求到最优 prefill 节点。

3. **潜在不足:**
   - CPP 的阈值（`prefill_chunk`）和热点迁移的 `kvcache_balancing_threshold` 目前均为手动设置（论文坦承）
   - P/D 比例固定为 1:1，无法自适应动态变化的工作负载
   - 实验仅基于 LLaMA3-70B 架构的虚拟模型，对 MoE 架构（如 Mixtral）或更小/更大的模型的适用性未充分探索

4. **领域定位:** MOONCAKE 处于 LLM 推理系统与分布式缓存研究的交叉点。它连接了三个研究方向——P/D 解耦（Splitwise/DistServe）、前缀缓存（SGLang/Prompt Cache）和高性能 RDMA 数据传输。

5. **适合谁读:** 适合从事 LLM 推理系统、分布式缓存、RDMA 网络编程的研究者和工程师。对 MaaS 服务架构决策者也有参考价值。

6. **实践价值:** 论文开源了 trace 数据和 transfer engine（https://github.com/kvcache-ai/Mooncake），可直接复现和复用。

---

*Generated by nature-reader v2.1.2 · 2026-08-12 (supplemented)*
