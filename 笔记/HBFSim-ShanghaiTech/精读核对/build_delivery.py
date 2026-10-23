from pathlib import Path
import re,json,sys,shutil,zipfile,hashlib
root=Path('/home/kurisu/Desktop/论文')
p=root/'笔记/HBFSim-ShanghaiTech'
work=p/'精读核对'
s=(work/'精读核对.md').read_text()
front=s.split('\n# HBFSim\n',1)[0]
chunks=re.split(r'^## (.+)\n',s,flags=re.M)
sections={chunks[i]:chunks[i+1].strip() for i in range(1,len(chunks),2)}
def numbered(body,start=1):
 count=start-1
 def repl(m):
  nonlocal count
  count+=1
  title=re.sub(r'^\d+\.\s*','',m.group(1)).replace('机制流程','工作流程')
  return f'### {count}. {title}'
 return re.sub(r'^### (.+)$',repl,body,flags=re.M),count
background,_=numbered(sections['研究问题'])
method,n=numbered(sections['方法主线'],2)
design='### 1. 改进机会\n\n'+sections['创新点']+'\n\n'+method
setup,n=numbered(sections['数据与任务定义'])
results,n=numbered(sections['关键结果'],n+1)
analysis=re.sub(r'^### ', '#### ', sections['深度分析'],flags=re.M)
mynotes=re.sub(r'^### ', '#### ', sections['我的笔记'],flags=re.M)
refs=sections['引用'].replace('(/home/kurisu/Desktop/论文/文献/HBFSim_上科大.pdf)','(source/HBFSim_原文.pdf)')
refs='\n'.join(l for l in refs.splitlines() if not l.startswith('- 已有逐段译文'))
refs=refs.replace('Hu 等，2026，HBFSim: Fast and Faithful Simulation of High-Bandwidth Flash Under Real GPU Execution，arXiv:2609.09800v3。','Hu 等，2026，HBFSim，arXiv:2609.09800v3。')
text=front+'\n# HBFSim\n\n'
text+='**论文：** HBFSim：真实 GPU 执行下高带宽闪存的快速、忠实模拟\n\n'
text+='**版本：** 上科大参与的这篇，本地原文标注 arXiv:2609.09800v3，2026 年 9 月 30 日。\n\n'
text+=sections['一句话总结']+'\n\n'
text+='## 一、背景动机\n\n'+background+'\n\n---\n\n'
text+='## 二、设计方案\n\n'+design+'\n\n---\n\n'
text+='## 三、实验结果\n\n'+setup+'\n\n'+results
text+=f'\n\n### {n+1}. 这些结果怎样理解\n\n'+analysis
text+=f'\n\n### {n+2}. 局限\n\n'+sections['局限']
text+=f'\n\n### {n+3}. 阅读回顾与后续方向\n\n'+mynotes
text+=f'\n\n### {n+4}. 来源\n\n'+refs+'\n'
text=text.replace('为什么 C 没有可比较的词元柱','为什么 C 没有给出 KV 容量数值').replace('KV词元数','KV 容量数值').replace('每词元','每个词元')
# Materialize the exact reviewed originals next to the user-facing note.
sys.path.insert(0,str(root/'.agents/skills/deeppapernote/scripts'))
from write_obsidian_note import materialize_insert_decisions
p.joinpath('HBFSim.md').write_text(text)
decisions=json.loads((work/'hbfsim_figure_table_decisions.json').read_text())
materialize_insert_decisions(text,p/'HBFSim.md',decisions,'images')
(p/'source').mkdir(exist_ok=True)
shutil.copy2(root/'文献/HBFSim_上科大.pdf',p/'source/HBFSim_原文.pdf')
# Save style decisions without copying unrelated browser data or login state.
style={'source':'https://www.yuque.com/jabberwocky-zubgb/dwv0ny/yfgfqn94quli1up5','observed_headings':['一、背景动机','二、设计方案','三、实验结果'],'style':['编号小节','加粗短语引出原因或做法','短句分点解释','图片放在相应机制或实验后','用紧凑表格列核心结果'],'adaptation':'因用户未读懂而扩展原理、术语、步骤、公式和每个子图；明确补充推导及原文边界。'}
(work/'style_profile.json').write_text(json.dumps(style,ensure_ascii=False,indent=2))
print(p/'HBFSim.md')
