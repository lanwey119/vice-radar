import json, urllib.request, urllib.parse, xml.etree.ElementTree as ET, re, hashlib
from pathlib import Path
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
ROOT=Path(__file__).parent
queries={'PC':'GTA VI PC Rockstar Steam release','Comunidad':'GTA VI mods emulation technical research','Noticias':'GTA VI Rockstar Games update','Online':'GTA VI online Rockstar'}
p=ROOT/'news.json'; old=json.loads(p.read_text()) if p.exists() else []
items={x['url']:x for x in old}; errors=[]
for cat,q in queries.items():
 try:
  url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':q+' when:7d','hl':'es','gl':'ES','ceid':'ES:es'})
  req=urllib.request.Request(url,headers={'User-Agent':'ViceRadar/1.0'})
  with urllib.request.urlopen(req,timeout=25) as r: root=ET.fromstring(r.read())
  for e in root.findall('./channel/item')[:12]:
   title=e.findtext('title',''); link=e.findtext('link',''); source=e.findtext('source','Medio externo'); date=parsedate_to_datetime(e.findtext('pubDate')).astimezone(timezone.utc).isoformat()
   if not link.startswith('https://') or not re.search(r'GTA\s*(VI|6)|Grand Theft Auto\s*(VI|6)',title,re.I): continue
   if link in items: continue
   items[link]={'date':date,'cat':cat,'art':{'PC':'PC','Comunidad':'DEV','Online':'ON'}.get(cat,'VI'),'title':title,'desc':'Referencia externa de '+source+'. Pendiente de verificación editorial; consulta el artículo original.','url':link,'status':'Pendiente de verificar','source':source}
 except Exception as e: errors.append(str(e))
if len(errors)==len(queries): raise SystemExit('Todas las fuentes fallaron: '+str(errors))
# Imagen de cada noticia
for noticia in items.values():
    if noticia.get('image'):
        continue

    categoria = noticia.get('cat', 'Noticias')
    imagenes = {
        'PC': 'assets/pc.jpg',
        'Comunidad': 'assets/comunidad.jpg',
        'Online': 'assets/online.jpg',
        'Noticias': 'assets/gta6.jpg',
        'Música': 'assets/musica.jpg',
        'Mundo': 'assets/leonida.jpg',
        'Tráilers': 'assets/trailer.jpg'
    }

    noticia['image'] = imagenes.get(
        categoria, 'assets/gta6.jpg'
    )
    noticia['imageAlt'] = (
        'Imagen ilustrativa de GTA VI - ' + categoria
    )

p.write_text(json.dumps(sorted(items.values(),key=lambda x:x['date'],reverse=True)[:200],ensure_ascii=False,indent=2)+'\n')
print('Referencias:',len(items),'Errores:',errors)
