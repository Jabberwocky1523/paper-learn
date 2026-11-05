from pathlib import Path
import pdfplumber,json,re,hashlib
ROOT=Path(__file__).resolve().parents[1]
PDF=ROOT.parents[1]/'文献/Gandalf.pdf'
# image box; caption box, PDF points
ASSETS=[
('figure',1,1,[350,218,517,296],[317,303,560,338]),
('table',1,1,[317,385,560,430],[317,348,560,375]),
('table',2,2,[317,115,560,210],[317,80,560,105]),
('figure',2,3,[83,86,258,176],[53,185,296,222]),
('figure',3,4,[53,86,296,168],[53,179,296,203]),
('figure',4,4,[318,86,559,155],[317,167,560,212]),
('figure',5,5,[343,86,535,178],[317,192,560,217]),
('figure',6,6,[353,86,528,179],[317,193,560,219]),
('table',3,8,[61,116,286,224],[53,80,296,105]),
('figure',7,9,[53,87,559,208],[53,219,560,256]),
('figure',8,9,[77,273,272,434],[53,445,296,503]),
('figure',9,9,[321,274,557,405],[317,415,560,441]),
('figure',10,10,[78,87,273,202],[53,215,296,251]),
('figure',11,10,[350,87,507,196],[317,206,560,242]),
('figure',12,11,[53,87,293,196],[53,209,296,246]),
('figure',13,11,[322,87,552,184],[317,196,560,221]),
('figure',14,12,[77,87,273,181],[53,193,296,240]),
]
EQS=[(1,3,0,477,504,r'T_{\mathrm{SSD}}=\frac{E_{\mathrm{TBW}}}{\mathrm{WAF}\times E_{\mathrm{workload}}}\quad\text{Terabytes Written}'),(2,3,0,627,654,r'T_{\mathrm{HDD}}=\frac{E_{\mathrm{HDD}}}{E_{\mathrm{workload}}}\quad\text{Terabytes Read and Written}'),(3,5,1,347,375,r'I_{\mathrm{type\text{-}aware}}=\frac{T_{\mathrm{type\text{-}aware}}}{T_{\mathrm{write\text{-}back}}}\approx\frac{W_{\mathrm{write\text{-}back}}}{W_{\mathrm{type\text{-}aware}}}=\frac{s(F+L)-C}{s(F+pL)}'),(4,6,0,301,327,r'\max C_r(H-H_{\mathrm{left}})-C_wW\;\Longleftrightarrow\;\max(H-H_{\mathrm{left}})-\lambda W,\qquad\lambda=\frac{C_w}{C_r}'),(5,6,0,432,464,r'C_i(x_i)=\underbrace{(1-x_i)H_iC_r}_{\text{recompute if dropped / 丢弃后重新计算}}+\underbrace{x_iC_ws_i}_{\text{write if kept / 保留时写入}}'),(6,6,1,253,280,r'\alpha\cdot\mathrm{move\_cost}_j<\mathrm{drop\_cost}_j\;\Longleftrightarrow\;\frac{\mathrm{drop\_cost}_j}{\mathrm{move\_cost}_j}>\alpha'),(7,6,1,687,713,r'\mathrm{drop\_cost}=H_dv_dC_r\;\longrightarrow\;h_d=\frac{H_dv_dC_r}{s_da_d}'),(8,7,0,263,312,r'\mathrm{move\_cost}=\underbrace{C_ws_j}_{\text{cost of writing }j\text{ / 写入成本}}+\underbrace{\sum_{e\in E_j}H_ev_eC_r}_{\text{replacement cost in SSD / SSD 替换成本}}\;\longrightarrow\;\frac{t_LC_w}{a_j}+\min_{e\in E_j}h_e')]
KEEP={'high','low','full','linear','sparse','sliding','write','read','multi','one','two','short','long','end','cost','cache','attention','type','capacity','host','device','layer','prefix','probability','workload','flash','retention','GPU','CPU','SSD','NAND','per','round','root','single','off','on','state','least','most','cold','reuse','recompute','key','hyperparameter','frequency','life','write−back'}
def clean(s):
 s=s.replace('ﬀ','ff').replace('ﬁ','fi').replace('ﬂ','fl').replace('ﬃ','ffi').replace('ﬄ','ffl')
 s=re.sub(r'\bGan-\s*dalf\b','Gandalf',s,flags=re.I)
 s=re.sub(r'\s+',' ',s).strip()
 return s

def join(ls):
 s=''
 for l in ls:
  t=l['text'].strip()
  if s.endswith('-'):
   m=re.search(r'([\w]+)-$',s); keep=m and (m.group(1).lower() in {x.lower() for x in KEEP} or t[:1].isupper() or t[:1].isdigit())
   s=s+t if keep else s[:-1]+t
  else:s+=(' ' if s else '')+t
 return clean(s)
