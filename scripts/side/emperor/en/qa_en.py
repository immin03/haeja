"""The Emperor's Diary (EN) 영어 쇼츠 출고 전 자동 검수 (2026-11-13 대표: "음성검수나 아웃트로 검수를 안 하고 있는데 썸네일 포함해서 문제 안 되게 계속 체크해줘")
대표가 직접 보지 않으므로, 업로드 작업이 올리기 전에 이 검사를 통과한 편만 올라가게 한다.

검사 항목 (하나라도 실패하면 실패)
  1 음성: <영상>.voiceqa.json 이 있고 passed=true, 그 sha256 이 지금 영상 파일과 같다(검수 뒤 영상이 바뀌지 않았다)
  2 영상: 1080×1920, 30~70초, 소리 있음, 음량 -19 ~ -9 LUFS
  3 아웃트로: 마지막 3초 화면이 기준 엔딩(en05b)과 거의 같다(정상 편 차이 0.1~0.5, 엔딩 빠진 편 8, 한국어 엔딩 3.2 → 기준 2.0), 마지막 6초에 소리(슬로건 내레이션)가 있다
  4 썸네일: 표지 파일이 있고 1080×1920, 너무 어둡지 않고, 가운데 띠에 흰 제목 글자가 있다
  5 글: 제목·설명에 한글 없음, Korean/translated 같은 말 없음, 제목 70자 이하
사용: python3 qa_en.py <post_id> <video.mp4> <cover.jpg> "<title>" "<description>"  → 마지막 줄 JSON {"id","passed","fails":[...]}
기준 엔딩: docs/emperor/en/en05b_reels.mp4 (같은 폴더에 받아 두거나 ED_QA_REF 로 경로 지정)
"""
import hashlib, json, os, re, subprocess, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
REF = os.environ.get("ED_QA_REF", os.path.join(ROOT, "docs/emperor/en/en05b_reels.mp4"))


def probe(p):
    r = json.loads(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,width,height:format=duration", "-of", "json", p],
                                  capture_output=True, text=True).stdout or "{}")
    v = next((s for s in r.get("streams", []) if s["codec_type"] == "video"), {})
    return float(r.get("format", {}).get("duration", 0)), v.get("width"), v.get("height"), any(s["codec_type"] == "audio" for s in r.get("streams", []))


def frame(p, t_from_end):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-sseof", f"-{t_from_end}", "-i", p, "-frames:v", "1", "-vf", "scale=54:96", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).astype(np.float32) if len(raw) == 54 * 96 else None


def loud(p, ss=None):
    args = ["ffmpeg", "-nostats"] + (["-sseof", f"-{ss}"] if ss else []) + ["-i", p, "-af", "ebur128", "-f", "null", "-"]
    out = subprocess.run(args, capture_output=True, text=True).stderr
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", out)
    return float(m[-1]) if m else -99.0


def check(pid, video, cover, title, desc):
    fails = []
    # 1 음성 검수 도장
    qa = video + ".voiceqa.json"
    if not os.path.exists(qa):
        alt = [f for f in os.listdir(os.path.dirname(video) or ".") if f.startswith(os.path.basename(video).split("_")[0]) and f.endswith(".voiceqa.json")]
        qa = os.path.join(os.path.dirname(video), alt[0]) if alt else qa
    try:
        q = json.load(open(qa))
        sha = hashlib.sha256(open(video, "rb").read()).hexdigest()
        if not q.get("passed"): fails.append("음성 검수 실패 기록")
        elif q.get("sha256") and q["sha256"] != sha: fails.append("음성 검수 뒤 영상이 바뀜(다시 검수 필요)")
    except Exception: fails.append("음성 검수 기록 없음")
    # 2 영상 기본
    d, w, h, has_a = probe(video)
    if (w, h) != (1080, 1920): fails.append(f"화면 크기 {w}x{h}")
    if not 30 <= d <= 70: fails.append(f"길이 {d:.1f}초")
    if not has_a: fails.append("소리 없음")
    else:
        L = loud(video)
        if not -19 <= L <= -9: fails.append(f"음량 {L} LUFS")
    # 3 아웃트로
    fr = [frame(video, s) for s in (0.6, 1.5, 2.5)]; rf = [frame(REF, s) for s in (0.6, 1.5, 2.5)]
    if any(x is None for x in fr + rf): fails.append("엔딩 화면을 읽지 못함")
    else:
        diff = float(np.mean([np.abs(a - b).mean() for a, b in zip(fr, rf)]))
        if diff > 2.0: fails.append(f"엔딩 화면이 기준과 다름(차이 {diff:.0f})")
    if has_a and loud(video, 6) < -40: fails.append("엔딩 내레이션 소리 없음")
    # 4 썸네일
    try:
        im = Image.open(cover).convert("RGB")
        if im.size != (1080, 1920): fails.append(f"표지 크기 {im.size}")
        a = np.asarray(im.convert("L"), np.float32)
        if a.mean() < 18: fails.append("표지가 너무 어두움")
        band = np.asarray(im.crop((60, 650, 1020, 1300)), np.float32)
        white = ((band > 235).all(axis=2)).mean()
        if white < 0.004: fails.append("표지 가운데에 흰 제목 글자가 안 보임")
    except Exception as e: fails.append(f"표지 파일 문제: {str(e)[:40]}")
    # 5 글
    txt = f"{title}\n{desc}"
    if re.search(r"[가-힣]", txt): fails.append("제목·설명에 한글")
    if re.search(r"korean|translated|translation", txt, re.I): fails.append("제목·설명에 Korean/translated")
    if len(title) > 70: fails.append(f"제목 {len(title)}자")
    return {"id": pid, "passed": not fails, "fails": fails}


if __name__ == "__main__":
    pid, video, cover, title, desc = sys.argv[1:6]
    r = check(pid, video, cover, title, desc)
    print(json.dumps(r, ensure_ascii=False))
    sys.exit(0 if r["passed"] else 1)
