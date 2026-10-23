from pathlib import Path
import xml.etree.ElementTree as ET
import json, re, subprocess, hashlib
from PIL import Image

ROOT=Path('/home/kurisu/Desktop/论文/笔记/HBFSim-MBZUAI')
PDF=ROOT/'source/HBFSim_MBZUAI.pdf'
NS={'x':'http://www.w3.org/1999/xhtml'}
PAGES=ET.parse(ROOT/'source/layout.html').findall('.//x:page',NS)

FIGS=[
 (1,2,[52,82,296,195],[52,207,297,242]),
 (2,3,[53,82,296,242],[52,255,297,291]),
 (3,5,[51,81,297,193],[52,205,297,263]),
 (4,6,[52,82,297,274],[52,282,297,362]),
 (5,7,[52,80,561,224],[52,233,561,258]),
 (6,7,[317,259,561,355],[317,365,561,413]),
 (7,8,[52,82,297,200],[52,211,297,236]),
 (8,8,[316,82,561,191],[316,199,562,257]),
 (9,9,[51,82,297,181],[52,193,297,240]),
]
TABLES=[
 (1,5,[331,99,543,173],[317,82,560,96]),
 (2,5,[334,228,539,283],[317,178,561,225]),
 (3,8,[316,297,561,382],[316,259,562,295]),
]
def rect(line):
 return [float(line.attrib[x]) for x in ['xMin','yMin','xMax','yMax']]
def within(r,b):
 return b[0]-1 <= (r[0]+r[2])/2 <= b[2]+1 and b[1]-1 <= (r[1]+r[3])/2 <= b[3]+1
def text(line):
 return ' '.join(w.text or '' for w in line.findall('x:word',NS))
KEEP={'application','host','page','block','request','address','cycle','operator','compute','memory','read','write','capacity','first','full','coarse','fine','device','trace','out','per','long','short','steady','end','large','multi','cost','one','two','three','four','eight','fixed','cache','layer','data','model','instruction','command','pseudo','in','off','on','non','high','low','frequency','key','bit','held','closed','cycle','real','input','output','16','8','4','32','70B','CXL','KVCache','HBM','GPU','4.3'}
def joined(lines):
 s=''
 for l in lines:
  t=l['text'].strip()
  if s.endswith('-'):
   last=re.search(r'([A-Za-z0-9.]+)-$',s)
   keep=bool(last and (last.group(1).lower() in {k.lower() for k in KEEP|{'complete','whole'}} or t[:1].isupper() or t[:1].isdigit()))
   s=s+ t if keep else s[:-1]+t
  else:s+=((' ' if s else '')+t)
 s=re.sub(r'\s+',' ',s).replace('𝜇 s','μs').replace('𝜇s','μs')
 for a,b in {'per-formance':'performance','in-terface':'interface','out-puts':'outputs','in-cur':'incur'}.items():s=s.replace(a,b)
 return re.sub(r'(?<=\d)– +(?=\d)', '–', s)
def extract_box(pn,box):
 ls=[]
 for l in PAGES[pn-1].findall('.//x:line',NS):
  r=rect(l)
  if within(r,box):ls.append({'text':text(l),'bbox':r})
 return joined(sorted(ls,key=lambda x:(round(x['bbox'][1],1),x['bbox'][0])))

blocks=[]
def add(t,pages,typ='paragraph',fragments=None):
 sid=f'S{len(blocks)+1:03}'
 b={'id':sid,'page':pages[0],'pages':pages,'type':typ,'order':len(blocks)+1,'original_text':t,'translation':'','confidence':'high','refs':[],'source_fragments':fragments or []}
 if fragments and len(pages)==1:
  b['bbox']=[min(f['bbox'][0] for f in fragments),min(f['bbox'][1] for f in fragments),max(f['bbox'][2] for f in fragments),max(f['bbox'][3] for f in fragments)]
 blocks.append(b)

add('HBFSim: A Simulator for Exploring HBF in Memory Hierarchies for LLMs. Jinheng Li; Guosheng Wang; Hongchao Du; Shangyu Wu; Qiao Li; Chun Jason Xue. Mohamed bin Zayed University of Artificial Intelligence, Abu Dhabi, United Arab Emirates. Emails: jinheng.li@mbzuai.ac.ae; guosheng.wang@mbzuai.ac.ae; hongchao.du@mbzuai.ac.ae; shangyu.wu@mbzuai.ac.ae; qiao.li@mbzuai.ac.ae; jason.xue@mbzuai.ac.ae. arXiv:2610.23503v1 [cs.AR], 16 Oct 2026.',[1],'metadata')
add('ABSTRACT',[1],'heading')
add(extract_box(1,[52,313,297,546]),[1])
add('KEYWORDS: '+extract_box(1,[317,313,561,337]),[1],'metadata')
add('CCS CONCEPTS: '+extract_box(1,[52,572,297,608]),[1],'metadata')
add(extract_box(1,[52,659,297,712]),[1],'metadata')
add(extract_box(1,[317,339,561,402]),[1],'metadata')

