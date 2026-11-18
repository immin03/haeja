# Higgsfield 체험 영상 → 쇼츠 라이브러리 등록 (2026-11-18)

대표 11/18 15:11: 재사용 높은 편을 새 장면으로 갈아치운다. 체험 결과는 E 드라이브에만 있으면 제작에 못 쓴다. 완료될 때마다 아래 순서로 라이브러리에 넣는다(컴퓨터·E 드라이브 필요 없음 — 결과 주소에서 바로 받는다).

1. 대상: `select id, bundle, duration_s, scene_ko, public.ed_hf_expand(prompt_en) p, result_url from ed_hf_queue where status='완료' and kind='video' and bundle in ('R','CMP','D') and coalesce(tags->>'lib_done','')='' order by id;`
2. 받기: `curl -sS -m 180 -o <id>.mp4 <result_url>` (cloudfront 주소, 클라우드 작업 공간에서 받아진다).
3. 보기: `ffmpeg -i <id>.mp4 -vf "fps=1/2.5,scale=320:-1,tile=6x2" -frames:v 1 sheet.jpg` 로 한 장을 보고 구도가 다른 구간을 고른다. 15초 = 2컷, 30초 = 3~4컷(넓게·중간·가까이). 얼굴·손이 무너진 구간, 글자가 보이는 구간은 버린다.
4. 자르기: `ffmpeg -ss <시작> -t 5 -i <id>.mp4 -an -c:v libx264 -preset slow -crf 20 -pix_fmt yuv420p -movflags +faststart social/side/gen/hfr_<장면>_<구도>.mp4` (5~6초, 소리 없음).
5. 등록(세 군데, 한 커밋):
   - `scripts/side/gen/EDH<yymmdd>-trial<n>.json`: `{"id","kind":"video","endpoint":"higgsfield-trial/seedance","source":"ed_hf_queue <id>","body":{"prompt":"<그 컷에 실제로 보이는 것, 영어 한두 문장>","aspect_ratio":"16:9","duration":5}}`. 밤·촛불·막사 컷은 night/candle/tent 를, 낮 컷은 daylight 를 문장에 넣는다(밤 50% 검사가 이 문장을 본다).
   - `social/side/gen/<id>.json`: `{"id","status":"completed","est_usd":0.001,"usd_hf":0,"body":{…}}` (파일이 있으면 gen.py 는 다시 만들지 않는다 — 돈이 나가지 않는다).
   - `CLIPS.json` clips 에 `{"name","cx","scene":"한국어 장면","use":"쓰임새","added","look":"photoreal"}` (cx = 세로로 자를 때 가로 중심).
6. `python3 library.py build` → 커밋 메시지에 `[skip ci]` → `update ed_hf_queue set tags = tags || '{"lib_done":"<날짜>"}' where id in (…)`.
7. 로마 영상 클립 수를 센다(`LIBRARY.json` era roman·kind video). 300개를 넘으면 영어 하루 3편 복귀를 대표에게 묻고, 800개를 넘으면 REUSE_MAX 0.30 → 0.10.

1차(11/18): ed_hf_queue 10·11·13·16·48·2001 → hfr_ 클립 14개(낮 8·밤 6).
