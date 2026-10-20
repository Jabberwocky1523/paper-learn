# 原文摘要
## 原文

MOONCAKE is the serving platform for Kimi, ashn LLM chatbot service developed by Moonshot AI. This platform features a KVCache-centric disaggregated architecture that not only separates prefill and decoding clusters but also efficiently utilizes the underexploited CPU, DRAM, SSD and NIC resources of the GPU cluster to establish a disaggregated KVCache. At the core of MOONCAKE is its KVCache-centric global cache and a scheduler designed to maximize throughput while adhering to stringent latency-related Service Level Objectives (SLOs).

## 翻译
MOONCAKE是KIMI的在线服务平台.这个平台采用以KVCache为中心的分散式架构,不仅分离了prefill与decoding集群,而且有效利用了CPU集群里面未充分利用的CPU,DRAM,SSD,NIC资源去构建一个分散式KVCache.MOONCAKE的核心是他的以KVCache为中心的全局缓存和一个在满足严格延迟要求的SLOs的同时最大化吞吐量的调度器.

---

# 研究问题
在满足不同场景下的SLOs的同时,如何增加kimi的有效吞吐量?

---
# 发现的问题
1. 现存的方案一般严格将kvcache储存在本地gpu的HBM或者cpu的DRAM，认为全局调度器所需要的运输带宽过高，但是经过数学验证发现如果只用本地的DRAM最高只能达到理论cache命中率的一半。
2. 跨节点tp方案需要两次RDMA  all-reduce操作会减少prefill nodes的mfu，且跨界点sp方案又会占用运输kvcache所需要的网卡资源，所以采用cpp方式。

---

# 创新点
1. **MOONCAKE Store**:将gpu集群里的cpu,dram,ssd和rdma资源池化后的分散式kvcache,利用上述未充分利用的资源实现近gpu前缀缓存,用于提供更大的kvcache容量.
2. **全局调度器Conductor**:负责基于当前kvcache的分布与工作负载情况去分发requst。
3. **以cpp方式处理prefill阶段**:将prefill pool中的每x个节点划分为一个流水线组。之后将每个请求的token划分为若干个chunk，让其在不同节点上并行处理。相较于tp和sp方式，cpp对短上下文不需要引入额外开销，不需要动态调整node分组，所需要的跨界点交流可以与计算开销重叠，更适合长上下文和短上下文的处理。

---

# 关键结论
1. 当运输reuse kvcache的时间小于重新计算kvcache的时间的时候会减小prefill阶段的ttft。
    
$$
T_{transfer} = \frac{p \cdot l \cdot \frac{2d}{gqa} \cdot s}{B}
$$

$$
T_{recompute} = \frac{l \cdot (a p^2 d + b p d^2)}{G}
$$
$$
    T_{transfer} <  T_{recompute}
$$

化简得到

$$
\frac{B}{G}  >  \frac{2ds}{gqa \cdot (apd + bd^2)}
$$
    其中B是加载带宽，G是平均计算吞吐量，p是复用前缀，d是模型维度，gqa是gqa分组数，s是每个元素字节数。
---

# MOONCAKE设计

## 总体架构
由三部分组成分别是:
- prefill/decoding node:分别负责prefill与decoding阶段。
- mooncake store:负责管理并运输kvcache块。
- global conductor:

## 工作流程
Conductor选择一对prefill与decoding实例，然后按照以下方式处理request
1. **kvcache reuse**:将尽可能多的可复用的kvcache传输到算法得出的最短ttft的prefill instance。
2. **Incremental prefill and  kvcache transfer**:完成prefill阶段，在这一阶段可以异步的将处理后的kvcache(包含重复kvcache以及新处理的kvcache)传输到decoding instance。如果未缓存的部分超过了阈值，会以分块流水线的形式处理。
3. **decoding**:decoding阶段加载kvcache，然后将request加入到decoding instance的连续批处理流程中生成回复内容。

## mooncake store
1. **管理kvcache**:所有kvcache会以paged block的形式储存。每个block通常存储16-512个token。mooncake store会在cache pool里为每个cache块分配空间并记录其元信息(如block key,block address)，还会为hot-cache分配副本。当cache pool满的时候采用LRU来淘汰其他block。
2. **transfer engine**:采用拓扑结构的路径选择方案来分发运输任务。在处理请求前，每个服务器会生成一个拓扑矩阵并且将其广播在服务器集群中，这个矩阵中按照各类内存(在内存注册时决定)将网卡分为首选和次选。接着通过当前状况来挑选local and target nics。而一个request的运输会以分片的形式运输，每片分为16KB通过不同的路径运输。最后当某一条特定的链路发生错误时，engine会自动寻找一条替代链路，并重新提交请求。

## prefill pool
基于decoder-only transfomer的自回归机制，采用cpp方式处理长短上下文，将pool中的每x个节点划分为一个流水线组。之后将每个请求的token划分为若干个chunk，让其在不同节点上并行处理。

# 调度方案
## prefill全局调度
对每个请求会将token的block key依次与每个prefill instance所存储的cache key做比较去寻找找到他们的前缀匹配长度prefix_len。conductor会基于请求长度与prefix_len去估算相关的处理时间，之后加上预估的等待时间得到每个prefill instance的ttft。每个request会被分配到最短ttft的prefill instance上执行prefill阶段。具体算法如下:

```
Algorithm 1: KVCache-centric Scheduling Algorithm
Input:  prefill instance pool P, decoding instance pool D,
        request R, cache block size B
Output: the prefill and decoding instances (p, d) to process R

 1: block_keys ← PrefixHash(R.prompt_tokens, B)
 2: TTFT, p ← inf, 0/
 3: best_len, best_instance ← FindBestPrefixMatch(P, block_keys)
 4: for instance ∈ P do
 5:   if best_len / instance.prefix_len > kvcache_balancing_threshold then
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

## cache load balancing
当请求因实例负载过高而未路由到前缀匹配最长的实例时，Conductor 将缓存位置和请求转发给备用的instance（如果估算的额外 prefill 时间小于传输时间），备用instance会主动从缓存持有者拉取 kvcache 并在本地存储。而当best prefill_len不超过local prefill_len * kvcache_balancing_threshold时会倾向于重算token。

