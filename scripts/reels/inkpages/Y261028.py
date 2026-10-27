"""스타벅스 롱폼(L261026-starbucks-float) 파생 쇼츠 Y261028a·b·c 잉크 노트 대본 (2026-10-27)
python3 scripts/reels/inkpages/Y261028.py 로 specs/Y261028a.json, b, c 를 새로 쓴다. 숫자는 승인된 롱폼 대본과 .data.json(10월 26일 종가)만 쓴다."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); SPECS = os.path.join(HERE, "..", "specs")
LIB = "scripts/blog/media/lib/"; BR = "scripts/reels/assets/broll/"
def L(cap, say=None, **k):
    d = {"cap": cap}
    if say: d["say"] = say
    d.update(k); return d

LONG = "L261026-starbucks-float"
BASE = {"approved": False, "platform": "youtube", "threads_tag": "주식", "long": LONG, "world": "ink", "allow_long": True, "end": "subscribe",
        "full_say": "풀버전은 하단 프로필 링크에서 보세요.", "full_cap": ["풀버전은 하단 프로필 링크에서"]}
CREDIT = "\n\n사진: Wikimedia Commons (작가·라이선스는 각 파일 페이지) · 매수·매도 권유가 아닙니다."

def cta(head, rows, photo, pcap):
    return {"type": "cta", "l1": "더 많은 정보를 원하시면", "l2": "좋아요와 구독",
            "lines": [L(["더 많은 정보를 원하시면 좋아요와 구독", "풀영상은 하단 프로필 링크에서"], "더 많은 정보를 원하시면, 좋아요와 구독 눌러 주세요.", pause=1.6)],
            "page": {"head": "VALUENOTE", "beats": [
                dict(kind="write", rows=rows, x=80, y=190, size=96, color="gold", line=0, at=0, dur=.9),
                dict(kind="write", rows=["더 많은 정보는", "좋아요 + 구독"], x=80, y=470, size=112, line=0, at=.25, dur=1.2),
                dict(kind="under", x0=90, x1=720, y=715, color="red", line=0, at=.7),
                dict(kind="photo", src=LIB + photo, x=90, y=800, w=380, h=290, rot=-3, cap=pcap, line=0, at=.85),
                dict(kind="write", rows=["풀영상은", "하단 프로필 링크"], x=520, y=830, size=80, color="red", line=0, at=1.0, dur=1.0),
                dict(kind="arrow", pts=[[760, 1030], [760, 1170]], color="red", line=0, at=1.25, width=12)]}}

# ───────────────────────── a. 앱에 잠든 2조 원 (충전금의 정체) ─────────────────────────
A = dict(BASE, id="Y261028a", scheduled_at="2026-10-28T11:00:00+09:00", mood="calm", broll="money",
         title="스타벅스 앱에 잠든 2조 원, 진짜 돈은 이자가 아니었다 #스타벅스",
         title_en="$1.75B sits in the Starbucks app. The real money isn't the interest #Starbucks",
         banner=["스타벅스 앱에 잠든 2조 원", "진짜 돈은 이자가 아니었다"], cover_title="스타벅스 앱에\n잠든 2조 원\n진짜 돈은?",
         hashtags=["스타벅스", "스타벅스주가", "스타벅스충전금", "미국주식", "밸류노트", "shorts"],
         message="손님이 앱에 넣어 둔 17억 5천만 달러는 이자 없는 빚이지만, 이자로 버는 돈은 작고 진짜 힘은 손님을 다시 오게 만드는 데 있다.")
A["scenes"] = [
    {"type": "hook", "lines": [
        L(["미국 스타벅스 손님들이 앱에 넣어 두고", "안 쓴 돈, 다 합치면 얼마일까요?"], "미국 스타벅스 손님들이 앱에 넣어 두고 안 쓴 돈, 다 합치면 얼마일까요?"),
        L(["약 17억 5천만 달러", "우리 돈 2조 3천억 원이 넘습니다"], "약 십칠억 오천만 달러, 우리 돈 이조 삼천억 원이 넘습니다."),
    ], "page": {"head": "STARBUCKS  ·  SBUX", "beats": [
        dict(kind="photo", src=LIB + "phone_4915_a.jpg", x=600, y=150, w=400, h=290, rot=4, cap="출근길 앱 주문", line=0, at=0),
        dict(kind="print", text="미국 스타벅스 앱 · 카드 잔액", x=80, y=190, size=40, w="ExtraBold", line=0, at=.15),
        dict(kind="write", rows=["손님이 넣어 두고", "안 쓴 돈"], x=80, y=260, size=96, line=0, at=.4, dur=1.0),
        dict(kind="write", text="17억 5천만 달러", x=70, y=560, size=128, color="red", line=1, at=.0),
        dict(kind="under", x0=80, x1=900, y=700, color="red", line=1, at=.4),
        dict(kind="write", text="= 2조 3천억 원+", x=80, y=760, size=110, color="gold", line=1, at=.55),
        dict(kind="print", text="2026년 6월 28일 기준 · 1달러 1,324.2원", x=84, y=930, size=32, w="Medium", color="gray", line=1, at=.75),
    ]}},
    {"type": "statement", "l1": "석 달 충전", "l2": "31억 달러", "lines": [
        L(["돈이 모자라면 앱이", "25달러씩 자동으로 채워 주죠"], "돈이 모자라면, 앱이 이십오 달러씩 자동으로 채워 주죠."),
        L(["쌓인 돈은 2조인데, 석 달마다 4조 원이", "새로 들어왔다 나가요, 계속 도는 돈이죠"], "쌓인 돈은 이조인데, 석 달마다 사조 원이 새로 들어왔다 나가요. 계속 도는 돈이죠."),
    ], "page": {"head": "돈이 먼저 들어온다", "beats": [
        dict(kind="pop", src=LIB + "commons_sbuxcup_3.jpg", cap="커피는 나중에", line=0, at=0),
        dict(kind="write", text="자동 충전 +25달러", x=70, y=180, size=100, line=0, at=.45),
        dict(kind="icons", icon="dollar", n=5, x=90, y=360, size=100, gap=60, color="green", line=0, at=.7, dur=.7),
        dict(kind="write", text="석 달 새 충전", x=70, y=560, size=88, line=1, at=0),
        dict(kind="write", text="31억 달러", x=70, y=680, size=150, color="red", line=1, at=.3),
        dict(kind="write", text="약 4조 원", x=640, y=720, size=96, color="gold", line=1, at=.6),
        dict(kind="print", text="FY2026 3분기 (2026년 4~6월) · 미국", x=84, y=890, size=32, w="Medium", color="gray", line=1, at=.75),
    ]}},
    {"type": "statement", "l1": "이자 없는 빚", "l2": "갚는 날짜도 없다", "lines": [
        L(["회계로 보면 이 돈은", "스타벅스가 커피로 갚아야 하는 빚입니다"], "회계로 보면 이 돈은, 스타벅스가 커피로 갚아야 하는 빚입니다."),
        L(["그런데 이자도, 갚는 날짜도 없어요", "이런 조건이면 저도 빌리고 싶네요"], "그런데 이자도, 갚는 날짜도 없어요. 이런 조건이면 저도 빌리고 싶네요."),
        L(["그럼 스타벅스는 이 돈을 굴려", "이자로 큰돈을 벌까요?"], "그럼 스타벅스는 이 돈을 굴려서, 이자로 큰돈을 벌까요?"),
    ], "page": {"head": "장부 속 이름은 '빚'", "beats": [
        dict(kind="write", text="충전금 = 빚", x=80, y=180, size=130, line=0, at=.1),
        dict(kind="print", text="갚는 방법: 돈 대신 커피", x=86, y=360, size=40, w="Bold", color="gray", line=0, at=.6),
        dict(kind="write", text="이자 0원", x=80, y=470, size=110, color="red", line=1, at=.05),
        dict(kind="write", text="만기 없음", x=560, y=470, size=110, color="red", line=1, at=.3),
        dict(kind="circle", cx=780, cy=530, rx=250, ry=85, color="gold", line=1, at=.6),
        dict(kind="write", rows=["이 돈 굴려서", "이자로 대박?"], x=80, y=720, size=118, color="ink", line=2, at=.05, dur=1.1),
        dict(kind="write", text="?", x=850, y=760, size=230, color="gold", line=2, at=.6),
    ]}},
    {"type": "bars", "title": "2025 회계연도", "lines": [
        L(["답은, 생각보다 작습니다", "2025 회계연도에 커피로 100원을 남길 때"], "답은, 생각보다 작습니다. 이천이십오 회계연도에 커피로 백 원을 남길 때,"),
        L(["현금에서 나온 이자는", "다른 수익까지 합쳐도 고작 4원이에요"], "현금에서 나온 이자는, 다른 수익까지 합쳐도 고작 사 원이에요."),
        L(["오히려 아무도 끝내 쓰지 않을 돈, 낙전 수익이 8원 가까이", "안 쓴 돈이 이자보다 두 배를 번 셈이죠"], "오히려 아무도 끝내 쓰지 않을 돈, 낙전 수익이 팔 원 가까이 됩니다. 안 쓴 돈이 이자보다 두 배를 번 셈이죠."),
    ], "page": {"head": "2025 회계연도 (2025년 9월까지 1년)", "beats": [
        dict(kind="bars", items=[{"label": "커피로 남긴 돈", "v": 29.4, "text": "29.4억$", "color": "ink"},
                                 {"label": "낙전 수익", "v": 2.22, "text": "2.2억$", "color": "gold"},
                                 {"label": "이자·기타", "v": 1.1, "text": "1.1억$", "color": "red"}], x=90, y=200, w=900, h=440, line=0, at=.15),
        dict(kind="write", text="이자는 어디?", x=560, y=260, size=92, color="gray", line=0, at=.4, over=True),
        dict(kind="circle", cx=230, cy=420, rx=150, ry=240, color="ink", line=0, at=.75),
        dict(kind="arrow", pts=[[640, 380], [760, 560]], color="red", line=1, at=0),
        dict(kind="write", text="이자 = 4%뿐", x=560, y=800, size=100, color="red", line=1, at=.3),
        dict(kind="arrow", pts=[[760, 770], [860, 690]], color="red", line=1, at=.6),
        dict(kind="photo", src=LIB + "commons_giftcard_1.jpg", x=90, y=900, w=330, h=250, rot=-4, cap="서랍 속 기프트카드", line=2, at=.05),
        dict(kind="write", text="낙전이 이자의 2배", x=470, y=950, size=100, color="gold", line=2, at=.45),
    ]}},
    {"type": "statement", "l1": "진짜 힘은", "l2": "다시 오게 만드는 것", "lines": [
        L(["그러니까 충전금의 진짜 힘은", "이자가 아니에요"], "그러니까 충전금의 진짜 힘은, 이자가 아니에요."),
        L(["앱에 12달러가 남아 있으면", "옆 카페 커피가 왠지 아깝게 느껴지죠"], "앱에 십이 달러가 남아 있으면, 옆 카페 커피가 왠지 아깝게 느껴지죠."),
        L(["리워드 회원 3,580만 명이 미국 직영점 매출의 59%를 내요", "충전금이 단골을 만든 거죠"], "리워드 회원 삼천오백팔십만 명이, 미국 직영점 매출의 오십구 퍼센트를 내요. 충전금이 단골을 만든 거죠."),
    ], "page": {"head": "락인 효과", "beats": [
        dict(kind="write", text="이자 X", x=80, y=180, size=120, color="gray", line=0, at=.05),
        dict(kind="cross", x0=80, y0=190, x1=400, y1=320, color="red", line=0, at=.6),
        dict(kind="write", text="다시 오게 O", x=470, y=180, size=120, color="green", line=0, at=.75),
        dict(kind="photo", src=LIB + "commons_sbuxcup_4.jpg", x=90, y=400, w=300, h=360, rot=-3, cap="잔액 12달러", line=1, at=.05),
        dict(kind="write", rows=["내일 아침도", "여기로"], x=440, y=460, size=110, line=1, at=.4, dur=1.0),
        dict(kind="icons", icon="person", n=10, hl=[0, 1, 2, 3, 4, 5], x=90, y=860, size=80, gap=12, color="gray", hlcolor="green", line=2, at=.05, dur=.9),
        dict(kind="write", text="회원이 매출 59%", x=80, y=990, size=96, color="green", line=2, at=.5),
    ]}},
    {"type": "statement", "l1": "내 돈 팁", "l2": "충전은 한 달 치만", "lines": [
        L(["내 돈 팁 하나, 충전은", "한 달에 쓸 만큼만 하세요"], "내 돈 팁 하나. 충전은 한 달에 쓸 만큼만 하세요."),
        L(["앱에 남은 돈이 다음 커피를", "대신 골라 주고 있을지 모르니까요"], "앱에 남은 돈이, 다음 커피를 대신 골라 주고 있을지 모르니까요."),
    ], "page": {"head": "내 지갑에서는", "beats": [
        dict(kind="check", text="충전은 한 달 치만", x=90, y=260, size=84, line=0, at=.1),
        dict(kind="photo", src=LIB + "commons_sbuxcup_2.jpg", x=600, y=450, w=400, h=290, rot=4, line=0, at=.6),
        dict(kind="write", rows=["잔액이", "발걸음을 정한다"], x=80, y=470, size=110, color="red", line=1, at=.05, dur=.9),
        dict(kind="under", x0=90, x1=560, y=760, color="red", line=1, at=.7),
    ]}},
    cta("VALUENOTE", ["앱이 손님을 줄인 반전은", "9분 풀영상에"], "commons_cafequeue_3.jpg", "앱이 만든 줄"),
]
A["caption"] = ("미국 스타벅스 앱과 카드에 손님들이 넣어 두고 아직 안 쓴 돈은 약 17억 5천만 달러(2026년 6월 28일 기준, 우리 돈 2조 3천억 원 이상)입니다. "
                "석 달 동안 새로 충전되는 돈만 31억 달러입니다.\n\n회계로는 커피로 갚을 빚이지만 이자도 만기도 없습니다. 그런데 2025 회계연도에 회사 현금 전체에서 나온 이자·기타 수익은 1억 1천만 달러로 "
                "커피를 팔아 남긴 돈(29억 4천만 달러)의 약 4%, 끝내 안 쓰일 잔액을 매출로 잡는 낙전 수익(2억 2,240만 달러)이 그 두 배였습니다. "
                "충전금의 진짜 힘은 손님을 다시 오게 만드는 데 있습니다. 리워드 활성 회원 3,580만 명이 미국 직영점 매출의 59%를 냅니다.\n\n"
                "자료: 스타벅스 10-K(FY2025)·10-Q·FY2026 3분기 실적. 같은 앱이 왜 손님을 줄게 만들었는지는 9분 풀영상에 정리했습니다." + CREDIT)
A["subs_en"] = ["Money customers left in the U.S. Starbucks app, still unspent", "About $1.75 billion, over 2.3 trillion won",
                "When the balance runs low, the app tops up $25 automatically", "New loads in three months: $3.1 billion, about 4 trillion won",
                "On the books, it's a debt Starbucks repays in coffee", "No interest, no due date. I'd borrow on those terms too",
                "So does Starbucks earn big interest on it?", "Smaller than you'd think. FY2025 profit from selling coffee: $2.94 billion",
                "Interest plus other income on all its cash: $110 million", "Breakage, balances never used, was $222 million, twice the interest",
                "So the real power of stored value isn't interest", "With $12 left in the app, it's hard to go elsewhere tomorrow",
                "35.8M Rewards members make up 59% of U.S. company-store sales", "A money tip: load only a month's worth",
                "The interest goes to Starbucks anyway", "Like and subscribe for more. Full video: profile link"]

# ───────────────────────── b. 손님 10% 증발, 범인은 앱 ─────────────────────────
B = dict(BASE, id="Y261028b", scheduled_at="2026-10-28T16:00:00+09:00", mood="tense", broll="city",
         title="스타벅스 손님 10% 증발, 범인은 앱이었다? #스타벅스",
         title_en="Starbucks lost 10% of transactions. The culprit was its app? #Starbucks",
         banner=["스타벅스 손님 10% 증발", "범인은 앱이었다?"], cover_title="스타벅스 손님\n10% 증발\n범인은 앱?",
         hashtags=["스타벅스", "스타벅스주가", "브라이언니콜", "하워드슐츠", "밸류노트", "shorts"],
         message="앱 주문이 몰리며 매장이 느려져 결제 횟수가 10% 줄었고, 2008년처럼 매장 경험을 고치자 손님이 돌아왔다.")
B["scenes"] = [
    {"type": "hook", "lines": [
        L(["미국 스타벅스", "손님 열 명 중 한 명이 사라졌습니다"], "미국 스타벅스, 손님 열 명 중 한 명이 사라졌습니다."),
        L(["2024년 7~9월, 결제 횟수가", "1년 전보다 10% 줄었거든요"], "이천이십사년 칠월부터 구월까지, 결제 횟수가 일 년 전보다 십 퍼센트 줄었거든요."),
    ], "page": {"head": "STARBUCKS  ·  2024", "beats": [
        dict(kind="photo", src=LIB + "commons_sbuxstore_1.jpg", x=600, y=150, w=400, h=280, rot=4, cap="미국 스타벅스 매장", line=0, at=0),
        dict(kind="print", text="2024년 7~9월 · 결제 횟수", x=80, y=190, size=40, w="ExtraBold", line=0, at=.2),
        dict(kind="write", text="-10%", x=70, y=250, size=200, color="red", line=0, at=.5),
        dict(kind="icons", icon="person", n=10, hl=[9], x=90, y=600, size=80, gap=12, color="ink", hlcolor="red", line=1, at=.05, dur=.8),
        dict(kind="cross", x0=820, y0=600, x1=900, y1=690, color="red", line=1, at=.5),
        dict(kind="write", text="10명이 9명으로", x=80, y=760, size=120, color="red", line=1, at=.6),
    ]}},
    {"type": "statement", "l1": "범인은", "l2": "가장 아끼던 앱", "lines": [
        L(["손님을 쫓아낸 건, 바로", "스타벅스가 가장 아끼던 앱이었어요"], "손님을 쫓아낸 건, 바로 스타벅스가 가장 아끼던 앱이었어요."),
        L(["미국 직영점 주문 세 건 중 한 건이", "매장에 오기 전 앱으로 들어옵니다"], "미국 직영점 주문 세 건 중 한 건이, 매장에 오기 전 앱으로 들어옵니다."),
    ], "page": {"head": "범인 찾기", "beats": [
        dict(kind="pop", src=LIB + "phone_14669_a.jpg", cap="모바일 주문", line=0, at=0),
        dict(kind="write", text="범인 = 앱", x=80, y=200, size=150, color="red", line=0, at=.5),
        dict(kind="icons", icon="cup", n=3, hl=[0], x=110, y=520, size=150, gap=110, color="gray", hlcolor="red", line=1, at=.05, dur=.6),
        dict(kind="write", text="3잔 중 1잔은 앱", x=80, y=740, size=110, line=1, at=.45),
        dict(kind="print", text="미국 직영점 · 디지털 IR 대시보드 (FY2026 3분기)", x=84, y=900, size=32, w="Medium", color="gray", line=1, at=.7),
    ]}},
    {"type": "statement", "l1": "옵션이 붙을수록", "l2": "느려지는 매장", "lines": [
        L(["앱 주문엔 시럽 추가, 콜드폼 추가", "같은 옵션이 잔뜩 붙어요"], "앱 주문엔 시럽 추가, 콜드폼 추가 같은 옵션이 잔뜩 붙어요."),
        L(["한 잔에 남는 돈은 늘지만", "만드는 시간도 그만큼 길어지죠"], "한 잔에 남는 돈은 늘지만, 만드는 시간도 그만큼 길어지죠."),
        L(["아침 8시, 픽업대는 앱으로 주문한 컵으로 꽉 차요", "줄 선 손님은 커피보다 인내심이 먼저 식었죠"], "아침 여덟 시, 픽업대는 앱으로 주문한 컵으로 꽉 차요. 줄 선 손님은, 커피보다 인내심이 먼저 식었죠."),
    ], "page": {"head": "아침 8시, 픽업대", "beats": [
        dict(kind="print", rows=["+ 시럽 추가", "+ 콜드폼 추가", "+ 우유 변경 ..."], x=90, y=190, size=46, w="Bold", line=0, at=.15),
        dict(kind="photo", src=LIB + "commons_barista_1.jpg", x=600, y=150, w=400, h=290, rot=4, line=0, at=.5),
        dict(kind="write", text="남는 돈 늘고", x=80, y=480, size=110, color="green", line=1, at=.05),
        dict(kind="write", text="시간도 늘고", x=560, y=480, size=110, color="red", line=1, at=.45),
        dict(kind="photo", src=LIB + "commons_cafequeue_2.jpg", x=90, y=700, w=520, h=380, rot=-2, cap="기다리는 손님", line=2, at=.1),
        dict(kind="write", rows=["앱 컵 먼저,", "줄은 그 뒤"], x=650, y=760, size=92, color="red", line=2, at=.5, dur=.9),
    ]}},
    {"type": "statement", "l1": "아킬레스건", "l2": "결국 CEO 교체", "lines": [
        L(["창업자 하워드 슐츠는 이 앱을", "스타벅스의 가장 큰 아킬레스건이라고 했어요"], "창업자 하워드 슐츠는 이 앱을, 스타벅스의 가장 큰 아킬레스건이라고까지 했어요."),
    ], "page": {"head": "창업자의 경고", "beats": [
        dict(kind="write", rows=["\"가장 큰", "아킬레스건\""], x=80, y=200, size=140, line=0, at=.15, dur=1.2),
        dict(kind="print", text="하워드 슐츠 (창업자) · 앱을 두고", x=86, y=520, size=38, w="Bold", color="gray", line=0, at=.75),
        dict(kind="print", rows=["결제 횟수  2024년 4~6월  -6%", "결제 횟수  2024년 7~9월  -10%"], x=90, y=640, size=44, w="ExtraBold", color="red", line=0, at=.85),
    ]}},
    {"type": "compare", "title": "스타벅스가 손님을 잃은 두 번", "l": {"label": "2008년", "v": "커피 맛"}, "r": {"label": "2024년", "v": "느린 매장"}, "lines": [
        L(["그런데 스타벅스는 2008년에도 이런 위기를 이겨 냈어요", "그때 창업자는 미국 매장 약 7,000곳의 문을 한꺼번에 닫고"], "그런데 스타벅스는 2008년에도 이런 위기를 이겨 냈어요. 그때 창업자는 미국 매장 약 7,000곳의 문을 한꺼번에 닫고,"),
        L(["세 시간 반 동안", "에스프레소 교육을 다시 했죠"], "세 시간 반 동안, 에스프레소 교육을 다시 했죠."),
        L(["그때는 커피를 고쳤고", "이번엔 앱 때문에 느려진 매장을 고쳐야 했죠"], "그때는 커피를 고쳤고, 이번엔 앱 때문에 느려진 매장을 고쳐야 했죠."),
    ], "page": {"head": "2008년 2월 26일", "beats": [
        dict(kind="pop", src=LIB + "commons_sbuxpike_1.jpg", cap="2008년, 7,000곳 휴점", line=0, at=0),
        dict(kind="write", text="7,000곳 문 닫음", x=80, y=180, size=110, line=0, at=.55),
        dict(kind="write", text="3시간 반 에스프레소 재교육", x=80, y=360, size=80, color="gold", line=1, at=.05),
        dict(kind="photo", src=LIB + "commons_barista_3.jpg", x=640, y=480, w=360, h=260, rot=3, line=1, at=.5),
        dict(kind="write", text="2008년 커피 맛", x=80, y=800, size=100, color="gray", line=2, at=.05),
        dict(kind="write", text="2024년 느린 매장", x=80, y=950, size=110, color="red", line=2, at=.45),
        dict(kind="circle", cx=430, cy=1010, rx=380, ry=85, color="red", line=2, at=.75),
    ]}},
    {"type": "statement", "l1": "매장을 고치자", "l2": "손님이 돌아왔다", "lines": [
        L(["새 최고경영자 브라이언 니콜은", "앱을 버리지 않고 고쳐서 썼어요"], "새 최고경영자 브라이언 니콜은, 앱을 버리지 않고 고쳐서 썼어요."),
        L(["메뉴를 30% 줄이고 음료가 4분 안에 나오게 했어요", "시럽 대신 속도를 더한 셈이죠"], "메뉴를 삼십 퍼센트 줄이고, 음료가 사 분 안에 나오게 했어요. 시럽 대신 속도를 더한 셈이죠."),
        L(["그리고 올해, 2026년 4~6월", "결제 횟수가 4.2% 늘었습니다"], "그리고 올해, 이천이십육년 사월부터 유월까지, 결제 횟수가 사 점 이 퍼센트 늘었습니다."),
        L(["실적 발표에선 결제 횟수 한 줄부터 찾아보세요", "스타벅스는 거기서 무너졌고, 거기서 살아났거든요"], "실적 발표에선 결제 횟수 한 줄부터 찾아보세요. 스타벅스는 거기서 무너졌고, 거기서 살아났거든요."),
    ], "page": {"head": "브라이언 니콜의 처방", "beats": [
        dict(kind="check", text="앱은 고쳐서 쓴다", x=90, y=200, size=72, line=0, at=.3),
        dict(kind="check", text="메뉴 -30%", x=90, y=360, size=72, line=1, at=.05),
        dict(kind="check", text="4분 안에 한 잔", x=90, y=500, size=72, line=1, at=.5),
        dict(kind="photo", src=LIB + "commons_sbuxcup_1.jpg", x=700, y=180, w=290, h=380, rot=4, cap="손글씨 컵", line=1, at=.75),
        dict(kind="print", text="2026년 4~6월 · 미국 결제 횟수", x=84, y=700, size=38, w="Bold", color="gray", line=2, at=.05),
        dict(kind="write", text="+4.2%", x=70, y=760, size=200, color="green", line=2, at=.3),
        dict(kind="write", text="손님 귀환", x=600, y=830, size=110, color="green", line=2, at=.7),
        dict(kind="write", text="결제 횟수 한 줄부터", x=80, y=1020, size=104, color="red", line=3, at=.1),
        dict(kind="under", x0=90, x1=800, y=1145, color="red", line=3, at=.6),
    ]}},
    cta("VALUENOTE", ["앱에 잠든 2조 원의 정체는", "9분 풀영상에"], "commons_sbuxcup_2.jpg", "스타벅스 편"),
]
B["caption"] = ("2024년 7~9월 미국 스타벅스에서 손님이 결제한 횟수는 1년 전보다 10% 줄었습니다(4~6월 -6%). 범인은 앱 주문이었습니다. "
                "미국 직영점 주문 세 건 중 한 건이 매장에 오기 전 앱으로 들어오고, 옵션이 많이 붙어 한 잔을 만드는 시간이 길어졌습니다. "
                "창업자 하워드 슐츠는 이 앱을 '가장 큰 아킬레스건'이라고 했고 당시 최고경영자는 취임 1년 5개월 만에 교체됐습니다.\n\n"
                "2008년 2월 26일 슐츠는 미국 매장 약 7,000곳을 세 시간 반 닫고 에스프레소 교육을 다시 했습니다. 이번 처방도 매장이었습니다. "
                "브라이언 니콜은 메뉴를 30% 줄이고 4분 목표를 세웠고, 2026년 4~6월 미국 결제 횟수는 4.2% 늘었습니다.\n\n"
                "자료: 스타벅스 실적 발표(FY2024·FY2026 3분기), NPR(2008), NBC(2024). 손님이 앱에 넣어 둔 17억 달러의 정체는 9분 풀영상에 있습니다." + CREDIT)
B["subs_en"] = ["Jul-Sep 2024: transactions at U.S. Starbucks fell 10%", "A store that served ten now served nine",
                "The culprit was the app Starbucks loved most", "One in three U.S. company-store orders comes in by app before arrival",
                "App orders pile on extras like syrup and cold foam", "More profit per cup, but each takes longer to make",
                "8 a.m.: app cups line the pickup counter, and the line waits behind them", "Founder Howard Schultz called the app Starbucks' biggest Achilles' heel",
                "The CEO was replaced after one year and five months", "It happened in 2008 too. Schultz shut about 7,000 U.S. stores at once",
                "For three and a half hours of espresso retraining", "Then the cause was taste; this time, stores swamped by app orders",
                "New CEO Brian Niccol didn't kill the app", "He cut the menu 30% and set a 4-minute goal per drink",
                "Apr-Jun this year, transactions rose 4.2%", "Like and subscribe for more. Full video: profile link"]

# ───────────────────────── c. 같은 1억, 언제 샀느냐 + 10월 29일 숫자 3개 ─────────────────────────
C = dict(BASE, id="Y261028c", scheduled_at="2026-10-28T21:30:00+09:00", mood="tense", broll="market",
         title="스타벅스 주가, 같은 1억이 8천만 원 vs 1억 3천만 원? 산 날 하나 차이 #스타벅스",
         title_en="Starbucks stock: why the same 100M won became 80M or 130M #Starbucks",
         banner=["같은 스타벅스 주식 1억", "8천만 원 vs 1억 3천만 원?"], cover_title="스타벅스 1억\n8천만 vs\n1억 3천만",
         hashtags=["스타벅스", "스타벅스주가", "스타벅스실적", "미국주식", "밸류노트", "shorts"],
         message="같은 스타벅스 주식도 언제 샀느냐(최고가 근처 vs 니콜 발표 전날)에 따라 결과가 갈렸고, 회복이 이익으로 이어지는지는 10월 29일 숫자 3개가 보여 준다.")
C["scenes"] = [
    {"type": "hook", "lines": [
        L(["같은 스타벅스 주식 1억 원인데", "한 명은 2천만 원을 잃고, 한 명은 3천만 원을 벌었어요"], "같은 스타벅스 주식 일억 원인데, 한 명은 이천만 원을 잃고, 한 명은 삼천만 원을 벌었어요."),
        L(["2021년 7월 최고가 근처에 산 사람은 8천만 원", "2024년 8월 12일에 산 사람은 1억 3천만 원"], "이천이십일년 칠월 최고가 근처에 산 사람은 팔천만 원, 이천이십사년 팔월 십이일에 산 사람은 일억 삼천만 원이 됐죠."),
        L(["10월 26일 종가 기준, 주가로만 따진 숫자예요", "그리고 이 승부, 10월 29일 실적에서 또 갈립니다"], "시월 이십육일 종가 기준, 주가로만 따진 숫자예요. 그리고 이 승부, 시월 이십구일 실적에서 또 갈립니다."),
    ], "page": {"head": "STARBUCKS  ·  SBUX", "beats": [
        dict(kind="write", text="1억 원은 지금?", x=80, y=180, size=150, line=0, at=.1),
        dict(kind="photo", src=LIB + "commons_sbuxpike_2.jpg", x=700, y=300, w=300, h=220, rot=4, line=0, at=.5),
        dict(kind="print", text="2021년 7월 23일 · 126달러", x=84, y=470, size=38, w="Bold", color="gray", line=0, at=.6),
        dict(kind="write", text="8천만 원 (-18%)", x=80, y=530, size=120, color="red", line=1, at=.05),
        dict(kind="print", text="2024년 8월 12일 · 77.03달러", x=84, y=760, size=38, w="Bold", color="gray", line=1, at=.4),
        dict(kind="write", text="1억 3천만 원 (+33%)", x=80, y=820, size=120, color="green", line=1, at=.55),
        dict(kind="print", text="10월 26일 종가 102.7달러 · 주가만, 배당·환율 빼고", x=84, y=1000, size=32, w="Medium", color="gray", line=2, at=.05),
        dict(kind="write", text="다음 승부는 10월 29일", x=80, y=1060, size=80, color="red", line=2, at=.55),
    ]}},
    {"type": "statement", "l1": "8월 12일", "l2": "니콜 발표 전날", "lines": [
        L(["8월 12일은 브라이언 니콜이 새 최고경영자로", "발표되기 바로 전날이었어요"], "팔월 십이일은, 브라이언 니콜이 새 최고경영자로 발표되기 바로 전날이었어요."),
        L(["발표 당일, 주가는 장중 24% 올랐습니다", "실적보다 기대가 먼저 움직인 거예요"], "발표 당일, 주가는 장중 이십사 퍼센트 올랐습니다. 실적보다 기대가 먼저 움직인 거예요."),
    ], "page": {"head": "2024년 8월 13일", "beats": [
        dict(kind="pop", src=LIB + "commons_niccol_1.jpg", cap="새 CEO 브라이언 니콜 발표", line=0, at=0),
        dict(kind="write", rows=["새 CEO", "브라이언 니콜"], x=80, y=190, size=120, line=0, at=.55, dur=.9),
        dict(kind="write", text="장중 +24%", x=80, y=560, size=180, color="green", line=1, at=.05),
        dict(kind="arrow", pts=[[760, 860], [900, 600]], color="green", line=1, at=.35, width=12),
        dict(kind="print", text="장중 기준 스타벅스 역사상 최대 상승", x=84, y=830, size=40, w="Bold", color="gray", line=1, at=.6),
    ]}},
    {"type": "statement", "l1": "출근길은", "l2": "비행기", "lines": [
        L(["니콜은 캘리포니아 집에서 본사까지", "1,600km 넘는 길을 회사 전용기로 출근하기로 했어요"], "니콜은 캘리포니아 집에서 본사까지, 천육백 킬로미터가 넘는 길을 회사 전용기로 출근하기로 했어요."),
        L(["저는 지하철 두 정거장도 멀던데", "이분 출근길은 마일리지가 쌓이네요"], "저는 지하철 두 정거장도 멀던데, 이분 출근길은 마일리지가 쌓이네요."),
    ], "page": {"head": "화제가 된 출근길", "beats": [
        dict(kind="print", text="뉴포트비치 (캘리포니아)", x=90, y=200, size=42, w="ExtraBold", line=0, at=.15),
        dict(kind="arrow", pts=[[200, 280], [760, 560]], color="gold", line=0, at=.35, width=12),
        dict(kind="print", text="시애틀 본사", x=700, y=600, size=42, w="ExtraBold", line=0, at=.55),
        dict(kind="write", text="1,600km+ 전용기", x=80, y=720, size=120, color="red", line=0, at=.7),
        dict(kind="write", text="vs 지하철 두 정거장", x=80, y=920, size=96, color="gray", line=1, at=.1),
    ]}},
    {"type": "compare", "title": "100달러 팔아 남는 돈", "l": {"label": "2025 회계연도", "v": "7.9달러"}, "r": {"label": "올해 회사 예상", "v": "11달러+"}, "lines": [
        L(["니콜은 직원과 매장에 먼저 돈을 써서 2025 회계연도엔", "100달러어치를 팔아 7.9달러만 남겼죠, 올해 회사 목표는 11달러 이상이에요"], "니콜은 직원과 매장에 먼저 돈을 썼습니다. 그래서 2025 회계연도엔 100달러어치를 팔아 7.9달러만 남겼죠. 올해 회사 목표는 11달러 이상이에요."),
    ], "page": {"head": "100달러 팔면 남는 돈", "beats": [
        dict(kind="bars", items=[{"label": "2025 회계연도", "v": 7.9, "text": "7.9달러", "color": "red"},
                                 {"label": "올해 회사 예상", "v": 11, "text": "11달러+", "color": "green"}], x=90, y=340, w=900, h=380, line=0, at=.3),
        dict(kind="write", text="직원과 매장에 먼저 썼다", x=80, y=170, size=80, color="red", line=0, at=.05),
        dict(kind="arrow", pts=[[330, 480], [560, 400]], color="green", line=0, at=.8, width=10),
        dict(kind="under", x0=90, x1=800, y=270, color="red", line=0, at=.55),
        dict(kind="print", text="올해 회사 목표 11달러 이상", x=560, y=785, size=36, w="Bold", color="green", line=0, at=.95),
    ]}},
    {"type": "list", "title": "10월 29일 볼 숫자 3개", "items": ["미국 기존 매장 매출", "결제 횟수", "100달러당 남는 돈"], "lines": [
        L(["산 날은 못 고르더라도, 이번 실적에서", "꼭 볼 숫자는 딱 세 개입니다"], "산 날은 못 고르더라도, 이번 실적에서 꼭 볼 숫자는 딱 세 개입니다."),
        L(["첫째, 미국 기존 매장 매출, 새 매장을 빼고 원래 매장이 더 판 정도", "회사는 이번 분기 6.5% 이상을 내걸었어요"], "첫째, 미국 기존 매장 매출. 새 매장을 빼고 원래 매장이 얼마나 더 팔았나예요. 회사는 이번 분기 육 점 오 퍼센트 이상을 내걸었어요."),
        L(["둘째, 결제 횟수", "지난 분기 4.2%보다 높으면 손님이 계속 느는 거예요"], "둘째, 결제 횟수. 지난 분기 사 점 이 퍼센트보다 높으면, 손님이 계속 느는 거예요."),
        L(["셋째, 100달러어치 팔아 남는 돈", "작년 7.9달러보다 늘면 매장에 쓴 돈이 돌아오는 거예요"], "셋째, 백 달러어치 팔아 남는 돈. 작년 칠 점 구 달러보다 늘면, 매장에 쓴 돈이 돌아오는 거예요."),
    ], "page": {"head": "10월 29일, 이 숫자 3개", "beats": [
        dict(kind="write", text="10월 29일 실적", x=80, y=170, size=110, color="red", line=0, at=.1),
        dict(kind="print", text="미국 장 마감 뒤 발표", x=86, y=320, size=36, w="Bold", color="gray", line=0, at=.6),
        dict(kind="check", text="기존 매장 매출 6.5%+", x=90, y=470, size=66, line=1, at=.1),
        dict(kind="check", text="결제 횟수 계속 +?", x=90, y=690, size=66, line=2, at=.1),
        dict(kind="check", text="100달러당 남는 돈", x=90, y=910, size=66, line=3, at=.1),
        dict(kind="write", text="11달러로 갈까?", x=600, y=1030, size=80, color="green", line=3, at=.6),
    ]}},
    cta("VALUENOTE", ["지금 주가, 비싼가 싼가는", "9분 풀영상에"], "commons_sbuxkorea_1.jpg", "스타벅스 편"),
]
C["caption"] = ("스타벅스 주식을 1억 원어치 샀다면? 주가만 따지면(배당·환율 제외, 10월 26일 종가 102.7달러 기준) 최고가 근처였던 2021년 7월 23일(126달러)에 산 사람은 약 8천만 원(-18%), "
                "브라이언 니콜 발표 전날인 2024년 8월 12일(77.03달러)에 산 사람은 약 1억 3천만 원(+33%)입니다.\n\n"
                "발표 당일 주가는 장중 24% 올랐습니다. 니콜은 직원과 매장에 돈을 먼저 써 2025 회계연도엔 100달러를 팔아 7.9달러만 남겼지만, 2026년 4~6월 결제 횟수는 4.2% 늘었습니다.\n\n"
                "10월 29일 실적에서 볼 숫자 3개: ① 미국 기존 매장 매출(회사 목표 이번 분기 6.5% 이상) ② 결제 횟수 ③ 100달러어치 팔아 남는 돈(회사 연간 예상 11달러 이상). "
                "지금 주가가 비싼지 싼지는 9분 풀영상에 정리했습니다." + CREDIT)
C["subs_en"] = ["If you'd bought 100 million won of Starbucks stock, what's it worth now?", "Price only: bought near the July 2021 peak, 80 million won",
                "Bought Aug 12, 2024: 130 million won, as of the Oct 26 close", "Aug 12 was the day before Brian Niccol was named CEO",
                "On the news the stock rose 24% intraday, its biggest intraday jump ever", "Niccol would fly 1,600+ km from California to Seattle HQ by company jet",
                "Two subway stops feel far to me", "Niccol spent on staff and stores first: $7.90 kept per $100 sold in FY2025",
                "Meanwhile customers came back: transactions +4.2% in Apr-Jun", "So on Oct 29, watch three numbers",
                "One: U.S. comparable-store sales, the company targets 6.5%+ this quarter", "Two: transactions, are customers still growing?",
                "Three: profit per $100 sold, is store spending turning into profit?", "Like and subscribe for more. Full video: profile link"]

A["subs_en"] = ["How much have U.S. Starbucks customers left unspent in the app?", "About $1.75 billion, over 2.3 trillion won",
                "When the balance runs low, the app tops up $25 automatically", "2 trillion sits there, but 4 trillion flows in and out every three months",
                "On the books, it's a debt Starbucks repays in coffee", "No interest, no due date. I'd borrow on those terms too",
                "So does Starbucks earn big interest on it?", "Smaller than you'd think. For every 100 won Starbucks kept from coffee in FY2025",
                "Interest plus other income on its cash: just 4 won", "Breakage, money nobody ever spends, is close to 8 won, twice the interest",
                "So the real power of stored value isn't interest", "With $12 left in the app, the coffee next door feels like a waste",
                "35.8M Rewards members make up 59% of U.S. company-store sales. Stored value made regulars", "A money tip: load only a month's worth",
                "Money left in the app may be picking your next coffee for you", "Like and subscribe for more. Full video: profile link"]
B["subs_en"] = ["At U.S. Starbucks, one in ten customers vanished", "Jul-Sep 2024, transactions fell 10% from a year earlier",
                "What drove them away was the app Starbucks loved most", "One in three U.S. company-store orders comes in by app before arrival",
                "App orders pile on extras like syrup and cold foam", "More profit per cup, but each takes longer to make",
                "8 a.m.: the pickup counter fills with app cups; patience cools before the coffee", "Founder Howard Schultz called the app Starbucks' biggest Achilles' heel",
                "Starbucks beat a crisis like this in 2008 too. The founder shut about 7,000 U.S. stores at once",
                "For three and a half hours of espresso retraining", "Then they fixed the coffee; this time, stores slowed by the app",
                "New CEO Brian Niccol fixed the app instead of dropping it", "Menu cut 30%, drinks in 4 minutes: speed added instead of syrup",
                "This year, Apr-Jun 2026, transactions rose 4.2%", "In earnings, find the transactions line first. That's where Starbucks fell and recovered",
                "Like and subscribe for more. Full video: profile link"]
C["subs_en"] = ["Same 100 million won in Starbucks stock: one lost 20 million, one made 30 million", "Bought near the July 2021 peak: 80 million. Bought Aug 12, 2024: 130 million",
                "Oct 26 close, price only. And the next round is decided at the Oct 29 earnings", "Aug 12 was the day before Brian Niccol was named CEO",
                "On the news the stock rose 24% intraday. Hope moved before results", "Niccol would commute 1,600+ km from his California home by company jet",
                "Two subway stops feel far to me; his commute earns miles", "He spent on staff and stores first: $7.90 kept per $100 in FY2025; this year's goal is $11+",
                "You can't pick the day you buy, but there are just three numbers to watch",
                "One: U.S. comparable-store sales, the company targets 6.5%+ this quarter", "Two: transactions, above last quarter's 4.2% means customers keep growing",
                "Three: profit per $100 sold. Above last year's $7.90 means store spending is paying back", "Like and subscribe for more. Full video: profile link"]
import re
for d in (A, B, C):   # 연결어미 뒤 쉼표 빼기 (humanize_ko C-11)
    for sc in d["scenes"]:
        for ln in sc["lines"]:
            if ln.get("say"): ln["say"] = re.sub(r"(고|지만), ", r"\1 ", ln["say"])
            ln["cap"] = [re.sub(r"(고|지만), ", r"\1 ", c) for c in ln["cap"]]
for d in (A, B, C):
    for sc in d["scenes"]:
        if sc["type"] == "bars" and "items" not in sc:
            sc["items"] = [dict(label=i["label"], v=i["v"], text=i["text"]) for b_ in sc["page"]["beats"] if b_["kind"] == "bars" for i in b_["items"]]
    assert len(d["subs_en"]) == sum(len(x["lines"]) for x in d["scenes"]), d["id"]
for d in (A, B, C):   # 쇼츠 썸네일: 첫 페이지가 꽉 찬 순간 (ink_preview 로 뽑은 그림)
    d["thumb_file"] = f"scripts/reels/assets/logo/{d['id']}_thumb.jpg"
for d in (A, B, C):
    json.dump(d, open(os.path.join(SPECS, d["id"] + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("wrote", d["id"], sum(len(s["lines"]) for s in d["scenes"]), "lines")
