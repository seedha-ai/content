import os
import math
FD=os.path.join(os.path.dirname(os.path.abspath(__file__)),"fonts")+"/"
CSS_FONTS=f"""
@font-face{{font-family:'ISerif';src:url('file://{FD}InstrumentSerif-Regular.ttf');}}
@font-face{{font-family:'ISerif';font-style:italic;src:url('file://{FD}InstrumentSerif-Italic.ttf');}}
@font-face{{font-family:'ISans';font-weight:400;src:url('file://{FD}InstrumentSans-Regular.ttf');}}
@font-face{{font-family:'ISans';font-weight:700;src:url('file://{FD}InstrumentSans-Bold.ttf');}}
"""
GRAIN="url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 .55 0'/></filter><rect width='300' height='300' filter='url(%23n)'/></svg>\")"
def smooth(x):
    x=max(0,min(1,x)); return x*x*(3-2*x)
def mark_svg(w,h,lw=3,alpha=.42,sw=8,nr=13,color="244,246,250",cls=""):
    cy=h/2; n=9; paths=[]
    for i in range(n):
        base=(i-(n-1)/2)*(h/(n+2))*0.55; fr=1.3+0.37*i; ph=i*1.7; pts=[]
        for k in range(0,301):
            t=k/300; env=1-smooth((t-0.05)/0.5)
            yy=cy+env*(base*1.3+(h*0.22)*math.sin(2*math.pi*fr*t*0.9+ph)*(0.4+0.6*math.sin(math.pi*min(t/0.55,1))))
            pts.append(f"{t*w*0.98:.1f},{yy:.1f}")
        paths.append(f'<polyline points="{" ".join(pts)}" fill="none" stroke="rgba({color},{alpha})" stroke-width="{lw}" stroke-linejoin="round"/>')
    x1=w*0.52; x2=w*0.98
    return (f'<svg class="{cls}" width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg">'
            + "".join(paths)
            + f'<line class="sl" x1="{x1}" y1="{cy}" x2="{x2}" y2="{cy}" stroke="#F5B800" stroke-width="{sw}" stroke-linecap="round"/>'
            + f'<circle class="nd" cx="{x2}" cy="{cy}" r="{nr}" fill="#F5B800"/></svg>')
