

---

# <!-- 这是一张图片，ocr 内容为：FLASHACCEL: LEVERAGING HIGH-BANDWIDTH FLASH FOR HIGH-THROUGHPUT I UT LLM INFERENCE XINYU WANG YALONG XUE XIAOTIAN SUN INSTITUTE OF COMPUTING TECHNOLOGY, INSTITUTE OF COMPUTING TECHNOLOGY, INSTITUTE OF COMPUTING TECHNOLOGY, CHINESE ACADEMY OF SCIENCES CHINESE ACADEMY OF SCIENCES CHINESE ACADEMY OF SCIENCES BEIJING,CHINA BEIJING, CHINA BEIJING,CHINA UNIVERSITY OF CHINESE ACADEMY OF SCHOOL OF ADVANCED INTERDISCIPLINARY UNIVERSITY OF CHINESE ACADEMY OF SCIENCES SCIENCES SCIENCES,UNIVERSITY OF CHINESE BEIJING,CHINA BEIJINGCHINA ACADEMY OF SCIENCES BEIJING, CHINA SUNXIAOTIAN21S@ICT.AC.CN WANGXINYU22S@ICT.AC.CN XUEYALONG22@MAILS.UCAS.AC.CN XIAOYU ZHANG XUEGI LI CHUNMENG DOU INSTITUTE OF COMPUTING TECHNOLOGY INSTITUTE OF MICROELECTRONICS,CHINESE INSTITUTE OF COMPUTING TECHNOLOGY, CHINESE ACADEMY OF SCIENCES CHINESE ACADEMY OF SCIENCES ACADEMY OF SCIENCES BEIJING,CHINA BEIJING,CHINA BEIJING,CHINA DOUCHUNMENG@IME.CN LIXUEQICT.AC.CN ZHANGXIAOYU@ICT.AC.CN XIAOMING CHEN* INSTITUTE OF COMPUTING TECHNOLOGY, CHINESE ACADEMY OF SCIENCES BEIJING,CHINA CHENXIAOMING@ICT.AC.CN -->
![](https://cdn.nlark.com/yuque/0/2026/png/40624596/1792033203517-3cce06d7-8568-4e06-b3cd-6ff7b0c9a74c.png)
## <font style="color:rgb(17, 17, 17);">一、背景动机</font>
### <font style="color:rgb(17, 17, 17);">1. LLM推理吞吐量受限</font>
+ **<font style="color:rgb(17, 17, 17);">权重和 KV 缓存快速增长：</font>**<font style="color:rgb(17, 17, 17);"> 权重由各请求共享，KV 缓存保存每个请求已经处理过的 token 的注意力键和值；模型越大、上下文越长、并发越多，容量压力越大。</font>
+ **<font style="color:rgb(17, 17, 17);">容量限制批量大小：</font>**<font style="color:rgb(17, 17, 17);"> 论文举例，Qwen3-32B 的 FP16 权重约占 64 GB，H100 的 80 GB 显存只剩约 16 GB。8K 上下文下每请求约需 2 GB KV 缓存，理论上最多容纳约 8 个请求，实际还需留出运行空间。并且HBM容量太小会限制KV Cache的复用机会，服务更多请求时，KV Cache会被频繁驱逐，导致Cache hit下降。当前用的LLM推理系统常常互联多个GPU来缓解压力，但是这样做故障率会提升。</font>
+ **<font style="color:rgb(17, 17, 17);">更大批量提高吞吐：</font>**<font style="color:rgb(17, 17, 17);"> decode 每步为每个请求生成一个 token。同批请求共享权重读取，批量增大可提高算术强度和 GPU 利用率；保留历史 KV 缓存还可减少多轮对话中的 prefill 重算。更大的内存才能支持更大的batch size。</font>

<!-- 这是一张图片，ocr 内容为： -->
![](https://cdn.nlark.com/yuque/0/2026/png/40624596/1791892131323-4fdbe6a8-a497-4023-94ee-9b69b48bc9f5.png)

_<font style="color:rgb(17, 17, 17);">原论文图 2 批处理与 KV 复用的收益。左图使用 8 层 Qwen3-32B，并非完整模型。</font>_

### <font style="color:rgb(17, 17, 17);">2. HBF 的机会与核心问题</font>
+ **<font style="color:rgb(17, 17, 17);">机会：</font>**<font style="color:rgb(17, 17, 17);"> 高带宽闪存 HBF 用大量 NAND 平面并行读取，兼顾大容量与高带宽。论文建模的单堆栈为 192 GB、768 GB/s，容量约为对照 HBM 堆栈的 8 倍。并且在耐久性方向上论文中根据统计结果说明一个1 TB SLC方式的HBF要承受55TB的负载，但是SLC闪存可以支持平均每天55次P/E循环，因此可以满足推理工作负载。</font>
+ **<font style="color:rgb(17, 17, 17);">挑战 1 访问延迟高：</font>**<font style="color:rgb(17, 17, 17);"> 即便HBF的读取带宽与HBM相近，但HBF 读延迟约 4 μs，HBM 约 100 ns，相差约 40 倍；这样会让 GPU 等待数据。</font>
+ **<font style="color:rgb(17, 17, 17);">挑战 2 并行度难利用：</font>**<font style="color:rgb(17, 17, 17);"> HBF需要用4 μs读取一个4KB页，一个plane的带宽就是</font>1 GB/s，要达到更高的聚合带宽就得利用更多的plane。论文里面定义了新的逻辑访问单位超页：聚合每个平面的一个页面。尽量顺序访问多个超页可以提高带宽利用率.总体的读取延迟应该由所有平面中的最大负载所决定。
+ <!-- 这是一张图片，ocr 内容为：(A) PLANE-3071PLANE-3072 PLANE-4915 PLANE-0 PLANE-1 PAGE PAGE PAGE PAGE PAGE ... HYPER PAGE A WEIGHT T HT TENSOR ONLY OCCUPIES 2/3 OF A HYPER PAGE -->
![](https://cdn.nlark.com/yuque/0/2026/png/40624596/1792030700196-beacfa3a-9cdb-49c5-9bea-4066c22ca012.png)
+ **<font style="color:rgb(17, 17, 17);">挑战 3 异构资源难管理：</font>**<font style="color:rgb(17, 17, 17);"> 既要保存 HBF 中的持久化对象，又要协调 HBF、HBM 和 SRAM 的数据访问与迁移。</font>

## <font style="color:rgb(17, 17, 17);">二、设计方案</font>
### <font style="color:rgb(17, 17, 17);">1. 改进机会</font>
+ <font style="color:rgb(17, 17, 17);">权重基本只读，request执行顺序可用于提前安排数据布局和提前预取。KV 缓存则主要追加新 token，可按活跃请求统一组织。</font>
+ <font style="color:rgb(17, 17, 17);">HBF 存放权重与大部分 KV 缓存，HBM 存放频繁更新的小数据和少量热点 KV，SRAM 暂存下一轮即将计算的数据。</font>

### <font style="color:rgb(17, 17, 17);">2. 系统概览</font>
<!-- 这是一张图片，ocr 内容为： -->
![](https://cdn.nlark.com/yuque/0/2026/png/40624596/1791892131397-6b6f2256-852a-4131-8205-5601d9068794.png)

_<font style="color:rgb(17, 17, 17);">原论文图 6 GPU 与 HBF 的集成方式，以及 HBF 内部的 SRAM 缓存。</font>_

+ **<font style="color:rgb(17, 17, 17);">两种集成方式：</font>**<font style="color:rgb(17, 17, 17);"> CLI 用 5 个 HBF 堆栈替换原有 6 个 HBM 中的 5 个，保留 1 个 HBM；CSI 通过 HBM 基底级联 6 个 HBF，保留 6 个 HBM 堆栈，但将各 HBM 缩为 2 层 DRAM 以降低成本。</font>
+ **<font style="color:rgb(17, 17, 17);">缓存位置：</font>**<font style="color:rgb(17, 17, 17);"> 每个 HBF 堆栈含 8 个 Flash 裸片，每片 96 个平面；每平面配置 32 KB SRAM，基底另有 8 MB SRAM，单堆栈总计约 32 MB，用于预取与双缓冲。</font>

### <font style="color:rgb(17, 17, 17);">3. 权重布局按执行顺序连续铺开</font>
+ **<font style="color:rgb(17, 17, 17);">具体做法：</font>**<font style="color:rgb(17, 17, 17);"> 把权重切成闪存页大小，按算子执行顺序轮询分配到各平面；下一个算子接着上一个算子的结束位置继续放。连续预取时可同时利用更多平面，减少串行读取。</font>
+ <!-- 这是一张图片，ocr 内容为：OP B OP A OP C EXECUTION C1 CO C2 A1 A2 B1 ORDER BO AO ROUND ROBIN LAYOUT STATIC DATA AO A2 A1 BO - SPLIT INTO 3 PAGES ALL PLANES OF B1 C1 C2 CO ALL CHANNELS PLANE I PLANE PLANE PLANE -->
![](https://cdn.nlark.com/yuque/0/2026/png/40624596/1792031497054-8c41f3b0-8b8c-40fa-99be-5ef9839d93c8.png)



### <font style="color:rgb(17, 17, 17);">4. KV 缓存动态均衡与超页访问</font>
<font style="color:rgb(17, 17, 17);">请求会不断加入和退出，只把数据最初均匀写入还不够。FlashAccel 将当前活跃请求的 KV 块组成统一集合，按下图的五个步骤处理。</font>

<!-- 这是一张图片，ocr 内容为： -->
![](https://cdn.nlark.com/yuque/0/2026/png/40624596/1791892131397-0e163d8d-14ba-469f-8fa9-361308906821.png)

_<font style="color:rgb(17, 17, 17);">原论文图 8 KV 缓存的写入、迁移、读取与回写流程。</font>_

+ **<font style="color:rgb(17, 17, 17);">① 写入 HBF：</font>**<font style="color:rgb(17, 17, 17);"> 将新进入的 KV 块尽量凑成完整超页再写入，不足一超页的剩余块随机分布，避免集中在少数平面。</font>
+ **<font style="color:rgb(17, 17, 17);">② 迁移到 HBM：</font>**<font style="color:rgb(17, 17, 17);"> 统计当前活跃 KV 在各平面的负载，把超过平均负载的页迁到 HBM。这样能缓解热点，同时避免为重新均衡而额外写入 Flash。</font>
+ **<font style="color:rgb(17, 17, 17);">③ 读取并计算：</font>**<font style="color:rgb(17, 17, 17);"> 按超页读取 HBF，再并行计算各 KV 块的局部注意力结果，最后按请求归并；迁到 HBM 的少量 KV 块在同一步读取。</font>
+ **<font style="color:rgb(17, 17, 17);">④⑤ 缓冲与回写：</font>**<font style="color:rgb(17, 17, 17);"> 新生成的 KV 先存 HBM，积累成足够的完整块和超页后再批量写回 HBF。论文采用 256 KB KV 块，在平面均衡、HBM 占用和内部碎片之间折中。</font>

### <font style="color:rgb(17, 17, 17);">5. SRAM 预取</font>
<font style="color:rgb(51, 51, 51);">将数据预取到 SRAM，在返回地址上执行计算，然后释放 SRAM 资源。对于大于 SRAM 容量的数据对象，运行时将其划分为多个可放入 SRAM 的较小分块，并依次执行。</font><font style="color:rgb(17, 17, 17);">按“预取下一块 → 计算当前块 → 释放已用块”循环。运行时把预取操作按计算图顺序放入异步队列，尽量用计算时间覆盖 Flash 读取。</font>

<!-- 这是一张图片，ocr 内容为： -->
![](https://cdn.nlark.com/yuque/0/2026/png/40624596/1791892131394-56f6d667-0e2d-4c9a-b18b-d35a3f2cdec9.png)

_<font style="color:rgb(17, 17, 17);">原论文图 12 权重分块、异步预取队列，以及预取与计算的重叠。</font>_

### <font style="color:rgb(17, 17, 17);">6. 存储管理与编程接口</font>
+ **<font style="color:rgb(17, 17, 17);">持久化管理：</font>**<font style="color:rgb(17, 17, 17);"> FTL对HBF的开销很大，需要一个GB级别的L2F表存在SRAM或者DRAM中。把权重和每个请求的 KV 缓存分别作为对象，利用只读或追加写特征，直接在对象元数据中记录物理 Flash 地址，省去传统 FTL 的一层映射。不同对象使用独立擦除块，删除某请求时减少对其他数据的影响。</font>
+ **<font style="color:rgb(17, 17, 17);">统一地址空间：</font>**<font style="color:rgb(17, 17, 17);"> NandMmap 映射权重对象到虚拟空间；GroupCreate</font><font style="color:rgb(51, 51, 51);">在逻辑上将同一推理步骤内活跃请求的 KV 缓存对象合并为一个组对象</font><font style="color:rgb(17, 17, 17);">；GroupMmap 将活跃请求的 KV 组织为可按超页访问的连续逻辑地址；GroupArrange 实现4里面所说的卸载机制，GroupWrite 追加写，将数据尽可能按照超页的形式写到HBF；SramPrefetch 与 SramRelease 管理预取缓存，页表跟随数据位置更新。</font>



## <font style="color:rgb(17, 17, 17);">三、实验结果</font>
**<font style="color:rgb(17, 17, 17);">平台与方法：</font>**<font style="color:rgb(17, 17, 17);"> 基于 LLMCompass、ScaleSim 和 NAND模拟器进行事件驱动仿真，在LLMCompass上构建了事件驱动模拟器并且修改了内存模型，让其模拟LLM推理延迟以及闪存和SRAM中数据访问的延迟；对照为 DGX-H200 的 8 张 H200，每卡 141 GB HBM、4.8 TB/s内存带宽。</font>

**<font style="color:rgb(17, 17, 17);">模型与负载：</font>**<font style="color:rgb(17, 17, 17);"> Qwen3-235B、Qwen3-Coder-480B、LLaMA3.1-405B、DeepSeek-V3；除 DeepSeek-V3 权重为 FP8，其余采用 FP16。输入/输出长度为 8.11K/2.53K 和 15K/6K。</font>

<!-- 这是一张图片，ocr 内容为： -->
![](https://cdn.nlark.com/yuque/0/2026/png/40624596/1791892131373-7d17ddf1-62d7-4ca6-a78c-35c55fb9fc06.png)

_<font style="color:rgb(17, 17, 17);">原论文图 13 不同配置的每 GPU 解码吞吐量，按 8×H200 归一化。</font>_

<!-- 这是一张图片，ocr 内容为：8XCSI 8XH200 8X CLI NORMALIZED TOKENS/J TO 8XH200 3 2 0 8.11K 15K 8.11KL 15K 15K 15K 8.11K 8.11K 2.53K 2.53K 2.53K 2.53K 6K 6K 6K 6K DEEPSEEKV3 QWEN3 235B LLAMA3.1 405B QWEN3 480B -->
![](https://cdn.nlark.com/yuque/0/2026/png/40624596/1792034330935-b84b01e0-6b95-4a6c-8ae1-0188e9a50075.png)

_<font style="color:rgb(17, 17, 17);">功耗图</font>_

<font style="color:rgb(17, 17, 17);">以下为 100 ms 解码每步延迟约束下的平均结果；每种配置使用满足延迟和容量限制的最大批量。</font>

| **<font style="color:rgb(17, 17, 17);">配置</font>** | **<font style="color:rgb(17, 17, 17);">每 GPU 吞吐量</font>** | **<font style="color:rgb(17, 17, 17);">能效 token/J</font>** |
| --- | --- | --- |
| <font style="color:rgb(17, 17, 17);">8×H200</font> | <font style="color:rgb(17, 17, 17);">1.00 倍</font> | <font style="color:rgb(17, 17, 17);">1.00 倍</font> |
| **<font style="color:rgb(17, 17, 17);">8×CSI</font>** | **<font style="color:rgb(17, 17, 17);">2.54 倍</font>** | **<font style="color:rgb(17, 17, 17);">1.93 倍</font>** |
| <font style="color:rgb(17, 17, 17);">8×CLI</font> | <font style="color:rgb(17, 17, 17);">2.04 倍</font> | <font style="color:rgb(17, 17, 17);">1.66 倍</font> |


<font style="color:rgb(17, 17, 17);"></font>

<!-- 这是一张图片，ocr 内容为：G COMPUTATION HIT RATE(%) CSIOKVCACHE H200 CLI NORMALIZED TOKENS 100 O CACHE HIT RATE 80 60 40 5 REQUIRING 20 O 0 4X8X16X 8 4 X 8 X CSI CLI CSI H200H200H200 CLI -->
![](https://cdn.nlark.com/yuque/0/2026/png/40624596/1792034270545-444c7e1d-716f-4a67-b1ac-a2ce2580f3f2.png)

+ **<font style="color:rgb(17, 17, 17);">KV 复用：</font>**<font style="color:rgb(17, 17, 17);"> 在论文多轮交互轨迹上，8×CLI 与 8×CSI 能缓存所有会话，达到该轨迹的理想命中率；相对 8×H200，需要实际计算的 token 数最多减少 89%。</font>