def center_inside(l,r):return r[0]-1<=(l['x0']+l['x1'])/2<=r[2]+1 and r[1]-1<=(l['top']+l['bottom'])/2<=r[3]+1
nodes=[];assets=[]
with pdfplumber.open(PDF) as pdf:
 for typ,n,p,img,cap in ASSETS:
  page=pdf.pages[p-1]
  caption=join(page.crop(cap).extract_text_lines(x_tolerance=1))
  path=f'assets/{typ}-{n:02}.png'
  page.crop(img).to_image(resolution=216).save(ROOT/path)
  assets.append(dict(type=typ,number=n,page=p,bbox=img,caption_bbox=cap,original_text=caption,path=path,translation=''))
 for pn,page in enumerate(pdf.pages,1):
  for col,(x0,x1) in enumerate([(53,296),(317,560)]):
   top=216 if pn==1 and col==0 else 80
   bottom=687 if pn==1 and col==0 else 713
   ls=page.crop((x0,top,x1,bottom)).extract_text_lines(x_tolerance=1)
   local=[]
   for a in assets:
    if a['page']==pn and ((a['bbox'][0]<310)==(col==0) or a['number']==7 and a['type']=='figure'):
     ls=[l for l in ls if not center_inside(l,a['bbox']) and not center_inside(l,a['caption_bbox'])]
     if col==0 or a['bbox'][0]>310:local.append(dict(type='asset',asset=f"{a['type']}-{a['number']:02}",page=pn,top=min(a['bbox'][1],a['caption_bbox'][1])))
   for n,p,c,y0,y1,tex in EQS:
    if (p,c)==(pn,col):
     ls=[l for l in ls if not y0<=(l['top']+l['bottom'])/2<=y1]
     local.append(dict(type='equation',number=n,latex=tex,page=pn,top=y0))
   group=[]
   def flush():
    if not group:return
    t=join(group); ishead=(max(c['size'] for c in group[0]['chars'])>10 and not t.startswith('HDDs ')) or t=='Abstract' or t=='References'
    local.append(dict(type='heading' if ishead else 'paragraph',original_text=t,pages=[pn],page=pn,top=group[0]['top'],bbox=[min(l['x0'] for l in group),group[0]['top'],max(l['x1'] for l in group),group[-1]['bottom']],indented=group[0]['x0']>x0+6))
    group.clear()
   prev=None
   for l in ls:
    # Separate section headings, indented paragraphs, reference entries and bullet starts.
    big=max(c['size'] for c in l['chars'])>10
    prevbig=bool(group and max(c['size'] for c in group[0]['chars'])>10)
    start=bool(group and ((l['top']-group[-1]['bottom']>5) or (l['x0']>x0+6 and l['x0']<x0+13) or re.match(r'^\[\d+\]',l['text']) or re.match(r'^(?:\(\d\)|•|3\.3\.[12])\s',l['text']) or big!=prevbig))
    if start:flush()
    group.append(l)
   flush();local.sort(key=lambda z:z['top']);nodes.extend(local)
# Merge paragraph continuations over columns/pages, including intervening floats.
merged=[]
for n in nodes:
 if n['type']=='paragraph' and not n['indented'] and not re.match(r'^(?:\[\d+\]|\(\d\)|•|3\.3\.[12])',n['original_text']):
  k=next((k for k in range(len(merged)-1,-1,-1) if merged[k]['type'] not in ['asset']),None)
  if k is not None and merged[k]['type']=='paragraph' and not re.search(r'[.!?:]$',merged[k]['original_text']) and (n['page']!=merged[k]['page'] or n['top']<merged[k]['top']):
   prev=merged[k]; prev['original_text']=join([{'text':prev['original_text']},{'text':n['original_text']}]);prev['pages']=sorted(set(prev['pages']+n['pages']));prev.setdefault('continuation_regions',[]).append({'page':n['page'],'bbox':n['bbox']});continue
 merged.append(n)
for i,n in enumerate(merged,1):n['id']=f'S{i:03}';n['translation']=''
(ROOT/'source/blocks.json').write_text(json.dumps(merged,ensure_ascii=False,indent=2))
(ROOT/'source/assets.json').write_text(json.dumps(assets,ensure_ascii=False,indent=2))
(ROOT/'source/blocks.txt').write_text('\n\n'.join(f"{n['id']} [{n['type']}] p.{n['page']}\n{n.get('original_text',n.get('latex',n.get('asset')))}" for n in merged))
print(len(merged),'blocks',len(assets),'assets')
