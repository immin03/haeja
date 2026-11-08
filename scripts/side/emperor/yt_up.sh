#!/bin/bash
# 사용: yt_up.sh <id> <mp4> <meta.json> <hook_<id>.jpg>   meta.json = {"title","description","tags":[],"publish_at"}
# ★ 4번째 인자(첫 화면 표지)는 필수 — 2026-11-05 대표 지시: 쇼츠 썸네일 = 초반 양식 첫 화면, 유튜브 자동 선택 금지
set -e
ID=$1; F=$2; M=$3; J=${4:?썸네일(hook_<id>.jpg) 필요}
[ -s "$J" ] || { echo "썸네일 파일 없음: $J"; exit 1; }
# ★ 제목 검사 (2026-11-06 대표: 제목에 #shorts 같은 태그 금지, 40자 이내) — 어기면 올리지 않는다
python3 - "$M" <<'CHK' || exit 1
import json,sys
t=json.load(open(sys.argv[1])).get("title","").strip()
bad=[]
if not t: bad.append("제목 없음")
if "#" in t: bad.append("제목에 해시태그")
# 2026-11-08: 꼬리는 ` | 명상록` 하나만 허용 (TEMPLATE 제목 규칙, 11/7 대표) — 예전 검사가 모든 | 를 막아 규칙과 충돌했다
body=t[:-len(" | 명상록")] if t.endswith(" | 명상록") else t
if "|" in body: bad.append("제목에 다른 꼬리(|)")
if len(t)>40: bad.append(f"{len(t)}자(40자 초과)")
if bad: print("제목 규칙 위반:", t, "·", ", ".join(bad)); sys.exit(1)
CHK
# ★ 음성 관문 (2026-11-08 대표: "검수를 꼭 해야 돼") — 데일리 쇼츠(ep숫자)는 voice_gate.py 도장의 sha256 이 이 파일과 같아야 올린다
python3 - "$ID" "$F" <<'CHK' || exit 1
import hashlib,json,os,re,sys
i,f=sys.argv[1:]
if re.match(r"ep\d+",i):
    s=f+".voiceqa.json"
    if not os.path.exists(s): print("음성 관문 도장 없음 — voice_gate.py 통과 전에는 올리지 않는다:",s); sys.exit(1)
    d=json.load(open(s)); h=hashlib.sha256(open(f,"rb").read()).hexdigest()
    if not d.get("passed") or d.get("sha256")!=h: print("음성 관문 도장이 이 파일과 다름 — 다시 검사할 것"); sys.exit(1)
    print("음성 관문 도장 확인")
CHK
# ★ 썸네일 검사 (2026-11-06: 13편에 중간 장면 사진이 썸네일로 올라간 사고) — 넘긴 jpg 가 영상 0초 첫 화면과 같아야 올린다
python3 - "$F" "$J" <<'CHK' || exit 1
import subprocess,sys,tempfile,os
from PIL import Image, ImageChops, ImageStat
v,j=sys.argv[1:]; f=os.path.join(tempfile.mkdtemp(),"f0.jpg")
subprocess.run(["ffmpeg","-v","error","-y","-ss","0","-i",v,"-frames:v","1",f],check=True)
a=Image.open(f).convert("L").resize((108,192)); b=Image.open(j).convert("L").resize((108,192))
d=ImageStat.Stat(ImageChops.difference(a,b)).mean[0]
if d>4: print(f"썸네일이 영상 첫 화면과 다름(차이 {d:.1f}) — 0초 프레임으로 다시 뽑을 것: {j}"); sys.exit(1)
print(f"썸네일 검사 통과(차이 {d:.1f})")
CHK
U=https://msjbrwyzkiueqnzjeicm.supabase.co/functions/v1/ed-yt-long
A="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1zamJyd3l6a2l1ZXFuemplaWNtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTE4NTk0NTcsImV4cCI6MjEwNzQzNTQ1N30.RIq2MRW8bwHQUO_dPeIarujjWcYD_dXn06icr1Mpmuw"
K="${ED_KEY:?ED_KEY 필요: app_config ed_yt_long_key}"
SKEY="ed_yt_up_$ID"; T=$(mktemp -d)
call(){ curl -s -m 150 -X POST $U -H "Content-Type: application/json" -H "Authorization: Bearer $A" -H "apikey: $A" --data-binary "$1"; }
split -b 33554432 -d -a 3 "$F" $T/p
N=$(ls $T/p* | wc -l); TOTAL=$(stat -c%s "$F")
R=$(call "{\"key\":\"$K\",\"action\":\"sign\",\"prefix\":\"$ID\",\"n\":$N}")
i=0; for u in $(echo "$R" | python3 -c "import sys,json;print('\n'.join(json.load(sys.stdin)['urls']))"); do
  curl -s -m 300 -X PUT "$u" -H "Content-Type: application/octet-stream" -H "x-upsert: true" --data-binary @$T/p$(printf %03d $i) >/dev/null; i=$((i+1)); done
python3 - "$K" "$ID" "$TOTAL" "$SKEY" "$M" > $T/start.json <<'P'
import json,sys
k,i,t,s,m=sys.argv[1:]; d=json.load(open(m)); d.update({"key":k,"action":"start","prefix":i,"total":int(t),"state_key":s,"category":"27"}); print(json.dumps(d,ensure_ascii=False))
P
call @$T/start.json; echo
for n in $(seq 1 20); do R=$(call "{\"key\":\"$K\",\"action\":\"push\",\"state_key\":\"$SKEY\"}"); echo "$R"; echo "$R" | grep -q '"done":true' && break; done
ED_KEY=$K "$(dirname "$0")/yt_thumb.sh" "$ID" "$J"
call "{\"key\":\"$K\",\"action\":\"clean\",\"state_key\":\"$SKEY\"}"; echo; rm -rf $T
