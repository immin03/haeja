#!/bin/bash
# 사용: yt_up.sh <id> <mp4> <meta.json>   meta.json = {"title","description","tags":[],"publish_at"}
set -e
ID=$1; F=$2; M=$3
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
call "{\"key\":\"$K\",\"action\":\"clean\",\"state_key\":\"$SKEY\"}"; echo; rm -rf $T
