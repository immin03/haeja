"""음악 시안 내려받기 (2026-11-06) — scripts/music/candidates.json 의 Pixabay 곡을 받아 45초 미리듣기로 자른다.
결과: social/music/samples/<key>.mp3 + social/music/samples/meta.json (페이지에서 읽은 BPM·조회·다운로드·Content ID 문구)
클라우드 작업 공간에서는 Pixabay에 닿지 않아 GitHub Actions(music-samples)에서 돌린다."""
import json, os, re, subprocess, sys, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "social", "music", "samples"); os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36", "Accept-Language": "en-US,en;q=0.9"}

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read()

def page_html(url):
    try: return get(url).decode("utf-8", "ignore")
    except Exception as e:
        print("  urllib 실패, 브라우저로:", e)
        js = "const {chromium}=require('playwright');(async()=>{const b=await chromium.launch();const p=await b.newPage({userAgent:%r});await p.goto(%r,{waitUntil:'domcontentloaded',timeout:60000});await p.waitForTimeout(4000);process.stdout.write(await p.content());await b.close()})()" % (UA["User-Agent"], url)
        return subprocess.run(["node", "-e", js], capture_output=True, text=True, timeout=120).stdout

cands = json.load(open(os.path.join(HERE, "candidates.json"), encoding="utf-8"))["tracks"]
meta = []
for c in cands:
    print("곡:", c["key"], c["title"], flush=True)
    html = page_html(c["url"]); m = dict(c)
    mp3 = re.findall(r'https://cdn\.pixabay\.com/(?:download/)?audio/[^"\'\s<>]+?\.mp3', html.replace("\\/", "/"))
    m["bpm"] = (re.search(r'(\d{2,3})\s*BPM', html) or [None, None])[1]
    m["content_id"] = bool(re.search(r'Content ID|contentid|registered with', html, re.I))
    for k in ("views", "downloads", "likes"):
        r = re.search(r'"%s"\s*:\s*(\d+)' % k, html); m[k] = int(r.group(1)) if r else None
    if not mp3: m["error"] = "mp3 주소 못 찾음"; meta.append(m); continue
    raw = os.path.join(OUT, c["key"] + "_full.mp3")
    try:
        open(raw, "wb").write(get(mp3[0]))
        dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", raw], capture_output=True, text=True).stdout.strip() or 0)
        st = 0 if c["role"] == "인트로" else min(20, max(0, dur - 50))
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(st), "-t", "45", "-i", raw, "-af", "afade=t=in:d=0.5,afade=t=out:st=42:d=3,loudnorm=I=-16:TP=-1.5", "-b:a", "128k", os.path.join(OUT, c["key"] + ".mp3")], check=True)
        m["duration"] = round(dur, 1); m["file"] = f"social/music/samples/{c['key']}.mp3"
    except Exception as e: m["error"] = str(e)[:200]
    finally:
        if os.path.exists(raw): os.remove(raw)
    meta.append(m)
json.dump(meta, open(os.path.join(OUT, "meta.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(meta, ensure_ascii=False, indent=1))
