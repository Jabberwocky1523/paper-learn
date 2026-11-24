const pptxgen = require('/home/Jabberwocky/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/pptxgenjs');
const { imageSize } = require('/home/Jabberwocky/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/image-size');
const fs = require('fs');
const path = require('path');

const pptx = new pptxgen();
pptx.defineLayout({ name: 'SWISS_WIDE', width: 13.333, height: 7.5 });
pptx.layout = 'SWISS_WIDE';
pptx.author = '研究生课堂文献汇报';
pptx.company = 'FlashAccel Reading Group';
pptx.subject = 'FlashAccel: Leveraging High-Bandwidth Flash for High-Throughput LLM Inference';
pptx.title = 'FlashAccel 课堂文献汇报';
pptx.lang = 'zh-CN';
pptx.theme = {
  headFontFace: 'Microsoft YaHei',
  bodyFontFace: 'Microsoft YaHei',
  lang: 'zh-CN'
};
pptx.defineSlideMaster({
  title: 'SWISS',
  background: { color: 'FAFAF8' },
  objects: []
});

const C = {
  paper: 'FAFAF8', paper2: 'F0F0EE', ink: '0A0A0A', body: '252524',
  secondary: '525252', helper: '737373', line: 'D4D4D2', subtle: 'E0E0E0',
  accent: '002FA7', accentDeep: '001D6B', accentSoft: 'D5DEEF', white: 'FFFFFF',
  green: '61A86F', orange: 'F28C28', red: 'D94D52'
};
const FONT = 'Microsoft YaHei';
const MONO = 'Aptos Mono';
const OUT = path.join(__dirname, 'FlashAccel_课堂汇报.pptx');
const ASSETS = path.resolve(__dirname, '..', 'FlashAccel_assets');
const TOTAL = 14;

function fig(n) { return path.join(ASSETS, `figure-${String(n).padStart(2, '0')}.png`); }
function addText(slide, text, x, y, w, h, opts = {}) {
  slide.addText(text, {
    x, y, w, h, fontFace: opts.fontFace || FONT, fontSize: opts.fontSize || 18,
    color: opts.color || C.ink, bold: opts.bold || false, margin: opts.margin ?? 0,
    breakLine: false, valign: opts.valign || 'mid', align: opts.align || 'left',
    fit: opts.fit || 'shrink', paraSpaceAfterPt: opts.paraSpaceAfterPt || 0,
    lineSpacingMultiple: opts.lineSpacingMultiple || 1.0,
    italic: opts.italic || false, underline: opts.underline || false,
    isTextBox: true, ...opts
  });
}
function line(slide, x1, y1, x2, y2, color = C.line, width = 1, dash = 'solid') {
  slide.addShape(pptx.ShapeType.line, { x: x1, y: y1, w: x2 - x1, h: y2 - y1, line: { color, width, dashType: dash, beginArrowType: 'none', endArrowType: 'none' } });
}
function rect(slide, x, y, w, h, fill, opts = {}) {
  slide.addShape(pptx.ShapeType.rect, { x, y, w, h, fill: { color: fill, transparency: opts.transparency || 0 }, line: { color: opts.lineColor || fill, transparency: opts.lineTransparency ?? 100, width: opts.lineWidth || 0 }, radius: 0 });
}
function squareMatrix(slide, x, y, cols, rows, size, gap, color, transparency = 70) {
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    slide.addShape(pptx.ShapeType.rect, { x: x + c * (size + gap), y: y + r * (size + gap), w: size, h: size, fill: { color, transparency }, line: { transparency: 100 } });
  }
}
function chrome(slide, page, section, opts = {}) {
  const color = opts.inverse ? C.white : C.helper;
  addText(slide, `FLASHACCEL  /  ${section.toUpperCase()}`, 0.66, 0.24, 7.6, 0.22, { fontFace: MONO, fontSize: 9.5, color, charSpacing: 1.5, bold: true });
  addText(slide, `${String(page).padStart(2, '0')} / ${TOTAL}`, 11.82, 0.24, 0.85, 0.22, { fontFace: MONO, fontSize: 9.5, color, align: 'right', charSpacing: 1.2, bold: true });
  line(slide, 0.66, 0.55, 12.67, 0.55, opts.inverse ? 'FFFFFF' : C.subtle, 0.6);
}
function pageBase(page, section, opts = {}) {
  const slide = pptx.addSlide('SWISS');
  slide.background = { color: opts.bg || C.paper };
  chrome(slide, page, section, { inverse: opts.inverse });
  return slide;
}
function title(slide, kicker, heading, opts = {}) {
  addText(slide, kicker.toUpperCase(), 0.66, opts.y || 0.74, 4.7, 0.25, { fontFace: MONO, fontSize: 10, color: opts.inverse ? C.white : C.accent, bold: true, charSpacing: 1.4 });
  addText(slide, heading, 0.66, (opts.y || 0.74) + 0.31, opts.w || 11.6, opts.h || 0.72, { fontSize: opts.fontSize || 28, color: opts.inverse ? C.white : C.ink, bold: false, breakLine: false, fit: 'shrink', valign: 'top' });
}
function source(slide, text, opts = {}) {
  addText(slide, text, opts.x || 0.66, opts.y || 7.10, opts.w || 11.95, 0.16, { fontFace: MONO, fontSize: 8.5, color: opts.inverse ? 'D5DEEF' : C.helper, charSpacing: 0.4, italic: false });
}
function addImageContain(slide, imgPath, x, y, w, h, opts = {}) {
  const dim = imageSize(fs.readFileSync(imgPath));
  const ar = dim.width / dim.height;
  const box = w / h;
  let iw, ih, ix, iy;
  if (ar > box) { iw = w; ih = w / ar; ix = x; iy = y + (h - ih) / 2; }
  else { ih = h; iw = h * ar; ix = x + (w - iw) / 2; iy = y; }
  if (opts.bg) rect(slide, x, y, w, h, opts.bg);
  slide.addImage({ path: imgPath, x: ix, y: iy, w: iw, h: ih, transparency: opts.transparency || 0 });
  if (opts.topLine) rect(slide, x, y, w, 0.03, opts.topLine);
}
function note(slide, { title, purpose, talk, transition, minutes }) {
  slide.addNotes([
    `【${title}】`,
    `[页面目的] ${purpose}`,
    `[建议时长] ${minutes} 分钟`,
    '[讲述要点]',
    ...talk.map((t, i) => `${i + 1}. ${t}`),
    `[转场] ${transition}`
  ].join('\n'));
}
function bulletList(slide, items, x, y, w, h, opts = {}) {
  const runs = [];
  items.forEach((it, i) => {
    runs.push({ text: `${it.title}  `, options: { bold: true, color: it.color || C.ink, breakLine: false } });
    runs.push({ text: it.body, options: { color: opts.color || C.secondary, breakLine: i < items.length - 1, bullet: { indent: 14 }, hanging: 3 } });
  });
  slide.addText(runs, { x, y, w, h, fontFace: FONT, fontSize: opts.fontSize || 15, color: opts.color || C.secondary, margin: 0.05, breakLine: false, valign: 'top', fit: 'shrink', paraSpaceAfterPt: 10, lineSpacingMultiple: 1.04 });
}
function kpi(slide, x, y, w, number, label, body, accent = false) {
  rect(slide, x, y, w, 0.025, accent ? C.accent : C.ink);
  addText(slide, label.toUpperCase(), x, y + 0.12, w, 0.23, { fontFace: MONO, fontSize: 8.5, color: accent ? C.accent : C.helper, bold: true, charSpacing: 1.2 });
  addText(slide, number, x, y + 0.38, w, 0.58, { fontFace: 'Aptos', fontSize: 30, color: accent ? C.accent : C.ink, bold: false, valign: 'top' });
  addText(slide, body, x, y + 1.01, w, 0.52, { fontSize: 10.5, color: C.secondary, valign: 'top', breakLine: true });
}

