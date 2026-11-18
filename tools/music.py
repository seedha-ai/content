"""Original background track for slide reels: beat + whoosh on each cut. music.py out.wav duration bpm transpose cut1,cut2,..."""
import sys, numpy as np, scipy.io.wavfile as w
from scipy.signal import butter, lfilter
out=sys.argv[1]; D=float(sys.argv[2]); BPM=float(sys.argv[3]); tr=int(sys.argv[4]); cuts=[float(x) for x in sys.argv[5].split(",") if x]
sr=44100; n=int(D*sr); rng=np.random.default_rng(int(BPM*7+tr))
L=np.zeros(n); R=np.zeros(n)
def add(t,s,pan=0.0,g=1.0):
    i=int(t*sr)
    if i>=n or i<0: return
    s=s[:n-i]; L[i:i+len(s)]+=s*g*(1-max(pan,0)); R[i:i+len(s)]+=s*g*(1+min(pan,0))
def T(d): return np.arange(int(d*sr))/sr
def lp(x,f): b,a=butter(2,f/(sr/2)); return lfilter(b,a,x)
def hp(x,f): b,a=butter(2,f/(sr/2),'high'); return lfilter(b,a,x)
def kick(): t=T(.35); return .9*np.sin(2*np.pi*(48+110*np.exp(-t*28))*t)*np.exp(-t*9)
def hat(o=False): d=.18 if o else .05; t=T(d); return .2*hp(rng.standard_normal(len(t)),7000)*np.exp(-t*(18 if o else 70))
def snare(): t=T(.2); return .32*(hp(rng.standard_normal(len(t)),1500)*np.exp(-t*24)+.5*np.sin(2*np.pi*190*t)*np.exp(-t*30))
def bass(f,d=.4): t=T(d); return .36*np.tanh(2*np.sin(2*np.pi*f*t))*np.exp(-t*4)*np.minimum(1,t*200)
def pluck(f,d=.5,g=.16): t=T(d); x=sum(np.sin(2*np.pi*f*k*t)/k for k in (1,2,3)); return g*lp(x,3500)*np.exp(-t*7)
def whoosh(d=.35,g=.22):
    t=T(d); env=np.sin(np.pi*t/d)**2; return g*lp(hp(rng.standard_normal(len(t)),900),6000)*env
def boom(g=.8): t=T(1.0); return g*np.sin(2*np.pi*(38+60*np.exp(-t*8))*t)*np.exp(-t*3.2)
def nz(m): return 440*2**((m-69)/12)
beat=60/BPM; prog=[45,45,41,43]; prog=[p+tr for p in prog]
arp=[69,72,76,72,64,67,71,67]
add(0,boom(.85))
k=0
for t in np.arange(0,D-.3,beat):
    full=t>=(cuts[0] if cuts else 0)
    if full or k%2==0: add(t,kick(),0,.9 if full else .6)
    if full and k%2==1: add(t,snare(),-.1)
    add(t,hat(),.3); add(t+beat/2,hat(k%4==3),-.3,.7)
    add(t,bass(nz(prog[(k//2)%4]+tr*0),beat*.9))
    if full: add(t,pluck(nz(arp[(2*k)%8]+tr)),.4); add(t+beat/2,pluck(nz(arp[(2*k+1)%8]+tr)),-.4)
    k+=1
for c in cuts: add(c-.18,whoosh()); add(c,kick(),0,.5)
y=np.stack([L,R],1)
fade=np.minimum(1,(D-np.arange(n)/sr)/.6)[:,None]; y*=fade
y=np.tanh(y*1.25)/np.tanh(1.25); y/=np.abs(y).max()/0.85
w.write(out,sr,(y*32767).astype(np.int16))
