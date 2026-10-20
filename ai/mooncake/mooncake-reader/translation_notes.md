# Translation Notes — Mooncake (FAST '25)

## 翻译范围
- **全文翻译:** 是（覆盖所有章节，含致谢与参考文献）
- **翻译块数:** 51 个主要源块（S001–S042，含 S025a/b, S026a–d, S027a, S035a），1 个算法块（A001），1 个表格块（T001），2 个公式块（E001–E002）
- **提取方式:** pdftotext 文本层提取（高质量，非 OCR）
- **补充日期:** 2026-08-12

## 本次补充的章节 / Sections Supplemented

以下内容在初始 paper.md 中缺失或过于精简，现已补充完整：

1. **Table 1 (T001)** — 符号与参数表，含 LLaMA3-70B / 8×A800 的具体参数值
2. **§3.2.3 Network Setup (S025a)** — 网络配置：HGX、RoCEv2、与 NCCL 的对比
3. **§3.2.3 Failure Handling (S025b)** — 多 NIC 故障恢复机制
4. **§3.3 扩展 (S026a–d)** — 从 1 个压缩 block 拆分为 4 个独立 block：
   - 为何维持解耦架构 vs chunked prefill
   - TP 跨节点的昂贵 all-reduce 问题
   - SP 的局限性（短输入 MFU 低）
   - CPP 设计与首次在推理阶段应用 pipeline parallelism
5. **§4.1 Algorithm 1 (A001)** — KVCache 中心调度算法伪代码
6. **§4.1 调度框架细节 (S027a)** — 预测模型、排队时间计算、传输时间预测的挑战
7. **§5.2.1 工作负载详细描述** — 三种工作负载的详细构建方式和特征
8. **§5.3.3 Cache Replica (S035a)** — 缓存副本数量分布分析（全新子节）
9. **§5.4.2 扩展 (S037)** — 带宽需求模拟实验细节
10. **§5.4.3 扩展 (S038)** — E2E 延迟五组件分解
11. **§6 扩展 (S040)** — 按生产级系统、前缀缓存、并发工作三方向详细梳理
12. **Acknowledgments (S042)** — 致谢与基金信息
13. **References (REF)** — 43 条完整参考文献

## 不确定项 / Low Confidence Items
- 无。PDF 文本层质量良好，所有公式和数字完整可读。

## 未包含内容
- **Figures:** 未提取图片（缺少 pdftoppm）。原文图片可在原 PDF 中查看（共 15 张图，已全部索引）。
- **公式 (3)-(4):** Algorithm 1 中的伪代码已用完整算法块呈现。

## 术语一致性
术语表（16 条）已在 paper.md 头部建立并全文保持一致性。

## 文件清单
- [x] paper.md — 全文双语阅读器（已补充）
- [x] source_map.json — 块锚点索引（已更新至 51 个源块 + 1 算法 + 2 表格）
- [x] translation_notes.md — 本文件（已更新）
- [ ] assets/ — 图片提取（未生成，缺少 pdftoppm）
