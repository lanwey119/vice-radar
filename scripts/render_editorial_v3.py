import json, math, subprocess as sp, urllib.request, zipfile
from pathlib import Path
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageOps
from kokoro import KPipeline
from faster_whisper import WhisperModel

W=Path("work").resolve(); O=Path("output").resolve()
W.mkdir(exist_ok=True); O.mkdir(exist_ok=True)
def ff(*args):
    sp.run(["ffmpeg","-hide_banner","-loglevel","error","-y",*map(str,args)],check=True)
def probe(path):
    return float(sp.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=nw=1:nk=1",str(path)]))
def download(url,path,maxbytes):
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
    with urllib.request.urlopen(req,timeout=60) as r, open(path,"wb") as f:
        total=0
        while b:=r.read(1024*1024):
            total+=len(b)
            if total>maxbytes: raise ValueError("Asset too large")
            f.write(b)

# Review copies only. Promotional downloads are not proof of commercial reuse permission.
clips=[]; photos=[]
try:
    download("https://media-rockstargames-com.akamaized.net/VI/downloads/videos/GTAVI_Videos.zip",W/"videos.zip",800000000)
    with zipfile.ZipFile(W/"videos.zip") as z:
        for item in z.infolist():
            if Path(item.filename).suffix.lower() not in (".mp4",".mov") or item.file_size>200000000: continue
            dest=W/("clip"+str(len(clips))+Path(item.filename).suffix)
            dest.write_bytes(z.read(item))
            if probe(dest)>2: clips.append(dest)
except Exception as e: print("Clip download failed:",e)
for i,uri in enumerate([
"https://www.rockstargames.com/VI/_next/static/media/Jason_and_Lucia_14.10e7v.06pcm_t.jpg?akim=1&imdensity=1&imwidth=3840",
"https://www.rockstargames.com/VI/_next/static/media/Vice_City_13.0iq8ff474tsdx.jpg?akim=1&imdensity=1&imwidth=3840",
"https://www.rockstargames.com/VI/_next/static/media/Vice_City_14.0fu8u9jh5hkg7.jpg?akim=1&imdensity=1&imwidth=3840"]):
    try:
        dest=W/f"photo{i}.jpg";download(uri,dest,20000000)
        with Image.open(dest) as im: im.verify()
        photos.append(dest)
    except Exception as e: print("Photo failed:",e)
clips=[c for c in clips if probe(c)>=18]
if not clips or not photos: raise RuntimeError("Required real promotional visuals unavailable; do not substitute static cards")
episodes=[
{"id":"002","hook":"¿GTA 6 YA FUNCIONA EN PC?","source":"Computer Hoy | 25 NOV 2026","url":"https://computerhoy.20minutos.es/gaming/adios-gta-6-pc-take-two-cierra-leonida-proyecto-mas-avanzado-para-llevar-grand-theft-auto-vi-ordenador_7065463_0.html","headline":"Take-Two cierra el proyecto Leonida","script":"¿GTA seis ya funciona en ordenador? Hay un detalle que cambia todo. Según Computer Hoy, el proyecto Leonida consiguió avances experimentales para arrancar el juego en Windows. Pero arrancar no es lo mismo que jugar. Take Two ha cerrado el proyecto y no existe una adaptación no oficial completamente jugable que se haya verificado. Así que cuidado con las descargas milagrosas. ¿Tú esperarías al lanzamiento oficial para ordenador?"},
{"id":"003","hook":"¿GTA 6 EN PC A PRINCIPIOS DE 2027?","source":"MeriStation | GamesBeat","url":"https://as.com/meristation/noticias/cuando-sale-gta-6-para-pc-todo-lo-que-se-sabe-de-su-lanzamiento-en-ordenadores-f202611-n/","headline":"Cuatro fuentes apuntan a principios de 2027","script":"¿Y si GTA seis llega a ordenador entre enero y marzo? MeriStation recoge una investigación de GamesBeat que cita cuatro fuentes de la industria. Apuntan al primer trimestre de dos mil veintisiete. Pero Rockstar todavía no ha confirmado ninguna fecha para ordenador. Y los avances no oficiales no demuestran que la compañía haya cambiado sus planes. Es un rumor interesante, no una fecha de lanzamiento. ¿Lo comprarías en Steam o en el lanzador de Rockstar?"}]
bold="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
def font(size): return ImageFont.truetype(bold,size)
def wrap(s,f,d,width):
    lines=[];line=""
    for w in s.split():
        trial=(line+" "+w).strip()
        if line and d.textlength(trial,font=f)>width: lines.append(line);line=w
        else:line=trial
    return "\n".join(lines+[line])
def timecode(t): return f"{int(t//3600)}:{int(t//60)%60:02}:{int(t)%60:02}.{int(t%1*100):02}"
p=KPipeline(lang_code="e",repo_id="hexgrad/Kokoro-82M")
whisper=WhisperModel("base",device="cpu",compute_type="int8")
report=[]
for ep in episodes:
    folder=W/ep["id"];folder.mkdir(exist_ok=True)
    audio=np.concatenate([a for _,_,a in p(ep["script"],voice="em_alex",speed=0.98) if a is not None])
    raw=folder/"voice.wav";sf.write(raw,audio,24000)
    dur=len(audio)/24000
    segments,_=whisper.transcribe(str(raw),language="es",word_timestamps=True,initial_prompt=ep["script"],condition_on_previous_text=False)
    words=[w for s in segments for w in (s.words or []) if w.end>w.start]
    if len(words)<20: raise RuntimeError("Subtitle alignment failed")
    ass=folder/"subs.ass"
    header="[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,DejaVu Sans,62,&H00FFFFFF,&H0000FFFF,&H00100A18,&H78000000,-1,0,0,0,100,100,0,0,1,5,2,2,100,100,300,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    lines=[]
    for k in range(0,len(words),4):
        g=words[k:k+4]
        txt="".join(w.word for w in g).strip().replace("{","").replace("}","")
        txt=txt.replace("2017","2027").replace("GAMES-BEAT","GamesBeat").replace("Games-Beat","GamesBeat")
        lines.append(f"Dialogue: 0,{timecode(g[0].start)},{timecode(g[-1].end)},Default,,0,0,0,,{txt}")
    ass.write_text(header+"\n".join(lines),encoding="utf-8")
    shots=[];counts={"clip":0,"photo":0,"news":0}
    n=math.ceil(dur/2.0)
    for i in range(n):
        seconds=min(2,dur-i*2)
        if i in (2,3): kind="news";asset=photos[i%len(photos)]
        elif i%3==1: kind="photo";asset=photos[i%len(photos)]
        else: kind="clip";asset=clips[(i+(1 if ep["id"]=="003" else 0))%len(clips)]
        counts[kind]+=1
        ov=Image.new("RGBA",(1080,1920),(0,0,0,0));d=ImageDraw.Draw(ov)
        d.rectangle((0,0,1080,305),fill=(12,9,26,224))
        d.text((58,68),"VICE RADAR NEWS",font=font(38),fill="#ff77be")
        d.multiline_text((58,145),wrap(ep["hook"] if i<2 else ("ARRANCAR ≠ JUGAR" if ep["id"]=="002" else "RUMOR · SIN FECHA OFICIAL"),font(49),d,960),font=font(49),fill="white")
        if kind=="news":
            d.rounded_rectangle((55,570,1025,1070),radius=24,fill=(19,15,35,245))
            d.text((95,635),ep["source"],font=font(32),fill="#ff77be")
            d.multiline_text((95,740),wrap(ep["headline"],font(61),d,880),font=font(61),fill="white",spacing=12)
            d.text((95,1000),"RESUMEN EDITORIAL · NO CAPTURA",font=font(24),fill="#c4b5d8")
        d.rectangle((0,1765,1080,1920),fill=(12,9,26,240))
        d.text((55,1790),"Rockstar Games · material promocional",font=font(24),fill="white")
        d.text((55,1840),"PREVIA EDITORIAL · NO PUBLICAR",font=font(24),fill="#ff77be")
        overlay=folder/f"overlay{i}.png";ov.save(overlay)
        out=folder/f"shot{i}.mp4"
        if kind=="clip":
            length=probe(asset)
            # Avoid rating cards and end logos: sample different interior positions.
            low=max(6.0,length*.22); high=min(length-6.0-seconds,length*.72)
            if high<low: low=max(3.0,length*.30);high=max(low,length*.60-seconds)
            ratio=((i*0.381966+(0.23 if ep["id"]=="003" else 0.0))%1)
            start=low+(high-low)*ratio
            inputs=["-ss",str(start),"-stream_loop","-1","-i",str(asset)]
            vf="[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1[b];[b][1:v]overlay"
        else:
            inputs=["-loop","1","-framerate","30","-i",str(asset)]
            vf="[0:v]scale=1200:2134:force_original_aspect_ratio=increase,crop=1200:2134,zoompan=z='min(zoom+0.002,1.12)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1080x1920:fps=30,setsar=1[b];[b][1:v]overlay"
        ff(*inputs,"-loop","1","-framerate","30","-i",overlay,"-filter_complex_threads","1","-filter_complex",vf,"-t",str(seconds),"-r","30","-an","-c:v","libx264","-preset","veryfast","-crf","23","-pix_fmt","yuv420p",out)
        shots.append(out)
    listing=folder/"concat.txt";listing.write_text("".join("file '"+str(s)+"'\n" for s in shots))
    visual=folder/"visual.mp4";ff("-f","concat","-safe","0","-i",listing,"-c","copy",visual)
    sr=48000;t=np.arange(int(sr*dur))/sr
    music=sum(.009*np.sin(2*np.pi*f*t)*(.75+.25*np.sin(2*np.pi*1.5*t+j)) for j,f in enumerate([55,82.41,110,164.81]))
    music*=np.minimum(1,t/.3)*np.minimum(1,np.maximum(0,(dur-t)/.6))
    sf.write(folder/"music.wav",music,sr)
    dest=O/f"VICE_RADAR_V3_1_{ep['id']}_REVIEW.mp4"
    ff("-i",visual,"-i",raw,"-i",folder/"music.wav","-filter_complex_threads","1","-filter_complex",f"[0:v]ass={ass}[v];[1:a]highpass=f=80,acompressor=threshold=0.125:ratio=2[vocal];[vocal][2:a]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=7[a]","-map","[v]","-map","[a]","-t",str(dur),"-c:v","libx264","-preset","veryfast","-crf","22","-c:a","aac","-ar","48000","-ac","2","-b:a","256k","-movflags","+faststart",dest)
    with open(O/f"audio-{ep['id']}.txt","w") as f:sp.run(["ffmpeg","-hide_banner","-i",str(dest),"-af","ebur128=peak=true","-f","null","-"],stderr=f,check=True)
    report.append({"id":ep["id"],"duration":probe(dest),"shots":counts,"source":ep["url"],"rights":"Review only; commercial reuse not verified","captions":"ASR word timing; accuracy pending human review"})
(O/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2))
