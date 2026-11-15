from pathlib import Path
import json,re,hashlib,unicodedata
import pdfplumber
R=Path(__file__).resolve().parents[1];S=R/'source'
bs=json.loads((S/'corrected_blocks.json').read_text());tr={m[1]:m[2].strip() for m in re.finditer(r'@@(S\d{3})\n(.*?)(?=\n@@|\Z)',(S/'translations.txt').read_text(),re.S)}
assets=json.loads((S/'assets.json').read_text());ats=json.loads((S/'asset_translations.json').read_text())
# Restore inline mathematical subscripts from the visible PDF, keeping the author's wording.
patterns=[(r'\bW write−back\b',r'W_{\mathrm{write\text{-}back}}'),(r'\bW type−aware\b',r'W_{\mathrm{type\text{-}aware}}'),(r'\bI type−aware\b',r'I_{\mathrm{type\text{-}aware}}')]
for a in assets:
 a['id']=f"{a['type']}-{a['number']:02}";a['translation']=ats[a['id']]
 if a['id']=='figure-04':a['bbox']=[317,80,560,157]
 if a['id']=='figure-09':a['bbox']=[310,273,560,407]
 # Add a small top margin for top-of-page artwork.
 if a['bbox'][1] in [86,87]:a['bbox'][1]=80
with pdfplumber.open(R.parents[1]/'文献/Gandalf.pdf') as pdf:
 for a in assets:pdf.pages[a['page']-1].crop(a['bbox']).to_image(resolution=216).save(R/a['path'])
for b in bs:
 if b['type'] in ['asset','equation']:continue
 b['translation']=tr[b['id']]
 if b['id']=='S115':b['translation']=b['translation'].replace('不过，原文认为 WAF 与较高写入速率有关，因此','不过，由于 WAF 与较高写入速率有关，')
 if b['id']=='S079':b['original_text']=b['original_text'].replace('\\\\','\\')
 s=re.sub(r'\$(?=\d)',r'\\$',b['original_text'])
 # Replace fragments only outside existing math delimiters.
 parts=s.split('$')
 for k in range(0,len(parts),2):
  t=parts[k]
  for p,v in patterns:t=re.sub(p,lambda m:'$'+v+'$',t)
  for letter,sub in [('C','r'),('C','w'),('H','i'),('x','i'),('s','i'),('H','d'),('v','d'),('s','d'),('a','d'),('H','e'),('v','e'),('E','j'),('s','j'),('ℎ','d'),('ℎ','e')]:
   out=('h' if letter=='ℎ' else letter)+'_'+sub
   t=re.sub(r'(?<![\w$])'+re.escape(letter)+r' '+sub+r'(?!\w)',lambda m:'$'+out+'$',t)
  t=t.replace('N × reuse','$N$ × reuse')
  parts[k]=t
 b['original_text']='$'.join(parts)
# Figure/table locations follow the discussion, while source pages remain explicit.
place={'figure-01':'S012','table-01':'S014','table-02':'S029','figure-02':'S040','figure-03':'S054','figure-04':'S062','figure-05':'S077','figure-06':'S095','table-03':'S123','figure-07':'S130','figure-08':'S135','figure-09':'S144','figure-10':'S148','figure-11':'S153','figure-12':'S156','figure-13':'S165','figure-14':'S166'}
assetnodes={b['asset']:b for b in bs if b['type']=='asset'}
seq=[]
for b in bs:
 if b['type']=='asset':continue
 seq.append(b)
 for name,sid in place.items():
  if sid==b['id']:seq.append(assetnodes[name])
