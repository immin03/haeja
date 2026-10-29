#!/usr/bin/env bash
# 렌더 결과를 main 에 안전하게 올린다. (2026-10-29)
#
# 롱폼·릴스·사이드 채널 작업이 거의 같은 시각에 끝나면, 먼저 올라간 커밋 때문에
# 'git pull --rebase' 가 충돌하거나(얕은 체크아웃이라 exit 128) 결과 전체가 버려졌다.
# 이 스크립트는 리베이스를 하지 않는다. 이번 실행이 바꾼 파일만 따로 떼어 두고,
# 최신 main 위에 그 파일만 다시 얹어서 올린다. 실패하면 최신 main 을 다시 받아 최대 8번 반복한다.
# social/typecast_usage.json 은 덮어쓰지 않고 '저장소 값 + 이번 실행이 더 쓴 만큼'으로 합친다.
#
# 사용법:  bash scripts/ci/push_results.sh "커밋 메시지" 경로1 경로2 ...
set -u
msg="$1"; shift

git config user.name  >/dev/null || git config user.name "valuenote-bot"
git config user.email >/dev/null || git config user.email "bot@valuenote.co.kr"

# 존재하거나 저장소가 추적 중인 경로만 남긴다 (없는 경로를 넘기면 git add 가 실패하므로)
paths=()
for p in "$@"; do
  if [ -e "$p" ] || git ls-files --error-unmatch -- "$p" >/dev/null 2>&1; then paths+=("$p"); fi
done
[ ${#paths[@]} -eq 0 ] && { echo "올릴 경로 없음"; exit 0; }

base=$(git rev-parse HEAD)
git add -A -- "${paths[@]}"
changes=$(git diff --cached --no-renames --name-status "$base" -- "${paths[@]}")
[ -z "$changes" ] && { echo "바뀐 결과 없음"; exit 0; }

keep=$(mktemp -d)
usage="social/typecast_usage.json"
mkdir -p "$keep/files"
: > "$keep/deleted"; : > "$keep/list"
while IFS=$'\t' read -r st f; do
  echo "$f" >> "$keep/list"
  if [ "$st" = "D" ]; then echo "$f" >> "$keep/deleted"
  else mkdir -p "$keep/files/$(dirname "$f")"; cp -p "$f" "$keep/files/$f"; fi
done <<< "$changes"
git show "$base:$usage" > "$keep/usage_base.json" 2>/dev/null || echo '{}' > "$keep/usage_base.json"
echo "이번 실행에서 바뀐 파일 $(wc -l < "$keep/list")개"

for i in 1 2 3 4 5 6 7 8; do
  git fetch -q origin main || { sleep 5; continue; }
  git reset -q --hard origin/main
  while read -r f; do [ -n "$f" ] && rm -f -- "$f"; done < "$keep/deleted"
  while read -r f; do
    [ -f "$keep/files/$f" ] || continue
    if [ "$f" = "$usage" ] && [ -f "$f" ]; then
      python3 - "$keep/usage_base.json" "$f" "$keep/files/$f" <<'PY'
import json, sys
def load(p):
    try: return json.load(open(p))
    except Exception: return {}
base, up, mine = load(sys.argv[1]), load(sys.argv[2]), load(sys.argv[3])
out = dict(up)
for k in set(up) | set(mine):
    a, b, c = up.get(k, 0), mine.get(k, 0), base.get(k, 0)
    if all(isinstance(x, (int, float)) for x in (a, b, c)):
        out[k] = a + max(0, b - c)
    elif k not in up:
        out[k] = mine[k]
with open(sys.argv[2], "w") as fh:
    json.dump(out, fh, ensure_ascii=False, indent=1); fh.write("\n")
PY
    else
      mkdir -p "$(dirname "$f")"; cp -p "$keep/files/$f" "$f"
    fi
  done < "$keep/list"
  xargs -a "$keep/list" -d '\n' git add -A -- 2>/dev/null
  if git diff --cached --quiet; then echo "최신 main 에 이미 같은 결과가 있음"; exit 0; fi
  git commit -q -m "$msg"
  if git push -q origin HEAD:main; then echo "올림 (시도 $i)"; exit 0; fi
  echo "다른 작업이 먼저 올림 → 최신 main 으로 다시 시도 ($i/8)"
  sleep $((5 + RANDOM % 10))
done
echo "8번 시도했지만 올리지 못함"
exit 1
