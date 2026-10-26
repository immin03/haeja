"""삼성전자 쇼츠 Y261026c 잉크 노트 페이지 (2026-10-26) — python3 scripts/reels/inkpages/Y261026c.py 로 대본에 써 넣는다"""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); SPEC = os.path.join(HERE, "..", "specs", "Y261026c.json")
LOGO = "scripts/reels/assets/logo/samsung.png"; LIB = "scripts/blog/media/lib/"; BR = "scripts/reels/assets/broll/"; PU = "scripts/reels/assets/popup/"
ser = json.load(open(os.path.join(HERE, "Y261026c_series.json")))
xs, vs = ser["xs"], ser["vs"]; PK = vs.index(max(vs)); N = len(vs) - 1
def L(cap, say): return {"cap": cap, "say": say}
CH = dict(series=vs, xs=xs, x=110, y=560, w=840, h=440, lo=0, hi=380000)

d = json.load(open(SPEC, encoding="utf-8"))
old = d["scenes"]
# ── 1. 4만 전자 → 37만 → 21만 (한 페이지에 그래프가 이어서 그려진다)
p1 = {"type": "hook", "lines": old[0]["lines"] + old[1]["lines"] + old[2]["lines"], "page": {"head": "SAMSUNG  ·  005930", "beats": [
    dict(kind="sticker", src=LOGO, x=640, y=150, w=300, rot=-5, line=0, at=0),
    dict(kind="print", text="2024년 11월 14일", x=80, y=170, size=40, w="ExtraBold", line=0, at=0),
    dict(kind="write", text="49,900원", x=70, y=215, size=140, color="red", line=0, at=.35),
    dict(kind="write", text="'4만 전자'", x=80, y=390, size=90, line=1, at=.0),
    dict(kind="hl", x0=76, y0=408, x1=440, y1=486, color="yellow", line=1, at=.45),
    dict(kind="chart", **CH, to=PK, color="green", line=2, at=.05, dur=1.8, labels={"0": "4만 9,900"}, labcolor="ink", labdy=14),
    dict(kind="write", text="6월 37만 4천 원", x=330, y=470, size=72, color="green", line=2, at=.65),
    dict(kind="circle", cx=800, cy=600, rx=95, ry=70, color="green", line=3, at=0),
    dict(kind="write", text="1년 반 만에 7배+", x=110, y=1035, size=78, color="green", line=3, at=.3),
    dict(kind="chart", **CH, **{"from": PK}, to=N, color="red", line=4, at=.05, dur=1.6, axis=False, width=12),
    dict(kind="write", text="-42%", x=640, y=800, size=130, color="red", line=4, at=.55),
    dict(kind="print", text="지금 21만 5천 원 · 10월 23일", x=1000, y=1135, size=34, w="Bold", color="red", anchor="ra", line=4, at=.5),
]}}
# ── 2. 버틸 수 있을까?
p2 = {"type": "statement", "l1": old[3].get("l1", ""), "l2": old[3].get("l2", ""), "lines": old[3]["lines"], "page": {"head": "그럼 지금 가격은?", "beats": [
    dict(kind="pop", src=LIB + "commons_wafer_2.jpg", cap="반도체 공장 클린룸", line=0, at=0),
    dict(kind="write", rows=["21만 원대,", "버틸 수 있을까?"], x=80, y=200, size=118, line=0, at=.05, dur=.6),
    dict(kind="write", text="10월 29일 실적", x=80, y=560, size=104, color="red", line=1, at=.05),
    dict(kind="circle", cx=360, cy=620, rx=330, ry=95, color="red", line=1, at=.4),
    dict(kind="icons", icon="box", n=3, x=110, y=800, size=150, gap=110, color="ink", line=1, at=.55, dur=.6),
    dict(kind="write", text="?   ?   ?", x=150, y=820, size=120, color="gold", line=1, at=.8, dur=.5),
]}}
# ── 3. 볼 숫자 3개 (체크리스트 + 사진)
p3 = {"type": "list", "title": old[4]["title"], "items": old[4]["items"], "lines": old[4]["lines"], "page": {"head": "삼성전자 주가, 이 3가지", "beats": [
    dict(kind="check", text="빅테크 설비투자", x=80, y=230, size=70, line=0, at=0),
    dict(kind="photo", src=LIB + "commons_datacenter_3.jpg", x=700, y=170, w=300, h=230, rot=4, line=0, at=.3),
    dict(kind="check", text="삼성 HBM4 판매", x=80, y=530, size=70, line=1, at=0),
    dict(kind="photo", src=LIB + "commons_nvidiagpu_1.jpg", x=700, y=470, w=300, h=230, rot=-3, line=1, at=.3),
    dict(kind="check", text="D램 값 오르는 속도", x=80, y=830, size=70, line=2, at=0),
    dict(kind="photo", src=LIB + "commons_ddr5_3.jpg", x=700, y=770, w=300, h=230, rot=3, line=2, at=.3),
]}}
# ── 4. ① 빅테크 설비투자
p4 = {"type": "statement", "l1": old[5]["l1"], "l2": old[5]["l2"], "note": old[5].get("note"), "lines": old[5]["lines"], "page": {"head": "1. 빅테크 설비투자", "beats": [
    dict(kind="photo", src=BR + "datacenter_23282.mp4", x=80, y=150, w=470, h=330, rot=-2, cap="빅테크 데이터센터", line=0, at=0),
    dict(kind="print", rows=["아마존 · 알파벳", "마이크로소프트", "메타", "올해 계획 합계"], x=610, y=180, size=36, w="Bold", color="gray", line=0, at=.2),
    dict(kind="write", text="7,350억 달러", x=70, y=500, size=124, color="red", line=0, at=.45),
    dict(kind="under", x0=80, x1=760, y=635, color="red", line=0, at=.85),
    dict(kind="arrow", pts=[[300, 650], [300, 735]], color="ink", line=1, at=0),
    dict(kind="icons", icon="chip", n=6, x=90, y=745, size=84, gap=30, color="ink", line=1, at=.12, dur=.8),
    dict(kind="write", text="= AI 칩 + 메모리 예산", x=80, y=840, size=78, color="gold", line=1, at=.45),
    dict(kind="pop", src=LIB + "commons_metahq_1.jpg", cap="지난주 메타 -7% → 삼성전자 -4%", line=2, at=0),
    dict(kind="write", text="메타 -7%   삼성 -4%", x=80, y=950, size=84, color="red", line=2, at=.62),
    dict(kind="write", text="더 쓰면 O 좋은 신호", x=80, y=1050, size=70, color="green", line=3, at=.3),
    dict(kind="write", text="줄이면 X 경고", x=620, y=1050, size=70, color="red", line=3, at=.7),
]}}
# ── 5. ② HBM4
p5 = {"type": "compare", "title": old[6]["title"], "l": old[6]["l"], "r": old[6]["r"], "lines": old[6]["lines"], "page": {"head": "2. 삼성전자 HBM4 판매", "beats": [
    dict(kind="pop", src=LIB + "commons_nvidiahq_1.jpg", cap="HBM4, 2월부터 엔비디아에 공급", line=0, at=0),
    dict(kind="write", text="HBM4, 엔비디아로", x=70, y=170, size=96, line=0, at=.55),
    dict(kind="photo", src=LIB + "commons_nvidiagpu_1.jpg", x=700, y=140, w=300, h=210, rot=4, line=0, at=.8),
    dict(kind="print", text="2026년 2월부터 공급 · HBM 점유율 (카운터포인트리서치)", x=80, y=320, size=30, w="Medium", color="gray", line=0, at=.8),
    dict(kind="bars", items=[{"label": "삼성 1분기", "v": 21, "text": "21%", "color": "gray"}, {"label": "삼성 2분기", "v": 33, "text": "33%", "color": "green"},
                             {"label": "SK하이닉스", "v": 50, "text": "50%", "color": "ink"}], x=90, y=470, w=900, h=380, line=1, at=0),
    dict(kind="arrow", pts=[[330, 780], [520, 640]], color="green", line=1, at=.6),
    dict(kind="write", text="콜에서 'HBM4 공급 늘었다'?", x=70, y=960, size=76, line=2, at=0),
    dict(kind="write", text="O 추격 계속    X 멈춤", x=90, y=1060, size=78, color="red", line=2, at=.55),
]}}
# ── 6. ③ D램 값
p6 = {"type": "compare", "title": old[7]["title"], "l": old[7]["l"], "r": old[7]["r"], "lines": old[7]["lines"], "page": {"head": "3. D램 값이 오르는 속도", "beats": [
    dict(kind="photo", src=PU + "ram_dram1.mp4", x=620, y=150, w=380, h=270, rot=3, line=0, at=0),
    dict(kind="write", text="1분기: 석 달 +90%", x=70, y=170, size=80, line=0, at=.2),
    dict(kind="arrow", pts=[[110, 440], [330, 290]], color="ink", line=0, at=.75, width=12),
    dict(kind="write", text="9월: 한 달 +4%", x=70, y=470, size=92, color="red", line=1, at=.0),
    dict(kind="arrow", pts=[[110, 700], [430, 650]], color="red", line=1, at=.45, width=12),
    dict(kind="write", text="느려졌다", x=460, y=600, size=78, color="red", line=1, at=.7),
    dict(kind="print", rows=["값 100원 - 비용 50원 = 이익 50원", "값  90원 - 비용 50원 = 이익 40원"], x=80, y=770, size=40, w="Bold", line=2, at=.05),
    dict(kind="write", text="값 -10%면 이익 -20%", x=70, y=880, size=92, color="red", line=2, at=.45),
    dict(kind="write", text="주가는 '속도'를 먼저 본다", x=70, y=1010, size=84, color="gold", line=3, at=.05),
    dict(kind="under", x0=80, x1=880, y=1110, color="gold", line=3, at=.7),
]}}
# ── 7. 풀영상
p7 = dict(old[8]); p7["page"] = {"head": "메모리 수업 9분 풀버전", "beats": [
    dict(kind="pop", src=LIB + "commons_wafer_3.jpg", cap="HBM · 메모리 사이클 9분 수업", line=0, at=0),
    dict(kind="write", rows=["HBM이 뭔지,", "메모리 값이 왜", "오르내리는지"], x=80, y=180, size=100, line=0, at=.55, dur=.9),
    dict(kind="write", text="하단 프로필 링크", x=540, y=760, size=120, color="red", anchor="m", line=1, at=0),
    dict(kind="circle", cx=540, cy=830, rx=420, ry=110, color="red", line=1, at=.4),
    dict(kind="arrow", pts=[[540, 960], [540, 1180]], color="red", line=1, at=.6, width=12),
]}
d["scenes"] = [p1, p2, p3, p4, p5, p6, p7]
d["world"] = "ink"
json.dump(d, open(SPEC, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok", sum(len(s["lines"]) for s in d["scenes"]))