// 01 · Cover / S01
{
  const slide = pptx.addSlide();
  slide.background = { color: C.accent };
  squareMatrix(slide, 8.9, 0.55, 13, 10, 0.08, 0.13, C.white, 76);
  addText(slide, 'FLASHACCEL  /  PAPER REVIEW', 0.72, 0.38, 6.0, 0.24, { fontFace: MONO, fontSize: 9, color: 'D5DEEF', bold: true, charSpacing: 1.8 });
  addText(slide, '01 / 14', 11.82, 0.38, 0.78, 0.24, { fontFace: MONO, fontSize: 9, color: 'D5DEEF', bold: true, align: 'right' });
  addText(slide, 'FlashAccel', 0.72, 1.46, 8.7, 0.84, { fontFace: 'Aptos', fontSize: 44, color: C.white, bold: false, valign: 'top' });
  addText(slide, '利用高带宽闪存实现\n高吞吐 LLM 推理', 0.72, 2.34, 9.8, 1.55, { fontSize: 34, color: C.white, bold: false, breakLine: true, valign: 'top' });
  addText(slide, 'Leverage capacity · recover bandwidth · hide latency', 0.76, 4.18, 7.7, 0.36, { fontFace: 'Aptos', fontSize: 15, color: 'D5DEEF', italic: true });
  line(slide, 0.72, 5.42, 12.55, 5.42, '6E8DD4', 0.8);
  addText(slide, '研究生课堂文献汇报', 0.72, 5.65, 4.5, 0.32, { fontSize: 13, color: C.white, bold: true });
  addText(slide, 'Xinyu Wang et al. · arXiv:2607.10186v1 · 2026', 0.72, 6.09, 8.5, 0.25, { fontFace: MONO, fontSize: 8.5, color: 'D5DEEF' });
  addText(slide, '汇报人：________', 10.1, 5.65, 2.45, 0.32, { fontSize: 12, color: C.white, align: 'right' });
  note(slide, { title: 'FlashAccel', purpose: '用一句话建立论文主题：用 HBF 的容量换取更大的批量与 KV 复用，但必须通过协同设计把延迟和带宽问题补回来。', minutes: 0.4, talk: ['FlashAccel 面向的是数据中心高吞吐推理，而不是把 SSD 简单接到 GPU。', '汇报主线是“容量如何真正转化为吞吐量”。'], transition: '先看为什么现有 HBM 容量会直接卡住吞吐。' });
}

