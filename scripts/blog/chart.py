"""블로그·칼럼용 선 그래프 (1080×1080 PNG, 밸류노트 네이비·골드)

사용: python3 scripts/blog/chart.py <출력.png> <spec.json>
spec = {
  "eyebrow": "작은 머리말", "title": "제목 (한 줄 또는 두 줄)",
  "series": [{"name": "코스피", "points": [["2026-10-01", 231.9], ...], "color": "gold|ink|up|down|mute"}],
  "rebase": "2026-09-15"   # 선택: 이 날짜를 100으로 맞춰 비교
  "unit": "%",             # 선택: 축·끝값 뒤에 붙일 단위
  "decimals": 1,           # 선택: 끝값 소수 자릿수
  "highlight": ["2026-10-13", "2026-10-15"],   # 선택: 음영 구간
  "highlight_label": "검은 목요일",            # 선택
  "note": "그래프 아래 한 줄 설명", "foot": "출처·기준일"
}
글꼴: Pretendard (npm i --no-save pretendard@1.3.9 로 받은 node_modules 에서 읽는다)
"""
import json, sys, os, datetime as dt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
import matplotlib.dates as mdates

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
FD = os.path.join(ROOT, "node_modules", "pretendard", "dist", "public", "static")
for w in ("Medium", "Bold", "ExtraBold", "Black"):
    p = os.path.join(FD, f"Pretendard-{w}.otf")
    if os.path.exists(p):
        fm.fontManager.addfont(p)
plt.rcParams["font.family"] = "Pretendard"
plt.rcParams["axes.unicode_minus"] = False

C = {"bg": "#0E1A2B", "bg2": "#1A2C46", "ink": "#F3EEE3", "mute": "#AEB8C8", "dim": "#8E9AAD",
     "gold": "#EADBB9", "gold2": "#C9AF7A", "up": "#7FD3A8", "down": "#FF9BAC", "grid": "#2A3B55"}

out, specf = sys.argv[1], sys.argv[2]
sp = json.load(open(specf, encoding="utf-8"))
unit, dec = sp.get("unit", ""), sp.get("decimals", 1)

fig = plt.figure(figsize=(10.8, 10.8), dpi=100)
fig.patch.set_facecolor(C["bg"])
# 머리 (로고·머리말·제목)
fig.text(0.067, 0.94, "Value", color=C["ink"], fontsize=24, fontweight="black", va="center")
fig.text(0.155, 0.94, "Note", color=C["gold"], fontsize=24, fontweight="black", va="center")
fig.text(0.235, 0.94, "밸류노트", color=C["gold2"], fontsize=16, fontweight="bold", va="center")
y = 0.86
if sp.get("eyebrow"):
    fig.text(0.067, y, sp["eyebrow"], color=C["gold"], fontsize=19, fontweight="extra bold", va="top"); y -= 0.045
fig.text(0.067, y, sp["title"], color=C["ink"], fontsize=31, fontweight="black", va="top", linespacing=1.25)
nl = sp["title"].count("\n") + 1

ax = fig.add_axes([0.1, 0.2, 0.78, 0.65 - 0.06 * nl - (0.045 if sp.get("eyebrow") else 0)])
ax.set_facecolor(C["bg"])
for s in ax.spines.values():
    s.set_visible(False)
ax.grid(axis="y", color=C["grid"], linewidth=1)
ax.tick_params(colors=C["dim"], labelsize=14, length=0)

def pts(s):
    p = [(dt.date.fromisoformat(d), float(v)) for d, v in s["points"]]
    if sp.get("rebase"):
        base = next((v for d, v in p if d >= dt.date.fromisoformat(sp["rebase"])), p[0][1])
        p = [(d, v / base * 100) for d, v in p]
    return p

ends = []
for s in sp["series"]:
    p = pts(s)
    col = C.get(s.get("color", "gold"), s.get("color"))
    xs, ys = [d for d, _ in p], [v for _, v in p]
    ax.plot(xs, ys, color=col, linewidth=4, solid_capstyle="round")
    ax.scatter([xs[-1]], [ys[-1]], color=col, s=90, zorder=5)
    lab = f"{s['name']}  {ys[-1]:,.{dec}f}{unit}"
    ends.append((ys[-1], s["name"], f"{ys[-1]:,.{dec}f}{unit}", col, xs[-1]))
# 끝값 이름표: 그래프 오른쪽 바깥에, 겹치지 않게 위아래로 벌려 놓는다
x0, x1 = ax.get_xlim()
ax.set_xlim(x0, x1 + (x1 - x0) * 0.30)
lo, hi = ax.get_ylim(); gap = (hi - lo) * 0.1
ends.sort(key=lambda e: e[0])
placed = []
for v, name, val, col, xe in ends:
    y = v if not placed else max(v, placed[-1] + gap)
    placed.append(y)
    ax.annotate(f"{name}\n{val}", (xe, v), xytext=(mdates.date2num(xe) + (x1 - x0) * 0.03, y), textcoords="data",
                ha="left", va="center", color=col, fontsize=17, fontweight="extra bold", linespacing=1.1)
if sp.get("highlight"):
    a, b = [dt.date.fromisoformat(x) for x in sp["highlight"]]
    ax.axvspan(a - dt.timedelta(hours=12), b + dt.timedelta(hours=12), color=C["down"], alpha=0.13, lw=0)
    if sp.get("highlight_label"):
        ax.text(a, 1.01, sp["highlight_label"], transform=ax.get_xaxis_transform(), color=C["down"],
                fontsize=15, fontweight="bold", ha="right", va="bottom")
if sp.get("rebase"):
    ax.axhline(100, color=C["mute"], lw=1.2, ls=(0, (4, 4)), alpha=0.7)
_span = (x1 - x0) if isinstance(x1 - x0, float) else (mdates.date2num(x1) - mdates.date2num(x0))
if _span > 730:  # 2년 넘는 그래프는 연도로 (월/일로 쓰면 "1/1" 만 반복된다)
    _yrs = max(1, round(_span / 365 / 6))
    ax.xaxis.set_major_locator(mdates.YearLocator(_yrs))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
elif _span > 200:
    ax.xaxis.set_major_locator(mdates.MonthLocator(bymonth=[1, 4, 7, 10]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%y.%-m"))
else:
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%-m/%-d"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=4, maxticks=7))
_last = max(mdates.date2num(e[4]) for e in ends)
ax.set_xticks([t for t in ax.get_xticks() if t <= _last + 0.5])
ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v, _: f"{v:,.{max(0, dec - 1) if unit != '%' else dec}f}{unit if unit == '%' else ''}"))

if sp.get("note"):
    fig.text(0.067, 0.115, sp["note"], color=C["ink"], fontsize=19, fontweight="bold", va="top", wrap=True)
fig.text(0.067, 0.045, sp.get("foot", "투자 교육용 정보 · 매수·매도 권유가 아닙니다"), color=C["dim"], fontsize=14, fontweight="bold")
fig.text(0.933, 0.045, "valuenote.co.kr", color=C["dim"], fontsize=14, fontweight="bold", ha="right")
fig.savefig(out, facecolor=C["bg"])
print("✓", out)