alllines=[]
for pn,page in enumerate(PAGES,1):
 excluded=[]
 for _,p,r,c in FIGS+TABLES:
  if p==pn:excluded.extend([r,c])
 ls=[]
 for l in page.findall('.//x:line',NS):
  r=rect(l);t=text(l)
  if r[1]<80 or not t:continue
  if pn==1 and (r[0]<310 or r[1]<410):continue
  if any(within(r,b) for b in excluded):continue
  ls.append({'page':pn,'text':t,'bbox':r,'col':0 if r[0]<305 else 1})
 # The PDF splits section numbers from titles into adjacent same-baseline runs.
 ls.sort(key=lambda x:(x['col'],round(x['bbox'][1],1),x['bbox'][0]))
 merged=[]
 for l in ls:
  if merged and l['col']==merged[-1]['col'] and abs(l['bbox'][1]-merged[-1]['bbox'][1])<.2:
   m=merged[-1];m['text']+=' '+l['text'];m['bbox'][2]=max(m['bbox'][2],l['bbox'][2]);m['bbox'][3]=max(m['bbox'][3],l['bbox'][3])
  else:merged.append(l)
 alllines.extend(merged)

cur=[];refs=False
def flush():
 global cur
 if cur:
  pp=sorted(set(l['page'] for l in cur))
  add(joined(cur),pp,'reference' if refs else 'paragraph',cur)
  cur=[]
for l in alllines:
 t=l['text'];r=l['bbox'];base=53.8 if l['col']==0 else 317.955
 heading=(re.match(r'^[1-7](?:\.[1-5])?\s+[A-Z]',t) and r[3]-r[1]>9.6) or t=='REFERENCES'
 if heading:
  flush();add(t,[l['page']],'heading',[l]);refs=(t=='REFERENCES');continue
 if refs:
  if re.match(r'^\[\d+\]',t):flush()
 else:
  newp=(7<r[0]-base<13) or t.startswith('• ')
  if newp:flush()
 cur.append(l)
flush()

figures=[];tables=[];caps=[]
for kind,entries,target in [('figure',FIGS,figures),('table',TABLES,tables)]:
 for n,pn,r,c in entries:
  fid=('F' if kind=='figure' else 'T')+f'{n:03}'
  cid=f'C{len(caps)+1:03}'
  cap=extract_box(pn,c)
  image=f'assets/{kind}s/{kind}-{n:02}.png'
  target.append({'id':fid,'number':n,'page':pn,'caption_id':cid,'bbox':r,'caption_bbox':c,'image_path':image,'placement_hint':'near_first_substantive_mention','placed_after':None,'alt_text':f'{kind.title()} {n}'})
  caps.append({'id':cid,'page':pn,'type':'caption','original_text':cap,'translation':'','bbox':c,'confidence':'high','asset_id':fid})
  # Render a single source page at 240 dpi for a sharp, vector-faithful crop.
  png=ROOT/'source'/f'crop-source-{pn:02}.png'
  if not png.exists():subprocess.run(['pdftoppm','-f',str(pn),'-l',str(pn),'-r','240','-singlefile','-png',str(PDF),str(png.with_suffix(''))],check=True,stderr=subprocess.DEVNULL)
  im=Image.open(png);scale=im.width/612
  im.crop(tuple(round(v*scale) for v in r)).save(ROOT/image)

manifest={'paper':{'title':blocks[0]['original_text'].split('. Jinheng')[0],'source_type':'pdf','source_path':str(PDF),'language':'en','page_count':11,'source_sha256':hashlib.sha256(PDF.read_bytes()).hexdigest()},'blocks':blocks,'captions':caps,'figures':figures,'tables':tables,'equations':[],'glossary':[]}
(ROOT/'source_map.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
(ROOT/'source/source_blocks.txt').write_text('\n\n'.join(f"{b['id']} | p.{','.join(map(str,b['pages']))} | {b['type']}\n{b['original_text']}" for b in blocks))
print({'source_blocks':len(blocks),'captions':len(caps),'figures':len(figures),'tables':len(tables),'references':sum(b['type']=='reference' for b in blocks)})
