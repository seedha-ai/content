"""Turn post slides (1080x1350 jpgs) into a 9:16 reel with motion, a progress bar and original music.
slides_reel.py out.mp4 bpm transpose slide1.jpg slide2.jpg ..."""
import sys, subprocess, numpy as np
from PIL import Image, ImageFilter, ImageDraw
out=sys.argv[1]; bpm=sys.argv[2]; tr=sys.argv[3]; files=sys.argv[4:]
FPS=30; W,H=1080,1920; SH=1350; Y0=(H-SH)//2
n=len(files)
if n==1: durs=[7.0]
else: durs=[2.4]+[3.6]*(n-2)+[2.6]
cuts=list(np.cumsum(durs)[:-1]); D=float(sum(durs))
sl=[Image.open(f).convert("RGB").resize((W,SH)) for f in files]
def band(img):  # blurred, darkened backdrop
    b=img.resize((W,H)).filter(ImageFilter.GaussianBlur(60))
    return Image.blend(b,Image.new("RGB",(W,H),(14,14,52)),.55)
bgs=[band(s) for s in sl]
ease=lambda x:1-(1-x)**3
def frame(t):
    i=0; acc=0
    while i<n-1 and t>=acc+durs[i]: acc+=durs[i]; i+=1
    lt=t-acc
    canvas=bgs[i].copy()
    T=.28
    if i>0 and lt<T:  # slide transition from previous
        p=ease(lt/T); off=int(W*(1-p))
        canvas=Image.blend(bgs[i-1],bgs[i],p)
        canvas.paste(sl[i-1],(off-W,Y0)); canvas.paste(sl[i],(off,Y0))
    else:
        s=sl[i]
        if n==1 or i==0:  # gentle push-in
            z=1.0+0.04*min(1,lt/durs[i]) if n==1 else 1.06-0.06*ease(min(1,lt/.6))
            sw,shh=int(W*z),int(SH*z); s=s.resize((sw,shh)); s=s.crop(((sw-W)//2,(shh-SH)//2,(sw-W)//2+W,(shh-SH)//2+SH))
        canvas.paste(s,(0,Y0))
    if n>1:  # story-style progress bar above the slide
        d=ImageDraw.Draw(canvas); gap=10; x0=60; segw=(W-2*x0-gap*(n-1))/n; y=Y0-46
        for k in range(n):
            xa=x0+k*(segw+gap); d.rounded_rectangle([xa,y,xa+segw,y+8],4,fill=(255,255,255,0) if False else (90,92,140))
            fill=1 if k<i else (min(1,lt/durs[i]) if k==i else 0)
            if fill>0: d.rounded_rectangle([xa,y,xa+segw*fill,y+8],4,fill=(245,184,0))
    return canvas
wav=out.replace(".mp4",".wav")
subprocess.run(["python3","music.py",wav,str(D),bpm,tr,",".join(f"{c:.3f}" for c in cuts)],check=True)
p=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r",str(FPS),"-i","-","-i",wav,
   "-c:v","libx264","-preset","veryfast","-crf","19","-pix_fmt","yuv420p","-c:a","aac","-b:a","192k","-shortest","-movflags","+faststart",out],stdin=subprocess.PIPE)
for f in range(int(D*FPS)): p.stdin.write(np.asarray(frame(f/FPS)).tobytes())
p.stdin.close(); p.wait()
import os; os.remove(wav)
print(out, f"{D:.1f}s")
