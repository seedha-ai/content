import os
import asyncio, sys
from playwright.sync_api import sync_playwright
from common import *
BASE=CSS_FONTS+"""
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:1080px;height:1350px;overflow:hidden}
body{position:relative;font-family:'ISans',sans-serif;color:#F4F6FA;
 background:radial-gradient(900px 700px at 88% -8%,rgba(245,184,0,.13),transparent 62%),radial-gradient(800px 600px at -10% 105%,rgba(90,100,255,.14),transparent 60%),linear-gradient(180deg,#1C1C5E 0%,#0B0B2C 100%);}
body.light{color:#16164A;background:radial-gradient(900px 700px at 90% -10%,rgba(245,184,0,.20),transparent 60%),linear-gradient(180deg,#F7F8FC,#E9ECF5);}
body::before{content:'';position:absolute;inset:0;background-image:GRAIN;opacity:.07;mix-blend-mode:overlay;pointer-events:none}
body::after{content:'';position:absolute;inset:34px;border:1px solid rgba(244,246,250,.10);border-radius:6px;pointer-events:none}
body.light::after{border-color:rgba(22,22,74,.12)}
.hdr{position:absolute;left:78px;right:78px;top:74px;display:flex;justify-content:space-between;align-items:center}
.brand{display:flex;align-items:center;gap:14px;font-family:'ISerif';font-size:44px;letter-spacing:.2px}
.tag{font-weight:700;font-size:24px;letter-spacing:.3px;color:#F5B800;border:2.5px solid #F5B800;border-radius:30px;padding:9px 22px}
.light .tag{color:#16164A;border-color:#16164A}
.serif{font-family:'ISerif'}
.kick{font-weight:700;font-size:30px;color:#F5B800;letter-spacing:.2px}
.light .kick{color:#9A6B00}
.mute{color:#B0B6D6}.light .mute{color:#4A5078}
.h{font-family:'ISerif';line-height:1.04;letter-spacing:-.6px}
.prog{position:absolute;left:78px;right:78px;bottom:82px}
.prog .row{display:flex;justify-content:space-between;font-size:26px;color:#B0B6D6;margin-top:24px}
.light .prog .row{color:#4A5078}
.track{position:relative;height:3px;background:rgba(176,182,214,.28);border-radius:3px}
.light .track{background:rgba(22,22,74,.18)}
.fill{position:absolute;left:0;top:-1px;height:5px;background:#F5B800;border-radius:3px}
.node{position:absolute;top:-8px;width:19px;height:19px;border-radius:50%;background:#F5B800;transform:translateX(-50%)}
.abs{position:absolute}
mark{background:#F5B800;color:#16164A;padding:0 8px;border-radius:6px}
""".replace("GRAIN",GRAIN)
def prog(i,n,hint="Swipe"):
    p=i/n*100
    return f'<div class="prog"><div class="track"><div class="fill" style="width:{p}%"></div><div class="node" style="left:{p}%"></div></div><div class="row"><span>{i} / {n}</span><span>{hint}</span></div></div>'
def hdr(tag,light=False): return f'<div class="hdr"><div class="brand">{mark_svg(70,34,lw=2,alpha=.55,sw=4,nr=6,color=('22,22,74' if light else '244,246,250'))}seedha.ai</div><div class="tag">{tag}</div></div>'
def page(body,light=False): return f"<html><head><style>{BASE}</style></head><body class='{'light' if light else ''}'>{body}</body></html>"

