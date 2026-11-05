"""롱폼 일러스트 생성기 (2026-11-01, 제1 원칙 49 보완 — 벤치마크처럼 장면마다 그림으로)
작업 목록: scripts/youtube/long/illust/*.json (리스트, 형식은 scripts/side/gen.py 와 같다)
  {"id": "il_L261101_flyers", "kind": "image", "endpoint": "xai/grok-imagine-image-2.0",
   "body": {"prompt": "...", "aspect_ratio": "16:9"}}
결과: scripts/blog/media/lib/<id>.(png|jpg) + 같은 이름 .json — 원고에서 "lib": "<id>.jpg" 로 바로 쓴다.
- 밸류노트 그림체(STYLE)를 프롬프트 앞에 자동으로 붙인다. 글자·숫자·로고는 그림에 넣지 않는다(화면 글씨는 렌더러가 쓴다).
- 이미 결과가 있으면 건너뛴다. 한 번 실행 비용 상한: 환경변수 YT_ILLUST_MAX_USD (기본 2달러). 사이드 채널 예산과 별개.
"""
import glob, json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "scripts", "side")); sys.path.insert(0, os.path.join(ROOT, "scripts", "higgsfield"))
import gen  # noqa: E402  (Higgsfield 제출·대기·저장 재사용)
import hf   # noqa: E402

gen.OUT = os.path.join(ROOT, "scripts", "blog", "media", "lib")
STYLE = ("Editorial storybook illustration for a Korean finance explainer video. Hand-drawn deep navy ink linework with soft watercolor wash "
         "on warm ivory paper texture, limited palette of navy, ivory and muted gold with small warm accents, gentle light, clear single focal point, "
         "calm and intelligent mood, generous empty space around the subject. Absolutely no text, no letters, no numbers, no logos, no watermark. Scene: ")


SPACE = " Composition: keep the left 40 percent of the frame as calm, nearly empty ivory paper wash (room for handwritten notes); place the main subject in the right 60 percent."


def main(only=None):
    """4개씩 동시에 만든다 (한 장 30~100초)"""
    from concurrent.futures import ThreadPoolExecutor
    H = hf.auth_headers(); spent = 0.0; cap = min(float(os.environ.get("YT_ILLUST_MAX_USD", "2")), gen.HARD_CAP); batch = []
    for f in sorted(glob.glob(os.path.join(ROOT, "scripts", "youtube", "long", "illust", "*.json"))):
        if only and os.path.basename(f)[:-5] not in only: continue
        for j in json.load(open(f, encoding="utf-8")):
            if j.get("disabled"): continue
            j = dict(j); j.setdefault("kind", "image"); j.setdefault("endpoint", "xai/grok-imagine-image-2.0")
            b = dict(j.get("body", {})); b.setdefault("aspect_ratio", "16:9")
            if not j.get("raw_prompt"): b["prompt"] = STYLE + b.get("prompt", "") + (SPACE if j.get("space", True) else "")
            j["body"] = b
            c = gen.est(j)
            if spent + c > cap: print(f"[{j['id']}] 상한 {cap}달러 초과 — 건너뜀"); continue
            spent += c; batch.append(j)
    with ThreadPoolExecutor(4) as ex: list(ex.map(lambda j: gen.run(j, H, 0.0), batch))
    print(f"이번 실행 비용(추정 상한): {spent:.2f}달러 · {len(batch)}건")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
