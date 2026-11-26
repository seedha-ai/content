"""Fast-hook reels (v4). Built after metrics showed ~90% of viewers skipped our reels in the first 3 s.

Rules baked in:
- Frame 0 already shows the hook: huge bold text on Haldi yellow. No fade-in, no empty frames.
- Something moves every ~0.5 s. Total length 8 to 10 s, ends on a frame that loops into the start.
Kinds:
  fix:   hook -> "what you type" bubble + generic reply (stamped) -> "type this" bubble + better reply -> CTA
  list:  hook -> one big numbered card per item -> CTA
  trick: hook -> "instead of" -> "say this" -> CTA
Usage: python3 fast_reel.py spec.json out.mp4
"""
import sys, json, os, subprocess, math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FD = os.path.join(HERE, "fonts") if os.path.isdir(os.path.join(HERE, "fonts")) else "/mnt/user-data/outputs/seedha-repo/tools/fonts"
W, H, FPS = 1080, 1920, 30
INK, HALDI, CHALK, MUTE = (22, 22, 74), (245, 184, 0), (244, 246, 250), (176, 182, 214)
RED, GREEN, BUB = (229, 72, 77), (46, 160, 90), (255, 255, 255)
BOLD = lambda s: ImageFont.truetype(f"{FD}/InstrumentSans-Bold.ttf", s)
REG = lambda s: ImageFont.truetype(f"{FD}/InstrumentSans-Regular.ttf", s)
SERIF = lambda s: ImageFont.truetype(f"{FD}/InstrumentSerif-Regular.ttf", s)


def wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) <= maxw:
            cur = t
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines


def fit(d, text, maxw, maxh, start=150, minsize=60, face=BOLD, lh=1.05):
    s = start
    while s > minsize:
        f = face(s); ls = wrap(d, text, f, maxw)
        if len(ls) * s * lh <= maxh and all(d.textlength(l, font=f) <= maxw for l in ls):
            return f, ls, s
        s -= 6
    f = face(minsize); return f, wrap(d, text, f, maxw), minsize


def ease(x): x = max(0, min(1, x)); return 1 - (1 - x) ** 3


def pop(t0, t, dur=0.18):
    """scale for a pop-in that starts at t0 (1.0 when settled, small overshoot)."""
    x = (t - t0) / dur
    if x <= 0: return 0
    if x >= 1: return 1
    return 0.6 + 0.5 * math.sin(x * math.pi / 2) - 0.1 * math.sin(x * math.pi)


