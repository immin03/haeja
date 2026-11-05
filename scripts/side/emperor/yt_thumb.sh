#!/bin/bash
# 유튜브 쇼츠 썸네일을 첫 화면(훅) 표지로 고정한다 (2026-11-05 대표 지시: 첫 장면 = 초반 썸네일 양식, 왔다 갔다 금지)
# 사용: ED_KEY=<app_config ed_yt_long_key> ./yt_thumb.sh <id> <hook_<id>.jpg>
#   <id> = yt_up.sh 에 준 것과 같은 id (app_config ed_yt_up_<id> 에 video_id 가 있어야 함)
# yt_up.sh 가 업로드 끝에 자동으로 부른다. 이미 올린 편을 고칠 때도 이것만 돌리면 된다.
set -e
ID=$1; J=$2
U=https://msjbrwyzkiueqnzjeicm.supabase.co/functions/v1/ed-yt-long
A="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1zamJyd3l6a2l1ZXFuemplaWNtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTE4NTk0NTcsImV4cCI6MjEwNzQzNTQ1N30.RIq2MRW8bwHQUO_dPeIarujjWcYD_dXn06icr1Mpmuw"
K="${ED_KEY:?ED_KEY 필요: app_config ed_yt_long_key}"
[ -s "$J" ] || { echo "썸네일 파일 없음: $J"; exit 1; }
call(){ curl -s -m 150 -X POST $U -H "Content-Type: application/json" -H "Authorization: Bearer $A" -H "apikey: $A" --data-binary "$1"; }
SU=$(call "{\"key\":\"$K\",\"action\":\"sign\",\"prefix\":\"$ID\",\"n\":0,\"thumb\":true}" | python3 -c "import sys,json;print(json.load(sys.stdin)['urls'][0])")
curl -s -m 120 -X PUT "$SU" -H "Content-Type: image/jpeg" -H "x-upsert: true" --data-binary @"$J" >/dev/null
R=$(call "{\"key\":\"$K\",\"action\":\"thumb\",\"state_key\":\"ed_yt_up_$ID\"}")
echo "$R"
echo "$R" | grep -q '"status":200' || { echo "썸네일 지정 실패: $ID"; exit 1; }