// 02 · Capacity bottleneck / S03
{
  const slide = pageBase(2, 'Motivation');
  title(slide, '01 · Capacity bottleneck', '瓶颈不只是算力，更是 HBM 容量');
  rect(slide, 0.66, 1.77, 4.3, 4.86, C.accent);
  addText(slide, '80 GB', 1.02, 2.08, 3.5, 0.70, { fontFace: 'Aptos', fontSize: 38, color: C.white });
  addText(slide, 'H100 HBM', 1.05, 2.76, 3.2, 0.23, { fontFace: MONO, fontSize: 9, color: 'D5DEEF', bold: true, charSpacing: 1.2 });
  rect(slide, 1.03, 3.31, 3.47, 0.75, C.accentDeep);
  addText(slide, '64 GB  模型权重', 1.21, 3.42, 3.05, 0.42, { fontSize: 18, color: C.white, bold: true });
  rect(slide, 1.03, 4.19, 3.47, 0.50, C.white);
  addText(slide, '仅余 16 GB', 1.21, 4.24, 3.05, 0.34, { fontSize: 17, color: C.accent, bold: true });
  addText(slide, '8K context ≈ 2 GB KV / request\n→ 理论 batch ≤ 8', 1.05, 5.04, 3.4, 0.92, { fontSize: 16, color: C.white, breakLine: true, valign: 'top' });
  addImageContain(slide, fig(2), 5.35, 1.82, 7.29, 2.35, { bg: C.paper, topLine: C.accent });
  addText(slide, '容量不足带来两次损失', 5.38, 4.45, 5.7, 0.36, { fontSize: 20, bold: false });
  addText(slide, 'Batch 小', 5.38, 4.96, 1.15, 0.27, { fontSize: 14.5, bold: true });
  addText(slide, 'decode 的算术强度与 GPU 利用率上不去。', 6.55, 4.96, 5.48, 0.27, { fontSize: 13.5, color: C.secondary });
  addText(slide, 'KV 易驱逐', 5.38, 5.40, 1.15, 0.27, { fontSize: 14.5, bold: true });
  addText(slide, '多轮会话无法复用历史 KV，prefill 被迫重算。', 6.55, 5.40, 5.48, 0.27, { fontSize: 13.5, color: C.secondary });
  addText(slide, '核心问题：如何把“更大容量”变成“更高吞吐”？', 5.38, 6.24, 6.4, 0.35, { fontSize: 16, color: C.accent, bold: true });
  source(slide, 'Source: FlashAccel §2.2, Fig. 2. Qwen3-32B example uses FP16 weights.');
  note(slide, { title: 'HBM 容量瓶颈', purpose: '把容量限制与 batch、KV 复用和吞吐量连起来。', minutes: 1.1, talk: ['论文用 Qwen3-32B 举例：FP16 权重约 64GB，80GB H100 只余约 16GB。', '8K 上下文每请求约 2GB KV，理论 batch 上限约 8，实际还要给中间结果留空间。', '更大的 batch 让多个请求共享同一次权重读取；更大的 KV 容量还能减少多轮交互重算。'], transition: 'HBF 提供大容量和接近 HBM 的峰值带宽，但它自身有三个硬伤。' });
}

// 03 · Three challenges / S13
{
  const slide = pageBase(3, 'Challenges');
  title(slide, '02 · HBF is not free', 'HBF 有容量，但不是免费午餐');
  const cards = [
    { n: '40×', t: '访问延迟', d: 'HBF 首批数据约 4 μs；HBM 约 100 ns。对 4K×4K FP8 GEMV，额外延迟可使端到端时延增加约 50%。' },
    { n: '4,916', t: '并行度门槛', d: '单 plane 读 4KB / 4μs，仅约 1 GB/s。要匹配 H200 的 4.8 TB/s，需要数千 plane 同时工作。' },
    { n: '52%', t: '负载偏斜', d: '活跃请求集合持续变化，KV 在 plane 间失衡；论文模型中最大负载可高出平均值 52%，直接损失带宽。' }
  ];
  cards.forEach((c, i) => {
    const x = 0.66 + i * 4.02;
    rect(slide, x, 1.82, 3.72, 4.55, i === 2 ? C.accent : C.paper2);
    addText(slide, `0${i + 1}`, x + 0.22, 2.03, 0.54, 0.26, { fontFace: MONO, fontSize: 9, color: i === 2 ? C.white : C.helper, bold: true });
    addText(slide, c.n, x + 0.22, 2.47, 3.1, 0.76, { fontFace: 'Aptos', fontSize: i === 1 ? 33 : 38, color: i === 2 ? C.white : C.accent, bold: false });
    addText(slide, c.t, x + 0.22, 3.39, 3.0, 0.35, { fontSize: 19, color: i === 2 ? C.white : C.ink, bold: true });
    line(slide, x + 0.22, 3.92, x + 3.40, 3.92, i === 2 ? '6E8DD4' : C.line, 0.8);
    addText(slide, c.d, x + 0.22, 4.18, 3.12, 1.55, { fontSize: 13.5, color: i === 2 ? C.white : C.secondary, breakLine: true, valign: 'top' });
  });
  addText(slide, 'CAPACITY ≠ THROUGHPUT', 0.66, 6.58, 7.2, 0.34, { fontFace: 'Aptos', fontSize: 20, color: C.accent, bold: true, charSpacing: 1.3 });
  source(slide, 'Source: FlashAccel §3.1–3.3. 4,916 planes and 52% are paper-model results.');
  note(slide, { title: 'HBF 的三个挑战', purpose: '说明峰值带宽与有效带宽之间的差距来自延迟、并行度和动态负载。', minutes: 1.1, talk: ['第一，Flash 固有延迟约比 HBM 高 40 倍。', '第二，峰值带宽建立在数千 plane 并行的前提上，数据布局稍有偏斜就吃不满。', '第三，KV cache 的活跃集合动态变化，静态均匀放置不能保证后续仍然均衡。'], transition: 'FlashAccel 的答案不是单个技巧，而是硬件、布局和系统三层协同。' });
}

