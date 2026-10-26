from pathlib import Path
import xml.etree.ElementTree as ET
import json,re,subprocess,hashlib
from PIL import Image

ROOT=Path('/home/kurisu/Desktop/论文/笔记/HBF-Sucks')
PDF=ROOT/'source/HBF_Sucks.pdf'
NS={'x':'http://www.w3.org/1999/xhtml'}
PAGES=ET.parse(ROOT/'source/layout-clean.html').findall('.//x:page',NS)
FIGS=[
 (1,1,[317,254,560,357],[317,358,561,380]),
 (2,3,[53,82,296,213],[53,220,296,233]),
 (3,5,[53,82,296,210],[53,218,296,242]),
 (4,7,[317,82,561,154],[317,165,561,199]),
 (5,8,[53,222,561,324],[53,334,561,356]),
 (6,8,[53,369,561,466],[53,477,561,499]),
 (7,8,[53,510,561,614],[53,624,561,647]),
 (8,9,[53,231,296,322],[53,333,296,367]),
 (9,10,[318,259,560,347],[317,359,561,427]),
 (10,11,[53,81,296,312],[53,321,296,367]),
 (11,11,[318,82,560,175],[317,183,561,207]),
 (12,12,[53,82,296,246],[53,258,296,293]),
]
TABLES=[
 (1,1,[53,606,560,708],[53,590,560,604]),
 (2,3,[62,279,285,391],[53,248,296,272]),
 (3,5,[54,273,294,495],[53,252,296,265]),
 (4,6,[321,127,556,285],[317,83,561,118]),
 (5,8,[122,116,489,212],[53,83,561,107]),
 (6,9,[58,106,291,217],[53,83,296,96]),
 (7,9,[59,398,290,481],[53,379,296,392]),
 (8,9,[330,270,546,330],[317,248,561,261]),
 (9,10,[323,126,553,247],[317,83,561,118]),
]
EQ=[
 (1,2,[318,539,560,552],r'\mathrm{stack}\to\mathrm{die}\to\mathrm{plane}\to\mathrm{block}\to\mathrm{page}\to\mathrm{cell}', 'HBF 内部层级'),
 (2,3,[318,395,560,424],r'\begin{aligned} BW_{\mathrm{effective}}=\min(&BW_{\mathrm{interface}},BW_{\mathrm{array}},BW_{\mathrm{controller}},\\ &BW_{\mathrm{power}},BW_{\mathrm{thermal}},BW_{\mathrm{workload}}).\end{aligned}', '有效带宽由最紧的约束决定'),
 (3,4,[53,436,296,451],r'B_{\mathrm{KV/request}}=2NLH_{\mathrm{KV}}D_{\mathrm{head}}b,', '每个请求的 KV 容量'),
 (4,4,[318,286,560,301],r'\mathrm{save}:\quad\mathrm{GPU\ HBM}\to\mathrm{cache\ tier},', 'KV 保存方向'),
 (5,4,[318,301,560,315],r'\mathrm{load}:\quad\mathrm{cache\ tier}\to\mathrm{GPU\ HBM},', 'KV 加载方向'),
 (6,6,[53,389,296,453],r'\begin{aligned}\Delta_{\mathrm{HBF}}={}&\underbrace{f\Delta t_{\mathrm{media}}}_{\text{critical-path I/O}}-\underbrace{C_{\mathrm{move}}}_{\text{movement/control}}-\underbrace{C_{\mathrm{pkg}}}_{\text{near-tier opportunity}}\\ &-\underbrace{C_{\mathrm{var}}}_{\text{throttle/variability}}-\underbrace{C_{\mathrm{life}}}_{\text{endurance/capacity}}.\end{aligned}', 'HBF 的净收益与各项成本'),
 (7,6,[53,653,296,676],r'\frac{\Delta T}{T}=f\left(1-\frac{1}{k}\right)\le f.', '介质加速收益的上限'),
 (8,6,[318,400,560,421],r'\rho>\rho^{\star}=\frac{AC}{S}.', '每次写入所需的有效读取门槛'),
]
FINDINGS=[(1,7,[323,231,555,286]),(2,9,[59,495,291,551]),(3,9,[323,650,555,706]),(4,10,[59,543,291,599]),(5,11,[59,487,291,542]),(6,11,[323,483,555,549])]
def rect(e):return [float(e.get(k)) for k in ['xMin','yMin','xMax','yMax']]
def inside(r,b):return b[0]-1<=(r[0]+r[2])/2<=b[2]+1 and b[1]-1<=(r[1]+r[3])/2<=b[3]+1
KEEP=set('high low full end long short near far device host page block read write request memory serving critical capacity fixed per two three write once off on SSD HBF HBM write read microsecond package production model single cost shared read-mostly write-heavy'.lower().split())
def joined(ls):
 s=''
 for l in ls:
  t=l['text'].strip()
  if s.endswith('-'):
   last=re.search(r'([\w.]+)-$',s)
   keep=last and (last.group(1).lower() in KEEP or t[:1].isupper() or t[:1].isdigit())
   s+=t if keep else ''
   if not keep:s=s[:-1]+t
  else:s+=(' ' if s else '')+t
 return re.sub(r'\s+',' ',s).strip()
