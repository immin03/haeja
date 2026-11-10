"""11/10 대표: 실화극 1호 뮤직비디오 보컬곡 — Sascha Ende 'Battlefield 6 Streaming Music Vol. 9 [Epic Vocals]' (CC BY 4.0, 설명란에 출처 표기)
결과: social/side/ed_long/music/vocal_0.mp3 (music.py 단계에서 실행, 커밋 단계가 올린다)"""
import os, re, urllib.request
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
OUT = os.path.join(ROOT, "social", "side", "ed_long", "music", "vocal_0.mp3")
PAGES = ["https://filmmusic.io/en/song/13083-battlefield-6-streaming-music-vol-9-epic-vocals", "https://filmmusic.io/song/13083-battlefield-6-streaming-music-vol-9-epic-vocals",
         "https://ende.app/en/song/13083-battlefield-6-streaming-music-vol-9-epic-vocals"]
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/126 Safari/537.36"}


def get(u, binary=False):
    with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90) as r:
        return (r.read(), r.headers.get("Content-Type", "")) if binary else r.read().decode("utf-8", "replace")


def main():
    if os.path.exists(OUT): print("이미 있음", OUT); return
    cands = []
    for p in PAGES:
        try: s = get(p)
        except Exception as e: print("못 읽음", p, e); continue
        for m in re.findall(r'(https?://[^"\'\s<>]+?\.mp3[^"\'\s<>]*)', s) + [("https://filmmusic.io" if "filmmusic" in p else "https://ende.app") + x for x in re.findall(r'href="(/[^"]*download[^"]*)"', s)]:
            if m not in cands: cands.append(m)
    cands += ["https://filmmusic.io/song/13083-battlefield-6-streaming-music-vol-9-epic-vocals/download", "https://filmmusic.io/download/13083"]
    print("후보", len(cands), cands[:12])
    for u in cands:
        try:
            b, ct = get(u, True)
            if len(b) > 800_000 and (b[:3] == b"ID3" or b[:2] == b"\xff\xfb" or "audio" in ct):
                os.makedirs(os.path.dirname(OUT), exist_ok=True); open(OUT, "wb").write(b); print("저장", u, len(b)); return
            print("아님", u, len(b), ct)
        except Exception as e: print("실패", u, e)
    print("보컬곡 받기 실패")


if __name__ == "__main__": main()