// 04 · Co-design / S05
{
  const slide = pageBase(4, 'Co-design');
  title(slide, '03 · Design thesis', '让 HBF 持续并行，并把 4 μs 藏起来');
  const blocks = [
    { x: 0.66, bg: C.accent, fg: C.white, label: 'ARCHITECTURE', ttl: 'SRAM 预取缓冲', body: '在每个 plane 与 base die 放置 SRAM；用双缓冲把 Flash 访问与计算重叠。' },
    { x: 4.82, bg: C.paper2, fg: C.ink, label: 'DATA LAYOUT', ttl: '权重 + KV 专用布局', body: '权重按执行顺序轮转铺开；KV 按活跃请求统一组织并动态再平衡。' },
    { x: 8.98, bg: C.ink, fg: C.white, label: 'SYSTEM', ttl: '存储层 + 编程模型', body: '持久化对象、统一虚拟地址与预取接口共同协调 HBF、HBM、SRAM。' }
  ];
  blocks.forEach((b, i) => {
    rect(slide, b.x, 2.02, 3.68, 3.78, b.bg);
    addText(slide, `0${i + 1}  /  ${b.label}`, b.x + 0.25, 2.28, 3.1, 0.24, { fontFace: MONO, fontSize: 8.5, color: b.fg, bold: true, charSpacing: 1.0 });
    addText(slide, b.ttl, b.x + 0.25, 3.08, 3.1, 0.78, { fontSize: 23, color: b.fg, bold: false, valign: 'top' });
    addText(slide, b.body, b.x + 0.25, 4.47, 3.05, 0.95, { fontSize: 13.5, color: b.fg, breakLine: true, valign: 'top' });
  });
  line(slide, 1.15, 6.35, 12.15, 6.35, C.line, 1);
  ['HBF：权重 / 大部分 KV', 'HBM：更新频繁的小数据 / 热点 KV', 'SRAM：下一块即将计算的数据'].forEach((t, i) => {
    const x = 0.82 + i * 4.15;
    rect(slide, x, 6.20, 0.12, 0.12, i === 0 ? C.accent : i === 1 ? C.ink : C.helper);
    addText(slide, t, x + 0.2, 6.11, 3.65, 0.32, { fontSize: 11, color: C.secondary });
  });
  source(slide, 'Source: FlashAccel overview, §4–§6.');
  note(slide, { title: '三层协同设计', purpose: '给后续技术细节建立路线图。', minutes: 0.8, talk: ['架构层解决首访延迟，数据布局层解决 plane 并行度，系统层解决持久化和异构资源管理。', '三种存储各司其职：HBF 放大容量，HBM 处理低延迟更新，SRAM 承接预取。'], transition: '先看这三种资源在硬件上如何组合。' });
}

// 05 · Architecture / S22
{
  const slide = pageBase(5, 'Hardware');
  title(slide, '04 · Hardware integration', 'HBF + HBM + GPU：两种集成路径');
  addImageContain(slide, fig(6), 0.66, 1.68, 12.01, 2.40, { bg: C.paper, topLine: C.accent });
  kpi(slide, 0.66, 4.42, 3.66, '8', 'Flash dies / stack', '每个 HBF stack 在 base die 上堆叠 8 个 Flash die。');
  kpi(slide, 4.83, 4.42, 3.66, '96', 'Planes / die', '扩大 plane 级并行度，是高聚合带宽的基础。');
  kpi(slide, 9.00, 4.42, 3.67, '32 MB', 'SRAM / stack', '每 plane 32KB + base die 8MB，支持基本双缓冲。', true);
  addText(slide, 'CLI：替换 5/6 HBM，成本更低但总带宽少 16.7%', 0.66, 6.25, 5.75, 0.28, { fontSize: 11, color: C.secondary });
  addText(slide, 'CSI：保留更多 HBM，通过 base die 级联 HBF', 6.90, 6.25, 5.77, 0.28, { fontSize: 11, color: C.secondary, align: 'right' });
  source(slide, 'Source: FlashAccel Fig. 6, Table 2. SRAM total is approximately 32 MB per stack.');
  note(slide, { title: 'FlashAccel 硬件架构', purpose: '解释 CLI、CSI 以及 SRAM 缓冲的位置。', minutes: 1.1, talk: ['CLI 把 HBF 与 GPU 共置并替换大部分 HBM；CSI 通过 HBM base die 级联 HBF，保留更多 HBM。', '每个 HBF stack 有 8 个 Flash die，每 die 96 个 plane。', 'SRAM 总容量按至少 2×峰值带宽×读取延迟配置，以保证双缓冲。'], transition: '硬件提供并行资源，下一步要用正确的权重布局把这些 plane 同时喂满。' });
}

// 06 · Weight layout / S03 adapted
{
  const slide = pageBase(6, 'Weight layout');
  title(slide, '05 · Static weights', '按算子执行顺序，跨 plane 轮转铺开');
  addImageContain(slide, fig(7), 0.78, 1.70, 11.77, 2.46, { bg: C.paper, topLine: C.accent });
  rect(slide, 0.78, 4.48, 3.42, 1.68, C.accent);
  addText(slide, 'A0 / A1 / A2', 1.04, 4.78, 2.9, 0.45, { fontFace: 'Aptos', fontSize: 24, color: C.white });
  addText(slide, '算子 A 的静态模型权重\n被切成 page-sized units', 1.04, 5.31, 2.78, 0.62, { fontSize: 12.5, color: C.white, breakLine: true, valign: 'top' });
  bulletList(slide, [
    { title: '离线确定顺序', body: '给定模型的每步计算图固定，可预先获得 op 执行顺序。' },
    { title: '全局轮转映射', body: '当前 op 从上一个 op 的下一 plane 继续放置，跨 channel / plane 近似均衡。' },
    { title: '顺序预取', body: '读取顺序与物理布局一致，降低最大 plane load。' }
  ], 4.68, 4.43, 7.52, 1.65, { fontSize: 13.3 });
  addText(slide, '总读取时间 ∝ max(每个 plane 需要读取的 page 数)', 4.69, 6.18, 6.9, 0.32, { fontSize: 15, color: C.accent, bold: true });
  source(slide, 'Source: FlashAccel §5.1, Fig. 7. A0/A1/A2 are weight pages, not operator importance scores.');
  note(slide, { title: '权重布局', purpose: '澄清 A0/A1/A2 的含义，并解释执行顺序布局为什么提高带宽。', minutes: 1.0, talk: ['A 表示算子 A 的全部静态权重，A0/A1/A2 是切分后的 Flash 页面。', '它们不是给算子分配的“重要性权重”。', '布局按实际执行顺序，而不是源码变量声明顺序；这样连续预取时各 plane 负载更均衡。'], transition: '权重顺序是静态的，但 KV cache 的活跃集合一直变化，需要运行时再平衡。' });
}

