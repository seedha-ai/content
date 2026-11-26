"""Publish @seedha.ai posts from queue/ via the official Instagram Graph API, on the minute.

Folders: queue/YYYY-MM-DD[-a|-b|-c]. Slot a posts at 12:30 IST, slot b at 19:00 IST, slot c at 21:30 IST
(a folder with no suffix is slot a).

MODE=loop (default in the workflow): the run stays alive ~5.5 h, sleeps until 60 min before
each slot, uploads and lets Instagram process the post, then publishes on the exact minute.
At the end it starts the next run itself, so posting never depends on GitHub's cron timer.
It also saves account and post metrics to metrics/YYYY-MM-DD.json at 20:30 IST daily.
A run that starts late publishes straight away (catch-up).
One post per run. Writes published.json on success; failed.json counts failures
(a post is skipped after 2 failures so the queue keeps moving)."""
import json, os, sys, time, datetime, pathlib, subprocess, urllib.request, urllib.parse

API = "https://graph.facebook.com/v21.0"
TOKEN = os.environ["IG_TOKEN"]
REPO = os.environ.get("GITHUB_REPOSITORY", "seedha-ai/content")
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
RAW = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}"
ROOT = pathlib.Path(__file__).resolve().parent.parent
DRY = os.environ.get("DRY_RUN") == "1"

SLOT_TIME = {"": (12, 30), "a": (12, 30), "b": (19, 0), "c": (21, 30)}  # IST
PREP_MIN = 60  # start preparing a slot this many minutes early
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


def publish_one(f, at):
    post = json.loads((f / "post.json").read_text())
    print(f"Next: {f.name} ({post['type']}) at {at:%Y-%m-%d %H:%M} IST, now {now_ist():%H:%M:%S} IST", flush=True)
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
        print(f"FAILED (attempt {n}): {e.code}", flush=True)
        save(f"failed {f.name}")
        time.sleep(120)
        return
    (f / "published.json").write_text(json.dumps({"media_id": m, **info}, indent=1))
    print("Published:", info.get("permalink"), "at", now_ist().strftime("%H:%M:%S"), "IST", flush=True)
    write_status()
    save(f"published {f.name}")


# ---------- metrics (saved daily so analysis does not depend on scraping) ----------
MEDIA_METRICS = ["reach", "views", "saved", "shares", "likes", "comments", "total_interactions"]
REEL_METRICS = MEDIA_METRICS + ["ig_reels_avg_watch_time", "reels_skip_rate", "ig_reels_video_view_total_time"]
METRICS_AT = (20, 30)  # IST


def media_insights(mid, reel=False):
    out = {}
    if reel:  # retention metrics, asked one by one so one unsupported metric cannot hide the rest
        for x in ("ig_reels_avg_watch_time", "reels_skip_rate", "ig_reels_video_view_total_time"):
            u = f"{API}/{mid}/insights?" + urllib.parse.urlencode({"metric": x, "access_token": TOKEN})
            try:
                with urllib.request.urlopen(u, timeout=60) as r:
                    d = json.loads(r.read())
                for y in d.get("data", []):
                    out[y["name"]] = y["values"][0]["value"]
            except urllib.error.HTTPError as e:
                out[x + "_error"] = e.read().decode()[:120]
    for ms in (MEDIA_METRICS, ["reach", "saved", "shares", "likes", "comments"], ["reach"]):
        u = f"{API}/{mid}/insights?" + urllib.parse.urlencode({"metric": ",".join(ms), "access_token": TOKEN})
        try:
            with urllib.request.urlopen(u, timeout=60) as r:
                d = json.loads(r.read())
            out.update({x["name"]: x["values"][0]["value"] for x in d.get("data", [])})
            return out
        except urllib.error.HTTPError as e:
            err = e.read().decode()[:200]
    out["error"] = err
    return out


def collect_metrics():
    ig = ig_user()
    acct = call("GET", ig, {"fields": "username,followers_count,follows_count,media_count"})
    media = call("GET", f"{ig}/media", {"fields": "id,media_type,media_product_type,permalink,timestamp,like_count,comments_count,caption", "limit": "100"}).get("data", [])
    posts = []
    for m in media:
        row = {k: m.get(k) for k in ("id", "media_type", "media_product_type", "permalink", "timestamp", "like_count", "comments_count")}
        row["hook"] = (m.get("caption") or "").split("\n")[0][:90]
        row["insights"] = media_insights(m["id"], reel=m.get("media_product_type") == "REELS")
        posts.append(row)
    snap = {"at_ist": now_ist().strftime("%Y-%m-%d %H:%M"), "account": acct, "posts": posts}
    d = ROOT / "metrics"; d.mkdir(exist_ok=True)
    (d / f"{now_ist():%Y-%m-%d}.json").write_text(json.dumps(snap, indent=1, ensure_ascii=False))
    (d / "latest.json").write_text(json.dumps(snap, indent=1, ensure_ascii=False))
    write_status()
    print(f"Metrics saved: {acct.get('followers_count')} followers, {len(posts)} posts", flush=True)
    save("metrics " + now_ist().strftime("%Y-%m-%d"))


