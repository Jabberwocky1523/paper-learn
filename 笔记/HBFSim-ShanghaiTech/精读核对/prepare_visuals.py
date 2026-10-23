import json,hashlib
from pathlib import Path
import pymupdf as fitz
root=Path('/home/kurisu/Desktop/论文')
p=root/'笔记/HBFSim-ShanghaiTech/精读核对'
m=json.loads((p.parent/'source_map.json').read_text())
d=json.loads((p/'hbfsim_figure_table_decisions.json').read_text())
old={a['source_id']:a for a in d['decisions']}
doc=fitz.open(root/'文献/HBFSim_上科大.pdf')
(p/'visuals').mkdir(exist_ok=True)
for u in m['units']:
 if u.get('kind') not in ['figure','table']: continue
 label=u['en'].split(':')[0]
 item=old[label]
 page=doc[u['page']-1]
 rect=list(u['rect'])
 rect[3]=u['sources'][0]['bbox'][1]-4
 if label=='Table 1': rect=[50,92,562,193]
 if label=='Table 2': rect=[315,69,562,224]
 image=p/'visuals'/Path(u['asset']).name
 page.get_pixmap(dpi=300,clip=fitz.Rect(rect)).save(image)
 preview=p/'visuals'/f"page-{u['page']:02}.png"
 if not preview.exists(): page.get_pixmap(dpi=96).save(preview)
 sha=hashlib.sha256(image.read_bytes()).hexdigest()
 item.update({'caption':u['en'].split(': ',1)[1],'source_image_path':str(image),'source_image_filename':image.name,'source_image_sha256':sha,'relative_markdown_embed':f'![{label}](images/{image.name})','review_evidence':{'candidate_path':str(image),'page_preview_path':str(preview),'source_pdf_path':str(root/'文献/HBFSim_上科大.pdf'),'source_page':u['page'],'caption':u['en'].split(': ',1)[1],'bbox_pt':rect,'normalized_bbox':[rect[0]/page.rect.width,rect[1]/page.rect.height,rect[2]/page.rect.width,rect[3]/page.rect.height],'render_dpi':300}})
 item['target_section']='方法主线' if label=='Figure 1' else '研究问题' if label.startswith('Table') else '关键结果'
 item['reason']='逐图核对原页后选定；在对应论证旁插入原图并逐面板解释。'
# The parser captured a prose reference to panel 2c; it is not a separate figure.
old['Figure 2c'].update({'decision':'skip','skip_reason':'正文对子图的引用，不是独立图表；已并入 Figure 2','reason':'原页9为正文引用，完整图2位于原页10。'})
(p/'hbfsim_figure_table_decisions.json').write_text(json.dumps(d,ensure_ascii=False,indent=2))
