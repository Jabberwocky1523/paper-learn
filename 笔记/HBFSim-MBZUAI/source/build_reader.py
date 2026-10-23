from pathlib import Path
import json,re,hashlib
from collections import defaultdict

ROOT=Path('/home/kurisu/Desktop/论文/笔记/HBFSim-MBZUAI')
m=json.loads((ROOT/'source_map.json').read_text())
assert not any(b.get('translation') for b in m['blocks']), 'Run on the prepared source map only'
raw=(ROOT/'source/translations.txt').read_text()
translations={sid:t.strip() for sid,t in re.findall(r'@@(S\d{3})\n(.*?)(?=\n@@S\d{3}\n|\Z)',raw,re.S)}
ref_titles=json.loads((ROOT/'source/reference_titles_zh.json').read_text())
asset_notes=json.loads((ROOT/'source/asset_translations.json').read_text())

def math_text(s):
 s=s.replace('1.8 × 10 5','$1.8\\times10^5$').replace('1.0–1.7×10 7','$1.0\\text{–}1.7\\times10^7$').replace('2.7 × 10 5','$2.7\\times10^5$')
 s=s.replace('(𝑟 + 1) −𝛼','$(r+1)^{-\\alpha}$').replace('rank 𝑟 .','rank $r$.')
 s=re.sub(r'𝛼\s*=\s*1, 1\.5, and 2',r'$\\alpha=1,1.5,2$',s)
 s=re.sub(r'𝛼\s*=\s*1\.5',r'$\\alpha=1.5$',s)
 s=re.sub(r'𝛼\s*=\s*2',r'$\\alpha=2$',s)
 s=re.sub(r'𝛼\s*=\s*1',r'$\\alpha=1$',s)
 s=s.replace('𝛼',r'$\alpha$')
 return s

for b in m['blocks']:
 b['original_text']=math_text(b['original_text'])
 if b['type']=='reference':
  # Restore wrapped URLs against the URI annotations embedded in the supplied PDF.
  fixes={
   'https://doi.org/ 10.':'https://doi.org/10.',
   'https://doi.org/10. 1109':'https://doi.org/10.1109',
   'https://nvidia.github.io/ TensorRT':'https://nvidia.github.io/TensorRT',
   'https: //':'https://',
   'assets/public/ sandisk/':'assets/public/sandisk/',
   'https://arxiv.org/abs/2607. 10186':'https://arxiv.org/abs/2607.10186',
   'https://arxiv.org/abs/ 2606.':'https://arxiv.org/abs/2606.',
   'https://www.nvidia.com/enus/':'https://www.nvidia.com/en-us/',
   'ocp-hbf-architecturespecification-':'ocp-hbf-architecture-specification-',
   '/2025/scalingbeyond-':'/2025/scaling-beyond-',
   'sk-hynix-and-sandiskbegin-':'sk-hynix-and-sandisk-begin-',
  }
  for a,z in fixes.items():b['original_text']=b['original_text'].replace(a,z)
  n=int(re.match(r'\[(\d+)\]',b['original_text']).group(1))
  b['translation']=f'[{n}] 中文题名：{ref_titles[str(n)]}。作者、年份、出版载体、页码及 DOI／网址等书目信息保留上方原文，以便检索。'
 else:
  assert b['id'] in translations,b['id']
  b['translation']=translations[b['id']]

# Polish only the prose; the mathematical comparisons retain the source values.
byid={b['id']:b for b in m['blocks']}
byid['S057']['translation']=byid['S057']['translation'].replace('相比 2 HBM＋6 HBF，Llama-3.1-70B 耗时缩短至其约 1/1.4–1/1.5，Qwen3-235B-A22B 约为其 1/2.9。','换言之，2 HBM＋6 HBF 的耗时分别为该全 HBM 配置的 1.4–1.5 倍（Llama-3.1-70B）和 2.9 倍（Qwen3-235B-A22B）。')
byid['S086']['translation']=byid['S086']['translation'].replace('此时其 TPOT 比主机 DRAM 低至 1/11.0–1/19.0，比 NVMe SSD 低至 1/86.6–1/154.1。','此时，主机 DRAM 的 TPOT 为 HBF 的 11.0–19.0 倍，NVMe SSD 为其 86.6–154.1 倍。')
byid['S079']['translation']=byid['S079']['translation'].replace('重现一个代表性解码状态','重现一个代表性解码步')