byasset={a['id']:a for a in assets}
tables={
1:'''| Type / 类型 | 2nd-round / 第 2 轮 | 3rd-round / 第 3 轮 | Future rounds / 后续轮次 | Reuse count / 复用次数 |
| --- | --- | --- | --- | --- |
| Full attn / 全注意力 | ✓ | ✓ | ✓ | $N_{\\mathrm{rounds}}$ |
| Linear attn / 线性注意力 | ✓ | ✗ | ✗ | 1 |''',
2:'''| Workload / 工作负载 | Model / 模型 | KV cache size / KV 缓存量（TB） | SSD lifetime / SSD 寿命（年） |
| --- | --- | ---: | ---: |
| Claude Code · cc-traces-062126 | Qwen3.5-27B | 98 | 0.4 |
| Claude Code · cc-traces-062126 | Kimi-K3 | 240 | 0.2 |
| Claude Code · cc-traces-060826 | Qwen3.5-27B | 81 | 0.4 |
| Claude Code · cc-traces-060826 | Kimi-K3 | 199 | 0.2 |''',
3:'''| Trace / 轨迹 | Model / 模型 | Required DWPD / 所需 DWPD（1 TB SSD） | Required DWPD / 所需 DWPD（4 TB SSD） |
| --- | --- | ---: | ---: |
| cc-traces-weka-062126 | Qwen3.5-27B | 34.4 | 8.60 |
| cc-traces-weka-062126 | Kimi-K3 | 48.2 | 12.0 |
| qwen_traceA_blksz_16 | Qwen3.5-27B | 130 | 32.4 |
| qwen_traceA_blksz_16 | Kimi-K3 | 274 | 68.5 |
| aiperf-100r-500o-noshare | Qwen3.5-27B | 278 | 69.4 |
| aiperf-100r-500o-noshare | Kimi-K3 | 579 | 145 |'''
}
intro='''# Gandalf: Flash Shall Not Die! Increasing Flash Storage Lifetime for KV Cache Offloading in LLM Serving

# Gandalf：闪存不应消亡！延长 LLM 服务中 KV 缓存卸载的闪存存储寿命

## 文献信息 / Publication Information

- **Authors / 作者**：Maharani A. P. Irawan、Kuntai Du、Jiayi Yao、Dongjoo Seo、Yuyang Huang、Haryadi S. Gunawi、Junchen Jiang。
- **Version / 版本**：arXiv:2610.30791v1 [cs.LG]，2026-10-22。依据本地 PDF 页边版本标记；不混入其他版本。
- **Source / 来源**：[本地原论文（14 页）](../../文献/Gandalf.pdf)。正文至 PDF 第 12 页，参考文献延续至第 14 页。

| Author / 作者 | Affiliation / 单位 |
| --- | --- |
| Maharani A. P. Irawan* | The University of Chicago, USA / 芝加哥大学，美国 |
| Kuntai Du | TensorMesh Inc., USA / TensorMesh 公司，美国 |
| Jiayi Yao | The University of Chicago, USA / 芝加哥大学，美国 |
| Dongjoo Seo | Samsung Semiconductor, USA / 三星半导体，美国 |
| Yuyang Huang | The University of Chicago, USA / 芝加哥大学，美国 |
| Haryadi S. Gunawi | The University of Chicago, USA / 芝加哥大学，美国 |
| Junchen Jiang† | TensorMesh Inc., USA / TensorMesh 公司，美国 |

## 阅读说明 / Reading Notes

沿用已有笔记的“英文原文 → 中文译文”逐段格式，保留章节编号、引文编号、图表、公式及脚注。双栏正文按先左后右的顺序恢复，跨栏、跨页的段落已接回，排版断词和连字已整理。每个单元标注 PDF 页码及稳定来源编号；来源编号仅用于回查，并非原论文章节编号。图片移至相关讨论附近，页码仍指向原始位置。

14 幅图及 3 张表均直接裁剪自本地 PDF，保留原英文标签与数值，提供中英图注；3 张表另附可复制的中英表头表格。8 个编号公式以数学格式恢复，仅显示一次，公式中的文字标签提供中英对照。参考文献保留完整英文著录，并附中文题名与主要出版信息；完整作者和网址以相邻英文著录为准。引文未另作联网核验。

译文忠实保留作者的模型设定、模拟假设、结论和数值。原文的指标定义、倍数、图文差异等疑点单独记录在 [翻译与核对说明](translation_notes.md)，没有据此修改实验结果。

图片位于同目录 `assets/`，移动本文时请同时移动该文件夹。`source_map.json` 保存来源定位和对照文本。

## 目录 / Contents

'''
out=[intro]
for b in seq:
 if b['type']=='heading':
  en=b['original_text'];zh=b['translation'];num=re.match(r'^(\d+(?:\.\d+)*) ',en)
  if b['id']=='S026':out.append('- [2 研究动机 / Motivation](#section-2)\n- [2.1 KV 缓存超出内存容量](#section-2-1)\n');continue
  if b['id']=='S116':out.append('- [5 评估 / Evaluation](#section-5)\n- [5.1 实验设置](#section-5-1)\n');continue
  anchor='section-'+num[1].replace('.','-') if num else ('abstract' if en=='Abstract' else 'references')
  out.append(f'- [{zh} / {en}](#{anchor})\n')
