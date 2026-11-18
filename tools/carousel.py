import os
import sys, json, os
from playwright.sync_api import sync_playwright
from PIL import Image
from common import *
from feed import BASE, hdr, page
import feed
REEL=os.environ.get('REEL')=='1'
def prog(i,n,hint=None):
    if REEL: return ''  # reels get their own progress bar
    return feed.prog(i,n,'Swipe' if hint is None else hint)
EXTRA="""
.col{position:absolute;left:78px;right:78px;top:250px;bottom:170px;display:flex;flex-direction:column}
.item{border-top:1px solid rgba(176,182,214,.30);padding:42px 0}
.light .item{border-color:rgba(22,22,74,.18)}
.item .n{font-weight:700;font-size:44px;color:#F5B800;margin-bottom:12px}
.light .item .n{color:#9A6B00}
.item .d{font-size:42px;line-height:1.3;color:#DDE1F2}
.light .item .d{color:#2A2F5E}
.tight .item{padding:26px 0}.tight .item .d{font-size:38px}.tight .item .n{font-size:40px;margin-bottom:8px}
.pc{border:2px solid rgba(176,182,214,.30);border-radius:26px;padding:30px 36px;background:rgba(255,255,255,.05);margin-top:20px}
.light .tight .item{padding:26px 0}.tight .item .d{font-size:38px}.tight .item .n{font-size:40px;margin-bottom:8px}
.pc{background:rgba(255,255,255,.7);border-color:rgba(22,22,74,.18)}
"""
def hsize(t,big=False):
    n=len(t)
    if big: return 150 if n<=28 else 124 if n<=42 else 100
    return 112 if n<=30 else 92 if n<=52 else 78
def cover(s,i,n):
    return page(hdr(s["tag"])+f'''
<div class="abs" style="left:78px;top:250px">{mark_svg(924,230,lw=3,alpha=.5,sw=10,nr=17)}</div>
<div class="abs h" style="left:78px;top:560px;width:930px;font-size:{hsize(s["title"],True)}px">{s["title"]}</div>
<div class="abs mute" style="left:78px;top:1000px;width:900px;font-size:40px;line-height:1.3">{s["sub"]}</div>'''+prog(i,n))
def pts(s,i,n,light=False,tag="Guide"):
    items="".join(f'<div class="item"><div class="n">{a}</div><div class="d">{b}</div></div>' for a,b in s["items"])
    src=f'<div class="mute abs" style="left:78px;bottom:150px;font-size:24px">{s["src"]}</div>' if s.get("src") else ""
    return page(hdr(tag,light)+f'''
<div class="col {'tight' if s.get('src') else ''}"><div class="kick">{s["kicker"]}</div>
<div class="h" style="font-size:{hsize(s["head"])}px;margin:22px 0 {36 if s.get('src') else 56}px">{s["head"]}</div>{items}</div>{src}'''+prog(i,n),light=light)
def cta(s,i,n,tag):
    return page(hdr(tag)+f'''
<div class="abs" style="left:78px;top:250px">{mark_svg(924,230,lw=3,alpha=.5,sw=10,nr=17)}</div>
<div class="abs h" style="left:78px;top:560px;width:930px;font-size:{hsize(s["title"],True)}px">{s["title"]}</div>
<div class="abs" style="left:78px;top:1070px;font-weight:700;font-size:42px;color:#F5B800">Follow @seedha.ai for AI, made simple.</div>'''+prog(i,n,hint=""))
def stat(s):
    return page(hdr(s["tag"])+f'''
<div class="abs" style="left:-120px;top:230px;width:900px;height:700px;background:radial-gradient(closest-side,rgba(245,184,0,.18),transparent);filter:blur(10px)"></div>
<div class="abs serif" style="left:70px;top:230px;font-size:{s.get("bigsize",430)}px;line-height:1;color:#F5B800;letter-spacing:-8px">{s["big"]}</div>
<div class="abs h" style="left:78px;top:700px;width:930px;font-size:{90 if len(s["head"])>50 else 100}px">{s["head"]}</div>
<div class="abs mute" style="left:78px;top:1010px;width:900px;font-size:36px;line-height:1.4">{s["sub"]}</div>
<div class="abs" style="left:78px;right:78px;bottom:92px;border-top:1px solid rgba(176,182,214,.30);padding-top:26px;display:flex;justify-content:space-between;font-size:25px;color:#B0B6D6"><span>{s["src"]}</span><span style="font-weight:700;color:#F4F6FA">@seedha.ai</span></div>''')
def potd(s):
    return page(hdr("Prompt of the day")+f'''
<div class="abs kick" style="left:78px;top:250px">Copy, paste, change the brackets.</div>
<div class="abs" style="left:78px;top:350px;width:924px;border:2px solid rgba(176,182,214,.30);border-radius:30px;padding:56px 54px;background:rgba(255,255,255,.05)">
 <div style="font-size:26px;color:#B0B6D6;margin-bottom:22px">You</div>
 <div class="serif" style="font-size:{72 if len(s["prompt"])<90 else 62}px;line-height:1.15">{s["prompt"]}<span style="display:inline-block;width:5px;height:60px;background:#F5B800;margin-left:8px;vertical-align:-8px"></span></div></div>
<div class="abs kick" style="left:78px;top:960px">Why it works</div>
<div class="abs mute" style="left:78px;top:1020px;width:900px;font-size:40px;line-height:1.35">{s["why"]}</div>
<div class="abs" style="left:78px;right:78px;bottom:92px;border-top:1px solid rgba(176,182,214,.30);padding-top:26px;display:flex;justify-content:space-between;font-size:26px;color:#B0B6D6"><span>Save it for your next study session.</span><span style="font-weight:700;color:#F4F6FA">@seedha.ai</span></div>''')
def build(spec,outdir):
    os.makedirs(outdir,exist_ok=True)
    htmls=[]
    if spec["kind"]=="carousel":
        sl=spec["slides"]; n=len(sl)+2
        htmls.append(cover(spec["cover"],1,n))
        for k,s in enumerate(sl): htmls.append(pts(s,k+2,n,light=(k==1),tag=spec["cover"]["tag"]))
        htmls.append(cta(spec["cta"],n,n,spec["cover"]["tag"]))
    elif spec["kind"]=="stat": htmls=[stat(spec)]
    else: htmls=[potd(spec)]
    return htmls
if __name__=="__main__":
    specs=json.load(open(sys.argv[1]))
    with sync_playwright() as p:
        b=p.chromium.launch(**({"executable_path":"/usr/bin/google-chrome"} if os.path.exists("/usr/bin/google-chrome") else {}),args=["--no-sandbox","--allow-file-access-from-files"])
        pg=b.new_page(viewport={"width":1080,"height":1350})
        for sp in specs:
            out=f"{os.environ.get('OUT','week')}/{sp['id']}"; os.makedirs(out,exist_ok=True)
            for j,h in enumerate(build(sp,out)):
                h=h.replace("</style>",EXTRA+"</style>",1)
                open("tmp/_c.html","w").write(h)
                pg.goto("file://"+os.path.abspath("tmp")+"/_c.html"); pg.wait_for_timeout(700); pg.evaluate("document.fonts.ready"); pg.wait_for_timeout(250)
                png=f"{out}/s{j+1}.png"; pg.screenshot(path=png)
                Image.open(png).convert("RGB").save(f"{out}/s{j+1}.jpg",quality=93); os.remove(png)
            print(sp["id"])
        b.close()