gloss=[
 ('HBF','高带宽闪存','High Bandwidth Flash','HBF','保留 HBF；首次出现给出全称。'),
 ('HBM','高带宽内存','High Bandwidth Memory','HBM, HBM4','按代际保留 HBM4 等型号。'),
 ('capacity tier','容量层','用于扩展存储容量的层级','capacity tier, external tier','外部层级仅在原文强调封装外位置时使用。'),
 ('peer mode','并列模式','HBM 与 HBF 独立寻址、共同构成地址空间','peer mode','统一译为并列模式。'),
 ('tiered mode','分层模式','HBM 作为 HBF／其他容量层的缓存','tiered mode','统一译为分层模式。'),
 ('weights first','权重优先','先把权重放入 HBM','weights first','与 KV 优先对应。'),
 ('KV first','KV 优先','运行中 KV、权重、保留前缀依次放入 HBM','KV first, KV-first','保留 KV 缩写。'),
 ('prefill','预填充','处理提示词并建立相应 KV 的阶段','prefill, chunked prefill','chunked prefill 译为分块预填充。'),
 ('decode','解码','逐步生成输出词元的阶段','decode, decoding','统一译为解码。'),
 ('TPOT','输出词元平均耗时','time per output token','TPOT','越低越好；与吞吐量区别。'),
 ('TTFT','首词元时间','time to first token','time to first token','保留其延迟含义。'),
 ('FTL','闪存转换层','flash translation layer','host FTL, host-managed FTL','host FTL 译为主机端 FTL。'),
 ('page-level mapping','页级映射','每页一个映射表项','page-level mapping','不与页内偏移混淆。'),
 ('extent mapping','区段映射','以连续页区间表示映射','extent mapping, extent index','extent index 译为区段索引。'),
 ('block-level mapping','块级映射','每逻辑块一个映射表项','block-level mapping','保留其单平面布局条件。'),
 ('GC','垃圾回收','garbage collection','GC','主机端执行。'),
 ('wear leveling','磨损均衡','均衡块的擦除磨损','wear leveling, static wear leveling','不与写放大混淆。'),
 ('P/E cycle','编程／擦除循环','program/erase cycle','P/E, program/erase','保持原文次数与假设条件。'),
 ('write-back','回写','将脏数据写回下一存储层','write-back, writeback','eviction 统一译为淘汰。'),
 ('decayed LFU','衰减 LFU','定期衰减访问计数的最不常用替换','decayed-LFU, decayed LFU','保持与 LRU、FIFO 的区别。'),
 ('plane','平面','NAND 的内部并行资源','plane, planes per die','不译作页。'),
 ('bank','存储体','页感测与页编程的服务资源','bank','与通道、裸片、平面分别保留。'),
 ('TSV','硅通孔','through-silicon via','TSVs','保留 TSV 缩写。'),
 ('ECC','纠错码','error-correcting code','ECC','ECC engine 译为 ECC 引擎。'),
]
m['glossary']=[dict(term=t,translation=z,first_use_definition=d,variants=v,decision=n) for t,z,d,v,n in gloss]

caps={c['id']:c for c in m['captions']}
insertions=defaultdict(list)
for asset in m['figures']+m['tables']:
 data=asset_notes[asset['id']]
 asset['placed_after']=data['placed_after']
 asset['title']=data['title']
 asset['reading_note']=data['note']
 cap=caps[asset['caption_id']]
 cap['original_text']=math_text(cap['original_text']).replace('500token','500-token')
 cap['translation']=data['translation']
 cap['refs']=[asset['id']]
 asset['original_caption']=cap['original_text']
 asset['translated_caption']=cap['translation']
 if asset['id'].startswith('T'):
  asset['original_table']=data['original_table'];asset['translated_table']=data['translated_table']
 insertions[asset['placed_after']].append(asset)
 byid[asset['placed_after']]['refs'].append(asset['id'])

