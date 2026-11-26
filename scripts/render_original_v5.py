import os, json, subprocess as sp
from pathlib import Path
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont, ImageOps
from kokoro import KPipeline
import torch
from diffusers import StableDiffusionPipeline

# Local inference, no paid API. SD 1.5 uses CreativeML Open RAIL-M.
model="stable-diffusion-v1-5/stable-diffusion-v1-5"
device="cuda" if torch.cuda.is_available() else "cpu"
pipe=StableDiffusionPipeline.from_pretrained(model,torch_dtype=torch.float16 if device=="cuda" else torch.float32).to(device)
pipe.enable_attention_slicing()
if device=="cpu": torch.set_num_threads(4)
voice=KPipeline(lang_code="e",repo_id="hexgrad/Kokoro-82M")
out=Path("output-v5"); out.mkdir(exist_ok=True)
def ff(*args): sp.run(["ffmpeg","-y","-v","error",*map(str,args)],check=True)
def font(n): return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",n)
def wrap(d,t,f,w):
    lines=[]; line=""
    for word in t.split():
        trial=(line+" "+word).strip()
        if line and d.textlength(trial,font=f)>w: lines.append(line); line=word
        else: line=trial
    return "\n".join(lines+[line])
queue=json.loads(Path("scripts/editorial_queue_v5.json").read_text())
for ep in queue:
    folder=out/ep["id"]; folder.mkdir(exist_ok=True)
    shots=[]; manifest=[]
    for i,scene in enumerate(ep["scenes"]):
        spoken=scene["spoken"]; prompt=scene["visual"]
        for attempt in range(3):
            seed=20261126+i+attempt*1009
            safe_prompt=prompt if attempt==0 else "Family friendly technology editorial still life, objects only, no people, "+prompt
            result=pipe(safe_prompt+", cinematic editorial illustration, neon magenta and cyan, vertical composition, no text, no logos",negative_prompt="text, watermark, logo, blurry, screenshot, gameplay interface, nudity, sexual content, violence, people",width=384,height=640,num_inference_steps=12,guidance_scale=7,generator=torch.Generator(device=device).manual_seed(seed))
            if result.nsfw_content_detected is not None and not any(result.nsfw_content_detected):
                break
            print(f"Scene {i}: rejected image discarded, attempt {attempt+1}",flush=True)
        else:
            raise RuntimeError("No approved image after three attempts; stop for review")
        raw=folder/f"scene-{i:02}.png"; result.images[0].save(raw)
        im=ImageOps.fit(result.images[0].convert("RGB"),(1080,1920),method=Image.Resampling.LANCZOS)
        overlay=Image.new("RGBA",im.size); d=ImageDraw.Draw(overlay)
        d.rectangle((0,0,1080,260),fill=(12,7,24,220))
        d.text((65,75),"VICE RADAR NEWS",font=font(52),fill="#ff72bf")
        d.text((65,150),ep["label"],font=font(32),fill="white")
        d.rectangle((0,1300,1080,1920),fill=(12,7,24,220))
        caption=wrap(d,spoken,font(53),940)
        if d.multiline_textbbox((65,1390),caption,font=font(53),spacing=12)[3]>1740: raise ValueError("Caption overflow")
        d.multiline_text((65,1390),caption,font=font(53),fill="white",spacing=12)
        d.text((65,1780),"ILUSTRACIÓN IA · NO GAMEPLAY",font=font(30),fill="#ff72bf")
        frame=folder/f"frame-{i:02}.png"; Image.alpha_composite(im.convert("RGBA"),overlay).convert("RGB").save(frame)
        audio=np.concatenate([a for _,_,a in voice(spoken,voice="em_alex") if a is not None])
        wav=folder/f"{i}.wav"; sf.write(wav,audio,24000); duration=len(audio)/24000
        shot=folder/f"{i}.mp4"
        ff("-loop","1","-i",frame,"-i",wav,"-vf","scale=1200:2134,zoompan=z='min(1.05,1+on*0.0004)':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d=1:s=1080x1920:fps=30,setsar=1","-af","loudnorm=I=-14:TP=-1.5:LRA=7","-t",duration,"-c:v","libx264","-preset","veryfast","-pix_fmt","yuv420p","-c:a","aac","-ar","48000","-ac","2",shot)
        shots.append(shot.resolve()); manifest.append({"spoken":spoken,"prompt":prompt,"seed":seed,"duration":duration,"image":raw.name})
    listing=folder/"concat.txt"; listing.write_text("".join("file '"+str(s)+"'\n" for s in shots))
    dest=out/(ep["id"]+".mp4"); ff("-f","concat","-safe","0","-i",listing,"-c","copy","-movflags","+faststart",dest)
    sp.run(["ffmpeg","-v","error","-i",str(dest),"-f","null","-"],check=True)
    (out/(ep["id"]+".json")).write_text(json.dumps({"model":model,"scenes":manifest,"status":"review","source":ep["source"]},ensure_ascii=False,indent=2))