out.append('- [作者脚注 / Author Footnotes](#footnotes)\n- [术语对照 / Terminology](#terminology)\n\n---\n\n')
for b in seq:
 sid=b['id']; pages=b.get('pages',[b['page']]);src='、'.join(map(str,pages))
 out.append(f'<a id="{sid}"></a>\n\n')
 if b['type']=='heading':
  en=b['original_text'];zh=b['translation'];num=re.match(r'^(\d+(?:\.\d+)*) ',en)
  if sid in ['S026','S116']:
   n,main,sub=('2','Motivation','KV Caches Exceed Memory Capacity') if sid=='S026' else ('5','Evaluation','Setup')
   zm,zs=('研究动机','KV 缓存超出内存容量') if n=='2' else ('评估','实验设置')
   out.append(f'<a id="section-{n}"></a>\n\n## {n} {main} / {n} {zm}\n\n<a id="section-{n}-1"></a>\n\n### {n}.1 {sub} / {n}.1 {zs}\n\n');continue
  anchor='section-'+num[1].replace('.','-') if num else ('abstract' if en=='Abstract' else 'references')
  level='###' if num and '.' in num[1] else '##'
  out.append(f'<a id="{anchor}"></a>\n\n{level} {en} / {zh}\n\n')
 elif b['type']=='equation':
  out.append(f'**Source:** PDF p.{src} · {sid} · Equation / 公式（{b["number"]}）\n\n$$\n{b["latex"]}\\tag{{{b["number"]}}}\n$$\n\n')
  if b['number'] in [1,2]:out.append('公式末尾的英文原标签分别为“写入 TB 数”和“读写 TB 数”；原式的量纲与寿命推算口径见翻译说明。\n\n')
 elif b['type']=='asset':
  a=byasset[b['asset']];label=('图' if a['type']=='figure' else '表')+str(a['number'])
  out.append(f'<a id="{a["id"]}"></a>\n\n**Source:** PDF p.{a["page"]} · {sid}\n\n![{label} / {a["id"]}]({a["path"]})\n\n**Original:** {a["original_text"]}\n\n**中文：** {a["translation"]}\n\n')
  if a['type']=='table':out.append(tables[a['number']]+'\n\n')
 else:
  out.append(f'**Source:** PDF p.{src} · {sid}\n\n**Original:** {b["original_text"]}\n\n**中文：** {b["translation"]}\n\n')
footnotes=[dict(id='F001',page=1,original_text='* Part of this work was done while the author was an intern at TensorMesh Inc.',translation='* 本工作的一部分在作者于 TensorMesh 公司实习期间完成。',bbox=[53,690,296,700]),dict(id='F002',page=1,original_text='† Also with The University of Chicago.',translation='† 同时隶属于芝加哥大学。',bbox=[53,700,296,711])]
out.append('<a id="footnotes"></a>\n\n## 作者脚注 / Author Footnotes\n\n')
for f in footnotes:out.append(f'<a id="{f["id"]}"></a>\n\n**Source:** PDF p.1 · {f["id"]}\n\n**Original:** {f["original_text"]}\n\n**中文：** {f["translation"]}\n\n')
glossary=[('KV cache / key-value state','KV 缓存／键值状态'),('offloading','卸载'),('full attention','全注意力'),('linear attention / recurrent state','线性注意力／递归状态'),('sliding-window attention','滑动窗口注意力'),('hybrid model','混合模型'),('admission / admission gate','准入／准入门控'),('placement','放置'),('eviction / victim','驱逐／被驱逐对象'),('promotion / demotion','提升／降级；具体传输方向以所在段落为准'),('write-through / write-back','直写／回写'),('write endurance / wear','写入耐久性／磨损'),('TBW / DWPD','总写入量额度／每日整盘写入次数'),('WAF','写放大系数'),('TTFT','首 token 延迟'),('cache miss ratio / cache hit rate','缓存未命中率／缓存命中率'),('prefix-hit boundary','前缀命中边界'),('oracle','离线预知算法'),('drop cost / move cost','丢弃成本／移动成本'),('replacement cost','替换成本'),('retention relaxation','放宽数据保持要求'),('root-side node / leaf','根侧节点／叶节点'),('lazy min-heap','惰性最小堆'),('HBF / HBM','高带宽闪存／高带宽内存')]
out.append('<a id="terminology"></a>\n\n## 术语对照 / Terminology\n\n| English | 中文 |\n| --- | --- |\n')
out.extend(f'| {a} | {b} |\n' for a,b in glossary)
(R/'Gandalf_中英对照.md').write_text(''.join(out))
meta={'title':'Gandalf: Flash Shall Not Die! Increasing Flash Storage Lifetime for KV Cache Offloading in LLM Serving','version':'arXiv:2610.30791v1 [cs.LG], 22 Oct 2026','source_path':str(R.parents[1]/'文献/Gandalf.pdf'),'page_count':14,'source_sha256':hashlib.sha256((R.parents[1]/'文献/Gandalf.pdf').read_bytes()).hexdigest()}
manifest={'paper':meta,'blocks':seq,'assets':assets,'footnotes':footnotes,'glossary':[{'en':a,'zh':b} for a,b in glossary]}
(R/'source_map.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
print('Built',R/'Gandalf_中英对照.md',len(''.join(out)),'characters')