headings=[b for b in m['blocks'] if b['type']=='heading']
parts=['''---
title: "HBFSim（MBZUAI）全文中英对照"
aliases: ["HBFSim MBZUAI", "HBFSim Jinheng Li", "HBFSim RACS 2026"]
tags: [papers/HBF, papers/LLM, readers/bilingual]
date: 2026-10-23
arxiv_id: "2610.23503v1"
doi: "10.1145/3848591.3856870"
---

# HBFSim（MBZUAI）全文中英对照

**英文题名：** HBFSim: A Simulator for Exploring HBF in Memory Hierarchies for LLMs  
**中文题名：** HBFSim：用于探索大语言模型存储层次中 HBF 的模拟器  
**作者与机构：** Jinheng Li、Guosheng Wang、Hongchao Du、Shangyu Wu、Qiao Li、Chun Jason Xue；MBZUAI，阿联酋阿布扎比。  
**来源版本：** 用户提供的 11 页 PDF；首页标注 arXiv:2610.23503v1，2026-10-16；RACS ’26，DOI 10.1145/3848591.3856870。  
**原文：** [本文件夹保存的 PDF](source/HBFSim_MBZUAI.pdf)

> 本文为逐段中英对照阅读版，完整覆盖摘要、正文、讨论、结论、图表和 37 条参考文献。英文与中文按段落配对，Source 标记对应 PDF 页码和稳定块编号；跨栏、跨页段落已接续。9 张原图和 3 张原表放在相关讨论旁，表格另附中文转写。参考文献保留完整英文书目，补充中文题名。下文单独标记的“读图提示”是辅助说明，与作者原文分开。

## 章节索引
''']
for b in headings:parts.append(f"- [{b['translation']}](#{b['id']})")
parts.append('\n## PDF 页码索引\n')
for page in range(1,12):
 first=next(b for b in m['blocks'] if page in b.get('pages',[b['page']]))
 parts.append(f"- [PDF 第 {page} 页](#{first['id']})" + ('（参考文献 [37] 的续页）' if page==11 else ''))
parts.append('\n## 术语对照\n\n| 原文统一用语 | 中文统一用语 | 首次定义／说明 | 原文变体 | 处理决定 |\n| --- | --- | --- | --- | --- |')
for t,z,d,v,n in gloss:parts.append(f'| {t} | {z} | {d} | {v} | {n} |')
parts.append('\n---\n\n## 全文中英对照\n')

ordered=[]
for b in m['blocks']:
 if b['type']=='heading':
  lvl='###' if re.match(r'^\d+\.\d+',b['original_text']) else '##'
  parts.append(f"\n<a id=\"{b['id']}\"></a>\n{lvl} {b['translation']} · {b['original_text']}\n\n**Source:** p.{b['page']} {b['id']}\n\n**Original:** {b['original_text']}\n\n**中文:** {b['translation']}\n")
 else:
  pp='–'.join(map(str,[min(b['pages']),max(b['pages'])])) if len(b['pages'])>1 else str(b['page'])
  parts.append(f"\n<a id=\"{b['id']}\"></a>\n**Source:** p.{pp} {b['id']}\n\n**Original:** {b['original_text']}\n\n**中文:** {b['translation']}\n")
 ordered.append(b)
 for a in insertions[b['id']]:
  cid=a['caption_id'];c=caps[cid]
  parts.append(f"\n<a id=\"{a['id']}\"></a>\n#### {a['title']}\n\n**Placed near:** p.{b['page']} {b['id']}  \n**Source:** p.{a['page']} {a['id']} · {cid}\n\n![{a['alt_text']}]({a['image_path']})\n\n<a id=\"{cid}\"></a>\n**Original:** {c['original_text']}\n\n**中文:** {c['translation']}\n")
  if a['id'].startswith('T'):
   parts.append(f"\n**中文表格：**\n\n{a['translated_table']}\n")
  parts.append(f"\n**读图提示（辅助说明）：** {a['reading_note']}\n")
  ordered.append({'id':a['id'],'page':a['page'],'type':'figure' if a['id'].startswith('F') else 'table','original_text':a.get('original_table',a['alt_text']),'translation':a.get('translated_table',a['title']),'bbox':a['bbox'],'image_path':a['image_path'],'confidence':'high','refs':[cid],'insert_after':b['id']})
  ordered.append(c)

parts.append('''
---

## 阅读提示（辅助说明）

1. **先区分这篇与上科大 HBFSim。** 本文是 MBZUAI 团队的事件驱动、闭环存储系统模拟器；此处的 GPU 计算耗时来自经实测校准的算子模型，见 [S036](#S036)、[S048](#S048)。
2. **把实测校准与器件假设分开。** 调度器和 A100/H200 算子经过验证；HBM4、HBF 的内部时序和部分参数仍是假设，见 [S049](#S049)。表 1 的 4 μs 读取时间也属于这些条件。
3. **读性能图前固定比较口径。** 图 4 两组比较的数据放置与封装位置条件不同；图 5、6 的缓存收益依赖工作集相对 HBM 的大小和专家热度；图 7 的吞吐上升伴随 TPOT 上升。对应 [S056](#S056)–[S066](#S066)。
4. **寿命是条件化估计。** 表 3 使用已公布的峰值词元速率、100,000 次 P/E 假设、全天候负载及理想磨损均衡；性能窗口不包含 GC 干扰，而寿命回放包含 GC，见 [S073](#S073)、[S079](#S079)。

提取、术语及版面处理说明见 [translation_notes.md](translation_notes.md)，段落与原图位置见 [source_map.json](source_map.json)。
''')

