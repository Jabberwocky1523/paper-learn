from pathlib import Path
from collections import defaultdict
import json,re,hashlib

ROOT=Path('/home/kurisu/Desktop/论文/笔记/HBF-Sucks')
m=json.loads((ROOT/'source_map.json').read_text())
assert not any(b.get('translation') for b in m['blocks'])
translations={i:s.strip() for i,s in re.findall(r'@@(S\d{3})\n(.*?)(?=\n@@S\d{3}\n|\Z)',(ROOT/'source/translations.txt').read_text(),re.S)}
refs=json.loads((ROOT/'source/reference_titles_zh.json').read_text())
assetdata=json.loads((ROOT/'source/asset_translations.json').read_text())
raw_blocks=json.loads(json.dumps(m['blocks']))

def normalize(s):
 fixes={'Mooncakestyle':'Mooncake-style','Token-Sim':'TokenSim','realmachine':'real-machine','existingblock':'existing-block','channellevel':'channel-level','secondarytier':'secondary-tier','end-toend':'end-to-end','KVaware':'KV-aware','Recencyonly':'Recency-only','basedie':'base-die','flashtier':'flash-tier','highesttraffic':'highest-traffic','PCIe/N-VMe':'PCIe/NVMe','GDDR– HBF':'GDDR–HBF','copackage':'co-package','Per-formance':'Performance','of≈':'of ≈','80 ◦ C':'80°C','85 ◦ C':'85°C','𝜇s':'μs','𝜇 s':'μs','nobatch':'no-batch'}
 for a,b in fixes.items():s=s.replace(a,b)
 s=re.sub(r'(?<=\d)– +(?=\d)','–',s)
 # Correct PDF reading-order artifacts inside inline fractions/superscripts.
 s=s.replace('𝑓 = ( Δ𝑇 1 𝑇 )/(1 − 𝑘 ) ≈ 1%',r'$f=(\Delta T/T)/(1-1/k)\approx1\%$')
 s=s.replace('Two facts push 𝜌 above one:','Two facts push $\\rho^{\\star}$ above one:').replace('unconditionally, ★ while','unconditionally, while')
 ordered=[('𝜌 > 𝜌 ★ ≳ 1',r'$\rho>\rho^{\star}\gtrsim1$'),('𝜌 > 𝜌 ★',r'$\rho>\rho^{\star}$'),('𝜌 ≫ 1',r'$\rho\gg1$'),('Δ HBF > 0',r'$\Delta_{\mathrm{HBF}}>0$'),('𝑇 = 𝑇 rest + 𝑡 io',r'$T=T_{\mathrm{rest}}+t_{\mathrm{io}}$'),('𝑓 = 𝑡 io /𝑇',r'$f=t_{\mathrm{io}}/T$'),('𝜌𝑆 > 𝐴𝐶',r'$\rho S>AC$'),('𝑓 Δ𝑡 media',r'$f\Delta t_{\mathrm{media}}$'),('𝐶 pkg',r'$C_{\mathrm{pkg}}$'),('𝐶 life',r'$C_{\mathrm{life}}$'),('𝑡 io',r'$t_{\mathrm{io}}$'),('𝑇 rest',r'$T_{\mathrm{rest}}$'),('𝐻 KV',r'$H_{\mathrm{KV}}$'),('𝐷 head',r'$D_{\mathrm{head}}$'),('𝑘 → ∞',r'$k\to\infty$'),('𝑘 = 3.75×',r'$k=3.75\times$'),('𝑓 ≈ 1%',r'$f\approx1\%$')]
 for a,b in ordered:s=s.replace(a,b)
 for a,b in {'𝑁':'N','𝐿':'L','𝑏':'b','𝑓':'f','𝑘':'k','𝜌':r'\rho','𝑆':'S','𝐴':'A','𝐶':'C'}.items():s=s.replace(a,'$'+b+'$')
 s=s.replace('∼5%',r'$\sim5\%$')
 for a,b in {'doi:10.1109/ LCA.':'doi:10.1109/LCA.','doi:10.1109/ ICCAD.':'doi:10.1109/ICCAD.','https://arxiv.org/ abs/':'https://arxiv.org/abs/','https://arxiv. org/':'https://arxiv.org/','/atc24/ presentation/':'/atc24/presentation/','/2024/file/ a66':'/2024/file/a66','/business/ ssd/':'/business/ssd/','/atc25/presentation/wangjiahao':'/atc25/presentation/wang-jiahao'}.items():s=s.replace(a,b)
 return s

