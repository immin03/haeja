"""황제의 밤 편지(롱폼) 효과음·음악 후보 받기 (2026-11-03)
GitHub Actions(side-gen, music.py 단계)에서 실행된다. 작업 공간에서는 사이트 접속이 막혀 있다.
Mixkit 무료 라이선스(상업 이용 가능, 저작자 표시 불필요) 소스만 받는다.
결과: social/side/ed_long/sfx/<분류>_<n>.mp3, social/side/ed_long/music/<분류>_<n>.mp3, 각 폴더 index.json(제목·원본 주소)
"""
import html, json, os, re, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(ROOT, "social", "side", "ed_long")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}
SFX = ["wind", "fire", "horse", "paper", "drum", "cinematic", "heartbeat", "whoosh", "swords", "war", "night", "rain", "impact", "transition"]
MUSIC = ["https://mixkit.co/free-stock-music/mood/dramatic/", "https://mixkit.co/free-stock-music/mood/sad/",
         "https://mixkit.co/free-stock-music/tag/cinematic/", "https://mixkit.co/free-stock-music/tag/epic/"]


def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r: return r.read()


def grab(page, pat, n, folder, key, idx):
    try: s = get(page).decode("utf-8", "ignore")
    except Exception as e: print("페이지 실패", page, e); return
    urls = list(dict.fromkeys(re.findall(pat, s)))
    titles = [html.unescape(t).strip() for t in re.findall(r'item-grid-card__title[^>]*>\s*([^<]+)<', s)]
    for i, u in enumerate(urls[:n]):
        name = f"{key}_{i}.mp3"; p = os.path.join(folder, name)
        if os.path.exists(p): continue
        try: open(p, "wb").write(get(u)); idx[name] = {"title": titles[i] if i < len(titles) else "", "src": u, "page": page}
        except Exception as e: print("  실패", u, e)
    print(key, len(urls), flush=True)


def main():
    sd, md = os.path.join(OUT, "sfx"), os.path.join(OUT, "music"); os.makedirs(sd, exist_ok=True); os.makedirs(md, exist_ok=True)
    si = json.load(open(os.path.join(sd, "index.json"))) if os.path.exists(os.path.join(sd, "index.json")) else {}
    mi = json.load(open(os.path.join(md, "index.json"))) if os.path.exists(os.path.join(md, "index.json")) else {}
    for c in SFX:
        grab(f"https://mixkit.co/free-sound-effects/{c}/", r"https://assets\.mixkit\.co/active_storage/sfx/\d+/\d+-preview\.mp3", 8, sd, c, si)
    for p in MUSIC:
        key = p.rstrip("/").split("/")[-1]
        grab(p, r"https://assets\.mixkit\.co/music/[^\"'\s]+?\.mp3", 6, md, key, mi)
    json.dump(si, open(os.path.join(sd, "index.json"), "w"), ensure_ascii=False, indent=1)
    json.dump(mi, open(os.path.join(md, "index.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