for i,b in enumerate(ordered,1):b['order']=i
m['blocks']=ordered
m['pages']=[{'page':p,'block_ids':[b['id'] for b in ordered if p in b.get('pages',[b['page']])]} for p in range(1,12)]
m['paper'].update({'authors':['Jinheng Li','Guosheng Wang','Hongchao Du','Shangyu Wu','Qiao Li','Chun Jason Xue'],'institution':'Mohamed bin Zayed University of Artificial Intelligence','arxiv_id':'2610.23503v1','doi':'10.1145/3848591.3856870','original_filename':'HBFSIM_.pdf','renamed_source':'/home/kurisu/Desktop/论文/文献/HBFSim_MBZUAI.pdf','venue':'RACS ’26 (as printed in supplied PDF)'})
m['coverage']={'pages':11,'body_source_blocks':124,'captions':12,'figures':9,'tables':3,'references':37,'display_equations':0,'translated_blocks':len(ordered),'untranslated_blocks':[]}
(ROOT/'source_map.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
md='\n'.join(parts)
(ROOT/'paper.md').write_text(md)
(ROOT/'HBFSim_MBZUAI_中英对照.md').write_text(md)
(ROOT/'translation_notes.md').write_text('''# 翻译与提取说明

- 来源为用户提供的 `HBFSIM_.pdf`，已改名为 `文献/HBFSim_MBZUAI.pdf`；PDF 字节未修改。笔记中保留同一原文副本。来源 SHA-256：`4641ccbbe62ccdab3aa26faf6bda5dd3bd8354e8281d27b599b59fd72216ab1c`。
- 处理完整 11 页：正文至第 10 页上方；第 10–11 页为 37 条参考文献，第 11 页仅包含参考文献 [37] 的续文和卷号。没有省略正文页、附加正文或参考文献。
- 依据双栏的自然阅读顺序接续段落；移除重复页眉、页脚，将断行连字符与连字恢复为连续英文。跨页段落保留所有来源页和逐行边界框。作者信息中的重复机构合并为同一署名机构，各作者与邮箱保留。参考文献中跨行断开的网址依据 PDF 内嵌链接恢复，未更换引用目标。
- 9 张图与 3 张表均以 240 dpi 从原 PDF 渲染后紧裁，未重绘数据。图注单独双语呈现；各图放到首次实质讨论旁，因此其展示位置可能不同于 PDF 浮动排版位置。3 张表另外提供中文表格；原表图片是数值核对依据。
- 本文没有独立编号的展示公式。正文中的科学计数、Zipf 指数及图 6 图注的权重公式已按原页视觉核对，使用行内数学排版，未擅自添加公式编号。
- 英文正文与中文逐段配对。引用编号、模型名、单位和数值条件保留。参考文献保留完整英文书目，提供中文题名；作者姓名、刊会名称和标识不自行汉译或外部修订。
- “读图提示”和末尾“阅读提示”是辅助说明，与原文及译文分开；不将器件假设写成实测结果。
- 术语以正文“术语对照”为准；FTL 统一为闪存转换层，peer mode 为并列模式，tiered mode 为分层模式，extent mapping 为区段映射。
- 原文在正文把文献 [4] 简称为 GTSim，而参考文献题名为 GPU-Tile-Sim；本译文照录两处称呼，没有替作者修正。原文元数据和引用列表按所提供 PDF 保留，未另行联网验证刊会状态或参考文献。
- 跳过／待译内容：无。低置信度 OCR：无，原文件为可提取文字 PDF。数学和图表资产检查结果见 `reader_validation.json`。
- `paper.md` 与 `HBFSim_MBZUAI_中英对照.md` 内容完全相同；前者为标准入口，后者便于在笔记目录中识别。
''')
(ROOT/'README.md').write_text('''# HBFSim（MBZUAI）

[打开全文中英对照](HBFSim_MBZUAI_中英对照.md)

完整 11 页，包含 9 张图、3 张表及 37 条参考文献。原文为 Jinheng Li 等、MBZUAI 团队的 *HBFSim: A Simulator for Exploring HBF in Memory Hierarchies for LLMs*。

- [原文 PDF](source/HBFSim_MBZUAI.pdf)
- [翻译与提取说明](translation_notes.md)
- [来源映射](source_map.json)
''')
print(json.dumps(m['coverage'],ensure_ascii=False))
