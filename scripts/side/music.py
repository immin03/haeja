"""What Korea Says — 배경음악 후보 (Mixkit 무료 음악, 저작자 표시 불필요 라이선스) (2026-10-27)
Mixkit 분위기 페이지에서 곡 주소를 모아 원하는 제목만 받아 릴리스 side-assets 에 music_<slug>.mp3 로 올린다
결과: social/side/music.json [{title, slug, src, url, sec}]
"""
import html, json, os, re, subprocess, urllib.request

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "social", "side"); os.makedirs(OUT, exist_ok=True)
REPO = os.environ.get("GITHUB_REPOSITORY", "immin03/haeja")
PAGES = ["https://mixkit.co/free-stock-music/mood/quirky/", "https://mixkit.co/free-stock-music/mood/quirky/?page=2",
         "https://mixkit.co/free-stock-music/mood/playful/", "https://mixkit.co/free-stock-music/tag/ukulele/"]
WANT = ["comical", "kidding around", "fun and games", "keep smiling", "owies ukulele", "be happy 2", "gummies",
        "secret garden", "happy and all that", "goo lee goo lee yup"]
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}


def get(u):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60) as r: return r.read().decode("utf-8", "replace")


def main():
    found = {}
    for p in PAGES:
        try: s = get(p)
        except Exception as e: print("못 읽음", p, e); continue
        # 곡 카드마다 제목과 미리듣기 mp3 주소가 같이 있다 — 카드 단위로 자른다
        for block in re.split(r'<div[^>]+class="[^"]*item-grid__item', s)[1:]:
            mp3 = re.search(r'https://assets\.mixkit\.co/music/[^"\'\s]+?\.mp3', block)
            t = re.search(r'item-grid-card__title[^>]*>\s*([^<]+)<', block)
            if mp3 and t: found.setdefault(html.unescape(t.group(1)).strip(), mp3.group(0))
        if not found:  # 구조가 바뀐 경우: 주소만이라도
            for m in re.findall(r'https://assets\.mixkit\.co/music/[^"\'\s]+?\.mp3', s): found.setdefault(m.split("/")[-1], m)
        print(p, "누적", len(found), flush=True)
    json.dump(found, open(os.path.join(OUT, "music_all.json"), "w"), ensure_ascii=False, indent=1)
    res, files = [], []
    for title, src in found.items():
        if not any(w == title.lower() for w in WANT): continue
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-"); fn = f"music_{slug}.mp3"; dst = os.path.join(OUT, fn)
        try:
            open(dst, "wb").write(urllib.request.urlopen(urllib.request.Request(src, headers=UA), timeout=120).read())
            sec = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", dst], capture_output=True, text=True).stdout or 0)
            files.append(dst); res.append({"title": title, "slug": slug, "src": src, "sec": round(sec), "file": fn,
                                           "url": f"https://github.com/{REPO}/releases/download/side-assets/{fn}"})
            print("받음", title, round(sec), flush=True)
        except Exception as e: print("실패", title, e)
    if files:
        subprocess.run(["gh", "release", "upload", "side-assets", *files, "--clobber", "-R", REPO], check=True)
        for f in files: os.remove(f)
    json.dump(res, open(os.path.join(OUT, "music.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