for b in m['blocks']:
 if b['type']=='equation':continue
 b['original_extracted_text']=b['original_text'];b['original_text']=normalize(b['original_text'])
 if b['type']=='reference':
  n=int(re.match(r'^\[(\d+)\]',b['original_text']).group(1))
  b['translation']=f'[{n}] 中文题名：{refs[str(n)]}。作者、年份、出版信息、页码及 DOI／网址保留上方英文书目，便于检索。'
 else:
  assert b['id'] in translations,b['id'];b['translation']=translations[b['id']]
 if b['id']=='S179':
  url='https://github.com/pku-lemonade/TokenSim'
  for key in ['original_text','translation']:b[key]=b[key].replace(url,f'[{url}]({url}/tree/hbf)')

# Restore footnote position in the relevant method discussion without renumbering stable IDs.
foot=next(b for b in m['blocks'] if b['id']=='S179')
m['blocks'].remove(foot)
m['blocks'].insert(next(i for i,b in enumerate(m['blocks']) if b['id']=='S068')+1,foot)
byid={b['id']:b for b in m['blocks']}
caps={c['id']:c for c in m['captions']}
insertions=defaultdict(list)
for a in m['figures']+m['tables']:
 d=assetdata[a['id']];a.update(title=d['title'],placed_after=d['placed_after'],reading_note=d['note'])
 c=caps[a['caption_id']];c.update(original_text=normalize(c['original_text']),translation=d['translation'],refs=[a['id']])
 a['original_caption']=c['original_text'];a['translated_caption']=c['translation']
 if a['id'].startswith('T'):a.update(original_table=d['original_table'],translated_table=d['translated_table'])
 insertions[a['placed_after']].append(a);byid[a['placed_after']]['refs'].append(a['id'])

gloss=[
('HBF','高带宽闪存','High-Bandwidth Flash；接口更宽，但介质仍是 NAND。','HBF, HBF-1/2/3','保留代际编号和路线图年份。'),
('near tier','近端层','直接承担权重、活跃 KV 和准入容量的快速层。','near tier, local tier','本文为 HBM 或 GDDR7，不一律译成 HBM。'),
('far tier','远端存储层','相对于近端层更慢、容量更大的层级。','far tier, far-memory tier','不必位于远端机器；HBF 可以在同一封装。'),
('secondary tier','次级层','近端层之外的后备容量层。','secondary tier, backing tier','backing tier 也译后备层，按上下文保留。'),
('KV cache','KV 缓存','推理保存的键和值状态。','KV, key–value cache','保留 KV，不与数据库键值对泛化混用。'),
('transient KV','短暂 KV','寿命随请求等状态结束而终止的 KV。','transient KV, private decode KV','私有解码 KV 按上下文明确说明。'),
('prefill','预填充','并行处理提示并生成 KV 的阶段。','prefill','保留与解码的区别。'),
('decode','解码','逐步自回归生成输出词元。','decode, decoding','不译为预填充。'),
('TTFT','首词元时间','time to first token。','TTFT','越低越好。'),
('TBT','词元间隔时间','time between tokens。','TBT','不擅自等同于上一份笔记中的 TPOT。'),
('end-to-end latency','端到端延迟','从请求角度统计的整体耗时。','E2E, end-to-end latency','与累计连接器服务时间区分。'),
('SLO goodput','满足 SLO 的有效吞吐','只计满足服务等级目标的有效完成量。','goodput, maximum SLO goodput','不与总吞吐混用；按原文保留评价口径。'),
('exposed fraction','暴露比例','无法被其他工作重叠隐藏的次级层服务时间占比 $f$。','exposed fraction, read-I/O exposure','强调关键路径，不等于原始 I/O 耗时之和。'),
('critical path','关键路径','其耗时会直接限制请求完成的路径。','critical-path I/O','与可异步隐藏的工作区分。'),
('reads per write','每次写入对应的读取量','本文按有效读取字节／写入字节计算 $\\rho$。','reads/write, reads-per-write','与 write/read ratio 互为倒数；不是操作次数。'),
('write amplification','写放大','介质写入相对于有效数据写入的放大量 $A$。','write amplification','寿命比较中的单位写放大为有利假设。'),
('base die','基础裸片','堆栈底部承担接口或管理逻辑的裸片。','base die, base-die','与核心 NAND 裸片区别。'),
('NMP','近存储处理','near-memory processing，本文特指基础裸片注意力引擎。','NMP, base-die compute','不把本实验推成对全部存内计算的否定。'),
('plane','平面','NAND 内部可并行操作的资源层级。','plane','不与页、块、存储体混用。'),
('bank','存储体','页感测、页缓存和访问调度的资源单位。','bank','与通道、平面分别保留。'),
('program/erase','编程／擦除','NAND 写入与块擦除操作。','P/E, program, erase','program 不是执行程序。'),
('thermal throttling','热限流','达到温度约束后降低可用服务能力。','throttling, plane throttling','不擅自解释为单纯降低 GPU 频率。'),
('endurance','耐久性','有限编程／擦除和写入预算。','endurance, write budget, TBW','寿命按本文负载与预算外推，不是故障实测。'),
('DWPD','每日全盘写入次数','Drive Writes Per Day。','3-DWPD, DWPD','3 DWPD 表示每日可写三倍盘容量的额定预算。'),
('bucketing','分桶','把多个 KV 写入合并成较大对象。','bucket, write-batching','与调度请求的连续批处理区分。'),
('admission','准入','决定是否／何时让请求占用执行资源。','admission, admission policy','与介质读写调度区分。'),
('retention','数据保持／保留','器件语境为数据保持；缓存策略语境为保留。','retention, retained tokens','按语境区分，避免把缓存淘汰与器件丢数据混同。'),
]
m['glossary']=[dict(term=t,translation=z,first_use_definition=d,variants=v,decision=n) for t,z,d,v,n in gloss]