// 07 · KV cache loop / S14
{
  const slide = pageBase(7, 'KV layout');
  title(slide, '06 · Dynamic KV cache', '统一组织，动态再平衡，再按 hyper page 读取');
  const steps = [
    ['01', '聚合写入', '新 KV 尽量凑成完整 hyper page；尾块随机放置。'],
    ['02', '选择性卸载', '把超过平均负载的 page 移到 HBM，避免重写 Flash。'],
    ['03', '并行读取', '按 hyper page 读取 HBF，并与 HBM 中的热点 KV 一起计算。'],
    ['04', 'HBM 缓冲', '本轮新生成 KV 先进入 HBM，等待形成完整块。'],
    ['05', '批量回写', '按 append-only 方式批量写回 HBF。']
  ];
  steps.forEach((s, i) => {
    const y = 1.72 + i * 0.92;
    rect(slide, 0.68, y, 0.45, 0.45, i === 1 ? C.accent : C.ink);
    addText(slide, s[0], 0.68, y, 0.45, 0.45, { fontFace: MONO, fontSize: 8.5, color: C.white, bold: true, align: 'center' });
    addText(slide, s[1], 1.34, y - 0.01, 1.35, 0.28, { fontSize: 14.5, bold: true });
    addText(slide, s[2], 2.72, y - 0.01, 3.28, 0.50, { fontSize: 10.7, color: C.secondary, breakLine: true, valign: 'top' });
    if (i < 4) line(slide, 0.905, y + 0.45, 0.905, y + 0.88, C.line, 1.2, 'dash');
  });
  rect(slide, 0.68, 6.42, 5.35, 0.38, C.paper2);
  addText(slide, '论文折中：256 KB KV block', 0.88, 6.45, 4.95, 0.28, { fontSize: 11.5, color: C.accent, bold: true });
  addImageContain(slide, fig(8), 6.28, 1.54, 6.25, 5.30, { bg: C.paper, topLine: C.accent });
  source(slide, 'Source: FlashAccel §5.2, Fig. 8–9.');
  note(slide, { title: 'KV Cache 动态均衡', purpose: '讲清楚 5 步 KV 生命周期以及为什么仅靠初始均匀分布不够。', minutes: 1.3, talk: ['活跃请求不断进出，统一 KV cache 在各 plane 上会重新变得不均衡。', '系统只把超过平均负载的 page 卸到 HBM，不在 HBF 内部搬家，从而减少额外写入。', '读取时按 hyper page 聚合 plane 并行；新 KV 先在 HBM 中缓冲，再批量追加写回。', '256KB block 是 plane 偏斜、HBM 压力和内部碎片之间的折中。'], transition: '这些布局需要软件把 HBF 既当持久化存储，又当 GPU 可直接访问的内存。' });
}

// 08 · System software / S17
{
  const slide = pageBase(8, 'System software');
  title(slide, '07 · Programming model', '把持久化对象映射进统一虚拟地址空间');
  const layers = [
    { y: 1.74, bg: C.ink, fg: C.white, t: 'APPLICATION / KERNEL', b: '普通 load/store + attention / GEMM kernels' },
    { y: 2.76, bg: C.accent, fg: C.white, t: 'PROGRAMMING MODEL', b: 'NandMmap · GroupMmap · GroupArrange · GroupWrite · SramPrefetch / Release' },
    { y: 4.04, bg: C.paper2, fg: C.ink, t: 'HBF-AWARE STORAGE', b: '权重对象 + 每请求 KV 对象；元数据直接记录物理地址，省去传统 FTL' }
  ];
  layers.forEach(l => {
    rect(slide, 0.68, l.y, 5.05, l.y === 2.76 ? 1.02 : 0.80, l.bg);
    addText(slide, l.t, 0.92, l.y + 0.12, 4.45, 0.24, { fontFace: MONO, fontSize: 8.5, color: l.fg, bold: true, charSpacing: 1.0 });
    addText(slide, l.b, 0.92, l.y + 0.40, 4.45, l.y === 2.76 ? 0.46 : 0.30, { fontSize: 11.3, color: l.fg, breakLine: true, valign: 'top' });
  });
  addText(slide, '页表物理地址可动态指向 HBF / HBM / SRAM', 0.70, 5.25, 5.0, 0.44, { fontSize: 16, color: C.accent, bold: true });
  addText(slide, '关键观察：权重只读，KV 仅追加，因此无需通用 FTL 的完整更新语义。', 0.70, 5.85, 4.96, 0.58, { fontSize: 12.2, color: C.secondary, breakLine: true, valign: 'top' });
  addImageContain(slide, fig(10), 6.13, 1.68, 6.52, 2.72, { bg: C.paper, topLine: C.accent });
  addImageContain(slide, fig(11), 6.13, 4.63, 6.52, 2.18, { bg: C.paper });
  source(slide, 'Source: FlashAccel §6, Fig. 10–11.');
  note(slide, { title: '存储管理与编程接口', purpose: '解释为何 FlashAccel 能绕过传统 FTL，并让应用直接访问异构资源。', minutes: 1.0, talk: ['模型权重是只读对象，KV 是 append-only 对象，允许元数据直接记录物理 Flash 地址。', 'NandMmap 负责权重；Group 系列接口把活跃请求的 KV 组成逻辑连续空间并支持卸载与写回。', '页表映射可以在 HBF、HBM、SRAM 之间更新，程序始终使用统一逻辑地址。'], transition: '统一地址解决了可访问性，接下来还要用 SRAM 预取隐藏 Flash 首访延迟。' });
}

