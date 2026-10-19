#!/usr/bin/env bash
# 블로그용 움직이는 사진(GIF) 만들기 (2026-10-19 결정: 블로그에 동영상 대신 GIF)
# 사용: bash scripts/blog/to_gif.sh <원본 mp4> <출력 gif> [시작 초, 기본 0]
#   예: bash scripts/blog/to_gif.sh scripts/blog/media/lib/factory_47257.mp4 naver/b261020w/g1.gif
# 가로 640px · 초당 10장 · 4초 · 반복 재생. 6MB를 넘으면 가로를 줄여 다시 만든다.
# GIF는 사진과 똑같이 붙여넣기 본문에 들어가므로 사장님이 따로 영상을 받아 올릴 필요가 없다.
set -euo pipefail
src="$1"; out="$2"; ss="${3:-0}"
[ -f "$src" ] || { echo "원본이 없습니다: $src" >&2; exit 1; }
mkdir -p "$(dirname "$out")"
for w in 640 560 480; do
  ffmpeg -v error -y -ss "$ss" -t 4 -i "$src" \
    -vf "fps=10,scale=${w}:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=96:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" \
    -loop 0 "$out"
  size=$(stat -c%s "$out")
  if [ "$size" -le 6000000 ]; then echo "✓ $out · ${w}px · $((size / 1024))KB"; exit 0; fi
done
echo "✓ $out · 480px · $((size / 1024))KB (6MB 초과 — 다른 장면을 고르는 것을 권장)"