equation_notes={
'E001':'按原式依次为堆栈、裸片、平面、块、页、单元。它描述 NAND 层级，不能把每层都当成可独立并行的完整设备。',
'E002':'有效带宽取接口、阵列、控制器、功耗、温度和工作负载六类约束中的最小值。接口峰值只是其中一项。',
'E003':r'$N$ 为保留词元数，$L$ 为层数，$H_{\mathrm{KV}}$ 为 KV 头数，$D_{\mathrm{head}}$ 为头维度，$b$ 为元素字节数；键和值各一份，因此乘 2。原式未做跨 GPU 分片。',
'E004':'save 将 GPU HBM 中的 KV 保存到缓存层。它是方向定义，不表示每次保存都同步阻塞推理。',
'E005':'load 将缓存层中的 KV 恢复到 GPU HBM；命中卸载对象并不等于直接在闪存上完成注意力计算。',
'E006':'五项依次是关键路径 I/O 收益、搬移／控制成本、近端层机会成本、限流／波动成本、耐久性／容量成本。原式注释保留英文；中文只解释各项，不改变量。',
'E007':'介质快 $k$ 倍时，端到端可减少的比例受 $f$ 限制。关键是未被隐藏的 I/O 占比，而不是设备规格快了多少。',
'E008':r'每写入一字节带来的有用读取量 $\rho$ 必须超过门槛 $\rho^{\star}$；$A$、$C$ 越大，门槛越高；每读取字节实际节省的暴露时间 $S$ 越大，门槛越低。',
}

