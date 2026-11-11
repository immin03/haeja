#!/usr/bin/env bash
# 황제의 일기 롱폼 렌더 글꼴을 /root/fonts(또는 $1)에 모은다 — 한국어(longform.py)와 영어(en/longform_en.py, ED_EN_TYPE=a) 모두.
# 2026-11-11 구간 병렬 렌더(ed-long-render.yml)용. 저장소 글꼴(scripts/reels/fonts) + Google Fonts 원본 + fontsource(npm).
set -euo pipefail
D="${1:-/root/fonts}"; mkdir -p "$D"; T=$(mktemp -d)
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
cp "$ROOT"/scripts/reels/fonts/SUIT-*.ttf "$D"/ 2>/dev/null || true
g() { curl -sSL --retry 3 --max-time 120 -o "$D/$2" "https://raw.githubusercontent.com/google/fonts/main/ofl/$1"; }
g "pinyonscript/PinyonScript-Regular.ttf" PinyonScript-Regular.ttf
g "cormorantsc/CormorantSC-SemiBold.ttf" CormorantSC-SemiBold.ttf
g "cinzel/Cinzel%5Bwght%5D.ttf" Cinzel.ttf
g "inter/Inter%5Bopsz,wght%5D.ttf" Inter.ttf
g "hahmlet/Hahmlet%5Bwght%5D.ttf" "Hahmlet[wght].ttf"
g "anton/Anton-Regular.ttf" Anton.ttf; cp "$D/Anton.ttf" "$D/Anton.woff"
P=https://raw.githubusercontent.com/orioncactus/pretendard/main/packages/pretendard/dist/public/static
for w in SemiBold Medium Bold ExtraBold; do curl -sSL --retry 3 --max-time 120 -o "$D/Pretendard-$w.otf" "$P/Pretendard-$w.otf"; done
# fontsource (woff) — 영어 글꼴 체계 (a) 는 woff 그대로, 한국어 렌더러는 ttf 이름으로 찾으므로 바꿔 둔다
(cd "$T" && for p in eb-garamond cormorant-garamond cormorant-sc; do npm pack -s "@fontsource/$p" >/dev/null; done
 for f in *.tgz; do n=$(basename "$f" .tgz | sed 's/^fontsource-//; s/-[0-9.]*$//'); mkdir -p "$D/fs_$n"; tar xzf "$f"; cp package/files/*.woff "$D/fs_$n/"; rm -rf package; done)
python3 - "$D" <<'EOF'
import sys, os, glob
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
D = sys.argv[1]
for src, name, loc in [("Cinzel.ttf", "Cinzel-SemiBold.ttf", {"wght": 600}), ("Inter.ttf", "Inter-SemiBold.ttf", {"wght": 600, "opsz": 14}), ("Inter.ttf", "Inter-Bold.ttf", {"wght": 700, "opsz": 14}),
                        ("Hahmlet[wght].ttf", "hahmlet-korean-700-normal.ttf", {"wght": 700}), ("Hahmlet[wght].ttf", "hahmlet-korean-600-normal.ttf", {"wght": 600})]:   # 한글 전체 글리프
    f = TTFont(os.path.join(D, src)); ax = {a.axisTag for a in f["fvar"].axes}
    instancer.instantiateVariableFont(f, {k: v for k, v in loc.items() if k in ax}, inplace=True); f.save(os.path.join(D, name))
# 한국어 렌더러 이름 (longform.py font()): woff → ttf 로 저장
want = {"cormorant-sc-latin-600-normal.ttf": "fs_cormorant-sc/cormorant-sc-latin-600-normal.woff", "cormorant-sc-latin-500-normal.ttf": "fs_cormorant-sc/cormorant-sc-latin-500-normal.woff",
        "cormorant-garamond-latin-500-italic.ttf": "fs_cormorant-garamond/cormorant-garamond-latin-500-italic.woff",
        "CormorantGaramond-Bold.ttf": "fs_cormorant-garamond/cormorant-garamond-latin-700-normal.woff", "CormorantGaramond-SemiBold.ttf": "fs_cormorant-garamond/cormorant-garamond-latin-600-normal.woff",
        "CormorantGaramond-MediumItalic.ttf": "fs_cormorant-garamond/cormorant-garamond-latin-500-italic.woff"}
for out, src in want.items():
    p = os.path.join(D, src)
    if os.path.exists(p): f = TTFont(p); f.flavor = None; f.save(os.path.join(D, out))
    else: print("missing", src)
print("fonts ready:", len(os.listdir(D)))
EOF
rm -rf "$T"
