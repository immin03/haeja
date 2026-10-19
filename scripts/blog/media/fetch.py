"""블로그용 무료 실사 사진·영상 받기 (GitHub Actions에서 실행: 작업 공간에서는 Mixkit 접속이 막혀 있다)

출처: Mixkit Stock Video Free License — 상업적 이용 가능, 출처 표기 불필요.
사진은 영상의 한 장면(1280x720 JPG)을 뽑아 쓴다. 영상은 8초, 1280x720, 소리 없음 MP4.
(선택) GitHub 저장소 Secrets 에 PEXELS_API_KEY 가 있으면 Pexels 사진(Pexels License, 상업적 이용 가능·출처 표기 불필요)도 받는다.

wants.json = {
  "ids":  {"<이름>": [[mixkit 영상 번호, "영상 제목"], ...]},  # 글에 쓸 장면을 골라 둔 것 → 사진 2장 + 영상 1개씩
  "tags": {"<mixkit 태그>": 3},                    # 태그 페이지 앞쪽 N개 → 사진 2장씩 (공용 사진 창고)
  "pexels": {"<검색어>": 3}                        # PEXELS_API_KEY 가 있을 때만
}
결과: lib/<이름>_<번호>_a.jpg, _b.jpg, lib/<이름>_<번호>.mp4, lib/index.json (파일 → 제목·원본 주소·라이선스)
"""
import json, os, re, subprocess, urllib.request, urllib.parse, html

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "lib")
os.makedirs(LIB, exist_ok=True)
W = json.load(open(os.path.join(HERE, "wants.json")))
IDX_P = os.path.join(LIB, "index.json")
IDX = json.load(open(IDX_P)) if os.path.exists(IDX_P) else {}
UA = {"User-Agent": "Mozilla/5.0 (valuenote blog media)"}
MIXKIT_LIC = "Mixkit Stock Video Free License (상업적 이용 가능, 출처 표기 불필요)"


def get(url, path=None, headers=None):
    r = urllib.request.urlopen(urllib.request.Request(url, headers={**UA, **(headers or {})}), timeout=90).read()
    if path:
        open(path, "wb").write(r)
    return r


TITLES = {}


def tag_page(tag):
    page = get(f"https://mixkit.co/free-stock-video/{tag}/").decode("utf-8", "ignore")
    out = []
    for slug, vid in re.findall(r'/free-stock-video/([a-z0-9-]+)-(\d+)/', page):
        if vid not in [v for v, _ in out]:
            out.append((vid, slug.replace("-", " ")))
    return out


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", *args], check=True)


def mixkit(name, vid, title="", video=False):
    base = f"{name}_{vid}"
    a, b, mp4 = (os.path.join(LIB, base + s) for s in ("_a.jpg", "_b.jpg", ".mp4"))
    if os.path.exists(a) and (not video or os.path.exists(mp4)):
        return
    raw = f"/tmp/{vid}.mp4"
    if not os.path.exists(raw):
        for q in ("1080", "720"):
            try:
                get(f"https://assets.mixkit.co/videos/{vid}/{vid}-{q}.mp4", raw)
                break
            except Exception as e:
                print("  실패", vid, q, e)
        else:
            return
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", raw],
                               capture_output=True, text=True).stdout.strip() or 8)
    vf = "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720"
    for p, at in ((a, 0.3), (b, 0.7)):
        ff("-ss", f"{dur * at:.2f}", "-i", raw, "-frames:v", "1", "-vf", vf, "-q:v", "3", p)
    if video:
        ff("-ss", f"{min(1, dur * 0.1):.2f}", "-i", raw, "-t", "8", "-an", "-vf", vf + ",fps=30,format=yuv420p",
           "-c:v", "libx264", "-crf", "28", "-preset", "slow", "-movflags", "+faststart", mp4)
    src = f"https://mixkit.co/free-stock-video/{vid}/"
    for p in (a, b) + ((mp4,) if video else ()):
        IDX[os.path.basename(p)] = {"title": title or TITLES.get(vid, ""), "src": src, "id": f"mixkit:{vid}", "license": MIXKIT_LIC}
    print("받음", base, "영상" if video else "")


# 1) 글마다 골라 둔 장면 (사진 2장 + 영상)
for name, ids in W.get("ids", {}).items():
    for it in ids:
        vid, title = (it if isinstance(it, list) else [it, ""])
        try:
            mixkit(name, str(vid), title=title, video=True)
        except Exception as e:
            print("  오류", name, vid, e)

# 2) 공용 사진 창고 (태그 앞쪽 N개, 사진만)
for tag, n in W.get("tags", {}).items():
    try:
        items = tag_page(tag)
    except Exception as e:
        print("  태그 실패", tag, e)
        continue
    for vid, title in items[:n]:
        TITLES[vid] = title
        try:
            mixkit(tag.replace("-", ""), vid, title=title)
        except Exception as e:
            print("  오류", tag, vid, e)

# 제목이 비어 있는 것은 태그 페이지에서 본 제목으로 채운다
for k, v in IDX.items():
    vid = v.get("id", "").split(":")[-1]
    if not v.get("title") and vid in TITLES:
        v["title"] = TITLES[vid]

# 3) (선택) Pexels 사진
KEY = os.environ.get("PEXELS_API_KEY", "")
if KEY:
    for q, n in W.get("pexels", {}).items():
        try:
            r = json.loads(get(f"https://api.pexels.com/v1/search?query={urllib.parse.quote(q)}&per_page={n}&orientation=landscape",
                               headers={"Authorization": KEY}))
        except Exception as e:
            print("  Pexels 실패", q, e)
            continue
        for ph in r.get("photos", []):
            f = f"px{re.sub(r'[^a-z0-9]', '', q.lower())}_{ph['id']}.jpg"
            p = os.path.join(LIB, f)
            if os.path.exists(p):
                continue
            raw = f"/tmp/px{ph['id']}.jpg"
            get(ph["src"]["large2x"], raw)
            ff("-i", raw, "-vf", "scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720", "-q:v", "3", p)
            IDX[f] = {"title": ph.get("alt", ""), "src": ph["url"], "id": f"pexels:{ph['id']}",
                      "license": "Pexels License (상업적 이용 가능, 출처 표기 불필요)"}
            print("받음", f)
else:
    print("PEXELS_API_KEY 없음: Pexels 사진은 건너뜀")

json.dump(dict(sorted(IDX.items())), open(IDX_P, "w"), ensure_ascii=False, indent=1)
print("창고", len(IDX), "개")