parts=['''---
title: "HBF Sucks 全文中英对照"
aliases: ["HBF Sucks?", "HBF Sucks PKU", "HBF KV offloading"]
tags: [papers/HBF, papers/LLM, readers/bilingual]
date: 2026-10-26
arxiv_id: "2608.11668v4"
---

# HBF Sucks? 全文中英对照

**英文题名：** HBF Sucks? A Full-Stack Characterization of High-Bandwidth Flash for KV-Centric LLM Serving  
**中文题名：** HBF 真有那么糟吗？面向以 KV 为中心的 LLM 推理服务的高带宽闪存全栈特征分析  
**作者与机构：** Zhuoran Li、Zhuohang Bian、Xin Huang、Yibo Zhao、Guangyu Sun、Youwei Zhuo；北京大学、复旦大学。通讯作者为 Youwei Zhuo。  
**来源版本：** 用户桌面上的《HBF Sucks.pdf》，13 页；首页标注 arXiv:2608.11668v4，2026-09-14。  
**原文：** [本地 PDF](source/HBF_Sucks.pdf) · [arXiv 版本页](https://arxiv.org/abs/2608.11668v4) · [作者代码分支](https://github.com/pku-lemonade/TokenSim/tree/hbf)

> 沿用上一份 HBFSim（MBZUAI）的逐段中英对照格式，覆盖摘要、全文、六个发现、12 张原图、9 张原表、8 个编号公式，以及 28 条参考文献。英文与中文逐段配对；表格附完整中文转写；每张图表另有单独标记的“读图提示”。公式中英共用一份，避免改写符号。Source 标记可定位原 PDF 页码与稳定块编号。
>
> 阅读范围先固定：本文评估的是**路线图 HBF-1／HBF-2＋未修改的 Mooncake 式 KV 池化运行时**，使用 TokenSim、热模型及寿命预算；不能把结果理解成对所有 HBF 用途或已量产器件的实测结论。原文内部有少量口径问题，已在对应表图提示与翻译说明中保留并标注。

## 章节索引
''']
for b in m['blocks']:
 if b['type']=='heading':parts.append(f"- [{b['translation']}](#{b['id']})")
parts.append('\n## PDF 页码索引\n')
for p in range(1,14):
 first=next(b for b in m['blocks'] if p in b.get('pages',[b['page']]))
 parts.append(f'- [PDF 第 {p} 页](#{first["id"]})')
parts.append('\n## 公式索引\n')
for e in m['equations']:parts.append(f'- [{e["id"]} · Eq. ({e["equation_number"]})](#{e["id"]}) — p.{e["page"]}，{e["name"]}')
parts.append('\n## 术语对照\n\n| 原文用语 | 中文统一用语 | 定义／说明 | 原文变体 | 处理决定 |\n| --- | --- | --- | --- | --- |')
for t,z,d,v,n in gloss:parts.append(f'| {t} | {z} | {d} | {v} | {n} |')
parts.append('\n---\n\n## 全文中英对照\n')
ordered=[]
for b in m['blocks']:
 if b['type']=='equation':
  parts.append(f'\n<a id="{b["id"]}"></a>\n**Source:** p.{b["page"]} {b["id"]} · Eq. ({b["equation_number"]})\n\n$$\n{b["latex"]}\n$$\n\n式（{b["equation_number"]}）\n\n**中文说明（辅助）：** {equation_notes[b["id"]]}\n')
  b['reading_note']=equation_notes[b['id']];ordered.append(b);continue
 pp='–'.join(map(str,[min(b['pages']),max(b['pages'])])) if len(b['pages'])>1 else str(b['page'])
 heading=''
 if b['type']=='heading':
  level='###' if re.match(r'^\d+\.\d+',b['original_text']) else '##'
  heading=f'{level} {b["translation"]} · {b["original_text"]}\n\n'
 elif b['type']=='finding':heading=f'#### {b["translation"].split("：")[0]}\n\n'
 parts.append(f'\n<a id="{b["id"]}"></a>\n{heading}**Source:** p.{pp} {b["id"]}\n\n**Original:** {b["original_text"]}\n\n**中文:** {b["translation"]}\n')
 ordered.append(b)
 for a in insertions[b['id']]:
  c=caps[a['caption_id']]
  parts.append(f'\n<a id="{a["id"]}"></a>\n#### {a["title"]}\n\n**Placed near:** p.{b["page"]} {b["id"]}  \n**Source:** p.{a["page"]} {a["id"]} · {c["id"]}\n\n![{a["alt_text"]}]({a["image_path"]})\n\n<a id="{c["id"]}"></a>\n**Original:** {c["original_text"]}\n\n**中文:** {c["translation"]}\n')
  if a['id'].startswith('T'):parts.append('\n**中文表格：**\n\n'+a['translated_table']+'\n')
  parts.append('\n**读图提示（辅助说明）：** '+a['reading_note']+'\n')
  ordered.append(dict(id=a['id'],page=a['page'],type='table' if a['id'].startswith('T') else 'figure',original_text=a.get('original_table',a['alt_text']),translation=a.get('translated_table',a['title']),bbox=a['bbox'],image_path=a['image_path'],confidence='high',refs=[c['id']],insert_after=b['id']))
  ordered.append(c)