// 09 · Prefetch / S11
{
  const slide = pageBase(9, 'Prefetch');
  title(slide, '08 · Latency hiding', '用计算时间覆盖 4 μs Flash 读取');
  addImageContain(slide, fig(12), 0.72, 1.66, 11.88, 3.30, { bg: C.paper, topLine: C.accent });
  line(slide, 1.15, 5.78, 12.10, 5.78, C.line, 1.1);
  const xs = [1.25, 4.75, 8.25, 11.75];
  const labels = [
    ['01', '切成 SRAM 可容纳的 tile'],
    ['02', 'SramPrefetch 异步入队'],
    ['03', '计算当前 tile'],
    ['04', 'SramRelease 释放缓冲']
  ];
  labels.forEach((l, i) => {
    rect(slide, xs[i] - 0.06, 5.70, 0.14, 0.14, i === 2 ? C.accent : C.ink);
    addText(slide, l[0], xs[i] - 0.42, 5.28, 0.85, 0.23, { fontFace: MONO, fontSize: 8.5, color: i === 2 ? C.accent : C.helper, bold: true, align: 'center' });
    addText(slide, l[1], xs[i] - 1.13, 5.97, 2.3, 0.44, { fontSize: 11.3, color: C.secondary, align: 'center', breakLine: true });
  });
  addText(slide, 'Prefetch 不阻塞依赖 kernel；未预取完成的页仍保留原 HBF 映射，保证正确性。', 1.18, 6.62, 10.95, 0.30, { fontSize: 12, color: C.accent, bold: true, align: 'center' });
  source(slide, 'Source: FlashAccel §6.2.3, Fig. 12.');
  note(slide, { title: 'SRAM 预取', purpose: '说明分块、异步预取与计算重叠的关键机制。', minutes: 0.9, talk: ['大权重张量先切成能装进 SRAM 的 tile。', '运行时依据计算图生成预取队列，使下一块读取与当前块计算重叠。', 'SramPrefetch 不强制阻塞；若预取尚未完成，页表仍指向原 HBF 地址，保证 kernel 能正确访问。'], transition: '机制看完后，需要判断实验环境与数据是否足以支持论文结论。' });
}

// 10 · Evaluation setup / S21
{
  const slide = pageBase(10, 'Evaluation');
  title(slide, '09 · Evaluation setup', '基于模拟器的架构研究，而非实机原型');
  rect(slide, 0.68, 1.75, 4.20, 4.92, C.ink);
  addText(slide, '4', 1.00, 2.04, 1.20, 0.66, { fontFace: 'Aptos', fontSize: 39, color: C.white });
  addText(slide, 'models', 2.22, 2.22, 1.55, 0.28, { fontFace: MONO, fontSize: 9, color: 'C5C5C3', bold: true });
  addText(slide, '2', 1.00, 3.12, 1.20, 0.66, { fontFace: 'Aptos', fontSize: 39, color: C.white });
  addText(slide, 'SLOs · 50 / 100 ms', 2.22, 3.30, 1.95, 0.28, { fontFace: MONO, fontSize: 9, color: 'C5C5C3', bold: true });
  addText(slide, '5', 1.00, 4.20, 1.20, 0.66, { fontFace: 'Aptos', fontSize: 39, color: C.white });
  addText(slide, 'hardware configs', 2.22, 4.38, 1.95, 0.28, { fontFace: MONO, fontSize: 9, color: 'C5C5C3', bold: true });
  line(slide, 1.00, 5.28, 4.54, 5.28, '4D4D4D', 0.8);
  addText(slide, 'Baseline', 1.00, 5.53, 1.3, 0.24, { fontFace: MONO, fontSize: 8.5, color: 'C5C5C3', bold: true });
  addText(slide, 'DGX-H200 · 8×H200\n141GB HBM / GPU · 4.8TB/s', 1.00, 5.85, 3.30, 0.62, { fontSize: 12, color: C.white, breakLine: true, valign: 'top' });
  const specs = [
    ['SIMULATOR', 'LLMCompass + ScaleSim + plane-level NAND model'],
    ['WORKLOADS', 'Qwen3-235B / 480B · LLaMA3.1-405B · DeepSeek-V3'],
    ['CONTEXT', '8.11K/2.53K 与 15K/6K input/output'],
    ['HBF STACK', '192GB · 768GB/s · 4μs read · 75μs program'],
    ['CONFIGS', '4×/8× CLI · 4×/8× CSI · 8×H200']
  ];
  specs.forEach((s, i) => {
    const y = 1.76 + i * 0.92;
    line(slide, 5.25, y, 12.63, y, i === 0 ? C.accent : C.line, i === 0 ? 2.3 : 0.7);
    addText(slide, s[0], 5.25, y + 0.14, 1.42, 0.24, { fontFace: MONO, fontSize: 8.3, color: i === 0 ? C.accent : C.helper, bold: true, charSpacing: 0.8 });
    addText(slide, s[1], 6.85, y + 0.10, 5.65, 0.46, { fontSize: 12.5, color: C.secondary, valign: 'top' });
  });
  rect(slide, 5.25, 6.42, 7.38, 0.28, C.accentSoft);
  addText(slide, '解读结果时必须保留这一前提：HBF 参数与集成均为建模。', 5.42, 6.42, 7.05, 0.28, { fontSize: 11.5, color: C.accentDeep, bold: true });
  source(slide, 'Source: FlashAccel §7.1, Tables 1–2.');
  note(slide, { title: '评估设置', purpose: '让听众知道结果来自什么模型，以及哪些结论仍依赖假设。', minutes: 0.8, talk: ['作者在 LLMCompass 上增加 plane 粒度 NAND 模型，并修改内存模型模拟 Flash 与 SRAM。', '基线是 8×H200；工作负载覆盖 GQA、MLA、Dense 和 MoE。', '单 HBF stack 的 192GB、768GB/s、4μs read 等参数来自建模，并没有真实 FlashAccel 芯片。'], transition: '在这个评估框架下，容量优势确实转化为了更大的 batch 和更高吞吐。' });
}

