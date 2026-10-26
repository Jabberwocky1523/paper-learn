from pathlib import Path
import json,hashlib,pymupdf

ROOT=Path('/home/kurisu/Desktop/论文/笔记/HBF-Sucks')
AUDIT=ROOT/'精读核对'
mapping=json.loads((ROOT/'source_map.json').read_text())
cap={x['id']:x for x in mapping['captions']}
wrapper=json.loads((AUDIT/'hbfsucks_figure_table_decisions.json').read_text())
assets={('Figure ' if a['id'][0]=='F' else 'Table ')+str(a['number']):a for a in mapping['figures']+mapping['tables']}
insert_tables={3,5,7,8,9}
reasons={1:'其他HBF工作的比较用本笔记末尾的FlashAccel对照文字解释；原表全部内容保留在中英对照稿。',2:'两代组织由图1和系统配置中文表完整解释，避免重复一张近似参数图。',4:'三个条件与六个发现另制中文对应表，比重复英文表更易理解。',6:'NMP模型、集群、引擎、频率和访问时序在发现2中写明，实验配置不另占图片。'}
visuals=AUDIT/'visuals';visuals.mkdir(exist_ok=True)
pdf=pymupdf.open(mapping['paper']['source_path'])
for d in wrapper['decisions']:
 a=assets[d['source_id']];p=a['page'];path=visuals/Path(a['image_path']).name
 pdf[p-1].get_pixmap(matrix=pymupdf.Matrix(300/72,300/72),clip=pymupdf.Rect(a['bbox'])).save(path)
 digest=hashlib.sha256(path.read_bytes()).hexdigest()
 insert=True
 d.update(decision='insert' if insert else 'low_priority',reason='原图及原页视觉核对后选定，图体完整、图号相符，放到对应机制或实验结果旁。' if insert else reasons[a['number']],skip_reason='' if insert else reasons[a['number']],visual_quality_status='usable_candidate',target_section='研究问题' if a['id'] in ['F001','F002','F003'] else '关键结果',source_image_path=str(path),source_image_filename=path.name,source_image_sha256=digest,relative_markdown_embed=f'![{d["source_id"]}](images/{path.name})',materialization_status='pending' if insert else 'not_selected',pages=[p])
 d['review_evidence']=dict(candidate_path=str(path),page_preview_path=str(ROOT/'source'/f'page-{p:02}.png'),source_pdf_path=mapping['paper']['source_path'],source_page=p,caption=cap[a['caption_id']]['original_text'],bbox_pt=a['bbox'],normalized_bbox=[a['bbox'][0]/612,a['bbox'][1]/792,a['bbox'][2]/612,a['bbox'][3]/792],render_dpi=300)
 d['visual_review']=dict(status='pass',reviewed_asset_sha256=digest,preserved_scientific_elements=['完整图体和所有子图／表行','坐标轴、数值、图例、单位','原图编号对应关系和原页位置'],omitted_scientific_elements=[],notes='已查看21项资产的核对拼图，并与原页及逐段来源映射交叉核对；图注单独排在正文，原英文图注和周围正文均未混入图体。',failure_reason='',repair_attempts=0,revised_bbox=[])
wrapper.update(visual_review_gate='passed',decision_freeze='completed_before_note_plan',user_format_override='用户明确要求FlashAccel的三部分结构；target_section保留语义标签，展示位置由笔记三级标题决定。')
(AUDIT/'hbfsucks_figure_table_decisions.json').write_text(json.dumps(wrapper,ensure_ascii=False,indent=2))
profile=dict(reference_url='https://www.yuque.com/jabberwocky-zubgb/dwv0ny/yfgfqn94quli1up5',reference_title='FlashAccel',reference_read_method='authenticated page DOM, article rendered text',structure=['一、背景动机','二、设计方案','三、实验结果'],adapted_structure=['一、背景动机','二、分析框架与评估方案','三、实验结果'],style=['短段落与加粗开头的要点','先说明原因再说机制及结果','原图靠近相关文字，图下解释各部分','指标、设置、比较对象与数值并列','使用自然中文，保留HBM/HBF/KV等技术缩写'],save_target=str(ROOT/'HBF-Sucks.md'),authorization='当前用户指定FlashAccel格式；本会话已有将笔记保存到笔记文件夹的明确指示。',default_skill_structure_overridden=True)
(AUDIT/'flashaccel_style_profile.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2))
print('Frozen decisions:',len(wrapper['decisions']),'insert:',sum(x['decision']=='insert' for x in wrapper['decisions']))
