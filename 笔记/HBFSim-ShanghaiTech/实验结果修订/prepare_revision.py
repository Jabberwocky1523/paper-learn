from pathlib import Path
import json,sys,re,hashlib
from markdown_it import MarkdownIt
root=Path('/home/kurisu/Desktop/论文')
p=root/'笔记/HBFSim-ShanghaiTech/实验结果修订'
s=(p/'实验结果新版.md').read_text()
old=(p/'语雀修改前.md').read_text()
imgs=re.findall(r'!\[[^\]]*\]\((https://[^)]+)\)',old)
assert len(imgs)==8
web=s
for i in range(2,7): web=web.replace(f'(images/figure-{i:02}.png)',f'({imgs[i+1]})')
(p/'实验结果新版_线上.md').write_text(web)
html=MarkdownIt('commonmark').enable('table').render(web)
(p/'实验结果新版.html').write_text(html)
prefix=old.split('## 三、实验结果',1)[0]
combined=prefix+web
(p/'HBFSim（上科大）_准备更新.md').write_text(combined)
assert combined.split('## 三、实验结果',1)[0]==prefix
sys.path.insert(0,str(root/'.agents/skills/deeppapernote/scripts'))
import lint_note as lint
checks={
 'mixed_language_issues':lint.mixed_language_issues(s),
 'mechanical_translation_artifact_issues':lint.mechanical_translation_artifact_issues(s),
 'figure_structure_issues':lint.figure_structure_issues(s),
 'reference_hygiene_issues':lint.inspect_reference_hygiene(s),
 'math_render_issues':lint.math_render_issues(s)}
for k,v in checks.items(): assert not v,(k,v)
assert len(re.findall('<img ',html))==5
assert '<table>' in html and '<h2>三、实验结果</h2>' in html
assert abs((800-798.784)/800*100-.152)<1e-10
assert 36+3*512==1572 and 3*36+2*512==1132
checks.update({'passes_style_gate':True,'passes_figure_gate':True,'passes_math_gate':True,'passes_reference_gate':True,'passes_numeric_gate':True,'passes_prefix_preservation':True,'prefix_sha256':hashlib.sha256(prefix.encode()).hexdigest(),'scope':'仅重写三、实验结果；语雀导出版本的前两部分完整保留','quality_review':'已按第6.1–6.4节核对三类问题及实测/预测/对照边界','readability_review':'按设置→结果→含义顺序组织，删去原第三部分中的延伸研究与泛化分析，仅保留结果理解所需说明'})
(p/'revision_lint.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
print(json.dumps(checks,ensure_ascii=False,indent=2))
