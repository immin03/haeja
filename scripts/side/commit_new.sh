#!/usr/bin/env bash
# side-gen 커밋 (2026-11-14): 큰 저장소에서 'git pull --rebase' 가 300초를 넘겨 생성물이 커밋되지 못했다(11/13 st·pw 장면 유실).
# 이번 실행에서 새로 생기거나 바뀐 파일만 모아 두고 → 최신 main 을 얕게 받아 그 위에 얹어 커밋·푸시한다. 8회 재시도.
# 사용: bash scripts/side/commit_new.sh "<커밋 메시지>"   (시작 표시 /tmp/t0 필요)
set -u
MSG="$1"; KEEP=/tmp/commit_new; rm -rf $KEEP; mkdir -p $KEEP
find social/side scripts/side/emperor -type f -newer /tmp/t0 -exec cp --parents {} $KEEP/ \; 2>/dev/null
n=$(find $KEEP -type f | wc -l); echo "새 파일 $n개"; [ "$n" = "0" ] && exit 0
git config user.name "valuenote-bot"; git config user.email "bot@valuenote.co.kr"
for i in 1 2 3 4 5 6 7 8; do
  timeout 240 git fetch -q --depth 1 origin main && git reset -q --hard origin/main && cp -r $KEEP/. . \
    && git add -A social/side scripts/side/emperor && { git diff --cached --quiet && exit 0; git commit -qm "$MSG [skip ci]"; } \
    && timeout 240 git push -q origin HEAD:main && { echo "푸시 완료 ($i회)"; touch /tmp/t0; exit 0; }
  echo "재시도 $i"; sleep $((i*10))
done
exit 1