def metrics_due():
    n = now_ist()
    return n.time() >= datetime.time(*METRICS_AT) and not (ROOT / "metrics" / f"{n:%Y-%m-%d}.json").exists()


def write_status():
    """metrics/status.json: queue health, readable from raw.githubusercontent.com without the GitHub API."""
    q = []
    for f in sorted((ROOT / "queue").iterdir()):
        at = slot_time(f)
        if at is None or not (f / "post.json").exists():
            continue
        st = "published" if (f / "published.json").exists() else ("failed" if (f / "failed.json").exists() else "queued")
        row = {"folder": f.name, "due_ist": at.strftime("%Y-%m-%d %H:%M"), "status": st}
        if st == "published":
            row.update(json.loads((f / "published.json").read_text()))
        if st == "failed":
            row["error"] = json.loads((f / "failed.json").read_text()).get("error", "")[:200]
        q.append(row)
    queued = [r for r in q if r["status"] == "queued"]
    days = sorted({r["due_ist"][:10] for r in queued})
    snap = {"updated_ist": now_ist().strftime("%Y-%m-%d %H:%M"), "queued_count": len(queued), "queued_days": len(days),
            "last_queued_day": days[-1] if days else None, "next": queued[0] if queued else None,
            "failed": [r for r in q if r["status"] == "failed"], "recent_published": [r for r in q if r["status"] == "published"][-6:]}
    d = ROOT / "metrics"; d.mkdir(exist_ok=True)
    (d / "status.json").write_text(json.dumps(snap, indent=1))


# ---------- git + loop ----------
def git(*a):
    return subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True)


def sync():
    git("pull", "--rebase", "-q")


def save(msg):
    if not os.environ.get("GITHUB_ACTIONS"):
        return
    git("add", "queue", "metrics")
    if git("diff", "--cached", "--quiet").returncode == 0:
        return
    git("commit", "-qm", msg)
    for _ in range(3):
        if git("pull", "--rebase", "-q").returncode == 0 and git("push", "-q").returncode == 0:
            return
        time.sleep(5)
    print("WARN: could not push", msg, flush=True)


def loop(budget_min):
    """Stay alive up to budget_min minutes: sleep until each prep window, post on the minute."""
    end = time.time() + budget_min * 60
    last_post = 0
    while time.time() < end - 60:
        sync()
        if metrics_due():
            try:
                collect_metrics()
            except SystemExit as e:
                print("metrics failed:", e.code, flush=True)
                d = ROOT / "metrics"; d.mkdir(exist_ok=True)
                (d / f"{now_ist():%Y-%m-%d}.json").write_text(json.dumps({"error": str(e.code)[:400]}))
                save("metrics failed")
            continue
        f, at = due_folder()
        if f:
            gap = time.time() - last_post
            if at < now_ist() and gap < 45 * 60:  # overdue backlog: keep 45 min between posts
                time.sleep(min(45 * 60 - gap, max(5, end - 60 - time.time())))
                continue
            publish_one(f, at)
            last_post = time.time()
            continue
        # sleep until the next prep window, metrics time, or end of budget (check every 15 min for new queue items)
        nxt = next_event()
        wait = min(15 * 60, end - 60 - time.time())
        if nxt is not None:
            wait = min(wait, max(5, (nxt - now_ist()).total_seconds()))
        print(f"{now_ist():%H:%M} IST idle, next check in {int(wait)}s", flush=True)
        time.sleep(max(5, wait))


def next_event():
    now = now_ist()
    cands = []
    for f in sorted((ROOT / "queue").iterdir()):
        at = slot_time(f)
        if at and (f / "post.json").exists() and not (f / "published.json").exists():
            cands.append(at - datetime.timedelta(minutes=PREP_MIN))
    m = datetime.datetime.combine(now.date(), datetime.time(*METRICS_AT))
    if now >= m:
        m += datetime.timedelta(days=1)
    cands.append(m)
    return min(cands)


def main():
    mode = os.environ.get("MODE", "once")
    if mode == "metrics":
        collect_metrics(); return
    if mode == "loop" and not DRY:
        loop(int(os.environ.get("BUDGET_MIN", "330"))); return
    f, at = due_folder()
    if not f:
        print("Nothing due."); return
    publish_one(f, at)


if __name__ == "__main__":
    main()