parts.append('''
---

## 阅读提示（辅助说明）

1. **先把“快的是哪一段”分开。** 式（7）的 $f$ 是暴露在关键路径上的次级层服务比例。连接器累计耗时变短，不代表平均单请求 E2E 一定变短；发现 1 的实验证据见 [S093](#S093)–[S098](#S098)、[图 4](#F004)。
2. **三条条件串起六个发现。** C1：介质延迟扫描与 NMP 检验读取是否是真瓶颈；C2：闪存层字节统计与批量写入检验读取能否偿还写入；C3：热模型与 TBW 预算检验带宽及寿命能否维持。对应 [表 4](#T004)。
3. **别把命中率当成 HBF 的读取量。** 热点被近端层留下，整体前缀命中率高与 HBF 写多读少可以同时成立。[表 8](#T008) 的第一行是写／读，第二行是读／写，比较前先看清分子、分母。
4. **百分比和倍率分开读。** 表 5 的 +285.2% 是最终达到 3.852 倍；“寿命 0.56 倍”是剩余比例，不是下降 0.56 倍。NMP 负收益表示更慢，批处理 p50 的正收益表示延迟降低。
5. **结论带着配置和假设走。** NMP 实验仅用表 6 的 DeepSeek／八 H100 配置；热模型采用 80°C 阈值；耐久性使用单位写放大、固定预算和每日持续流量外推。这些都不是对真实 HBF 产品进行的故障或热实测。[S078](#S078)–[S079](#S079)、[S147](#S147) 给出了边界。
6. **与 FlashAccel 的结果放在相同前提下比较。** 本文主要看 SSD 式后备 KV 池，FlashAccel 等工作采用其他组织、数据对象和执行路径。这里的负结果不能直接推翻另一配置的正结果；要先对齐近端容量、驻留对象、I/O 路径和负载，见 [S144](#S144)。

原文口径冲突、提取修复及公式转写说明见 [translation_notes.md](translation_notes.md)。每个段落和图表的原页坐标见 [source_map.json](source_map.json)。
''')
for i,b in enumerate(ordered,1):b['order']=i
m['blocks']=ordered
m['pages']=[dict(page=p,block_ids=[b['id'] for b in ordered if p in b.get('pages',[b['page']])]) for p in range(1,14)]
m['paper'].update(authors=['Zhuoran Li','Zhuohang Bian','Xin Huang','Yibo Zhao','Guangyu Sun','Youwei Zhuo'],institutions=['Peking University','Fudan University'],original_path='/home/kurisu/Desktop/HBF Sucks.pdf',revision_date='2026-09-14',source_format='pdf-text')
m['coverage']=dict(pages=13,source_text_blocks=len(raw_blocks)-8,captions=21,figures=12,tables=9,display_equations=8,references=28,translated_blocks=len(ordered)-8,untranslated_blocks=[])
(ROOT/'source_map.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
md='\n'.join(parts)
(ROOT/'paper.md').write_text(md);(ROOT/'HBF_Sucks_中英对照.md').write_text(md)
(ROOT/'README.md').write_text('''# HBF Sucks?

[打开全文中英对照](HBF_Sucks_中英对照.md)

北京大学与复旦大学团队；arXiv:2608.11668v4，2026-09-14。完整覆盖 13 页、12 张图、9 张表、8 个编号公式及 28 条参考文献。

- [原文 PDF](source/HBF_Sucks.pdf)
- [翻译与提取说明](translation_notes.md)
- [来源映射](source_map.json)
''')
(ROOT/'translation_notes.md').write_text('''# 翻译与提取说明

- **来源与版本。** 使用用户本地 `/home/kurisu/Desktop/HBF Sucks.pdf`，复制到 `文献/HBF_Sucks.pdf` 和本笔记的 `source/HBF_Sucks.pdf`，未改动桌面原文件。首页为 arXiv:2608.11668v4，2026-09-14；共 13 页。SHA-256：`8aede6f264482075a8e0a8b6643b10a5bc9c02008e27d954e360515ef9808654`。arXiv 页面用于核实版本，正文以所给 PDF 为准；HTML 网络获取失败未影响本地完整处理。
- **完整性。** 覆盖标题、署名和邮箱、读者挑战、摘要、关键词、全部正文、六个发现框、代码脚注、12 张图、9 张表、8 个编号公式以及 28 条参考文献。正文至第 12 页，参考文献在第 12–13 页，文献 [7] 跨页接续。没有跳过页、正文段落或图注。
- **版面。** 按双栏自然阅读顺序重建正文，接续跨栏、跨页段落；页眉、页脚和旋转 arXiv 水印不重复放入正文。拆开被 PDF 错合并的左右栏文字，修复断行连字符、连字和断开的 URL。脚注 1 移到 TokenSim 方法段旁。原始提取文本和逐行坐标保存在 `source/`，`source_map.json` 保留提取原串及来源片段。
- **图表。** 从原 PDF 以 240 dpi 渲染并裁取，未重绘数据。图注单独英中配对，图表放到首次实质讨论旁；位置可与 PDF 浮动排版位置不同。9 张表均附完整中文表格，表 3 的三个子表全部转写，原表图片供核对。
- **数学。** 8 个编号展示式各显示一次，英文和中文共用同一个 E 锚点。LaTeX 从可选文字 PDF 重建并按原页视觉核对，标记 medium；非低置信度 OCR，因此没有以猜测填补的公式。式（6）的英文下括号标签保留，中文另说明。式（7）的分式、式（8）的星号和正文内反推公式按视觉顺序修复，避免 PDF 文本抽取将分子、分母、上标打乱。公式编号置于数学块外。
- **参考文献。** 完整保留英文书目，并提供中文题名；作者姓名、刊会名称和标识不自行翻译或修订。本文 [10] 是上科大 Yanpeng Hu 等的 HBFSim，不是上一份 MBZUAI Jinheng Li 等的同名论文。正文原有的模型简称按所在位置保留，不统一替换成别的版本名。
- **翻译口径。** 以完整翻译为主，没有将方法和实验改成摘要。E2E 的“2–5.5 倍”按正文明确的相对于基线倍数译；goodput 下降倍数写成降至基线的倒数，避免把下降百分比与剩余比例混淆。ρ 按字节读／写，write/read ratio 按字节写／读。原文“outside the write path”保留其措辞，由后续异步 DRAM 水位线说明提供语境，不额外推断全部写入均没有成本。
- **原文口径问题 1：容量匹配。** 第 6.1 节和表 5 图注称 HBF-1 对 SSD24、HBF-2 对 SSD12，表 5 又限定 B200；但表 3(c) 中 B200 的共享 HBF 容量分别是 48 TB、24 TB，而 H100 才是 24 TB、12 TB。两处未给出足够信息消除冲突。原文与译文保留各自值，表 5 读图提示明确提醒，未擅自把 SSD 基线改为其他容量。
- **原文口径问题 2：图 12。** 图 12 纵轴“每次写入的有效读取”只标 0–1，而式（8）及正文称门槛通常高于 1；原文未说明是否归一化。故保留原图并明确将其作为定性示意，不用刻度推导实际 ρ 阈值。第 9.1 节也说明该图不是标定后的精确边界。
- **原文口径问题 3：表头与汇总。** 表 3(a) 的 Prompt／Output 各有斜杠双值，表头没有明确解释统计含义，未自行补写成均值／P95。表 9 同时存在 overall 与 batched, all blocks，保留原行名，不假定其分母相同。表 5 只列 B200，虽正文有更宽泛的“every GPU”描述，未为不存在的 H100 行补数据。
- **统计与硬件边界。** 不把仿真测量写成真实 HBF 硬件实测；3D-ICE、80°C 阈值、TLC 预算、单位写放大、线性 TBW 耗尽和每日流量外推均随结果保留。图 6 高负载单点与正文全实验组平均口径不同，未互相替换。
- **辅助说明。** 各图的“读图提示”、公式中文辅助说明及末尾“阅读提示”为独立解释，不混入作者的英文或中文译文。原文结论针对未改运行时的 SSD 式短暂 KV 池，不推广为所有 HBF 用途都无效。
- **未完成／低置信度内容。** 无未译正文、无缺失图表、无低置信度 OCR。中等置信度的公式是 PDF 转写来源说明，已逐式视觉核对。确定性数学检查与资产验证见 `reader_validation.json`。
- `paper.md` 与 `HBF_Sucks_中英对照.md` 内容完全相同，分别作为标准入口与便于辨识的文件名。
''')
print(json.dumps(m['coverage'],ensure_ascii=False))
