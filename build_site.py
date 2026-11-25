"""Generate static, crawlable reference pages without inventing articles."""
import json, hashlib, html, re, shutil
from pathlib import Path
from urllib.parse import urlsplit
from xml.sax.saxutils import escape as xml_escape
ROOT=Path(__file__).parent
OUT=ROOT/'public'
BASE='https://vice-radar.maciasgilanto.workers.dev'
OUT.mkdir(exist_ok=True)
for f in ('index.html','robots.txt'):
    shutil.copy2(ROOT/f,OUT/f)
shutil.copytree(ROOT/'assets',OUT/'assets',dirs_exist_ok=True,ignore=shutil.ignore_patterns('*.md'))
items=json.loads((ROOT/'news.json').read_text(encoding='utf-8'))
def e(v): return html.escape(str(v),quote=True)
def safe_url(v):
    return isinstance(v,str) and urlsplit(v).scheme=='https' and bool(urlsplit(v).netloc)
def page(path,title,description,body,noindex=False):
    target=OUT/path.strip('/')/'index.html'
    target.parent.mkdir(parents=True,exist_ok=True)
    canonical=BASE+path
    target.write_text(f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)} | VICE RADAR</title><meta name="description" content="{e(description[:155])}"><link rel="canonical" href="{e(canonical)}"><meta name="robots" content="{'noindex,follow' if noindex else 'index,follow'}"><style>body{{margin:0;background:#100e19;color:#f9f2fa;font:17px system-ui;line-height:1.65}}main,nav{{max-width:820px;margin:auto;padding:24px}}nav{{display:flex;gap:18px;flex-wrap:wrap}}a{{color:#ff9fc0}}h1{{line-height:1.15;font-size:clamp(32px,6vw,52px)}}img{{width:100%;border-radius:12px}}small{{color:#e5b8d1}}article{{border-bottom:1px solid #49364e;padding:18px 0}}footer{{padding:24px;text-align:center;color:#c6b6ca}}</style></head><body><nav><a href="/">VICE RADAR</a><a href="/pc/">Radar PC</a><a href="/editorial/">Política editorial</a></nav><main>{body}</main><footer>Medio independiente, no afiliado a Rockstar Games. <a href="/privacidad/">Privacidad</a></footer></body></html>''',encoding='utf-8')
def theme(x):
    t=str(x.get('title','')).lower()
    if re.search(r'emul|recompil|modding|github|project|proyecto',t): return 'comunidad'
    if re.search(r'steam|epic|\bpc\b|fps|requisitos|rendimiento',t): return 'pc'
    return {'PC':'pc','Comunidad':'comunidad','Online':'online','Música':'musica','Mundo':'leonida','Tráilers':'trailer'}.get(x.get('cat'),'gta6')
pc=[]
for x in items:
    url=x.get('url','')
    if not safe_url(url): continue
    title=str(x.get('title','Referencia externa'))
    ident=hashlib.sha256(url.encode()).hexdigest()[:16]
    path='/noticias/'+ident+'/'
    x['page']=path
    image='/assets/'+theme(x)+'.svg'
    body=f'<small>{e(x.get("cat","Noticias"))} · {e(str(x.get("date",""))[:10])} · {e(x.get("status","Pendiente de verificar"))}</small><h1>{e(title)}</h1><img src="{image}" alt="Ilustración editorial temática, no captura del juego"><p>{e(x.get("desc","Referencia externa."))}</p><p>Esta ficha identifica una referencia externa; no equivale a un artículo original verificado por VICE RADAR.</p><p><a rel="noopener" href="{e(url)}">Consultar la fuente original ↗</a></p><p><a href="/pc/">Más información en el radar PC</a></p>'
    page(path,title,'Referencia externa sobre GTA VI. Consulta la fuente y su estado de verificación.',body,True)
    if theme(x) in ('pc','comunidad'):
        pc.append(f'<article><small>{e(str(x.get("date",""))[:10])} · {e(x.get("status","Pendiente de verificar"))}</small><h2><a href="{path}">{e(title)}</a></h2><p><a href="{e(url)}">Fuente externa ↗</a></p></article>')
page('/pc/','GTA VI para PC: noticias y seguimiento','Radar de GTA VI para PC, Steam, Epic Games, requisitos y rendimiento.','<h1>GTA VI para PC</h1><p>Seguimiento independiente de anuncios oficiales, requisitos, Steam, Epic Games, rendimiento e investigación técnica pública. No atribuimos fechas ni requisitos a Rockstar sin confirmación. Los experimentos no oficiales no son una versión comercial.</p><p><a href="https://www.rockstargames.com/VI/">Información oficial de Rockstar</a> · <a href="https://support.rockstargames.com/">Soporte oficial</a></p><h2>Últimas referencias</h2>'+''.join(pc[:25]))
page('/editorial/','Política editorial','Criterios de fuentes, verificación y transparencia de VICE RADAR.','<h1>Política editorial</h1><p>VICE RADAR es un medio independiente dedicado a GTA VI. Diferenciamos información confirmada, rumores, análisis y referencias externas pendientes de verificar. Priorizamos fuentes originales y fechas comprobables. Las ilustraciones temáticas no representan capturas reales del juego. No ofrecemos descargas ilícitas ni instrucciones para acceder sin autorización.</p><p>Los titulares recopilados automáticamente se identifican como referencias externas; consulta siempre la fuente original.</p>')
page('/privacidad/','Información de privacidad','Información provisional sobre analítica y preferencias locales.','<h1>Información de privacidad</h1><p>VICE RADAR utiliza Cloudflare para alojamiento y tiene configurada su analítica web. La preferencia de alertas se guarda localmente en el navegador; no constituye una suscripción a notificaciones de servidor. No hay publicidad activa.</p><p>Esta información es provisional: antes de activar publicidad, suscripciones o formularios se completará el aviso con la identidad y contacto del responsable, tratamientos, bases jurídicas y derechos aplicables.</p><p><a href="https://www.cloudflare.com/privacypolicy/">Política de privacidad de Cloudflare</a></p>',True)
(OUT/'news.json').write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
paths=['/','/pc/','/editorial/']
(OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+xml_escape(BASE+p)+'</loc></url>' for p in paths)+'</urlset>\n',encoding='utf-8')
print('Static reference pages:',len(items))
