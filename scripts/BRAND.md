# 밸류노트 로고 (2026-10-23 운영자 확정)

- 모양: **Value**(흰색) + **Note**(아이보리 베이지 #E2CFA6) — Montserrat ExtraBold. 그 아래 얇은 금색 줄(#CEB480), 그 아래 가운데 **밸류노트**(SUIT Bold, 영문 크기의 0.5배, 자간 넓게, #E2CFA6).
- 밝은 배경: Value 네이비 #0B1B33, Note #AE9260 · 줄 #C0A87C · 한글 #9E8456 (금빛을 조금 뺀 아이보리).
- 이전 세리프(Fraunces) 워드마크는 쓰지 않는다. 앱 아이콘·파비콘(작은 V)은 그대로 둔다.
- 그리는 곳은 하나로 모은다
  - 이미지·영상(Python): `scripts/brand.py` 의 `paste_logo()` / `logo_image()` — 롱폼·쇼츠·릴스·썸네일
  - 블로그 이미지(satori): `scripts/blog/kit.mjs` 의 `VNL()`
  - 웹: `.wm` (`<a class="wm"><span class="e">Value<i>Note</i></span><small>밸류노트</small></a>`), 앱은 `.wordmark.vn`
  - 파일: `brand/logo-dark.png`, `brand/logo-light.png`, `brand/profile-1080.png`(인스타·유튜브·네이버 블로그 프로필), `og.png`
- 글꼴: `scripts/reels/fonts/Montserrat-ExtraBold.ttf`, 웹은 `fonts/montserrat-800.woff2` (SIL Open Font License, `scripts/reels/fonts/Montserrat-OFL.txt`)
