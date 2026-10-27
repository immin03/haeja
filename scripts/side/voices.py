"""What Korea Says — 영어 성우 후보 듣기 샘플 (2026-10-27)
타입캐스트에서 영어를 읽을 수 있는 목소리 목록을 받아, 젊고 경쾌한 후보를 골라 같은 문장을 읽힌다.
결과: 릴리스 side-assets 에 voice_<번호>_<이름>.mp3, social/side/voices.json (후보 목록·주소)
"""
import json, os, subprocess, sys, urllib.request, urllib.error

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "social", "side"); os.makedirs(OUT, exist_ok=True)
REPO = os.environ.get("GITHUB_REPOSITORY", "immin03/haeja")
KEY = os.environ.get("TYPECAST_API_KEY", "")
LINE = ("In 2014, North Korea banned a snack. Not a weapon. Not a phone. A tiny, round, chocolate snack from South Korea. "
        "Wait... a snack? Yep. And honestly, the real story is even crazier.")


def get(url):
    req = urllib.request.Request(url, headers={"X-API-KEY": KEY})
    with urllib.request.urlopen(req, timeout=60) as r: return json.loads(r.read())


def tts(voice, model, path):
    body = {"text": LINE, "model": model, "voice_id": voice, "language": "eng", "output": {"audio_format": "mp3"}}
    req = urllib.request.Request("https://api.typecast.ai/v1/text-to-speech", method="POST", data=json.dumps(body).encode(),
                                 headers={"X-API-KEY": KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r: open(path, "wb").write(r.read())


def main():
    if not KEY: sys.exit("TYPECAST_API_KEY 없음")
    voices = None
    for u in ("https://api.typecast.ai/v2/voices?model=ssfm-v30", "https://api.typecast.ai/v1/voices?model=ssfm-v30", "https://api.typecast.ai/v1/voices"):
        try: voices = get(u); print("목록:", u); break
        except urllib.error.HTTPError as e: print(u, e.code)
    if voices is None: sys.exit("목소리 목록을 못 받음")
    if isinstance(voices, dict): voices = voices.get("voices") or voices.get("result") or voices.get("data") or []
    json.dump(voices, open(os.path.join(OUT, "voices_all.json"), "w"), ensure_ascii=False, indent=1)
    def txt(v): return json.dumps(v, ensure_ascii=False).lower()
    young = [v for v in voices if any(k in txt(v) for k in ("young", "teen", "child", "kid", "cute", "bright", "energetic", "cheerful", "playful"))]
    eng = [v for v in young if any(k in txt(v) for k in ("eng", "english", "en-us", "en_us", "american", "british"))] or young
    pick = eng[:10]
    print("후보", len(pick), "/ 전체", len(voices))
    res = []; files = []
    for i, v in enumerate(pick, 1):
        vid = v.get("voice_id") or v.get("id"); name = (v.get("voice_name") or v.get("name") or "voice").replace(" ", "_")[:24]
        models = v.get("models") or [{"version": "ssfm-v30"}]
        model = "ssfm-v30" if "ssfm-v30" in txt(models) else (models[0].get("version") if isinstance(models[0], dict) else str(models[0]))
        raw = os.path.join(OUT, f"_raw{i}.mp3"); fn = f"voice_{i:02d}_{name}.mp3"; dst = os.path.join(OUT, fn)
        try:
            tts(vid, model, raw)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", "atempo=1.12,loudnorm=I=-16:TP=-1.5", "-b:a", "160k", dst], check=True)
            os.remove(raw); files.append(dst)
            res.append({"n": i, "voice_id": vid, "name": v.get("voice_name") or v.get("name"), "gender": v.get("gender"), "age": v.get("age"),
                        "tags": v.get("use_cases") or v.get("tags") or v.get("styles"), "model": model,
                        "url": f"https://github.com/{REPO}/releases/download/side-assets/{fn}"})
            print("샘플", i, name, flush=True)
        except Exception as e: print("실패", name, str(e)[:120])
    if files:
        if subprocess.run(["gh", "release", "view", "side-assets", "-R", REPO], capture_output=True).returncode != 0:
            subprocess.run(["gh", "release", "create", "side-assets", "-R", REPO, "--title", "What Korea Says 제작 자료", "--notes", "성우 샘플 등", "--latest=false"], check=True)
        subprocess.run(["gh", "release", "upload", "side-assets", *files, "--clobber", "-R", REPO], check=True)
        for f in files: os.remove(f)
    json.dump(res, open(os.path.join(OUT, "voices.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
