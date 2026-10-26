from pathlib import Path
import json
A=Path('/home/kurisu/Desktop/论文/笔记/HBFSim-MBZUAI/精读核对')
p=A/'mbzuai_figure_table_decisions.json';w=json.loads(p.read_text())
for d in w['decisions']:
 d.update(decision='insert',reason='以原PDF来源映射重新渲染300dpi图体并查看三张核对拼图；图号、子图、坐标、图例和表行完整。',skip_reason='',visual_quality_status='usable_candidate',target_section='研究问题' if d['source_id']=='Figure 1' else '方法主线' if d['source_id']=='Figure 2' else '关键结果')
 d['visual_review']=dict(status='pass',reviewed_asset_sha256=d['source_image_sha256'],preserved_scientific_elements=['全部子图、坐标轴、图例、数值及单位','图表完整边界与原始编号对应','表格完整表头及数据行'],omitted_scientific_elements=[],notes='已查看review-1/2/3拼图；图4/5/6另与第6/7页原页对照。图注移到笔记紧邻图体的下一行，裁图不混入正文。',failure_reason='',repair_attempts=0,revised_bbox=[])
w.update(visual_review_gate='passed',decision_freeze='completed_before_note_plan',user_format_override='FlashAccel三部分结构；语义标签保留用于证据校验。')
p.write_text(json.dumps(w,ensure_ascii=False,indent=2))
style=dict(reference_url='https://www.yuque.com/jabberwocky-zubgb/dwv0ny/yfgfqn94quli1up5',reference_title='FlashAccel',reference_read_method='会话中已通过认证语雀页面读取正文',structure=['一、背景动机','二、设计方案','三、实验结果'],style=['短段落和加粗开头要点','先问题、再机制、后数字与原因','图片紧邻解释，中文图注放下一行','采用紧凑中文表格比较多种设置','沿用HBM/HBF/KV/FTL等稳定缩写'],save_target=str(A.parent/'HBFSim_MBZUAI.md'),authorization='用户要求同时整理该篇笔记；此前明确要求保存到笔记文件夹。',default_skill_structure_overridden=True)
(A/'flashaccel_style_profile.json').write_text(json.dumps(style,ensure_ascii=False,indent=2))