def boxtext(pn,b):
 ls=[]
 for line in PAGES[pn-1].findall('.//x:line',NS):
  ws=[w for w in line.findall('x:word',NS) if inside(rect(w),b)]
  if ws:ls.append({'text':' '.join(w.text or '' for w in ws),'bbox':[min(rect(w)[0] for w in ws),min(rect(w)[1] for w in ws),max(rect(w)[2] for w in ws),max(rect(w)[3] for w in ws)]})
 return joined(sorted(ls,key=lambda l:(round(l['bbox'][1],1),l['bbox'][0])))

blocks=[]
def add(t,ps,typ='paragraph',frags=None,**extra):
 b=dict(id=f'S{sum(x["id"].startswith("S") for x in blocks)+1:03}',page=ps[0],pages=ps,type=typ,original_text=t,translation='',confidence='high',refs=[],source_fragments=frags or [])
 if frags and len(ps)==1:b['bbox']=[min(f['bbox'][0] for f in frags),min(f['bbox'][1] for f in frags),max(f['bbox'][2] for f in frags),max(f['bbox'][3] for f in frags)]
 b.update(extra);blocks.append(b)
add('HBF Sucks? A Full-Stack Characterization of High-Bandwidth Flash for KV-Centric LLM Serving. Zhuoran Li¹; Zhuohang Bian¹; Xin Huang²; Yibo Zhao¹; Guangyu Sun¹; Youwei Zhuo¹,*. ¹School of Integrated Circuits, Peking University, Beijing, China. ²Fudan Institute of Systems for Advanced Computing, Fudan University, Shanghai, China. *Corresponding author. Emails: {zhuoranli, bianzhuohang26, yibozhao}@stu.pku.edu.cn; {gsun, youwei}@pku.edu.cn; huangxin25@m.fudan.edu.cn. arXiv:2608.11668v4 [cs.AR], 14 Sep 2026.',[1],'metadata')
add('A Challenge to the Reader. '+boxtext(1,[61,216,551,249]),[1],'challenge')
add('Abstract',[1],'heading');add(boxtext(1,[53,272,304,548]),[1])
add('Keywords: '+boxtext(1,[317,401,561,425]),[1],'metadata')

events=[]
for pn,page in enumerate(PAGES,1):
 ex=[z for _,p,r,c in FIGS+TABLES if p==pn for z in [r,c]]
 ex.extend(r for _,p,r,_,_ in EQ if p==pn);ex.extend(r for _,p,r in FINDINGS if p==pn)
 ls=[]
 for line in page.findall('.//x:line',NS):
  for col in [0,1]:
   ws=[w for w in line.findall('x:word',NS) if (0 if rect(w)[0]<306 else 1)==col and not any(inside(rect(w),b) for b in ex)]
   if not ws:continue
   r=[min(rect(w)[0] for w in ws),min(rect(w)[1] for w in ws),max(rect(w)[2] for w in ws),max(rect(w)[3] for w in ws)]
   t=' '.join(w.text or '' for w in ws)
   if r[1]<80 or r[1]>710 or not t:continue
   if pn==1 and (col==0 or r[1]<430):continue
   if pn==5 and col==0 and r[1]>700:continue
   ls.append(dict(page=pn,col=col,bbox=r,text=t))
 ls.sort(key=lambda l:(l['col'],round(l['bbox'][1],1),l['bbox'][0]))
 merged=[]
 for l in ls:
  if merged and l['col']==merged[-1]['col'] and abs(l['bbox'][1]-merged[-1]['bbox'][1])<.3:
   m=merged[-1];m['text']+=' '+l['text'];m['bbox'][2]=max(m['bbox'][2],l['bbox'][2]);m['bbox'][3]=max(m['bbox'][3],l['bbox'][3])
  else:merged.append(l)
 for n,p,r,latex,name in EQ:
  if pn==p:merged.append(dict(page=p,col=0 if r[0]<306 else 1,bbox=r,text='',equation=dict(id=f'E{n:03}',page=p,pages=[p],type='equation',equation_number=str(n),latex=latex,name=name,bbox=r,confidence='medium',image_path=None)))
 for n,p,r in FINDINGS:
  if pn==p:merged.append(dict(page=p,col=0 if r[0]<306 else 1,bbox=r,text=boxtext(p,r),finding=True))
 merged.sort(key=lambda l:(l['col'],round(l['bbox'][1],1),l['bbox'][0]))
 events+=merged

