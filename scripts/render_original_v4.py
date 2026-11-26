import subprocess as sp, json, math
from pathlib import Path
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont
from kokoro import KPipeline
O=Path("output"); O.mkdir(exist_ok=True)
W=Path("work"); W.mkdir(exist_ok=True)
p=KPipeline(lang_code="e",repo_id="hexgrad/Kokoro-82M")
font=lambda s: ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",s)
def ff(*a): sp.run(["ffmpeg","-y","-loglevel","error",*map(str,a)],check=True)
episodes=json.loads(Path("scripts/editorial_queue_v4.json").read_text())
for ep in episodes:
    folder=W/ep["id"]; folder.mkdir(exist_ok=True)
    shots=[]
    for i,(headline,spoken) in enumerate(ep["scenes"]):
        audio=np.concatenate([a for _,_,a in p(spoken,voice="em_alex",speed=1.0) if a is not None])
        wav=folder/f"{i}.wav"; sf.write(wav,audio,24000)
        dur=len(audio)/24000
        im=Image.new("RGB",(1080,1920),"#10091f"); d=ImageDraw.Draw(im)
        for y in range(1920):
            d.line((0,y,1080,y),fill=(16+int(y/1920*35),9,31+int(y/1920*45)))
        for j in range(18):
            x=(j*173+i*97)%1080; h=100+(j*83)%350
            d.rectangle((x,1250-h,x+65,1250),fill="#342050",outline="#a64d9c")
        d.text((70,110),"VICE RADAR NEWS",font=font(52),fill="#ff72bf")
        d.text((70,210),ep["label"],font=font(35),fill="#cbb9ff")
        d.rounded_rectangle((70,420,1010,1000),radius=40,fill="#211333",outline="#ff72bf",width=5)
        def wrap(t,f,w):
            lines=[]; line=""
            for word in t.split():
                v=(line+" "+word).strip()
                if line and d.textlength(v,font=f)>w: lines.append(line); line=word
                else: line=v
            return "\n".join(lines+[line])
        d.multiline_text((115,490),wrap(headline,font(80),850),font=font(80),fill="white",spacing=20)
        d.rounded_rectangle((80,1320,1000,1640),radius=25,fill="#120c20")
        d.multiline_text((120,1360),wrap(spoken,font(48),840),font=font(48),fill="white",spacing=12)
        d.text((90,1750),"GRÁFICOS ORIGINALES · NO GAMEPLAY",font=font(30),fill="#ff72bf")
        png=folder/f"{i}.png"; im.save(png)
        out=folder/f"{i}.mp4"
        ff("-loop","1","-i",png,"-i",wav,"-vf","scale=1200:2134,zoompan=z='min(1.06,1+on*0.0004)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1080x1920:fps=30,setsar=1","-af","loudnorm=I=-14:TP=-1.5:LRA=7","-t",dur,"-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p","-c:a","aac","-ar","48000","-ac","2",out)
        shots.append(out.resolve())
    listing=folder/"concat.txt"; listing.write_text("".join("file '"+str(s)+"'\n" for s in shots))
    dest=O/(ep["id"]+".mp4")
    ff("-f","concat","-safe","0","-i",listing,"-c","copy","-movflags","+faststart",dest)
    sp.run(["ffmpeg","-v","error","-i",str(dest),"-f","null","-"],check=True)
    (O/(ep["id"]+".json")).write_text(json.dumps(ep,ensure_ascii=False))
