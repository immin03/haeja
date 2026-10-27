"""What Korea Says — 진행자 까치(Kachi) 목소리 조율 샘플 (2026-10-27)
운영자: Artemis 정도의 젊은 여성 목소리, 톤만 조금 더 높게. 아이 전용으로 들리면 안 됨(시청자층이 어른도 많다)
같은 문장을 음높이(반음)·감정(normal/toneup/happy) 조합으로 읽혀 릴리스 side-assets 에 올리고 social/side/voice_tune.json 에 기록
타입캐스트 output.audio_pitch(반음)·audio_tempo 를 먼저 쓰고, 거절되면 ffmpeg 로 음높이를 올린다
"""
import json, os, subprocess, sys, urllib.request, urllib.error

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "social", "side"); os.makedirs(OUT, exist_ok=True)
REPO = os.environ.get("GITHUB_REPOSITORY", "immin03/haeja")
KEY = os.environ.get("TYPECAST_API_KEY", "")
VOICE = "tc_6a6ada630d2e817710d94e9c"  # Artemis
LINE = ("Hi, I'm Kachi! And today's story is honestly wild. In 2014, North Korea banned a snack. "
        "Not a weapon. Not a phone. A tiny, round, chocolate snack from South Korea. Wait... a snack? Yep.")
# 2차(2026-10-27 14시): 운영자 "전달력은 원래 톤이 좋은데 까치 이미지와 안 맞고, 아기 목소리는 듣기 싫을까 걱정" → 영어 원어민 계열 밝은 젊은 여성 10명 추가
NAMES = ["Riley", "Zoey", "Kelsey", "Skylar", "Audrey", "Starling", "Stephanie", "Jenna", "Tina", "Bell"]
VARIANTS_OLD = [  # (번호, 감정, 반음, 설명)
    (1, "normal", 0, "원래 톤"),
    (2, "toneup", 0, "밝게, 음높이 그대로"),
    (3, "normal", 2, "음높이 +2"),
    (4, "toneup", 2, "밝게 + 음높이 +2"),
    (5, "happy", 2, "신나게 + 음높이 +2"),
    (6, "toneup", 3, "밝게 + 음높이 +3"),
    (7, "happy", 4, "신나게 + 음높이 +4"),
]
TEMPO = 1.12


def call(body):
    req = urllib.request.Request("https://api.typecast.ai/v1/text-to-speech", method="POST", data=json.dumps(body).encode(),
                                 headers={"X-API-KEY": KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r: return r.read()


def make(emotion, semis, raw):
    """1) API 음높이·속도  2) 실패하면 감정만 API, 음높이·속도는 ffmpeg"""
    base = {"text": LINE, "model": "ssfm-v30", "voice_id": VOICE, "language": "eng"}
    prompt = {"emotion_type": "preset", "emotion_preset": emotion, "emotion_intensity": 1.0} if emotion != "normal" else None
    tries = []
    full = dict(base, output={"audio_format": "mp3", "audio_pitch": semis, "audio_tempo": TEMPO})
    if prompt: full["prompt"] = prompt
    tries.append(("api", full))
    lite = dict(base, output={"audio_format": "mp3"})
    if prompt: lite["prompt"] = prompt
    tries.append(("ffmpeg", lite))
    tries.append(("ffmpeg-noemo", dict(base, output={"audio_format": "mp3"})))
    last = ""
    for how, body in tries:
        try:
            open(raw, "wb").write(call(body)); return how
        except urllib.error.HTTPError as e:
            last = f"{e.code} {e.read().decode(errors='replace')[:200]}"; print(how, "거절:", last, flush=True)
    raise RuntimeError(last)


def main():
    if not KEY: sys.exit("TYPECAST_API_KEY 없음")
    global VOICE
    allv = json.load(open(os.path.join(OUT, "voices_all.json")))
    pick = [(i + 1, next(v for v in allv if v.get("voice_name") == nm)) for i, nm in enumerate(NAMES) if any(v.get("voice_name") == nm for v in allv)]
    res, files = [], []
    for n, v in pick:
        VOICE = v["voice_id"]; emo, semis, desc = "happy", 0, f"{v['voice_name']} · {v.get('age')} · {', '.join((v.get('use_cases') or [])[:3])}"
        raw = os.path.join(OUT, f"_t{n}.mp3"); fn = f"kachi2_{n:02d}_{v['voice_name']}.mp3"; dst = os.path.join(OUT, fn)
        try:
            how = make(emo, semis, raw)
            if False: af = ""
            else:  # 음높이 semis 반음 올리고 길이는 TEMPO 배 빠르게
                r = 2 ** (semis / 12)
                af = f"asetrate=44100*{r:.5f},aresample=44100,atempo={TEMPO / r:.5f},loudnorm=I=-16:TP=-1.5"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", af, "-ar", "44100", "-b:a", "160k", dst], check=True)
            os.remove(raw); files.append(dst)
            dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", dst], capture_output=True, text=True).stdout or 0)
            res.append({"n": n, "voice_id": VOICE, "name": v["voice_name"], "emotion": emo, "pitch": semis, "desc": desc, "method": how, "sec": round(dur, 1),
                        "url": f"https://github.com/{REPO}/releases/download/side-assets/{fn}", "file": fn})
            print("샘플", n, emo, semis, how, round(dur, 1), flush=True)
        except Exception as e: print("실패", n, str(e)[:200], flush=True)
    if files:
        if subprocess.run(["gh", "release", "view", "side-assets", "-R", REPO], capture_output=True).returncode != 0:
            subprocess.run(["gh", "release", "create", "side-assets", "-R", REPO, "--title", "What Korea Says 제작 자료", "--notes", "성우 샘플 등", "--latest=false"], check=True)
        subprocess.run(["gh", "release", "upload", "side-assets", *files, "--clobber", "-R", REPO], check=True)
        for f in files: os.remove(f)
    json.dump(res, open(os.path.join(OUT, "voice_tune2.json"), "w"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
