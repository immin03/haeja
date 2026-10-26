"""위키미디어 공용(Commons)에서 재사용 허락된 실제 사진 받기 (2026-10-25 운영자: 테슬라 새 사업은 실제 사진으로)
사용: python3 scripts/blog/media/commons.py  (scripts/blog/media/commons_wants.json 의 검색어마다 최대 5장)
- 라이선스가 CC0 · 퍼블릭 도메인 · CC BY · CC BY-SA 인 것만 받는다. 출처·작가·라이선스는 lib/commons_credits.json 에 남긴다.
- 파일 이름: commons_<slug>_<n>.jpg (가로 1920px 이하)
"""
import json, os, re, urllib.parse, urllib.request, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); LIB = os.path.join(HERE, "lib")
UA = {"User-Agent": "ValueNoteBot/1.0 (https://www.valuenote.co.kr; bot@valuenote.co.kr)"}
OK = re.compile(r"^(cc0|public domain|pd|cc by(-sa)? ?[0-9.]*)", re.I)
def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()
wants = json.load(open(os.path.join(HERE, "commons_wants.json")))
cp = os.path.join(LIB, "commons_credits.json"); credits = json.load(open(cp)) if os.path.exists(cp) else {}
for w in wants:
    q = w["q"]; slug = w["slug"]; n = 0
    api = "https://commons.wikimedia.org/w/api.php?" + urllib.parse.urlencode({"action": "query", "format": "json", "generator": "search", "gsrsearch": q + " filetype:bitmap", "gsrnamespace": 6, "gsrlimit": 25, "prop": "imageinfo", "iiprop": "url|extmetadata|size", "iiurlwidth": 1920})
    pages = sorted(json.loads(get(api)).get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 99))
    for p in pages:
        if n >= w.get("n", 5): break
        ii = (p.get("imageinfo") or [{}])[0]; md = ii.get("extmetadata", {})
        lic = md.get("LicenseShortName", {}).get("value", "")
        if not OK.match(lic) or ii.get("width", 0) < 1000: print("건너뜀", p["title"], lic); continue
        n += 1; name = f"commons_{slug}_{n}.jpg"; out = os.path.join(LIB, name)
        if os.path.exists(out): continue   # 이미 받은 사진은 건너뛴다
        raw = get(ii.get("thumburl") or ii["url"]); tmp = out + ".src"; open(tmp, "wb").write(raw)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-vf", "scale='min(1920,iw)':-2", "-q:v", "3", out], check=True); os.remove(tmp)
        artist = re.sub("<[^>]+>", "", md.get("Artist", {}).get("value", "")).strip()
        credits[name] = {"title": p["title"], "page": ii.get("descriptionurl"), "license": lic, "artist": artist, "q": q}
        print("받음", name, p["title"], lic, artist)
json.dump(credits, open(cp, "w"), ensure_ascii=False, indent=1)
