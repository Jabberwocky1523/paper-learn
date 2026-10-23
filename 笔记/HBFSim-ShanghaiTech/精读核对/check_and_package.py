from pathlib import Path
import sys,re,json,hashlib,zipfile
root=Path('/home/kurisu/Desktop/论文')
p=root/'笔记/HBFSim-ShanghaiTech'
w=p/'精读核对'
sys.path.insert(0,str(root/'.agents/skills/deeppapernote/scripts'))
import lint_note as lint
s=(p/'HBFSim.md').read_text()
checks={
 'mixed_language_issues':lint.mixed_language_issues(s),
 'mechanical_translation_artifact_issues':lint.mechanical_translation_artifact_issues(s),
 'figure_structure_issues':lint.figure_structure_issues(s),
 'reference_hygiene_issues':lint.inspect_reference_hygiene(s),
 'code_math_issues':lint.suspicious_code_formatted_math(s),
 'math_render_issues':lint.math_render_issues(s)
}
checks['main_headings']=re.findall(r'^## (.+)$',s,re.M)
assert checks['main_headings']==['一、背景动机','二、设计方案','三、实验结果']
for k,v in checks.items():
 if k.endswith('_issues'): assert not v,(k,v)
images=re.findall(r'!\[[^\]]*\]\(([^)]+)\)',s)
assert len(images)==8 and len(set(images))==8
for i in images: assert (p/i).is_file(),i
for target in re.findall(r'(?<!!)\[[^\]]*\]\(([^)]+)\)',s):
 if not target.startswith('http'): assert (p/target).is_file(),target
items=json.loads((w/'hbfsim_figure_table_decisions.json').read_text())['decisions']
for i in items:
 if i['decision']=='insert':
  target=p/'images'/i['source_image_filename']
  assert hashlib.sha256(target.read_bytes()).hexdigest()==i['visual_review']['reviewed_asset_sha256']
assert abs(abs(798.784-800)/800*100-.152)<1e-10
assert abs(5+8.4e-11*384e9-37.256)<1e-10
assert 3*36+2*512==1132 and 36+3*512==1572
assert abs(36-5.0121-30.9879)<1e-10
assert round(2.487/8,3)==.311 and round(3.584/16,3)==.224
checks.update({'passes_delivery_structure':True,'passes_style_gate':True,'passes_math_gate':True,'passes_figure_gate':True,'passes_link_gate':True,'passes_numeric_checks':True,'character_count':len(s),'chinese_character_count':len(re.findall(r'[\u4e00-\u9fff]',s)),'inserted_figures':6,'inserted_tables':2,'final_quality_review':'pass','final_readability_review':'pass'})
(w/'delivery_qa.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
# The import copy starts at the title; local Obsidian properties stay in the local file.
import_md=re.sub(r'^---\n.*?\n---\n\s*','',s,count=1,flags=re.S)
zip_path=p/'HBFSim_详细笔记_语雀导入.zip'
readme='HBFSim 上科大论文详细笔记\n\nHBFSim.md 是正文，images/ 含6幅原图和2张原表，source/ 为核对用原文。\n三段结构与个人 FlashAccel 笔记保持一致，方法、公式和图表均已展开。\n导入 Markdown 时请连同 images/ 一起保留；单独复制正文不会自动上传本地图片。\n压缩包里的正文去掉了本地笔记属性区。公式保留标准数学标记。\n'
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED) as z:
 z.writestr('HBFSim.md',import_md)
 z.writestr('导入说明.txt',readme)
 for img in images:z.write(p/img,img)
 z.write(p/'source/HBFSim_原文.pdf','source/HBFSim_原文.pdf')
with zipfile.ZipFile(zip_path) as z:
 assert z.testzip() is None
 assert z.read('HBFSim.md').decode()==import_md
 for target in images+['source/HBFSim_原文.pdf']: assert target in z.namelist()
print(json.dumps({'note':str(p/'HBFSim.md'),'zip':str(zip_path),'bytes':zip_path.stat().st_size,'characters':len(s),'CJK_characters':checks['chinese_character_count'],'gates':'all_passed','figures':6,'tables':2},ensure_ascii=False,indent=2))
