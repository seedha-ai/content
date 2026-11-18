import subprocess, sys
from playwright.sync_api import sync_playwright
from common import *
import json
SPEC=json.load(open(sys.argv[1]))
NAME=SPEC["name"]
FPS=30; DUR=15.0
HTML="<html><head><style>"+CSS_FONTS+"""
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1920px;overflow:hidden;background:#0B0B2C}
body{position:relative;font-family:'ISans';color:#F4F6FA;
 background:radial-gradient(1000px 900px at 85% 0%,rgba(245,184,0,.14),transparent 60%),radial-gradient(900px 800px at 0% 100%,rgba(90,100,255,.16),transparent 60%),linear-gradient(180deg,#1C1C5E,#0B0B2C)}
.g{position:absolute;inset:0;background-image:GRAIN;opacity:.08;mix-blend-mode:overlay}
.a{position:absolute;left:80px;right:80px}
.serif{font-family:'ISerif';letter-spacing:-.8px;line-height:1.02}
.pill{display:inline-block;font-weight:700;font-size:34px;padding:14px 30px;border-radius:40px;border:3px solid #F5B800;color:#F5B800}
.card{border:2px solid rgba(176,182,214,.32);border-radius:34px;background:rgba(255,255,255,.05);padding:44px 48px}
.mono{font-family:'ISans';font-size:44px;line-height:1.35}
.cur{display:inline-block;width:5px;height:48px;background:#F5B800;vertical-align:-8px;margin-left:4px}
.flash{position:absolute;inset:0;background:#F5B800;opacity:0;mix-blend-mode:screen}
.hk{position:absolute;left:0;right:0;top:0;bottom:0}
.sc{position:absolute;inset:0;opacity:0}
.bar{position:absolute;left:80px;right:80px;bottom:150px;height:5px;background:rgba(176,182,214,.25);border-radius:3px}
.bar i{display:block;height:100%;background:#F5B800;border-radius:3px}
</style></head><body><div class="g"></div>
<!-- S1 hook -->
<div class="sc" id="s1">
 <div class="a serif" id="h1" style="top:430px;font-size:190px">{{H1}}</div>
 <div class="a serif" id="h2" style="top:1180px;font-size:112px;color:#F5B800">{{H2}}</div>
</div>
<!-- S2 bad prompt -->
<div class="sc" id="s2">
 <div class="a" style="top:330px"><span class="pill" style="border-color:#FF6B6B;color:#FF6B6B">{{PILL2}}</span></div>
 <div class="a serif" style="top:440px;font-size:104px">{{TITLE2}}</div>
 <div class="a card" style="top:700px"><div style="font-size:28px;color:#B0B6D6;margin-bottom:18px">You</div><div class="mono" id="p1"></div></div>
 <div class="a card" id="o1" style="top:1050px;opacity:0"><div style="font-size:28px;color:#B0B6D6;margin-bottom:18px">ChatGPT</div><div class="mono" style="color:#8D93BC">{{O1}}</div></div>
 <div class="a serif" id="x1" style="top:1450px;font-size:96px;color:#FF6B6B;opacity:0">{{X1}}</div>
</div>
<!-- S3 formula -->
<div class="sc" id="s3">
 <div class="a" style="top:330px"><span class="pill">{{PILL3}}</span></div>
 <div class="a serif" style="top:440px;font-size:112px">{{TITLE3}}</div>
 <div class="a" id="f1" style="top:760px"><div class="serif" style="font-size:150px;color:#F5B800">{{N1}}</div><div style="font-size:42px;color:#B0B6D6;margin-top:6px">{{D1}}</div></div>
 <div class="a" id="f2" style="top:1060px"><div class="serif" style="font-size:150px;color:#F5B800">{{N2}}</div><div style="font-size:42px;color:#B0B6D6;margin-top:6px">{{D2}}</div></div>
 <div class="a" id="f3" style="top:1360px"><div class="serif" style="font-size:150px;color:#F5B800">{{N3}}</div><div style="font-size:42px;color:#B0B6D6;margin-top:6px">{{D3}}</div></div>
</div>
<!-- S4 good prompt -->
<div class="sc" id="s4">
 <div class="a" style="top:330px"><span class="pill">{{PILL4}}</span></div>
 <div class="a card" style="top:470px"><div style="font-size:28px;color:#B0B6D6;margin-bottom:18px">You</div><div class="mono" id="p2" style="font-size:40px"></div></div>
 <div class="a card" id="o2" style="top:1090px;opacity:0;border-color:#F5B800"><div style="font-size:28px;color:#B0B6D6;margin-bottom:18px">ChatGPT</div><div class="mono" style="font-size:46px">{{O2}}</div></div>
 <div class="a serif" id="x2" style="top:1560px;font-size:96px;color:#F5B800;opacity:0">{{X2}}</div>
</div>
<!-- S5 CTA -->
<div class="sc" id="s5">
 <div class="a" id="mk" style="top:470px">MARK</div>
 <div class="a serif" style="top:760px;font-size:150px">{{TITLE5}}</div>
 <div class="a" style="top:1250px;font-size:50px;font-weight:700;color:#F5B800">Follow @seedha.ai</div>
 <div class="a" style="top:1330px;font-size:40px;color:#B0B6D6">AI, made simple.</div>
</div>
<div class="flash" id="fl"></div>
<div class="bar"><i id="pb" style="width:0"></i></div>
<script>
const $=id=>document.getElementById(id);
const cl=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const ease=x=>1-Math.pow(1-cl(x),3);
const back=x=>{x=cl(x);const c=1.9;return 1+(c+1)*Math.pow(x-1,3)+c*Math.pow(x-1,2)};
const P1="{{P1}}";
const P2="{{P2}}";
const S=[[0,1.9],[1.9,4.9],[4.9,8.3],[8.3,12.3],[12.3,15]];
function typed(el,s,t,t0,cps){const n=Math.floor(cl((t-t0)*cps,0,s.length));el.innerHTML=s.slice(0,n)+(t<t0+s.length/cps+.6&&Math.floor(t*3)%2==0||n<s.length?'<span class="cur"></span>':'');}
function T(t){
 S.forEach((r,i)=>{const e=$('s'+(i+1));e.style.opacity=(t>=r[0]&&t<r[1])?1:0;});
 // flash on cuts
 let f=0;S.forEach(r=>{const d=t-r[0];if(d>=0&&d<.18&&r[0]>0)f=Math.max(f,.55*(1-d/.18));});$('fl').style.opacity=f;
 $('pb').style.width=(t/15*100)+'%';
 // s1
 let a=t;
 let k=back(a/.35);$('h1').style.transform=`scale(${.85+.15*k})`;$('h1').style.opacity=cl(a/.12);
 $('h2').style.opacity=cl((a-.85)/.15);$('h2').style.transform=`translateY(${(1-ease((a-.85)/.35))*50}px)`;
 // s2
 let b=t-1.9;typed($('p1'),P1,b,.3,22);
 $('o1').style.opacity=cl((b-1.5)/.25);$('o1').style.transform=`translateY(${(1-ease((b-1.5)/.35))*40}px)`;
 $('x1').style.opacity=cl((b-2.3)/.2);$('x1').style.transform=`scale(${.9+.1*back((b-2.3)/.3)})`;
 // s3
 let c=t-4.9;[['f1',.2],['f2',1.2],['f3',2.2]].forEach(([id,d])=>{const e=$(id);const k=back((c-d)/.4);e.style.opacity=cl((c-d)/.15);e.style.transform=`translateX(${(1-ease((c-d)/.4))*-120}px)`;});
 // s4
 let d=t-8.3;typed($('p2'),P2,d,.3,44);
 $('o2').style.opacity=cl((d-3.0)/.25);$('o2').style.transform=`translateY(${(1-ease((d-3.0)/.35))*40}px)`;
 $('x2').style.opacity=cl((d-3.7)/.2);$('x2').style.transform=`scale(${.9+.1*back((d-3.7)/.3)})`;
 // s5
 let e=t-12.3;$('mk').style.opacity=cl(e/.2);
 const sv=$('mk').querySelector('svg');if(sv){const w=cl(e/1.2);sv.style.clipPath=`inset(0 ${(1-ease(w))*100}% 0 0)`;}
}
window.T=T;
</script></body></html>""".replace("GRAIN",GRAIN).replace("MARK",mark_svg(920,260,lw=3,alpha=.5,sw=12,nr=19))
TOK={"H1":SPEC["h1"],"H2":SPEC["h2"],"PILL2":SPEC["pill2"],"TITLE2":SPEC["title2"],"O1":SPEC["o1"],"X1":SPEC["x1"],"PILL3":SPEC["pill3"],"TITLE3":SPEC["title3"],
"N1":SPEC["items"][0][0],"D1":SPEC["items"][0][1],"N2":SPEC["items"][1][0],"D2":SPEC["items"][1][1],"N3":SPEC["items"][2][0],"D3":SPEC["items"][2][1],
"PILL4":SPEC["pill4"],"O2":SPEC["o2"],"X2":SPEC["x2"],"TITLE5":SPEC["title5"],"P1":SPEC["p1"],"P2":SPEC["p2"]}
for k,v in TOK.items(): HTML=HTML.replace("{{"+k+"}}",v)
open(f"tmp/{NAME}.html","w").write(HTML)
mode=sys.argv[2] if len(sys.argv)>2 else "full"
with sync_playwright() as p:
    b=p.chromium.launch(**({"executable_path":"/usr/bin/google-chrome"} if os.path.exists("/usr/bin/google-chrome") else {}),args=["--no-sandbox","--allow-file-access-from-files"])
    pg=b.new_page(viewport={"width":1080,"height":1920})
    pg.goto("file://"+os.path.abspath("tmp")+"/"+NAME+".html"); pg.wait_for_timeout(1000)
    if mode=="test":
        for t in [0.5,1.5,3.6,6.5,10.5,13.8]:
            pg.evaluate(f"T({t})"); pg.wait_for_timeout(80); pg.screenshot(path=f"tmp/{NAME}_{t}.jpg",type="jpeg",quality=88)
    else:
        ff=subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","image2pipe","-framerate",str(FPS),"-i","-","-c:v","libx264","-crf","18","-preset","veryfast","-pix_fmt","yuv420p",f"tmp/{NAME}_v.part.mp4"],stdin=subprocess.PIPE)
        for i in range(int(DUR*FPS)):
            pg.evaluate(f"T({i/FPS})"); ff.stdin.write(pg.screenshot(type="jpeg",quality=92))
        ff.stdin.close(); ff.wait()
        import os; os.rename(f"tmp/{NAME}_v.part.mp4",f"tmp/{NAME}_v.mp4")
    b.close()