def handle(d, color):
    f = BOLD(40); d.text((W // 2, 120), "@seedha.ai", font=f, fill=color, anchor="mm")


def hook_frame(spec, t):
    im = Image.new("RGB", (W, H), HALDI); d = ImageDraw.Draw(im)
    handle(d, INK)
    f, ls, s = fit(d, spec["hook"], W - 140, 900, start=168)
    words = " ".join(ls).split()
    # word-by-word pop; first 2 words visible at frame 0
    shown = 10 ** 6
    y = H // 2 - len(ls) * s * 1.05 / 2 - 60
    k = 0
    for line in ls:
        lw = line.split(); x = (W - d.textlength(line, font=f)) / 2
        for w in lw:
            if k < shown:
                d.text((x, y), w, font=f, fill=INK)
            x += d.textlength(w + " ", font=f); k += 1
        y += s * 1.05
    if spec.get("sub"):
        f2, ls2, s2 = fit(d, spec["sub"], W - 200, 220, start=64, minsize=44, face=REG)
        yy = y + 40
        for l in ls2:
            d.text((W // 2, yy), l, font=f2, fill=INK, anchor="ma"); yy += s2 * 1.2
    # moving underline bar so the frame is never still
    bw = int((W - 280) * min(1, t / 1.2))
    d.rectangle([140, H - 380, 140 + bw, H - 366], fill=INK)
    z = 1.08 - 0.08 * ease(t / 1.4)  # push-in so frame 0 already moves
    if z > 1.001:
        zw, zh = int(W * z), int(H * z)
        im = im.resize((zw, zh)).crop(((zw - W) // 2, (zh - H) // 2, (zw - W) // 2 + W, (zh - H) // 2 + H))
    return im


def bubble(im, d, x, y, w, text, font, fill, fg, label=None, labfg=None, pad=44, lh=1.25, cursor=False, scale=1.0):
    ls = wrap(d, text, font, w - 2 * pad) or [""]
    fs = font.size
    h = int(len(ls) * fs * lh + 2 * pad + (60 if label else 0))
    if scale < 1:
        cx, cy = x + w / 2, y + h / 2
        w2, h2 = w * scale, h * scale
        d.rounded_rectangle([cx - w2 / 2, cy - h2 / 2, cx + w2 / 2, cy + h2 / 2], 36, fill=fill)
        return h
    d.rounded_rectangle([x, y, x + w, y + h], 36, fill=fill)
    yy = y + pad
    if label:
        d.text((x + pad, yy), label, font=BOLD(34), fill=labfg); yy += 60
    for i, l in enumerate(ls):
        d.text((x + pad, yy), l, font=font, fill=fg)
        if cursor and i == len(ls) - 1:
            cx = x + pad + d.textlength(l, font=font) + 6
            d.rectangle([cx, yy + 6, cx + 5, yy + fs], fill=HALDI)
        yy += fs * lh
    return h


def stamp(d, text, color, cx, cy, sc):
    if sc <= 0: return
    f = BOLD(int(84 * sc))
    tw = d.textlength(text, font=f)
    d.rounded_rectangle([cx - tw / 2 - 36, cy - 70 * sc, cx + tw / 2 + 36, cy + 70 * sc], 24, outline=color, width=10, fill=None)
    d.text((cx, cy), text, font=f, fill=color, anchor="mm")


def pill(d, text, color, y, mark=None):
    f = BOLD(46); tw = d.textlength(text, font=f); ex = 70 if mark else 0
    d.rounded_rectangle([90, y, 90 + tw + 70 + ex, y + 84], 42, fill=color)
    x = 125
    if mark == "x":
        d.line([x, y + 26, x + 32, y + 58], fill=CHALK, width=9); d.line([x, y + 58, x + 32, y + 26], fill=CHALK, width=9)
    if mark == "tick":
        d.line([x, y + 44, x + 12, y + 58, x + 36, y + 26], fill=CHALK, width=9, joint="curve")
    d.text((x + ex, y + 42), text, font=f, fill=CHALK, anchor="lm")


def typed(text, t0, t, cps):
    n = int(max(0, t - t0) * cps)
    return text[:n], n < len(text)


def fix_frame(spec, T, t):
    im = Image.new("RGB", (W, H), INK); d = ImageDraw.Draw(im)
    handle(d, MUTE)
    tb = T["bad"]; tg = T["good"]
    if t < tg:  # bad section
        pill(d, "What most people type", RED, 440, mark="x")
        txt, cur = typed(spec["bad_prompt"], tb + 0.1, t, 34)
        h = bubble(im, d, 70, 600, W - 140, txt or " ", BOLD(72), BUB, INK, label="You", labfg=MUTE, cursor=cur)
        if t > tb + 0.25 + len(spec["bad_prompt"]) / 34:
            sc = pop(tb + 0.3 + len(spec["bad_prompt"]) / 34, t)
            bubble(im, d, 70, 600 + h + 40, W - 140, spec["bad_reply"], REG(56), (44, 44, 104), CHALK, label="AI", labfg=MUTE, scale=sc if sc < 1 else 1)
        stamp(d, spec.get("bad_stamp", "Generic."), RED, W // 2, 1640, pop(tg - 0.85, t))
    else:
        pill(d, "Type this instead", GREEN, 360, mark="tick")
        txt, cur = typed(spec["good_prompt"], tg + 0.05, t, 75)
        h = bubble(im, d, 70, 520, W - 140, txt or " ", BOLD(60), BUB, INK, label="You", labfg=MUTE, cursor=cur)
        t_reply = tg + 0.15 + len(spec["good_prompt"]) / 75
        if t > t_reply:
            sc = pop(t_reply, t)
            bubble(im, d, 70, 520 + h + 40, W - 140, spec["good_reply"], REG(54), HALDI, INK, label="AI", labfg=INK, scale=sc if sc < 1 else 1)
        stamp(d, spec.get("good_stamp", "Better."), GREEN, W // 2, 1680, pop(T["cta"] - 0.8, t))
    return im


def card_frame(kicker, text, idx, total, t_in, t, light=False):
    bg, fg = (CHALK, INK) if light else (INK, CHALK)
    im = Image.new("RGB", (W, H), bg); d = ImageDraw.Draw(im)
    handle(d, INK if light else MUTE)
    # progress dots
    for i in range(total):
        x = W // 2 - (total - 1) * 30 + i * 60
        d.ellipse([x - 12, 230 - 12, x + 12, 230 + 12], fill=HALDI if i <= idx else (MUTE if not light else (190, 190, 210)))
    sc = pop(t_in, t, 0.16)
    if kicker:
        f = BOLD(96); d.text((W // 2, 520), kicker, font=f, fill=HALDI if not light else (154, 107, 0), anchor="mm")
    f, ls, s = fit(d, text, W - 140, 820, start=112, minsize=62, face=BOLD, lh=1.12)
    y = H // 2 - len(ls) * s * 1.12 / 2 + 40
    off = int((1 - min(1, sc)) * 80)
    for l in ls:
        d.text((W // 2, y + off), l, font=f, fill=fg, anchor="ma"); y += s * 1.12
    return im


def cta_frame(spec, t0, t):
    im = Image.new("RGB", (W, H), HALDI); d = ImageDraw.Draw(im)
    handle(d, INK)
    f, ls, s = fit(d, spec.get("cta", "Save this. Send it to a friend."), W - 160, 600, start=120)
    y = H // 2 - len(ls) * s * 1.05 / 2 - 80
    for l in ls:
        d.text((W // 2, y), l, font=f, fill=INK, anchor="ma"); y += s * 1.05
    sc = pop(t0 + 0.2, t)
    if sc:
        f2 = BOLD(int(76 * min(1, sc)))
        d.text((W // 2, y + 110), "Follow for 1 AI trick daily", font=f2, fill=INK, anchor="ma")
    return im


def build(spec):
    k = spec["kind"]
    if k == "fix":
        T = {"bad": 1.5}
        T["good"] = T["bad"] + 0.3 + len(spec["bad_prompt"]) / 34 + 0.25 + 1.4
        T["cta"] = T["good"] + 0.15 + len(spec["good_prompt"]) / 75 + 1.9
        D = T["cta"] + 1.4
        cuts = [T["bad"], T["good"], T["cta"]]
        def frame(t):
            if t < T["bad"]: return hook_frame(spec, t)
            if t < T["cta"]: return fix_frame(spec, T, t)
            return cta_frame(spec, T["cta"], t)
    elif k == "list":
        items = spec["items"]; per = spec.get("per", 1.7)
        t0 = 1.5; cuts = [t0 + i * per for i in range(len(items))] + [t0 + len(items) * per]
        D = cuts[-1] + 1.4
        def frame(t):
            if t < t0: return hook_frame(spec, t)
            i = int((t - t0) // per)
            if i < len(items):
                kk, tx = items[i]
                return card_frame(kk, tx, i, len(items), t0 + i * per, t, light=(i % 2 == 1))
            return cta_frame(spec, cuts[-1], t)
    elif k == "trick":
        t0 = 1.5; t1 = t0 + 2.2; t2 = t1 + 2.8
        cuts = [t0, t1, t2]; D = t2 + 1.4
        def frame(t):
            if t < t0: return hook_frame(spec, t)
            if t < t1: return card_frame("Instead of", spec["bad"], 0, 2, t0, t)
            if t < t2: return card_frame("Say this", spec["good"], 1, 2, t1, t, light=True)
            return cta_frame(spec, t2, t)
    else:
        raise SystemExit("unknown kind " + k)
    return frame, D, cuts


def render(spec, out):
    frame, D, cuts = build(spec)
    wav = out[:-4] + ".wav"
    subprocess.run(["python3", os.path.join(os.path.dirname(os.path.abspath(__file__)), "music.py"), wav, f"{D:.2f}",
                    str(spec.get("bpm", 118)), str(spec.get("tr", 0)), ",".join(f"{c:.3f}" for c in cuts)], check=True)
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
                          "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for i in range(int(D * FPS)):
        p.stdin.write(np.asarray(frame(i / FPS)).tobytes())
    p.stdin.close(); p.wait(); os.remove(wav)
    return D


if __name__ == "__main__":
    spec = json.load(open(sys.argv[1]))
    print(sys.argv[2], f"{render(spec, sys.argv[2]):.1f}s")
