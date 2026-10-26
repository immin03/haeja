"""마이크로소프트 쇼츠 Y261026m 잉크 노트 페이지 (2026-10-27) — 88초 판 대본(b459ac48) 그대로, 화면만 잉크 노트로"""
import json, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SPEC = os.path.join(HERE, "..", "specs", "Y261026m.json")
LOGO = "scripts/reels/assets/logo/msft_text.png"; LIB = "scripts/blog/media/lib/"
d = json.loads(subprocess.run(["git", "show", "b459ac48:scripts/reels/specs/Y261026m.json"], capture_output=True, text=True, cwd=ROOT).stdout)
o = d["scenes"]; Ls = lambda i: o[i]["lines"]
def sc(i, page, **kw): return dict({k: v for k, v in o[i].items() if k not in ("lines", "page")}, lines=kw.get("lines", Ls(i)), page=page)

p1 = sc(0, {"head": "MICROSOFT  ·  MSFT", "beats": [
    dict(kind="sticker", src=LOGO, x=560, y=150, w=380, rot=-4, line=0, at=0),
    dict(kind="print", rows=["앞으로 받기로 계약한 돈", "(받아 둔 주문 · 2025년 12월 말)"], x=80, y=180, size=36, w="Bold", line=0, at=.1),
    dict(kind="write", text="45%", x=70, y=300, size=230, color="red", line=0, at=.5, dur=.9),
    dict(kind="write", text="= 한 회사", x=470, y=400, size=100, line=0, at=.8),
    dict(kind="photo", src=LIB + "commons_chatgpt_1.jpg", x=80, y=640, w=430, h=320, rot=-3, cap="챗GPT", fy=.2, line=1, at=0),
    dict(kind="write", rows=["챗GPT를 만든", "오픈AI"], x=560, y=680, size=96, color="red", line=1, at=.3),
]})
p2 = sc(1, {"head": "마이크로소프트는 어떤 회사?", "beats": [
    dict(kind="write", text="윈도 · 엑셀", x=80, y=170, size=96, color="gray", line=0, at=0),
    dict(kind="arrow", pts=[[200, 300], [200, 570]], color="ink", line=0, at=.45),
    dict(kind="photo", src=LIB + "commons_msftdc_3.jpg", x=520, y=180, w=440, h=300, rot=3, cap="애저 데이터센터", line=0, at=.55),
    dict(kind="write", text="클라우드 '애저'", x=80, y=590, size=110, color="blue", line=0, at=.7),
    dict(kind="write", text="+43%", x=70, y=760, size=200, color="green", line=1, at=.05),
    dict(kind="print", rows=["애저 매출 · 1년 전보다 (2026년 4~6월)", "1년 매출 처음으로 1,000억 달러 넘음"], x=84, y=1000, size=36, w="Bold", line=1, at=.5),
]})
p3 = sc(2, {"head": "받아 둔 주문", "beats": [
    dict(kind="bars", items=[{"label": "1년 전", "v": 2980, "text": "약 2,980억", "color": "gray"}, {"label": "2025년 12월 말", "v": 6250, "text": "6,250억 달러", "color": "ink"}],
         x=120, y=330, w=840, h=360, line=0, at=0),
    dict(kind="print", text="받아 둔 주문 · 1년 새", x=84, y=170, size=40, w="ExtraBold", line=0, at=.15),
    dict(kind="write", text="2배+", x=700, y=140, size=100, color="green", line=0, at=.45),
    dict(kind="print", text="그중 오픈AI 몫 (네모 20칸 = 100%)", x=84, y=800, size=34, w="Bold", color="gray", line=1, at=0),
    dict(kind="icons", icon="box", n=10, hl=list(range(9)), x=80, y=850, size=80, gap=10, color="ink", hlcolor="red", line=1, at=.1, dur=.6),
    dict(kind="icons", icon="box", n=10, x=80, y=965, size=80, gap=10, color="gray", line=1, at=.35, dur=.4),
    dict(kind="write", text="45% = 오픈AI", x=80, y=1075, size=80, color="red", line=1, at=.6),
]})
p4 = sc(3, {"head": "왜 오픈AI일까?", "beats": [
    dict(kind="pop", src=LIB + "commons_openaihq_1.jpg", cap="샌프란시스코 · 오픈AI가 있던 파이오니어 빌딩", line=0, at=0),
    dict(kind="write", rows=["챗GPT를 돌리려면", "서버가 끝없이"], x=80, y=170, size=100, line=0, at=.55, dur=1.0),
    dict(kind="icons", icon="server", n=7, x=80, y=410, size=100, gap=22, color="ink", line=0, at=.8, dur=.5),
    dict(kind="write", text="2,500억 달러", x=70, y=570, size=130, color="red", line=1, at=.2),
    dict(kind="print", text="2025년 10월 계약 · 애저(마이크로소프트 클라우드)를 더 쓰기로", x=84, y=730, size=32, w="Bold", color="gray", line=1, at=.6),
    dict(kind="write", rows=["MS = 오픈AI 지분", "약 27% 주주"], x=80, y=830, size=92, color="blue", line=2, at=.1),
]})
p5 = sc(4, {"head": "오픈AI가 한 약속", "beats": [
    dict(kind="bars", items=[{"label": "오픈AI 1년 매출", "v": 200, "text": "200억+", "color": "gray"}, {"label": "애저 더 쓰기로 한 돈", "v": 2500, "text": "2,500억", "color": "red"}],
         x=120, y=230, w=840, h=520, line=0, at=0),
    dict(kind="arrow", pts=[[330, 700], [600, 280]], color="red", line=0, at=.45, width=10),
    dict(kind="print", text="2025년 · 오픈AI 발표 / 계약은 여러 해에 나눠 쓰는 돈", x=84, y=820, size=30, w="Bold", color="gray", line=0, at=.75),
    dict(kind="write", text="10배 안팎", x=80, y=880, size=120, color="red", line=1, at=0),
    dict(kind="write", text="더 벌거나 · 투자받거나", x=80, y=1050, size=80, line=1, at=.45),
]})
p6 = sc(5, {"head": "주문을 채우려면", "beats": [
    dict(kind="photo", src=LIB + "commons_msftdc_4.jpg", x=80, y=160, w=520, h=360, rot=-2, cap="애저 데이터센터 짓는 중", line=0, at=0),
    dict(kind="write", rows=["번 현금의", "63%"], x=640, y=190, size=110, color="red", line=0, at=.35),
    dict(kind="print", text="= 데이터센터 (2026 회계연도 · 1,829억 달러 중 1,159억)", x=84, y=620, size=32, w="Bold", color="gray", line=0, at=.75),
    dict(kind="write", rows=["오픈AI가 약속을 못 지키면", "건물만 남는다"], x=80, y=720, size=96, line=1, at=.1, dur=1.2),
]})
p7 = sc(6, {"head": "그래도", "beats": [
    dict(kind="write", text="오픈AI 빼도", x=80, y=170, size=96, line=0, at=0),
    dict(kind="write", text="+25%", x=520, y=140, size=170, color="green", line=0, at=.6),
    dict(kind="print", text="받아 둔 주문 · 1년 전보다 (2026년 6월 말)", x=84, y=360, size=32, w="Bold", color="gray", line=0, at=.8),
    dict(kind="write", text="이번 실적, 이 3가지", x=80, y=470, size=100, color="red", line=1, at=.1),
]}, lines=Ls(6))
p8 = sc(7, {"head": "마이크로소프트 주가, 이 3가지", "beats": [
    dict(kind="check", text="오픈AI 뺀 주문", x=80, y=200, size=70, line=0, at=0),
    dict(kind="print", text="지난번 +25%", x=720, y=215, size=40, w="ExtraBold", color="green", line=0, at=.6),
    dict(kind="check", text="애저 매출 증가율", x=80, y=480, size=70, line=1, at=0),
    dict(kind="print", text="지난번 +43%", x=720, y=495, size=40, w="ExtraBold", color="green", line=1, at=.6),
    dict(kind="check", text="데이터센터에 쓰는 돈", x=80, y=760, size=70, line=2, at=0),
    dict(kind="print", text="지난해 번 현금의 63%", x=170, y=865, size=40, w="ExtraBold", color="red", line=2, at=.6),
]})
p9 = {"type": "cta", "l1": "더 많은 정보를 원하시면", "l2": "좋아요와 구독",
      "lines": [{"cap": ["더 많은 정보를 원하시면", "좋아요와 구독 눌러 주세요"], "say": "더 많은 정보를 원하시면, 좋아요와 구독 눌러 주세요.", "pause": 1.4}],
      "page": {"head": "VALUENOTE", "beats": [
    dict(kind="sticker", src=LOGO, x=520, y=170, w=380, rot=4, line=0, at=0),
    dict(kind="write", rows=["더 많은 정보는", "좋아요 + 구독"], x=80, y=380, size=124, line=0, at=.05, dur=1.4),
    dict(kind="under", x0=90, x1=760, y=650, color="red", line=0, at=.8),
]}}
d["scenes"] = [p1, p2, p3, p4, p5, p6, p7, p8, p9]
d["world"] = "ink"; d["end"] = "subscribe"; d["ink_strict"] = True
d["subs_en"] = d["subs_en"][:-1] + ["Want more? Like and subscribe"]
json.dump(d, open(SPEC, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("ok", sum(len(s["lines"]) for s in d["scenes"]), len(d["subs_en"]))
