# 밸류노트 릴스 자동화

## 구조
- `specs/R*.json` 정기 편성 대본. 새 릴스는 여기에 JSON 하나만 추가하고 푸시하면 GitHub Actions(reels)가 렌더한다.
- `events.py` 3시간마다 지수·환율·금리 급변을 감지해 `events/E*.json` 대본을 규칙으로 만든다 (하루 최대 2편, AI 사용 없음).
- `engine.py` 대본 → 1080x1920 영상 (Supertonic 한국어 음성, 합성 배경음악·효과음, 모션, 노래방식 자막).
- `build.py` 바뀐 대본만 렌더 → `social/reels/<id>/reel.mp4, cover.jpg` + `social/reels/queue.json`.
- Supabase `social_reels_fetch/import`(매시 15·18분)가 queue.json을 게시 대기열에 넣고, `social-publish`가 인스타 릴스·쓰레드 영상으로 올린다.

## 대본 쓰는 법 (장면 종류는 engine.py 맨 위 설명 참고)
- 자막(`cap`)만 쓰면 숫자는 자동으로 한글 발음으로 읽는다. 발음이 어색하면 `say`에 한글로 적는다 ("세 배" 권장, "삼 배"는 "삼백"으로 들림).
- 영상 길이는 음성 길이로 정해진다. 장면 4~5개 + cta 면 15~20초.
- 금액 예시는 1,000만 원 기준, 결론 장면(statement)은 자극적으로 짧게.
- 고지문은 영상 하단과 게시 본문 끝에 자동으로 붙는다. 캡션에는 쓰지 않는다.

## 로컬 미리보기
```
pip install sherpa-onnx==1.13.8 soundfile scipy numpy pillow   # ffmpeg 필요
python3 scripts/reels/engine.py scripts/reels/specs/R01.json out/R01            # 영상
python3 scripts/reels/engine.py scripts/reels/specs/R01.json out/R01 stills 1.5,6,12   # 정지 화면
```