// 11 · Main results / S22
{
  const slide = pageBase(11, 'Results');
  title(slide, '10 · Throughput & energy', '100 ms SLO 下，CSI 的容量优势转化为吞吐');
  addImageContain(slide, fig(13), 0.68, 1.63, 12.00, 2.41, { bg: C.paper, topLine: C.accent });
  kpi(slide, 0.68, 4.33, 3.48, '2.54×', 'Throughput / GPU', '8×CSI 相对 8×H200 的平均结果（100ms SLO）。', true);
  kpi(slide, 4.45, 4.33, 3.48, '1.93×', 'Tokens / Joule', '虽然 Flash 每 bit 读取能耗更高，吞吐提升使总体能效仍上升。');
  kpi(slide, 8.22, 4.33, 3.48, '2.04×', '8×CLI throughput', '带宽比 CSI 少 16.7%，但在 100ms SLO 下仍显著提升。');
  addText(slide, '机制：更多容量 → 更大 batch → FFN 算术强度提高 → 每 GPU 吞吐上升', 0.68, 6.22, 11.97, 0.35, { fontSize: 15, color: C.accent, bold: true, align: 'center' });
  source(slide, 'Source: FlashAccel Fig. 13 & Fig. 17. KPI averages are reported under the 100 ms decode-step SLO.');
  note(slide, { title: '吞吐与能效结果', purpose: '报告最核心的数字，并说明收益来自容量解锁 batch，而不是单次访问比 HBM 更快。', minutes: 1.1, talk: ['在 100ms SLO 下，8×CSI 的每 GPU 吞吐平均达到 8×H200 的 2.54 倍，能效 1.93 倍。', '8×CLI 因只有 5 个 HBF stack，带宽比 CSI 低 16.7%，平均吞吐为 2.04 倍。', '这不是 HBF 单次访问更快，而是更大容量支持更大 batch，提高了 FFN 算术强度。'], transition: '消融实验进一步回答：这些收益到底由哪项优化贡献。' });
}

// 12 · Ablation & reuse / S08
{
  const slide = pageBase(12, 'Evidence');
  title(slide, '11 · Ablation & reuse', '真正的主角是预取；容量还带来 KV 复用');
  line(slide, 6.66, 1.70, 6.66, 6.65, C.line, 0.8);
  addText(slide, 'A  /  ABLATION', 0.70, 1.66, 2.0, 0.24, { fontFace: MONO, fontSize: 8.5, color: C.accent, bold: true });
  addImageContain(slide, fig(15), 0.70, 2.03, 5.61, 2.59, { bg: C.paper, topLine: C.accent });
  addText(slide, '去掉预取：吞吐下降 55%', 0.72, 4.94, 5.50, 0.34, { fontSize: 18, color: C.accent, bold: true });
  addText(slide, '去掉权重布局：−7%  ·  去掉 KV 布局：−15%\n完整方案与 HBM latency 差约 4%，其中 offloading 约 2%。', 0.72, 5.40, 5.55, 0.72, { fontSize: 12.5, color: C.secondary, breakLine: true, valign: 'top' });
  addText(slide, 'B  /  KV REUSE', 7.02, 1.66, 2.0, 0.24, { fontFace: MONO, fontSize: 8.5, color: C.accent, bold: true });
  addImageContain(slide, fig(16), 7.02, 2.03, 5.61, 2.50, { bg: C.paper, topLine: C.accent });
  addText(slide, '需要计算的 token 最多减少 89%', 7.04, 4.94, 5.48, 0.34, { fontSize: 18, color: C.accent, bold: true });
  addText(slide, '8×CLI / 8×CSI 可在该多轮交互轨迹中保存全部会话 KV，达到理想命中率。', 7.04, 5.40, 5.43, 0.72, { fontSize: 12.5, color: C.secondary, breakLine: true, valign: 'top' });
  source(slide, 'Source: FlashAccel §7.3 & §7.5, Fig. 15–16.');
  note(slide, { title: '消融与 KV 复用', purpose: '验证预取、布局和容量复用分别贡献了什么。', minutes: 1.0, talk: ['去掉预取吞吐下降 55%，说明隐藏访问延迟是第一优先级。', '权重和 KV 布局分别贡献约 7% 和 15%，负责把有效带宽拉近峰值。', '更大容量还能保留多轮会话 KV，在论文轨迹上最多减少 89% 需要重新计算的 token。'], transition: '这些结果很有吸引力，但作为研究生汇报，还要区分论文贡献与工程落地假设。' });
}

