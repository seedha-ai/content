import sys, json
SPEC=json.load(open(sys.argv[1]))
import numpy as np, scipy.io.wavfile as w
from scipy.signal import butter, lfilter
sr=44100; D=15.0; n=int(D*sr); rng=np.random.default_rng(3)
L=np.zeros(n); R=np.zeros(n)
def add(t,s,pan=0.0,g=1.0):
    i=int(t*sr)
    if i>=n: return
    s=s[:n-i]; L[i:i+len(s)]+=s*g*(1-max(pan,0)); R[i:i+len(s)]+=s*g*(1+min(pan,0))
def T(d): return np.arange(int(d*sr))/sr
def lp(x,f): b,a=butter(2,f/(sr/2)); return lfilter(b,a,x)
def hp(x,f): b,a=butter(2,f/(sr/2),'high'); return lfilter(b,a,x)
def kick(): t=T(.35); return .9*np.sin(2*np.pi*(48+110*np.exp(-t*28))*t)*np.exp(-t*9)
def hat(o=False): d=.18 if o else .05; t=T(d); return .22*hp(rng.standard_normal(len(t)),7000)*np.exp(-t*(18 if o else 70))
def snare(): t=T(.2); return .35*(hp(rng.standard_normal(len(t)),1500)*np.exp(-t*24)+.5*np.sin(2*np.pi*190*t)*np.exp(-t*30))
def bass(f,d=.4): t=T(d); return .38*np.tanh(2*np.sin(2*np.pi*f*t))*np.exp(-t*4)*np.minimum(1,t*200)
def pluck(f,d=.5,g=.2): t=T(d); x=sum(np.sin(2*np.pi*f*k*t)/k for k in (1,2,3)); return g*lp(x,3500)*np.exp(-t*7)
def riser(d,g=.28): t=T(d); x=rng.standard_normal(len(t)); f=np.linspace(400,9000,len(t)); y=np.zeros(len(t)); 
def riser(d,g=.3):
    t=T(d); x=rng.standard_normal(len(t)); out=hp(x,1500)*(t/d)**2.2; return g*out
def ding(f=1318.5,d=.9,g=.3): t=T(d); return g*(np.sin(2*np.pi*f*t)+.4*np.sin(2*np.pi*f*2.76*t))*np.exp(-t*4.5)
def buzz(d=.35,g=.25): t=T(d); return g*lp(np.sign(np.sin(2*np.pi*95*t))+np.sign(np.sin(2*np.pi*101*t)),1200)*np.exp(-t*5)
def tick(f=2600,g=.10): t=T(.025); return g*np.sin(2*np.pi*f*t)*np.exp(-t*150)
def boom(g=.8): t=T(1.0); return g*np.sin(2*np.pi*(38+60*np.exp(-t*8))*t)*np.exp(-t*3.2)
def noteHz(m): return 440*2**((m-69)/12)
BPM=SPEC.get('bpm',108); beat=60/BPM
cuts=[1.9,4.9,8.3,12.3]
# S1 hook 0-1.9: boom + riser; hot tension
add(0,boom(.9)); add(.0,riser(1.8,.35))
# S2 bad prompt 1.9-4.9: sparse, detuned, only hats+sub, buzz on "Generic"
for t in np.arange(1.9,4.9,beat/2): add(t,hat(),.3,.7)
for t in np.arange(1.9,4.9,beat*2): add(t,bass(noteHz(33),.8))
add(4.2,buzz()); 
# S3 formula 4.9-8.3: beat enters
tr=SPEC.get('tr',0); prog=[45+tr,45+tr,41+tr,43+tr]  # A,A,F,G low
for bi,t in enumerate(np.arange(4.9,8.3,beat)):
    k=int((t-4.9)/beat)
    if k%2==0: add(t,kick())
    if k%2==1: add(t,snare(),-.1)
    add(t,hat(),.3); add(t+beat/2,hat(),-.3,.8)
    add(t,bass(noteHz(prog[(k//2)%4]),beat*.9))
# S4 good prompt 8.3-12.3: full groove + arp, rising feel
arp=[69,72,76,72,64,67,71,67]
for t in np.arange(8.3,12.3,beat):
    k=int(round((t-8.3)/beat))
    add(t,kick()); 
    if k%2==1: add(t,snare(),-.1)
    add(t,hat(),.3); add(t+beat/2,hat(True),-.3,.7)
    add(t,bass(noteHz(prog[(k//2)%4]),beat*.9))
for i,t in enumerate(np.arange(8.3,12.3,beat/2)):
    add(t,pluck(noteHz(arp[i%8]+ (0 if (i//8)%2==0 else -2))),(-.4 if i%2 else .4))
# typing ticks
s1=SPEC["p1"]; 
for i in range(len(s1)): add(2.2+i/22,tick(2400+rng.integers(-200,200)),.1)
s2=SPEC["p2"]
for i in range(len(s2)): add(8.6+i/44,tick(3000+rng.integers(-300,300),.07),-.1)
# role/task/format pops
for t in [5.1,6.1,7.1]: add(t,pluck(noteHz(81),.4,.4)); add(t,kick())
# result ding
add(11.3,ding()); add(12.0,ding(1568,1.0,.3))
# cut accents: riser into cut + impact
for c in cuts: add(c-.5,riser(.5,.22)); add(c,boom(.45))
# S5 CTA 12.3-15: resolve, warm chord + final hit
for f in (57,61,64,69): 
    t=T(2.7); add(12.3,.07*np.sin(2*np.pi*noteHz(f)*t)*np.minimum(1,t*8)*np.exp(-t*.9))
add(12.3,kick()); add(12.3+beat,kick()); add(12.3+beat*2,kick())
add(14.3,ding(1760,.6,.25))
# master
y=np.stack([L,R],1)
fade=np.minimum(1,(D-np.arange(n)/sr)/.5)[:,None]; y*=fade
y=np.tanh(y*1.3)/ np.tanh(1.3)
y/=np.abs(y).max()/0.88
w.write(f"tmp/{SPEC['name']}.wav",sr,(y*32767).astype(np.int16))
