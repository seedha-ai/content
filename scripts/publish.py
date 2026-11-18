"""Publish @seedha.ai posts from queue/ via the official Instagram Graph API, on the minute.

Folders: queue/YYYY-MM-DD[-a|-b]. Slot a posts at 12:30 IST, slot b at 19:00 IST
(a folder with no suffix is slot a).

A run that starts up to PREP_MIN minutes before a slot does all the slow work first
(uploads, Instagram processing), then waits and publishes at the exact slot time.
A run that starts late publishes straight away (catch-up).
One post per run. Writes published.json on success; failed.json counts failures
(a post is skipped after 2 failures so the queue keeps moving)."""
import json, os, sys, time, datetime, pathlib, urllib.request, urllib.parse

API = "https://graph.facebook.com/v21.0"
TOKEN = os.environ["IG_TOKEN"]
REPO = os.environ.get("GITHUB_REPOSITORY", "seedha-ai/content")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
ROOT = pathlib.Path(__file__).resolve().parent.parent
DRY = os.environ.get("DRY_RUN") == "1"

SLOT_TIME = {"": (12, 30), "a": (12, 30), "b": (19, 0)}  # IST
PREP_MIN = 75  # how early a run may start preparing a slot
IST = datetime.timedelta(hours=5, minutes=30)


def now_ist():
    o = os.environ.get("NOW_IST")  # test override, e.g. 2026-11-17T12:31
    if o:
        return datetime.datetime.fromisoformat(o)
    return datetime.datetime.utcnow() + IST


def call(method, path, params=None, data=None, headers=None, url=None):
    params = dict(params or {})
    u = url or f"{API}/{path}"
    if data is None:
        params["access_token"] = TOKEN
        body = urllib.parse.urlencode(params).encode() if method == "POST" else None
        if method == "GET":
            u += "?" + urllib.parse.urlencode(params)
    else:
        body = data
    req = urllib.request.Request(u, data=body, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        msg = e.read().decode()[:500]
        sys.exit(f"API error {e.code} on {method} {path or u.split('?')[0]}: {msg}")


def ig_user():
    d = call("GET", "me/accounts", {"fields": "name,instagram_business_account{id,username}"})
    for p in d.get("data", []):
        ig = p.get("instagram_business_account")
        if ig:
            print(f"Page {p['name']} -> @{ig.get('username')} ({ig['id']})")
            return ig["id"]
    sys.exit("No Instagram account found on token's Pages: " + json.dumps(d)[:300])


def wait_ready(cid, tries=180):
    for _ in range(tries):  # up to 30 min, reels can take a while
        s = call("GET", cid, {"fields": "status_code,status"})
        if s.get("status_code") == "FINISHED":
            return
        if s.get("status_code") in ("ERROR", "EXPIRED"):
            sys.exit(f"Container {cid} failed: {s}")
        time.sleep(10)
    sys.exit(f"Container {cid} not ready in time")


def slot_time(f):
    name = f.name
    try:
        d = datetime.date.fromisoformat(name[:10])
    except ValueError:
        return None
    slot = name[11:]
    if slot not in SLOT_TIME:
        return None
    hh, mm = SLOT_TIME[slot]
    return datetime.datetime.combine(d, datetime.time(hh, mm))


def due_folder():
    """Earliest unpublished post whose prep window has opened."""
    now = now_ist()
    for f in sorted((ROOT / "queue").iterdir()):
        at = slot_time(f)
        if at is None or now < at - datetime.timedelta(minutes=PREP_MIN):
            continue
        if not (f / "post.json").exists() or (f / "published.json").exists():
            continue
        fj = f / "failed.json"
        if fj.exists() and json.loads(fj.read_text()).get("attempts", 0) >= 2:
            continue
        return f, at
    return None, None


def prepare(f, ig):
    """Upload everything and wait until Instagram has processed it. Returns container id."""
    post = json.loads((f / "post.json").read_text())
    rel = f.relative_to(ROOT).as_posix()
    cap, t = post["caption"], post["type"]
    if t == "image":
        c = call("POST", f"{ig}/media", {"image_url": f"{RAW}/{rel}/{post['files'][0]}", "caption": cap})["id"]
    elif t == "carousel":
        kids = []
        for name in post["files"]:
            k = call("POST", f"{ig}/media", {"image_url": f"{RAW}/{rel}/{name}", "is_carousel_item": "true"})["id"]
            wait_ready(k); kids.append(k)
        c = call("POST", f"{ig}/media", {"media_type": "CAROUSEL", "children": ",".join(kids), "caption": cap})["id"]
    elif t == "reel":
        r = call("POST", f"{ig}/media", {"media_type": "REELS", "upload_type": "resumable", "caption": cap, "share_to_feed": "true"})
        c = r["id"]
        blob = (f / post["files"][0]).read_bytes()
        call("POST", None, data=blob, url=r["uri"], headers={
            "Authorization": f"OAuth {TOKEN}", "offset": "0", "file_size": str(len(blob))})
    else:
        sys.exit(f"Unknown type {t}")
    wait_ready(c)
    return c


def hold_until(at):
    left = (at - now_ist()).total_seconds()
    if left > 0:
        print(f"Ready. Holding {int(left)}s until {at:%H:%M} IST")
        time.sleep(left)


def main():
    f, at = due_folder()
    if not f:
        print("Nothing due."); return
    post = json.loads((f / "post.json").read_text())
    print(f"Next: {f.name} ({post['type']}) at {at:%Y-%m-%d %H:%M} IST, now {now_ist():%H:%M:%S} IST")
    if DRY:
        print("DRY_RUN: stop before uploading"); ig_user(); return
    try:
        ig = ig_user()
        c = prepare(f, ig)
        hold_until(at)
        m = call("POST", f"{ig}/media_publish", {"creation_id": c})["id"]
        info = call("GET", m, {"fields": "permalink,timestamp"})
    except SystemExit as e:
        fj = f / "failed.json"
        n = (json.loads(fj.read_text()).get("attempts", 0) if fj.exists() else 0) + 1
        fj.write_text(json.dumps({"attempts": n, "error": str(e.code)[:400]}, indent=1))
        print(f"FAILED (attempt {n}): {e.code}")
        raise
    (f / "published.json").write_text(json.dumps({"media_id": m, **info}, indent=1))
    print("Published:", info.get("permalink"), "at", now_ist().strftime("%H:%M:%S"), "IST")


if __name__ == "__main__":
    main()