// 13 · Critical view / S19
{
  const slide = pageBase(13, 'Critical view');
  title(slide, '12 · Critical view', '贡献很强，但落地仍依赖四类假设');
  const cards = [
    ['01', '系统贡献', '从硬件、布局到运行时形成完整闭环；不是单点缓存技巧。'],
    ['02', '实证边界', '结果来自事件驱动模拟器；尚无 HBF-GPU 原型验证端到端时序。'],
    ['03', '功耗与制造', 'Flash 读取能耗约为 HBM3e 的 2.7×/bit；CSI TDP +31%，建模面积 +23%。'],
    ['04', '工作负载依赖', '收益偏向 decode、长上下文和大 batch；严格 50ms SLO 下 CLI 在部分模型会落后。']
  ];
  cards.forEach((c, i) => {
    const x = 0.68 + i * 3.01;
    rect(slide, x, 1.95, 2.72, 4.35, i === 1 ? C.accent : C.paper2);
    rect(slide, x, 1.95, 2.72, 0.04, i === 1 ? C.accent : C.ink);
    addText(slide, `— ${c[0]}`, x + 0.21, 2.20, 1.1, 0.24, { fontFace: MONO, fontSize: 8.5, color: i === 1 ? C.white : C.helper, bold: true });
    addText(slide, c[1], x + 0.21, 2.87, 2.27, 0.60, { fontSize: 20, color: i === 1 ? C.white : C.ink, bold: false, valign: 'top' });
    addText(slide, c[2], x + 0.21, 4.05, 2.27, 1.48, { fontSize: 12.5, color: i === 1 ? C.white : C.secondary, breakLine: true, valign: 'top' });
  });
  addText(slide, '我的判断：这是有说服力的“架构可行性论证”，还不是可直接采购部署的产品证明。', 0.70, 6.55, 11.88, 0.34, { fontSize: 15, color: C.accent, bold: true, align: 'center' });
  source(slide, 'Source: FlashAccel §7.2–§7.6; critical interpretation by presenter.');
  note(slide, { title: '批判性分析', purpose: '给论文一个平衡评价，区分贡献、证据与落地风险。', minutes: 0.9, talk: ['最大贡献是全栈协同设计，能把容量、带宽、延迟和持久化放进同一个框架。', '最大证据边界是没有实机原型，关键结论依赖 HBF 参数与模拟器准确性。', '能耗、面积和短保留期耐久性假设仍需要真实器件验证。', '收益更适合 memory-bound decode 与大 batch；在严格时延约束下并非所有配置都占优。'], transition: '最后用三句话收束 FlashAccel 的核心价值。' });
}

// 14 · Closing / S10
{
  const slide = pptx.addSlide();
  slide.background = { color: C.paper };
  rect(slide, 0, 0, 6.35, 7.5, C.accent);
  squareMatrix(slide, 0.45, 0.55, 10, 8, 0.07, 0.14, C.white, 82);
  addText(slide, '14 / 14', 0.62, 0.36, 0.9, 0.25, { fontFace: MONO, fontSize: 8.5, color: 'D5DEEF', bold: true });
  addText(slide, '容量只有配合\n布局与预取，\n才会变成吞吐。', 0.62, 1.50, 5.05, 2.30, { fontSize: 31, color: C.white, breakLine: true, valign: 'top' });
  addText(slide, 'FLASHACCEL / TAKEAWAY', 0.62, 6.58, 3.3, 0.24, { fontFace: MONO, fontSize: 8.5, color: 'D5DEEF', bold: true, charSpacing: 1.2 });
  addText(slide, 'THREE TAKEAWAYS', 6.88, 0.66, 3.2, 0.26, { fontFace: MONO, fontSize: 9, color: C.accent, bold: true, charSpacing: 1.2 });
  const take = [
    ['01', 'HBF 解决容量', '让模型权重、长上下文 KV 与更大 batch 有空间共存。'],
    ['02', '布局 + 预取弥合差距', '权重/KV 布局提高 plane 并行度，SRAM 预取隐藏访问延迟。'],
    ['03', '系统抽象让它可用', '持久化对象、统一地址和专用接口把 HBF 变成 GPU 的一等资源。']
  ];
  take.forEach((t, i) => {
    const y = 1.35 + i * 1.42;
    line(slide, 6.88, y, 12.55, y, i === 2 ? C.accent : C.line, i === 2 ? 2.2 : 0.8);
    addText(slide, t[0], 6.88, y + 0.18, 0.55, 0.26, { fontFace: MONO, fontSize: 9, color: i === 2 ? C.accent : C.helper, bold: true });
    addText(slide, t[1], 7.60, y + 0.12, 4.45, 0.36, { fontSize: 18, color: i === 2 ? C.accent : C.ink, bold: true });
    addText(slide, t[2], 7.60, y + 0.58, 4.55, 0.54, { fontSize: 11.5, color: C.secondary, breakLine: true, valign: 'top' });
  });
  addText(slide, 'Q & A', 6.88, 6.14, 3.15, 0.62, { fontFace: 'Aptos', fontSize: 32, color: C.ink, bold: false });
  addText(slide, '谢谢', 10.55, 6.30, 1.95, 0.34, { fontSize: 16, color: C.accent, bold: true, align: 'right' });
  note(slide, { title: '总结与问答', purpose: '用三句话结束正文，并进入 Q&A。', minutes: 0.5, talk: ['HBF 提供容量，但容量本身不会自动成为性能。', 'FlashAccel 通过布局恢复并行带宽，通过预取隐藏延迟，通过系统抽象统一管理。', '这是值得关注的架构方向，下一步关键是实机原型与真实器件验证。'], transition: '进入问答。' });
}

pptx.writeFile({ fileName: OUT });
console.log(OUT);
