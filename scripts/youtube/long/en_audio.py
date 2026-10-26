"""롱폼 영어 음성 트랙 만들기 (2026-10-25 운영자: 해외 시청자도 보게 — 유튜브 '다국어 오디오'에 올릴 영어 내레이션)
사용: python3 scripts/youtube/long/en_audio.py <롱폼 아이디>   (build.py 가 렌더·자막 뒤에 자동으로 부른다)
 - 문장 타이밍: 렌더 결과 meta.json 의 qa.lines [시작, 길이, 자막, 읽은 문장]
 - 영어 문장: 원고 장면의 "en" (subs.py 와 같은 짝짓기, 숫자 자리표는 영어 표기로)
 - 목소리: 타입캐스트 영어 원어민 성우 Landon (TYPECAST_VOICE_EN 으로 바꿀 수 있음). 운영자 클론은 쓰지 않는다. 같은 문장은 캐시
 - 영어가 한국어 자리보다 길면 최대 1.3배까지 빠르게, 그래도 길면 다음 문장을 조금 밀어 겹치지 않게
 - 배경음악은 한국어판과 같은 테마곡·같은 덕킹. 길이는 영상과 똑같이 맞춘다
 - 결과: social/youtube/<id>/audio_en.m4a (저장소에는 올리지 않고 릴리스에 올린다), meta.json subs.audio_en
"""
import hashlib, json, os, subprocess, sys, urllib.error, urllib.request
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts", "reels"))
SR = 44100
CACHE = os.path.join(ROOT, "scripts", "reels", ".cache", "typecast_en")
MODEL = "ssfm-v30"
EN_VOICE = "tc_6633457fb5267dbd4808a2dd"   # Landon (영어 원어민 남성, 다큐·뉴스·설명)


