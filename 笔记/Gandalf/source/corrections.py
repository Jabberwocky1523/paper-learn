import json,re,unicodedata
from pathlib import Path
R=Path(__file__).resolve().parent
bs=json.loads((R/'blocks.json').read_text()); d={b['id']:b for b in bs}
remove={f'S{i:03}' for i in range(5,10)}|{'S034','S037','S087','S208','S230'}
def settext(s,t):d[s]['original_text']=t
settext('S033',r'SSD stores data by programming charge in NAND-flash cells, which tolerate only a finite number of program/erase (write) cycles. Manufacturers quantify this endurance as Terabytes Written (TBW), or equivalently Drive Writes Per Day (DWPD) over a warranty period. For a drive with capacity $C$, rated for $D$ DWPD over $Y$ years, its host-write endurance budget is $E_{\mathrm{TBW}}=C\times D\times365\times Y$. Garbage collection can amplify host writes by copying live data while reclaiming space. The write-amplification factor (WAF) measures this additional write traffic: $\mathrm{WAF}=W_{\mathrm{NAND}}/W_{\mathrm{host}}$, where $W_{\mathrm{host}}$ and $W_{\mathrm{NAND}}$ denote the logical host writes and physical NAND writes, respectively. Thus, SSD will live until')
settext('S036',r'HDDs store data by magnetizing regions of rotating platters. Manufacturers specify an annual total read and write limit of $RW_{\mathrm{limit}}$ TB/year. Over $Y$ years, this rate corresponds to a nominal cumulative transfer envelope of $E_{\mathrm{HDD}}=RW_{\mathrm{limit}}\times Y$. Manufacturers also specify HDD reliability by Annualized Failure Rate (AFR) and Mean Time Between Failures (MTBF). Exceeding $E_{\mathrm{HDD}}$ results in increasing AFR and decreasing MTBF, hence more frequent failures and recovery overhead will occur, slowing the HDD for both reads and writes. For a KV-cache workload that writes $W_{\mathrm{host}}$ bytes and reads each written byte an average of $h$ times, the total HDD workload is $E_{\mathrm{workload}}=(1+h)W_{\mathrm{host}}$. HDD operates reliably until')
settext('S082',r'where $H$ and $H_{\mathrm{left}}$ are summed over all promotions and $W$ is the total bytes written to SSD. $\lambda$ tells us how many hits a written byte must earn to be worth writing.')
settext('S086',r'Eviction when the SSD is full. If the admission causes an eviction, there is additional replacement cost of losing the future hits of the evicted objects. The oracle picks the residents with the fewest future hits as eviction candidates. It writes the new object only if its benefit, $H_iC_r-C_ws_i$, is larger than the recompute cost of the hits lost by evicting the victim candidates, i.e., $H_i-\lambda s_i>H_{\mathrm{left}}$, where $H_{\mathrm{left}}$ sums the remaining hits of the evicted candidates. Otherwise it keeps the SSD as it is and drops the new object.')
for a,b in [('S207','S208'),('S229','S230')]:
 d[a]['original_text']+=('' if a=='S229' else '')+d[b]['original_text'];d[a]['pages']=sorted(set(d[a]['pages']+d[b]['pages']));d[a].setdefault('continuation_regions',[]).append({'page':d[b]['page'],'bbox':d[b]['bbox']})
for b in bs:
 if b.get('original_text'):
  s=b['original_text']
  for x,y in {'KVcache':'KV-cache','lowestmiss':'lowest-miss','longestlived':'longest-lived','nonuniform':'non-uniform','Gandalf ,':'Gandalf,','Gandalf ’s':"Gandalf’s",'Hot-Prefix':'HotPrefix',')syad( emitefil DSS ':''}.items():s=s.replace(x,y)
  s=''.join(unicodedata.normalize('NFKC',c) if 0x1D400<=ord(c)<=0x1D7FF else c for c in s)
  if re.match(r'^\[\d+\]',s):
   for x,y in {'buildwith-claude':'build-with-claude','github.com/aidynamo':'github.com/ai-dynamo','introducing-nvidiabluefield':'introducing-nvidia-bluefield','/knowledgebase/':'/knowledge-base/','arXiv.2608. 11668':'arXiv.2608.11668','H 2O:':'H₂O:'}.items():s=s.replace(x,y)
   s=re.sub(r'(?<=[/\.]) (?=\S)','',s)
  b['original_text']=s
# Recover inline subscripts using the visible PDF.
for sid,repl in {
 'S079':{'C r':'$C_r$','C w':'$C_w$','H hits':'$H_{\\mathrm{left}}$ hits','becomes left the':'becomes the','H left':'$H_{\\mathrm{left}}$'},
 'S100':{'C w':'$C_w$','s j':'$s_j$','P SSD /E TBW':'$P_{\\mathrm{SSD}}/E_{\\mathrm{TBW}}$','T years, target':'$T_{\\mathrm{target}}$ years,','t L':'$t_L$'},
}.items():
 for a,b in repl.items():d[sid]['original_text']=d[sid]['original_text'].replace(a,b)
bs=[b for b in bs if b['id'] not in remove]
(R/'corrected_blocks.json').write_text(json.dumps(bs,ensure_ascii=False,indent=2))