cur=[];typ='paragraph';refs=False
def flush():
 global cur
 if cur:add(joined(cur),sorted(set(l['page'] for l in cur)),typ,cur);cur=[]
for l in events:
 t=l['text'];r=l['bbox'];base=53.8 if l['col']==0 else 317.955
 if 'equation' in l:flush();blocks.append(l['equation']);continue
 if l.get('finding'):flush();add(t,[l['page']],'finding',[l]);continue
 h=(re.match(r'^\d+(?:\.\d+)?\s+[A-Z]',t) and r[3]-r[1]>9.6) or t=='References'
 if h:flush();typ='heading';cur=[l];refs=t=='References';continue
 if typ=='heading' and r[3]-r[1]>9.6 and r[0]>base+15:cur.append(l);continue
 if typ=='heading':flush();typ='reference' if refs else 'paragraph'
 if refs:
  if re.match(r'^\[\d+\]',t):flush()
 else:
  if (7<r[0]-base<13) or re.match(r'^(?:\d\.\d\.\d\s|\(\d\)|C[123][:—]|Reuse distribution|Composition of|Thermal model|Why the|KV-cache management\.|HBF\.|Flash reliability\.)',t):flush()
 cur.append(l)
flush()
add('Code (footnote 1): https://github.com/pku-lemonade/TokenSim',[5],'metadata')

figures=[];tables=[];caps=[]
for kind,entries,target in [('figure',FIGS,figures),('table',TABLES,tables)]:
 for n,p,r,c in entries:
  fid=('F' if kind=='figure' else 'T')+f'{n:03}';cid=f'C{len(caps)+1:03}'
  path=f'assets/{kind}s/{kind}-{n:02}.png'
  target.append(dict(id=fid,number=n,page=p,bbox=r,caption_bbox=c,caption_id=cid,image_path=path,alt_text=f'{kind.title()} {n}',placement_hint='near_first_substantive_mention',placed_after=None))
  caps.append(dict(id=cid,page=p,type='caption',bbox=c,original_text=boxtext(p,c),translation='',asset_id=fid,confidence='high'))
  png=ROOT/'source'/f'crop-source-{p:02}.png'
  if not png.exists():subprocess.run(['pdftoppm','-f',str(p),'-l',str(p),'-r','240','-singlefile','-png',str(PDF),str(png.with_suffix(''))],check=True,stderr=subprocess.DEVNULL)
  im=Image.open(png);scale=im.width/612;im.crop(tuple(round(v*scale) for v in r)).save(ROOT/path)
for i,b in enumerate(blocks,1):b['order']=i
m=dict(paper=dict(title=blocks[0]['original_text'].split('. Zhuoran')[0],source_type='pdf',source_path=str(PDF),language='en',page_count=13,source_sha256=hashlib.sha256(PDF.read_bytes()).hexdigest(),arxiv_id='2608.11668v4'),blocks=blocks,captions=caps,figures=figures,tables=tables,equations=[b for b in blocks if b['type']=='equation'],glossary=[])
(ROOT/'source_map.json').write_text(json.dumps(m,ensure_ascii=False,indent=2))
(ROOT/'source/source_blocks.txt').write_text('\n\n'.join(f"{b['id']} | p.{','.join(map(str,b.get('pages',[b['page']])))} | {b['type']}\n{b.get('original_text',b.get('latex'))}" for b in blocks))
(ROOT/'source/captions.txt').write_text('\n\n'.join(c['id']+' '+c['asset_id']+'\n'+c['original_text'] for c in caps))
print(dict(blocks=len(blocks),paragraphs=sum(b['type']=='paragraph' for b in blocks),headings=sum(b['type']=='heading' for b in blocks),refs=sum(b['type']=='reference' for b in blocks)))
