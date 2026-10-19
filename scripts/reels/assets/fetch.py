"""무료 영상 소스·효과음 후보 받기 (GitHub Actions에서 실행: 작업 공간에서는 사이트 접속이 막혀 있다)
영상: Mixkit 클립 → 세로 1080x1920, 6초, 소리 없음 → assets/broll/<주제>_<번호>.mp4
효과음: Mixkit 분류 페이지에서 앞쪽 8개 → assets/sfx_cand/<분류>_<n>.mp3 + index.json(제목)
"""
import json, os, re, subprocess, urllib.request, html
HERE = os.path.dirname(os.path.abspath(__file__))
M = json.load(open(os.path.join(HERE, "manifest.json")))
UA = {"User-Agent": "Mozilla/5.0 (valuenote reels)"}
def get(url, path=None):
    r = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
    if path: open(path, "wb").write(r)
    return r
os.makedirs(os.path.join(HERE, "broll"), exist_ok=True); os.makedirs(os.path.join(HERE, "sfx_cand"), exist_ok=True)
for key, ids in M["video"].items():
    for vid in ids:
        out = os.path.join(HERE, "broll", f"{key}_{vid}.mp4")
        if os.path.exists(out): continue
        raw = f"/tmp/{vid}.mp4"; ok = False
        for q in ("1080", "720"):
            try: get(f"https://assets.mixkit.co/videos/{vid}/{vid}-{q}.mp4", raw); ok = True; break
            except Exception as e: print("  실패", vid, q, e)
        if not ok: continue
        # 가로 영상 가운데를 세로로 잘라 1080x1920, 1초 지점부터 6초, 30fps, 소리 없음
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", "1", "-i", raw, "-t", "6", "-an",
                        "-vf", "crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',scale=1080:1920,fps=30,format=yuv420p",
                        "-c:v", "libx264", "-crf", "27", "-preset", "slow", "-movflags", "+faststart", out], check=True)
        print("영상", out, os.path.getsize(out) // 1024, "KB")
idx = {}
for cat in M["sfx"]:
    try: page = get(f"https://mixkit.co/free-sound-effects/{cat}/").decode("utf-8", "ignore")
    except Exception as e: print("  페이지 실패", cat, e); continue
    urls = list(dict.fromkeys(re.findall(r"https://assets\.mixkit\.co/active_storage/sfx/\d+/\d+-preview\.mp3", page)))
    titles = [html.unescape(t).strip() for t in re.findall(r'item-grid-card__title[^>]*>\s*([^<]+)<', page)]
    for i, u in enumerate(urls[:8]):
        p = os.path.join(HERE, "sfx_cand", f"{cat}_{i}.mp3")
        try: get(u, p); idx[f"{cat}_{i}"] = {"url": u, "title": titles[i] if i < len(titles) else ""}
        except Exception as e: print("  효과음 실패", u, e)
    print("효과음", cat, len(urls))
json.dump(idx, open(os.path.join(HERE, "sfx_cand", "index.json"), "w"), ensure_ascii=False, indent=1)
