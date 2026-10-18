# 네이버 블로그 운영 (주 3회) + 칼럼 소개 릴스

블로그 글은 사람이 붙여넣기만 하면 되도록 **사진·본문·태그를 한 페이지에** 만들어 둔다.
네이버는 블로그 글쓰기 API가 없어 자동 게시는 하지 않는다(매크로 게시는 저품질·정지 위험).

## 결과물
- `naver/<id>/post.json` 글 원본 (형식은 `naver_page.mjs` 맨 위 설명)
- `naver/<id>/NN.png` 사진 (1080×1080, `kit.mjs` 로 생성)
- `naver/<id>.html` 붙여넣기 페이지 → https://www.valuenote.co.kr/naver/<id> (noindex)
- `naver/<id>/photos.zip` 사진 묶음

id 규칙: `b` + yymmdd + 요일 글자(m·w·f). 예: b261019m. 처음 두 편은 a1·a2.

## 요일별 주제
- **월 · 주간 시장**: 그날 아침(08:40) 발행된 주간 칼럼 trends/col-YYYY-MM-DD 를 블로그용으로 다시 쓴다.
- **수 · 기업 분석**: "○○ 적정 주가, 계산해 보니". 많이 검색되는 대형주와 적정 주가와 차이가 큰 회사를 번갈아 고른다. 같은 회사를 8주 안에 다시 쓰지 않는다(naver/*/post.json 제목 확인).
- **금 · 가치투자 공부**: 버핏·그레이엄·멍거의 원칙, 투자자가 자주 하는 실수(PER 함정, 레버리지 ETF, 배당률 착각 등). 거장의 투자 칼럼(series giants)이 새로 나왔으면 그것을 쓴다.

## 글 규칙
- 제목: 검색어가 앞에 오게 (예: "삼성전자 적정 주가, 계산해 보니 … · 밸류노트 점수 47점"). 40자 안팎.
- 본문 1,500~2,500자, ~합니다체, 짧은 문장. 처음 보는 사람도 이해하게 낯선 말은 처음 나올 때 뜻을 붙인다.
- 사이트 칼럼을 그대로 옮기지 않는다(네이버 유사문서). 순서·문장을 새로 쓴다.
- 사진 4~7장. 첫 장은 cover. 숫자는 반드시 데이터나 출처에서 가져온다. 인용은 실제 출처가 있는 말만.
- 용어(claude/glossary.md): 밸류노트 점수, 재무 점수, 가격 점수, 정성 평가, 트렌드, 적정 주가, 적정 매수가(적정 주가의 70%), "적정 주가보다 N% 저평가/고평가", "적정 주가의 N배로 고평가". 쓰지 않는 말: 적정가·적정 가격·내재가치·품질 점수·저평가 점수·싸다/비싸다·무료/유료·매수 후보.
- 특정 종목 매수·매도 권유 금지. 끝에 링크 2개(관련 기업·순위 페이지, 칼럼 원문)와 고지 한 줄. 링크에는 `?utm_source=naver-blog`.
- 태그 6~8개.

## 만드는 법
```
npm i --no-save --no-package-lock satori@0.10.14 @resvg/resvg-js@2.6.2 pretendard@1.3.9
node scripts/blog/kit.mjs naver/<id> /tmp/jobs.json      # 사진
python3 scripts/blog/chart.py naver/<id>/NN.png /tmp/spec.json   # 실제 데이터 선 그래프 (형식은 chart.py 맨 위)
node scripts/blog/naver_page.mjs naver/<id>              # 페이지·zip
```
그래프 데이터는 Supabase REST(anon 키, config.js)로 공개 읽기: trends/series(d: kospi·spx·트렌드), fx/rates(series.*.daily), fx/current(series.USDKRW·JPYKRW100).
월요일에는 그래프 2~4장을 blog/weekly-<yyyymmdd>/ 에 복사해 사이트 칼럼 본문에도 넣는다(예: col-2026-10-15).
사진은 열어서 확인한다(글자가 넘치거나 겹치면 문장을 줄여 다시 만든다).

## 칼럼 소개 릴스
새 칼럼(trends/col-*)이 나왔는데 `scripts/reels/specs/C<칼럼 날짜 yymmdd><g?>.json` 이 없으면 하나 만든다.
- 그날 19:30 KST 게시(`scheduled_at`), 이미 지났으면 다음 날 19:30.
- 15~25초, scripts/reels/README.md 의 대본 규칙 1~10을 그대로 지킨다. 칼럼의 핵심 숫자 하나로 시작(hook) → 2~3문장 → cta.
- 캡션 끝: "전체 칼럼은 프로필 링크 → 칼럼에서 볼 수 있습니다."
