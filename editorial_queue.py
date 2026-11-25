"""Prepare an editorial review queue locally; never publish claims from headlines."""
import json, re
from pathlib import Path
ROOT=Path(__file__).parent
items=json.loads((ROOT/'news.json').read_text(encoding='utf-8'))
def priority(x):
    t=str(x.get('title','')).lower()
    return 0 if re.search(r'\bpc\b|steam|epic|rendimiento|requisitos|emul|recompil',t) else 1
queue=[]
for x in sorted(items,key=priority)[:30]:
    queue.append({'title':x.get('title'),'source':x.get('source'),'source_url':x.get('url'),'date':x.get('date'),'status':'requiere revisión','instructions':['Abrir fuente original y contrastar fecha y afirmaciones.','Buscar fuente primaria de Rockstar o Take-Two cuando corresponda.','Separar hechos confirmados, rumores y análisis.','Redactar texto original solo tras leer las fuentes; añadir enlaces y fecha de revisión.','Comprobar derechos de la imagen y no presentar ilustraciones como capturas.'],'publish':False})
(ROOT/'editorial_queue.json').write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Editorial review queue:',len(queue))