def _say_en(text):
    """영어 문장 → float32 mono (44.1kHz). 앞뒤 무음은 잘라 낸다"""
    # 2026-10-26 운영자: 영어는 운영자 목소리 클론이 어색하다 → 영어 원어민 전문 성우(타입캐스트 Landon, 다큐·뉴스·설명용)로. 클론으로 되돌리지 않는다
    voices = [os.environ.get("TYPECAST_VOICE_EN") or EN_VOICE]
    os.makedirs(CACHE, exist_ok=True)
    last = None
    for voice in voices:
        key = hashlib.sha1(f"{voice}|{MODEL}|eng|{text}".encode()).hexdigest()[:20]
        mp3 = os.path.join(CACHE, key + ".mp3")
        if not os.path.exists(mp3):
            body = {"text": text, "model": MODEL, "voice_id": voice, "language": "eng", "output": {"audio_format": "mp3"}}
            req = urllib.request.Request("https://api.typecast.ai/v1/text-to-speech", method="POST", data=json.dumps(body).encode(),
                                         headers={"X-API-KEY": os.environ["TYPECAST_API_KEY"], "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=90) as r: open(mp3, "wb").write(r.read())
                try:
                    import tts; tts._log_usage(len(text))
                except Exception: pass
            except urllib.error.HTTPError as e:
                last = f"HTTP {e.code}: {e.read().decode(errors='replace')[:200]}"; continue
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp3, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
        x = np.frombuffer(raw, dtype=np.float32).copy()
        idx = np.where(np.abs(x) > 0.012)[0]
        if len(idx): x = x[max(0, idx[0] - int(.05 * SR)): idx[-1] + int(.1 * SR)]
        return x
    raise RuntimeError(f"영어 음성 실패: {last}")


def _tempo(x, f):
    """f배 빠르게 (음높이 유지)"""
    if f <= 1.01: return x
    out = subprocess.run(["ffmpeg", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", "-filter:a", f"atempo={min(f, 1.3):.3f}",
                          "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], input=x.tobytes(), capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).copy()


def _movavg(x, w):
    """빠른 이동 평균 (np.convolve 'same' 과 같은 결과, 긴 오디오에서도 빠름)"""
    c = np.cumsum(np.concatenate([np.zeros(1), x.astype(np.float64)])); h = w // 2
    i = np.arange(len(x)); a = np.clip(i - h, 0, len(x)); b = np.clip(i - h + w, 0, len(x))
    return ((c[b] - c[a]) / w).astype(np.float32)


def build(sid, upload_tag=None, repo=None):
    if not os.environ.get("TYPECAST_API_KEY"): print("영어 음성: 타입캐스트 키 없음 — 건너뜀"); return None
    import subs
    d = os.path.join(ROOT, "social", "youtube", sid)
    mp = os.path.join(d, "meta.json"); meta = json.load(open(mp, encoding="utf-8"))
    sp = os.path.join(HERE, "specs", sid + ".json"); spec = json.load(open(sp, encoding="utf-8"))
    V = json.load(open(sp.replace(".json", ".data.json"), encoding="utf-8"))["vars"]
    lines = meta.get("qa", {}).get("lines") or []
    en = [subs.fill_en(e, V) if e else None for sc in spec["scenes"] for e in (sc.get("en") or [None] * len(sc["lines"]))]
    if sum(1 for e in en if e) < len(lines) * .8: print(f"영어 음성: 영어 문장이 부족함({sum(1 for e in en if e)}/{len(lines)}) — 건너뜀"); return None
    total = float(meta.get("duration") or (lines[-1][0] + lines[-1][1] + 3))
    mix = np.zeros(int((total + .5) * SR), np.float32); prev_end = 0.0; fast = 0
    for k, (t0, dur, _ko, _say) in enumerate(lines):
        txt = en[k] if k < len(en) else None
        if not txt: continue
        a = _say_en(txt)
        slot = (lines[k + 1][0] if k + 1 < len(lines) else total - 2.0) - t0 - .12   # 다음 한국어 문장이 시작하기 전까지
        if len(a) / SR > slot > .5:
            f = (len(a) / SR) / slot; a = _tempo(a, f); fast += 1
        st = max(t0, prev_end + .08); i = int(st * SR)
        if i >= len(mix): break
        mix[i:i + len(a)] += a[: len(mix) - i]; prev_end = st + len(a) / SR
    if np.abs(mix).max() > 0: mix = mix / np.abs(mix).max() * .9
    # 배경음악: 한국어판과 같은 테마곡·덕킹
    from scipy import signal as _sg
    import render2
    env = _movavg(np.abs(mix), int(SR * .25)); env = np.clip(env / (env.max() + 1e-9) * 4, 0, 1)
    env = _sg.lfilter([.0005], [1, -.9995], env); env = np.clip(env / (env.max() + 1e-9), 0, 1)
    boost = np.ones(len(mix), np.float32); first = int(lines[0][0] * SR); boost[:first] = 1.5
    boost = _movavg(boost, int(SR * 1.2)).astype(np.float32)
    mus = render2.load_theme(len(mix)) * (.19 * boost * (1 - .62 * env))[:, None]
    st_ = np.stack([mix, mix], 1) + mus; st_ = (st_ / max(1.0, np.abs(st_).max() / .95)).astype(np.float32)
    out = os.path.join(d, "audio_en.m4a")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-t", f"{total:.2f}", "-c:a", "aac", "-b:a", "160k", out],
                   input=st_.tobytes(), check=True)
    print(f"영어 음성: {sid} {len(lines)}문장, 빠르게 맞춘 문장 {fast}개 → {out}")
    if upload_tag and repo:
        stamp = (meta.get("thumb") or "").split("?v=")[-1] or "0"; name = f"{sid}-{stamp}-en.m4a"; up = os.path.join(d, name); os.replace(out, up)
        subprocess.run(["gh", "release", "upload", upload_tag, up, "--clobber", "-R", repo], check=True); os.remove(up)
        s = dict(meta.get("subs") or {}); s["audio_en"] = f"https://github.com/{repo}/releases/download/{upload_tag}/{name}"; meta["subs"] = s
        json.dump(meta, open(mp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return meta


if __name__ == "__main__":
    for a in sys.argv[1:]: build(a, "yt-" + a, os.environ.get("GITHUB_REPOSITORY", "immin03/haeja"))
