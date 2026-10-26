"""Run the skill's checks with the user's explicitly requested heading profile.

Only section names/locations differ from the default 12-section template.
Language, math, references, figure captions, plan and substance checks remain active.
"""
from pathlib import Path
import sys,re,json

HERE=Path(__file__).resolve().parent
SCRIPTS=Path('/home/kurisu/Desktop/论文/.agents/skills/deeppapernote/scripts')
sys.path.insert(0,str(SCRIPTS))
import lint_note

lint_note.REQUIRED_SECTIONS=['一、背景动机','二、分析框架与评估方案','三、实验结果']
original_body=lint_note.section_body
aliases={
 '研究问题':('h2','一、背景动机'),
 '数据与任务定义':('h3','4. 平台、模型与负载'),
 '创新点':('h2','二、分析框架与评估方案'),
 '方法主线':('h2','二、分析框架与评估方案'),
 '关键结果':('h2','三、实验结果'),
 '深度分析':('h3','7. 这篇和 FlashAccel 放在一起怎么看'),
 '局限':('h3','8. 阅读时需要保留的条件'),
 '引用':('footer','**原文与对照：**'),
}
def profile_body(text,heading):
 if heading not in aliases:return original_body(text,heading)
 level,name=aliases[heading]
 if level=='h2':return original_body(text,name)
 if level=='footer':return text[text.find(name):] if name in text else ''
 match=re.search(r'^###\s+'+re.escape(name)+r'\s*$',text,re.M)
 if not match:return ''
 rest=text[match.end():];end=re.search(r'^#{2,3}\s+',rest,re.M)
 return rest[:end.start()] if end else rest
lint_note.section_body=profile_body

# Identify the existing four-step procedure by its user-template subsection name.
old_mechanism=lint_note.mechanism_flow_warnings
def profile_mechanism(text):
 if '### 机制流程' in text:return old_mechanism(text)
 body=profile_body(text,'方法主线');first=body.split('### 2.',1)[0]
 steps=re.findall(r'^\d+\.\s+.+$',first,re.M)
 return [] if 3<=len(steps)<=4 else ['mechanism_flow_step_count_unexpected']
lint_note.mechanism_flow_warnings=profile_mechanism

if __name__=='__main__':
 lint_note.main()
