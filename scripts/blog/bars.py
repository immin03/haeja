"""블로그용 막대 비교 그림 (1080×1080 PNG, 밸류노트 네이비·아이보리) — 2026-10-30 운영자: "비교는 그래프로 보여 주는 게 더 낫다"

사용: python3 scripts/blog/bars.py <출력.png> <spec.json>
spec = {
  "title": "구글이 갚아야 할 빚\n1년 사이 다섯 배",       # 생활 말, 두 줄까지
  "bars": [{"label": "1년 전", "value": 216, "text": "216억 달러"},
           {"label": "2026년 3분기", "value": 1251, "text": "1,251억 달러"}],   # 2~4개, 마지막 막대가 강조
  "note": "갚을 날이 1년 넘게 남은 빚",                  # 그림 아래 한 줄 (선택)
  "foot": "알파벳 3분기 실적 기준"                       # 출처·기준일 (선택)
}
글꼴: Pretendard (node_modules/pretendard, npm i --no-save pretendard@1.3.9)
"""
import json, os, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FD = os.path.join(ROOT, "node_modules/pretendard/dist/public/static")
F = {w: fm.FontProperties(fname=os.path.join(FD, f"Pretendard-{w}.otf")) for w in ("Bold", "ExtraBold", "Medium", "Regular")}

BG, INK, MUTE, IVORY, DIM, LINE = "#0F1A2E", "#F4EFE4", "#9AA6B8", "#E9D9B4", "#4A5872", "#2A3650"

def main(out, spec):
    s = json.load(open(spec, encoding="utf-8"))
    bars = s["bars"]
    fig = plt.figure(figsize=(10.8, 10.8), dpi=100)
    fig.patch.set_facecolor(BG)
    # 제목
    fig.text(0.07, 0.90, s["title"], fontproperties=F["ExtraBold"], fontsize=40, color=INK, va="top", linespacing=1.35)
    ax = fig.add_axes([0.09, 0.20, 0.82, 0.50])
    ax.set_facecolor(BG)
    n = len(bars)
    vals = [b["value"] for b in bars]
    top = max(vals) if max(vals) > 0 else 1
    colors = [DIM] * (n - 1) + [IVORY]
    xs = list(range(n))
    ax.bar(xs, vals, width=0.56, color=colors, zorder=2)
    for x, b, c in zip(xs, bars, colors):
        ax.text(x, b["value"] + top * 0.03, b.get("text", str(b["value"])), ha="center", va="bottom",
                fontproperties=F["ExtraBold"], fontsize=34, color=INK if c == IVORY else MUTE)
        ax.text(x, -top * 0.06, b["label"], ha="center", va="top", fontproperties=F["Medium"], fontsize=24, color=MUTE)
    ax.set_ylim(0, top * 1.22)
    ax.set_xlim(-0.6, n - 0.4)
    ax.axhline(0, color=LINE, lw=2, zorder=3)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xticks([]); ax.set_yticks([])
    if s.get("note"):
        fig.text(0.07, 0.085, s["note"], fontproperties=F["Bold"], fontsize=22, color=IVORY, va="bottom")
    if s.get("foot"):
        fig.text(0.07, 0.045, s["foot"], fontproperties=F["Regular"], fontsize=18, color=MUTE, va="bottom")
    fig.savefig(out, facecolor=BG)
    print("✓", out)

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
