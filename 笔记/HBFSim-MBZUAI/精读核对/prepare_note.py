from pathlib import Path
import json,hashlib,pymupdf
ROOT=Path('/home/kurisu/Desktop/论文/笔记/HBFSim-MBZUAI'); A=ROOT/'精读核对'
m=json.loads((ROOT/'source_map.json').read_text()); w=json.loads((A/'mbzuai_figure_table_decisions.json').read_text())
cap={x['id']:x for x in m['captions']}; assets={('Figure ' if x['id'].startswith('F') else 'Table ')+str(x['number']):x for x in m['figures']+m['tables']}
v=A/'visuals'; v.mkdir(exist_ok=True); doc=pymupdf.open(ROOT/'source/HBFSim_MBZUAI.pdf')
for d in w['decisions']:
 a=assets[d['source_id']]; p=a['page']; path=v/Path(a['image_path']).name
 doc[p-1].get_pixmap(matrix=pymupdf.Matrix(300/72,300/72),clip=pymupdf.Rect(a['bbox'])).save(path)
 preview=v/f'page-{p:02}.png'
 if not preview.exists():doc[p-1].get_pixmap(matrix=pymupdf.Matrix(96/72,96/72)).save(preview)
 sha=hashlib.sha256(path.read_bytes()).hexdigest(); box=a['bbox']; rect=doc[p-1].rect
 d.update(decision='review_pending',source_image_path=str(path),source_image_filename=path.name,source_image_sha256=sha,relative_markdown_embed=f'![{d["source_id"]}](images/{path.name})',materialization_status='pending',pages=[p])
 d['review_evidence']=dict(candidate_path=str(path),page_preview_path=str(preview),source_pdf_path=str(ROOT/'source/HBFSim_MBZUAI.pdf'),source_page=p,caption=cap[a['caption_id']]['original_text'],bbox_pt=box,normalized_bbox=[box[0]/rect.width,box[1]/rect.height,box[2]/rect.width,box[3]/rect.height],render_dpi=300)
(A/'mbzuai_figure_table_decisions.json').write_text(json.dumps(w,ensure_ascii=False,indent=2))
print([(d['source_id'],Path(d['source_image_path']).name,d['pages']) for d in w['decisions']])