def s1():
    return page(hdr("Concept")+f'''
<div class="abs" style="left:78px;top:250px">{mark_svg(924,230,lw=3,alpha=.5,sw=10,nr=17)}</div>
<div class="abs h" style="left:78px;top:560px;width:930px;font-size:150px">How ChatGPT actually works, in 60 seconds.</div>
<div class="abs mute" style="left:78px;top:1090px;font-size:38px">The Transformer, explained simply.</div>
'''+prog(1,5))
def s2():
    words="Older models read one word at a time, and by the end of a long sentence, had forgotten the start.".split()
    return page(hdr("Concept")+f'''
<div class="abs kick" style="left:78px;top:250px">The problem</div>
<div class="abs h" style="left:78px;top:320px;width:930px;font-size:100px">Older models read one word at a time. Long sentences made them forget the start.</div>
<div class="abs serif" style="left:78px;top:860px;width:930px;font-size:58px;line-height:1.25">
<span style="opacity:.14">The animal didn't cross</span> <span style="opacity:.32">the street because</span> <span style="opacity:.6">it was too</span> <span style="opacity:1">tired.</span></div>
<div class="abs mute" style="left:78px;top:1070px;font-size:34px">The start fades as the sentence grows.</div>
'''+prog(2,5))
def s3():
    return page(hdr("Concept",True)+'''
<div class="abs kick" style="left:78px;top:250px">The idea: attention</div>
<div class="abs h" style="left:78px;top:320px;width:930px;font-size:92px">Every word looks at every other word, and decides which ones matter.</div>
<div id="sent" class="abs serif" style="left:78px;top:745px;width:930px;font-size:60px;line-height:2.1">
 <div><span id="w_the">The</span> <span id="w_animal"><mark>animal</mark></span> <span id="w_didnt">didn't</span> <span id="w_cross">cross</span></div>
 <div><span id="w_the2">the</span> <span id="w_street">street</span> <span id="w_because">because</span> <span id="w_it"><mark>it</mark></span> <span id="w_was">was</span> <span id="w_too">too</span> <span id="w_tired">tired.</span></div></div>
<svg id="arcs" class="abs" style="left:0;top:0" width="1080" height="1350"></svg>
<div class="abs mute" style="left:78px;top:1085px;font-size:34px">"It" points to the animal, not the street.</div>
<script>
document.fonts.ready.then(()=>{
 const svg=document.getElementById('arcs');const ns='http://www.w3.org/2000/svg';
 const r=id=>document.getElementById(id).getBoundingClientRect();
 const it=r('w_it');const ix=it.left+it.width/2, iy=it.top+it.height/2-26;
 const an=r('w_animal');const ax=an.left+an.width/2, ay=an.bottom+4;
 const p=document.createElementNS(ns,'path');
 p.setAttribute('d',`M${ix} ${it.top+8} C ${ix} ${(ay+it.top)/2}, ${ax} ${(ay+it.top)/2}, ${ax} ${ay}`);
 p.setAttribute('fill','none');p.setAttribute('stroke','#16164A');p.setAttribute('stroke-width',5);p.setAttribute('stroke-linecap','round');
 svg.appendChild(p);
 document.title='ready';});
</script>
'''+prog(3,5),light=True)
def s4():
    return page(hdr("Concept")+'''
<div class="abs kick" style="left:78px;top:250px">The training</div>
<div class="abs h" style="left:78px;top:320px;width:930px;font-size:100px">Then it learns one game: predict the next word.</div>
<div class="abs" style="left:78px;top:640px;width:924px;border:2px solid rgba(176,182,214,.30);border-radius:30px;padding:46px 50px;background:rgba(255,255,255,.04);backdrop-filter:blur(6px)">
 <div class="serif" style="font-size:64px;line-height:1.1">The capital of India is <span style="color:#F5B800">New Delhi</span><span style="display:inline-block;width:4px;height:58px;background:#F5B800;margin-left:8px;vertical-align:-8px"></span></div>
 <div style="margin-top:38px;font-size:27px;color:#B0B6D6;display:grid;grid-template-columns:150px 1fr;row-gap:14px;align-items:center">
   <span>New Delhi</span><div style="height:12px;border-radius:6px;background:linear-gradient(90deg,#F5B800 0 86%,rgba(176,182,214,.18) 86%)"></div>
   <span>Delhi</span><div style="height:12px;border-radius:6px;background:linear-gradient(90deg,#B0B6D6 0 9%,rgba(176,182,214,.18) 9%)"></div>
   <span>Mumbai</span><div style="height:12px;border-radius:6px;background:linear-gradient(90deg,#B0B6D6 0 3%,rgba(176,182,214,.18) 3%)"></div></div>
 <div style="margin-top:22px;font-size:22px;color:#7F86B3">Illustrative likelihoods</div></div>
<div class="abs mute" style="left:78px;top:1060px;width:900px;font-size:36px;line-height:1.35">Repeat that billions of times on huge amounts of text. Human feedback later tunes it to be helpful.</div>
'''+prog(4,5))
def s5():
    return page(hdr("Concept")+f'''
<div class="abs" style="left:78px;top:250px">{mark_svg(924,230,lw=3,alpha=.5,sw=10,nr=17)}</div>
<div class="abs h" style="left:78px;top:560px;width:930px;font-size:140px">Save this. Send it to a friend learning AI.</div>
<div class="abs" style="left:78px;top:1070px;font-weight:700;font-size:42px;color:#F5B800">Follow @seedha.ai for AI, made simple.</div>
'''+prog(5,5,hint=""))
def news():
    return page(hdr("News")+'''
<div class="abs" style="left:-120px;top:230px;width:900px;height:700px;background:radial-gradient(closest-side,rgba(245,184,0,.18),transparent);filter:blur(10px)"></div>
<div class="abs serif" style="left:70px;top:230px;font-size:430px;line-height:1;color:#F5B800;letter-spacing:-8px">100M</div>
<div class="abs h" style="left:78px;top:700px;width:930px;font-size:100px">people in India use ChatGPT every week.</div>
<div class="abs mute" style="left:78px;top:990px;width:900px;font-size:36px;line-height:1.4">India is OpenAI's second-largest market, after the US. People aged 18 to 24 send nearly half of all messages.</div>
<div class="abs" style="left:78px;right:78px;bottom:92px;border-top:1px solid rgba(176,182,214,.30);padding-top:26px;display:flex;justify-content:space-between;font-size:26px;color:#B0B6D6"><span>Source: OpenAI, India AI Impact Summit, Feb 2026</span><span style="font-weight:700;color:#F4F6FA">@seedha.ai</span></div>
''')
if __name__=="__main__":
    jobs={"c1":s1,"c2":s2,"c3":s3,"c4":s4,"c5":s5,"news":news}
    with sync_playwright() as p:
        b=p.chromium.launch(**({"executable_path":"/usr/bin/google-chrome"} if os.path.exists("/usr/bin/google-chrome") else {}),args=["--no-sandbox","--allow-file-access-from-files"])
        pg=b.new_page(viewport={"width":1080,"height":1350})
        for k,f in jobs.items():
            open(f"tmp/{k}.html","w").write(f())
            pg.goto(f"file://"+os.path.abspath("tmp")+"/{k}.html"); pg.wait_for_timeout(900)
            pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(300)
            pg.screenshot(path=f"out/{k}.png"); print(k)
        b.close()
