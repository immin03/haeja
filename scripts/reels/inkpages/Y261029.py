"""일본 종합상사 롱폼(L261028-japan-trading) 파생 쇼츠 Y261029a·b·c 잉크 노트 대본 (2026-10-28)
python3 scripts/reels/inkpages/Y261029.py 로 specs/Y261029a.json, b, c 를 새로 쓴다.
숫자는 승인된 롱폼 대본(scripts/youtube/long/specs/L261028-japan-trading.json)에 나온 것만 쓴다."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__)); SPECS = os.path.join(HERE, "..", "specs")
LIB = "scripts/blog/media/lib/"


def L(cap, say=None, **k):
    d = {"cap": cap}
    if say: d["say"] = say
    d.update(k); return d


LONG = "L261028-japan-trading"
BASE = {"approved": False, "platform": "youtube", "threads_tag": "주식", "long": LONG, "world": "ink", "allow_long": True, "end": "subscribe",
        "full_say": "풀버전은 하단 프로필 링크에서 보세요.", "full_cap": ["풀버전은 하단 프로필 링크에서"]}
CREDIT = "\n\n사진: Wikimedia Commons (작가·라이선스는 각 파일 페이지) · 매수·매도 권유가 아닙니다."
SRC = "자료: 버크셔 해서웨이 2020년 8월 30일 발표·2024년 주주서한(워렌 버핏)·2025년 주주서한(그레그 에이블), IMF 세계경제전망(2026년 10월), 일본 재무성 법인기업통계."


def cta(rows, photo, pcap):
    return {"type": "cta", "l1": "더 많은 정보를 원하시면", "l2": "좋아요와 구독",
            "lines": [L(["더 많은 정보를 원하시면 좋아요와 구독", "풀영상은 하단 프로필 링크에서"], "더 많은 정보를 원하시면, 좋아요와 구독 눌러 주세요.", pause=1.6)],
            "page": {"head": "VALUENOTE", "beats": [
                dict(kind="write", rows=rows, x=80, y=190, size=96, color="gold", line=0, at=0, dur=.9),
                dict(kind="write", rows=["더 많은 정보는", "좋아요 + 구독"], x=80, y=470, size=112, line=0, at=.25, dur=1.2),
                dict(kind="under", x0=90, x1=720, y=715, color="red", line=0, at=.7),
                dict(kind="photo", src=LIB + photo, x=90, y=800, w=380, h=290, rot=-3, cap=pcap, line=0, at=.85),
                dict(kind="write", rows=["풀영상은", "하단 프로필 링크"], x=520, y=830, size=80, color="red", line=0, at=1.0, dur=1.0),
                dict(kind="arrow", pts=[[760, 1030], [760, 1170]], color="red", line=0, at=1.25, width=12)]}}


# ───────────────────────── a. 아흔 번째 생일의 장바구니 (다섯 회사의 정체) ─────────────────────────
A = dict(BASE, id="Y261029a", scheduled_at="2026-10-29T11:00:00+09:00", mood="calm", broll="city",
         title="워렌 버핏이 90살 생일에 산 일본 회사 5곳, 6년 만에 2.3배 된 정체는? #워렌버핏",
         title_en="Warren Buffett bought 5 Japanese companies on his 90th birthday. Now 2.3x. What are they? #WarrenBuffett",
         banner=["워렌 버핏 90살 생일에 산", "일본 회사 5곳, 정체는?"], cover_title="워렌 버핏\n90살 생일\n장바구니는?",
         hashtags=["워렌버핏", "일본주식", "종합상사", "버크셔해서웨이", "밸류노트", "shorts"],
         message="워렌 버핏이 90살 생일에 공개한 일본 종합상사 5곳은 광산·에너지·편의점까지 거느리고 번 돈을 주주에게 돌려주는 '작은 버크셔'였고, 6년 뒤 평가액은 넣은 돈의 2.3배가 됐다.")
A["scenes"] = [
    {"type": "hook", "lines": [
        L(["보통 아흔 살 생일엔 가족이 선물을 사 오죠", "그런데 워렌 버핏은 직접 장을 봤습니다"], "보통 아흔 살 생일엔 가족이 선물을 사 오죠. 그런데 워렌 버핏은 직접 장을 봤습니다."),
        L(["장바구니에 담긴 건 일본 회사 다섯 곳", "6년 뒤 평가액은 넣은 돈의 2.3배가 됐어요"], "장바구니에 담긴 건 일본 회사 다섯 곳. 육 년 뒤 평가액은 넣은 돈의 이 점 삼 배가 됐어요."),
    ], "page": {"head": "BERKSHIRE  ·  2020.8.30", "beats": [
        dict(kind="photo", src=LIB + "commons_omaha_1.jpg", x=600, y=150, w=400, h=290, rot=4, cap="버크셔 본사, 오마하", line=0, at=0),
        dict(kind="print", text="2020년 8월 30일 · 일요일 아침", x=80, y=190, size=40, w="ExtraBold", line=0, at=.15),
        dict(kind="write", rows=["아흔 번째", "생일 선물?"], x=80, y=260, size=104, line=0, at=.45, dur=1.0),
        dict(kind="icons", icon="box", n=5, hl=[0, 1, 2, 3, 4], x=90, y=540, size=96, gap=70, color="ink", hlcolor="gold", line=1, at=0, dur=.8),
        dict(kind="write", text="일본 회사 5곳", x=80, y=690, size=110, line=1, at=.25),
        dict(kind="write", text="6년 뒤 2.3배", x=80, y=850, size=140, color="red", line=1, at=.6),
        dict(kind="under", x0=80, x1=760, y=1010, color="red", line=1, at=.85),
    ]}},
    {"type": "statement", "l1": "5곳 각각", "l2": "지분 5%", "lines": [
        L(["이토추, 마루베니, 미쓰비시상사, 미쓰이물산", "스미토모상사, 일본의 종합상사 다섯 곳이에요"], "이토추, 마루베니, 미쓰비시 상사, 미쓰이 물산, 스미토모 상사. 일본의 종합상사 다섯 곳이에요."),
        L(["1년 동안 도쿄 증시에서 조용히 사 모은 돈이", "약 62억 5천만 달러, 각각 지분 5% 남짓이었죠"], "일 년 동안 도쿄 증시에서 조용히 사 모은 돈이 약 육십이억 오천만 달러, 각각 지분 오 퍼센트 남짓이었죠."),
    ], "page": {"head": "장바구니 영수증", "beats": [
        dict(kind="print", text="이토추상사", x=90, y=180, size=52, w="ExtraBold", line=0, at=.0),
        dict(kind="print", text="마루베니", x=90, y=260, size=52, w="ExtraBold", line=0, at=.15),
        dict(kind="print", text="미쓰비시상사", x=90, y=340, size=52, w="ExtraBold", line=0, at=.3),
        dict(kind="print", text="미쓰이물산", x=90, y=420, size=52, w="ExtraBold", line=0, at=.5),
        dict(kind="print", text="스미토모상사", x=90, y=500, size=52, w="ExtraBold", line=0, at=.7),
        dict(kind="write", rows=["각 5%+"], x=640, y=300, size=110, color="red", line=0, at=.85),
        dict(kind="photo", src=LIB + "commons_itochuhq_1.jpg", x=700, y=560, w=300, h=380, rot=4, cap="도쿄 이토추 본사", line=1, at=0),
        dict(kind="write", rows=["1년 동안", "도쿄 증시에서"], x=80, y=660, size=88, line=1, at=.15),
        dict(kind="write", text="62억 5천만 달러", x=70, y=900, size=104, color="red", line=1, at=.5),
        dict(kind="under", x0=80, x1=780, y=1030, color="gold", line=1, at=.8),
    ]}},
    {"type": "statement", "l1": "1만 원 재산", "l2": "6~8천 원에", "lines": [
        L(["그때 다섯 곳 중 네 곳은 주가가", "회사가 가진 순자산보다도 낮았어요"], "그때 다섯 곳 중 네 곳은, 주가가 회사가 가진 순자산보다도 낮았어요."),
        L(["1만 원어치 재산을 6~8천 원에 파는 셈이었죠", "장보기 좋은 날이었네요"], "만 원어치 재산을 육천에서 팔천 원에 파는 셈이었죠. 장보기 좋은 날이었네요."),
    ], "page": {"head": "2020년 8월 28일 · 주가 vs 순자산", "beats": [
        dict(kind="icons", icon="box", n=5, hl=[0, 1, 2, 3], x=90, y=190, size=110, gap=70, color="gray", hlcolor="red", line=0, at=.05, dur=.9),
        dict(kind="write", text="5곳 중 4곳", x=80, y=350, size=110, color="red", line=0, at=.35),
        dict(kind="write", text="주가 < 순자산", x=80, y=500, size=110, line=0, at=.65),
        dict(kind="write", text="재산 10,000원", x=80, y=700, size=100, line=1, at=.0),
        dict(kind="arrow", pts=[[300, 810], [300, 850]], color="red", line=1, at=.2, width=8),
        dict(kind="write", text="6,000~8,000원", x=80, y=860, size=110, color="red", line=1, at=.3),
        dict(kind="photo", src=LIB + "calculator_34126_a.jpg", x=640, y=1000, w=340, h=240, rot=-4, cap="장보기 좋은 날", line=1, at=.7),
    ]}},
    {"type": "statement", "l1": "종합상사", "l2": "무엇을 할까", "lines": [
        L(["종합상사는 원래 석유, 밀, 철광석을", "일본에 사 오던 무역 회사였어요"], "종합상사는 원래 석유, 밀, 철광석을 일본에 사 오던 무역 회사였어요."),
        L(["지금은 칠레 구리 광산, 호주 석탄, LNG 사업의", "지분을 직접 갖고 이익을 나눠 받아요"], "지금은 칠레 구리 광산, 호주 석탄, 엘엔지 사업의 지분을 직접 갖고 이익을 나눠 받아요."),
    ], "page": {"head": "사고파는 회사에서 갖는 회사로", "beats": [
        dict(kind="print", text="출발: 무역 회사", x=80, y=180, size=48, w="ExtraBold", line=0, at=.0),
        dict(kind="write", rows=["사 오고", "내다 팔고"], x=80, y=250, size=100, line=0, at=.2, dur=.9),
        dict(kind="photo", src=LIB + "commons_tokyoport_1.jpg", x=560, y=200, w=440, h=300, rot=3, cap="석유·밀·철광석", line=0, at=.55),
        dict(kind="arrow", pts=[[300, 560], [300, 660]], color="red", line=1, at=.0, width=10),
        dict(kind="photo", src=LIB + "commons_coppermine_2.jpg", x=80, y=700, w=420, h=280, rot=-3, cap="칠레 구리 광산", line=1, at=.1),
        dict(kind="photo", src=LIB + "commons_lngcarrier_1.jpg", x=560, y=720, w=440, h=230, rot=3, cap="LNG 운반선", line=1, at=.45),
        dict(kind="write", text="지분 = 이익 나눠 받기", x=80, y=1060, size=92, color="red", line=1, at=.7),
    ]}},
    {"type": "statement", "l1": "삼각김밥 하나도", "l2": "상사 장부에", "lines": [
        L(["일본 편의점도 상사 손에 있어요", "로손은 미쓰비시상사와 통신 회사 KDDI가 절반씩 갖고 있고"], "일본 편의점도 상사 손에 있어요. 로손은 미쓰비시상사와 통신 회사 케이디디아이가 절반씩 갖고 있고,"),
        L(["패밀리마트는 이토추 그룹이 거의 다 갖고 있죠", "도쿄에서 삼각김밥 하나를 사도 상사 장부에 한 줄이 찍혀요"], "패밀리마트는 이토추 그룹이 거의 다 갖고 있죠. 도쿄에서 삼각김밥 하나를 사도, 상사 장부에 한 줄이 찍혀요."),
    ], "page": {"head": "편의점까지", "beats": [
        dict(kind="photo", src=LIB + "commons_lawson_2.jpg", x=80, y=170, w=440, h=300, rot=-3, cap="로손", line=0, at=.0),
        dict(kind="write", rows=["미쓰비시상사", "+ KDDI 반반"], x=560, y=200, size=84, line=0, at=.2, dur=.9),
        dict(kind="under", x0=560, x1=1000, y=400, color="gold", line=0, at=.85),
        dict(kind="photo", src=LIB + "commons_familymart_1.jpg", x=560, y=560, w=440, h=300, rot=3, cap="패밀리마트", line=1, at=.0),
        dict(kind="write", rows=["이토추 그룹", "거의 전부"], x=80, y=590, size=84, line=1, at=.2, dur=.9),
        dict(kind="pop", src=LIB + "commons_onigiri_1.jpg", cap="삼각김밥 하나", line=1, at=.5),
        dict(kind="write", text="= 상사 장부 한 줄", x=80, y=1000, size=104, color="red", line=1, at=.75),
    ]}},
    {"type": "statement", "l1": "작은 버크셔", "l2": "다섯 개", "lines": [
        L(["워렌 버핏은 이 회사들이 버크셔와 꽤 닮은 방식으로", "아주 잘 운영된다고 썼어요"], "워렌 버핏은 이 회사들이, 버크셔와 꽤 닮은 방식으로 아주 잘 운영된다고 썼어요."),
        L(["여러 사업을 거느리고 번 돈을 주주에게 돌려주는", "작은 버크셔 다섯 개를 산 셈이죠"], "여러 사업을 거느리고 번 돈을 주주에게 돌려주는, 작은 버크셔 다섯 개를 산 셈이죠."),
    ], "page": {"head": "워렌 버핏의 주주서한", "beats": [
        dict(kind="print", text="“버크셔와 꽤 비슷한 방식으로", x=80, y=190, size=46, w="ExtraBold", line=0, at=.05),
        dict(kind="print", text="  아주 성공적으로 운영되는 회사들”", x=80, y=260, size=46, w="ExtraBold", line=0, at=.3),
        dict(kind="hl", x0=80, y0=255, x1=760, y1=320, color="yellow", line=0, at=.6),
        dict(kind="photo", src=LIB + "commons_berkshiremtg_1.jpg", x=640, y=400, w=360, h=250, rot=3, cap="버크셔 주주총회", line=0, at=.8),
        dict(kind="write", rows=["광산 · 에너지", "편의점"], x=80, y=420, size=90, line=1, at=.0, dur=.8),
        dict(kind="arrow", pts=[[260, 640], [260, 740]], color="red", line=1, at=.3, width=10),
        dict(kind="write", text="작은 버크셔 x 5", x=80, y=780, size=130, color="red", line=1, at=.45),
        dict(kind="circle", cx=480, cy=860, rx=440, ry=110, color="gold", line=1, at=.8),
    ]}},
    {"type": "compare", "title": "넣은 돈 vs 평가액", "l": {"label": "넣은 돈", "v": "154억 달러"}, "r": {"label": "2025년 말", "v": "354억 달러"}, "lines": [
        L(["그 뒤로 6년 동안 나눠 넣은 돈이 154억 달러", "작년 말 평가액은 354억 달러예요"], "그 뒤로 육 년 동안 나눠 넣은 돈이 백오십사억 달러, 작년 말 평가액은 삼백오십사억 달러예요."),
        L(["작년 배당만 8억 6,200만 달러", "넣은 돈의 5.6%가 1년에 들어왔어요"], "작년 배당만 팔억 육천이백만 달러, 넣은 돈의 오 점 육 퍼센트가 일 년에 들어왔어요."),
    ], "page": {"head": "버크셔 · 일본 종합상사 5곳 (2025년 말)", "beats": [
        dict(kind="bars", items=[{"label": "넣은 돈", "v": 154, "text": "154억$", "color": "ink"},
                                 {"label": "평가액", "v": 354, "text": "354억$", "color": "red"}], x=120, y=180, w=820, h=460, line=0, at=.1),
        dict(kind="write", text="2.3배", x=640, y=230, size=130, color="red", line=0, at=.65, over=True),
        dict(kind="print", text="6년 동안 나눠 넣은 돈 154억 달러", x=90, y=740, size=40, w="Bold", line=0, at=.35),
        dict(kind="print", text="배당은 빼고 센 숫자", x=90, y=800, size=34, w="Medium", color="gray", line=0, at=.85),
        dict(kind="icons", icon="dollar", n=6, x=90, y=870, size=80, gap=50, color="green", line=1, at=.0, dur=.8),
        dict(kind="write", text="배당 8억 6,200만 달러", x=80, y=980, size=88, line=1, at=.3),
        dict(kind="write", text="1년에 5.6%", x=600, y=1100, size=100, color="red", line=1, at=.65),
    ]}},
    cta(["돈을 일본에서 빌린 이유는", "9분 풀영상에"], "commons_tokyocommute_1.jpg", "도쿄 출근길"),
]
A["caption"] = ("2020년 8월 30일, 워렌 버핏의 아흔 번째 생일에 버크셔 해서웨이는 일본 종합상사 5곳(이토추·마루베니·미쓰비시상사·미쓰이물산·스미토모상사)의 지분을 각각 5% 남짓 샀다고 밝혔습니다. "
                "1년 동안 도쿄 증시에서 사 모은 돈은 약 62억 5천만 달러였고, 그때 5곳 중 4곳은 주가가 순자산보다 낮았습니다.\n\n"
                "종합상사는 무역에서 출발해 지금은 칠레 구리 광산·호주 석탄·LNG 사업 지분과 로손·패밀리마트 같은 편의점까지 거느립니다. "
                "워렌 버핏은 이 회사들이 버크셔와 꽤 닮은 방식으로 잘 운영된다고 썼습니다.\n\n"
                "6년 동안 나눠 넣은 돈은 154억 달러, 2025년 말 평가액은 354억 달러(배당 제외 2.3배), 2025년 받은 배당은 8억 6,200만 달러입니다. "
                + SRC + " 굳이 일본에서 돈을 빌린 이유는 9분 풀영상에 정리했습니다." + CREDIT)
A["subs_en"] = ["Most people get gifts on their 90th birthday. Warren Buffett went shopping",
                "In the basket: five Japanese companies, now worth 2.3x what went in",
                "Itochu, Marubeni, Mitsubishi Corp., Mitsui & Co., Sumitomo Corp.: Japan's five trading houses",
                "Bought quietly on the Tokyo exchange over a year: about $6.25 billion, a little over 5% each",
                "Back then, four of the five traded below their net assets",
                "Like a shop selling 10,000 won of assets for 6,000 to 8,000 won",
                "Trading houses began as traders: oil, wheat and iron ore all came through them",
                "Now they own stakes in Chilean copper, Australian coal and LNG",
                "Even convenience stores: Lawson is half Mitsubishi Corp., half KDDI",
                "FamilyMart is almost all Itochu group. A rice ball in Tokyo adds a line to their books",
                "Warren Buffett wrote they are run much like Berkshire, and very well",
                "Five little Berkshires, each returning profits to shareholders",
                "Six years of buying: $15.4 billion in, worth $35.4 billion at the end of 2025",
                "Dividends last year alone: $862 million, 5.6% of the money put in",
                "Like and subscribe for more. Full video: profile link"]

# ───────────────────────── b. 엔화로 빌려 산 이유 ─────────────────────────
B = dict(BASE, id="Y261029b", scheduled_at="2026-10-29T16:00:00+09:00", mood="tense", broll="money",
         title="워렌 버핏은 왜 일본 주식 살 돈을 일본에서 빌렸을까? 이자의 6배 배당 #워렌버핏",
         title_en="Why did Warren Buffett borrow in Japan to buy Japanese stocks? Dividends 6x the interest #WarrenBuffett",
         banner=["워렌 버핏은 일본 주식 살 돈을", "왜 일본에서 빌렸을까?"], cover_title="일본 주식 살 돈\n일본에서\n빌린 이유",
         hashtags=["워렌버핏", "엔화", "일본주식", "버크셔해서웨이", "밸류노트", "shorts"],
         message="버크셔는 일본 주식 살 돈을 엔화 채권으로 빌려 환율 걱정을 덜었고, 받는 배당이 엔화 빚 이자의 약 6배인 구조를 만들었다.")
B["scenes"] = [
    {"type": "hook", "lines": [
        L(["워렌 버핏은 일본 주식을 살 때", "미국에서 달러를 보내지 않았습니다"], "워렌 버핏은 일본 주식을 살 때, 미국에서 달러를 보내지 않았습니다."),
        L(["살 돈을 일본에서, 엔화로 빌렸어요", "그런데 이게 이자의 6배를 버는 장치가 됐죠"], "살 돈을 일본에서, 엔화로 빌렸어요. 그런데 이게 이자의 여섯 배를 버는 장치가 됐죠."),
    ], "page": {"head": "BERKSHIRE  ·  JAPAN", "beats": [
        dict(kind="photo", src=LIB + "commons_omaha_1.jpg", x=600, y=150, w=400, h=290, rot=4, cap="오마하, 달러", line=0, at=0),
        dict(kind="write", rows=["미국 달러", "안 보냈다"], x=80, y=200, size=110, line=0, at=.3, dur=1.0),
        dict(kind="cross", x0=80, y0=230, x1=500, y1=420, color="red", line=0, at=.75),
        dict(kind="photo", src=LIB + "tokyo_28687_a.jpg", x=80, y=560, w=420, h=280, rot=-3, cap="도쿄, 엔화", line=1, at=0),
        dict(kind="write", rows=["일본에서", "엔화로 빌림"], x=560, y=590, size=96, color="blue", line=1, at=.2, dur=.9),
        dict(kind="write", text="이자의 6배", x=80, y=940, size=140, color="red", line=1, at=.65),
        dict(kind="under", x0=80, x1=720, y=1100, color="gold", line=1, at=.85),
    ]}},
    {"type": "statement", "l1": "엔화 채권", "l2": "평균 금리 1.2%", "lines": [
        L(["버크셔는 일본에서 엔화 채권", "그러니까 엔화 차용증을 내고 돈을 빌렸어요"], "버크셔는 일본에서 엔화 채권, 그러니까 엔화 차용증을 내고 돈을 빌렸어요."),
        L(["주식에 넣은 원금과 비슷한 만큼을 빌렸고", "평균 금리는 고작 1.2%였죠"], "주식에 넣은 원금과 비슷한 만큼을 빌렸고, 평균 금리는 고작 일 점 이 퍼센트였죠."),
    ], "page": {"head": "엔화 차용증 = 채권", "beats": [
        dict(kind="print", text="BERKSHIRE HATHAWAY  ·  엔화 채권", x=80, y=180, size=40, w="ExtraBold", line=0, at=.0),
        dict(kind="write", rows=["엔화로 이자 주는", "차용증"], x=80, y=250, size=100, line=0, at=.2, dur=1.0),
        dict(kind="hl", x0=80, y0=360, x1=360, y1=440, color="yellow", line=0, at=.75),
        dict(kind="write", text="빌린 돈 = 주식 원금 만큼", x=80, y=560, size=96, line=1, at=.0),
        dict(kind="print", text="평균 금리", x=90, y=740, size=48, w="ExtraBold", color="gray", line=1, at=.35),
        dict(kind="write", text="1.2%", x=80, y=800, size=200, color="red", line=1, at=.5),
        dict(kind="photo", src=LIB + "calculator_47415_a.jpg", x=600, y=780, w=380, h=270, rot=4, cap="그레그 에이블 서한", line=1, at=.7),
    ]}},
    {"type": "statement", "l1": "엔화가 떨어지면", "l2": "빚도 같이 줄어든다", "lines": [
        L(["엔화 값이 떨어지면 주식의 달러 가치는 줄어요", "그런데 갚을 빚의 달러 가치도 같이 줄어들죠"], "엔화 값이 떨어지면, 주식의 달러 가치는 줄어요. 그런데 갚을 빚의 달러 가치도 같이 줄어들죠."),
        L(["해외에 집을 사면서 그 나라 은행 대출을 낀 셈이죠", "그래서 환율로 잃을 걱정이 크게 줄었어요"], "해외에 집을 사면서 그 나라 은행 대출을 낀 셈이죠. 그래서 환율로 잃을 걱정이 크게 줄었어요."),
    ], "page": {"head": "엔화 약세가 오면", "beats": [
        dict(kind="print", text="엔화 값이 떨어지면", x=80, y=180, size=50, w="ExtraBold", color="red", line=0, at=.0),
        dict(kind="write", text="주식 (달러로)", x=80, y=270, size=90, line=0, at=.15),
        dict(kind="arrow", pts=[[640, 260], [640, 380]], color="red", line=0, at=.35, width=12),
        dict(kind="write", text="빚 (달러로)", x=80, y=420, size=90, line=0, at=.6),
        dict(kind="arrow", pts=[[640, 410], [640, 530]], color="blue", line=0, at=.8, width=12),
        dict(kind="photo", src=LIB + "tokyo_4231_a.jpg", x=600, y=600, w=400, h=280, rot=3, cap="해외 집 = 현지 대출", line=1, at=.0),
        dict(kind="write", rows=["해외 집 +", "그 나라 대출"], x=80, y=620, size=96, line=1, at=.15, dur=.9),
        dict(kind="write", text="환율 걱정 덜기", x=80, y=960, size=120, color="red", line=1, at=.6),
        dict(kind="circle", cx=400, cy=1030, rx=360, ry=100, color="gold", line=1, at=.88),
    ]}},
    {"type": "bars", "title": "2025년 예상 (워렌 버핏 2024년 주주서한)", "lines": [
        L(["워렌 버핏이 2024년 주주서한에 쓴 2025년 예상치를 볼게요", "받을 배당은 약 8억 1,200만 달러"], "워렌 버핏이 이천이십사년 주주서한에 쓴 이천이십오년 예상치를 볼게요. 받을 배당은 약 팔억 천이백만 달러,"),
        L(["엔화 빚 이자는 약 1억 3,500만 달러예요", "배당이 이자의 여섯 배쯤 되죠"], "엔화 빚 이자는 약 일억 삼천오백만 달러예요. 배당이 이자의 여섯 배쯤 되죠."),
        L(["1.2%에 빌려서 그보다 훨씬 많은 배당을 받는 거예요", "남의 돈으로 장 보고 거스름돈까지 챙긴 셈이죠"], "일 점 이 퍼센트에 빌려서 그보다 훨씬 많은 배당을 받는 거예요. 남의 돈으로 장 보고, 거스름돈까지 챙긴 셈이죠."),
    ], "page": {"head": "2025년 예상 · 1년", "beats": [
        dict(kind="bars", items=[{"label": "받을 배당", "v": 8.12, "text": "8.1억$", "color": "green"},
                                 {"label": "엔화 빚 이자", "v": 1.35, "text": "1.35억$", "color": "red"}], x=120, y=180, w=820, h=480, line=0, at=.12),
        dict(kind="print", text="워렌 버핏 2024년 주주서한", x=90, y=760, size=34, w="Medium", color="gray", line=0, at=.7),
        dict(kind="write", text="배당 8억 1,200만 달러", x=80, y=820, size=84, color="green", line=0, at=.4),
        dict(kind="write", text="약 6배", x=600, y=240, size=150, color="red", line=1, at=.5, over=True),
        dict(kind="circle", cx=740, cy=330, rx=230, ry=110, color="gold", line=1, at=.8),
        dict(kind="icons", icon="dollar", n=6, hl=[5], x=600, y=960, size=60, gap=50, color="green", hlcolor="gold", line=2, at=.05, dur=.8),
        dict(kind="write", rows=["남의 돈으로 장 보고", "거스름돈까지"], x=80, y=960, size=84, line=2, at=.45, dur=1.0),
    ]}},
    {"type": "statement", "l1": "사장이 바뀌어도", "l2": "장치는 그대로", "lines": [
        L(["이 장치는 워렌 버핏이 최고경영자에서 물러난 뒤에도 돌아가요", "올해 4월 버크셔는 엔화 채권 2,723억 엔어치를 새로 냈어요"], "이 장치는 워렌 버핏이 최고경영자에서 물러난 뒤에도 돌아가요. 올해 사월, 버크셔는 엔화 채권 이천칠백이십삼억 엔어치를 새로 냈어요."),
        L(["새 최고경영자 그레그 에이블도 일본 지분이", "미국 주요 보유 종목에 견줄 만큼 중요하다고 했죠"], "새 최고경영자 그레그 에이블도, 일본 지분이 미국 주요 보유 종목에 견줄 만큼 중요하다고 했죠."),
        L(["사장이 바뀌어도 단골집은 그대로인 셈이에요"], "사장이 바뀌어도, 단골집은 그대로인 셈이에요."),
    ], "page": {"head": "2026년 4월", "beats": [
        dict(kind="write", text="워렌 버핏 물러난 뒤에도", x=80, y=170, size=88, line=0, at=.03),
        dict(kind="print", text="2026년 4월 · 새 엔화 채권", x=80, y=300, size=44, w="ExtraBold", line=0, at=.4),
        dict(kind="write", text="2,723억 엔", x=80, y=360, size=140, color="red", line=0, at=.6),
        dict(kind="under", x0=80, x1=760, y=520, color="red", line=0, at=.88),
        dict(kind="write", rows=["일본 지분 =", "미국 주요 종목급"], x=80, y=600, size=92, line=1, at=.1, dur=1.0),
        dict(kind="hl", x0=80, y0=695, x1=700, y1=775, color="yellow", line=1, at=.7),
        dict(kind="photo", src=LIB + "commons_familymart_2.jpg", x=620, y=880, w=380, h=270, rot=3, cap="단골집", line=2, at=.0),
        dict(kind="write", rows=["사장 바뀌어도", "단골집 그대로"], x=80, y=900, size=92, color="gold", line=2, at=.2, dur=.9),
    ]}},
    {"type": "statement", "l1": "내 해외 투자는", "l2": "환율부터", "lines": [
        L(["해외 주식을 살 때 수익을 가르는 건", "회사만이 아니라 환율이기도 해요"], "해외 주식을 살 때 수익을 가르는 건, 회사만이 아니라 환율이기도 해요."),
        L(["내 계좌의 해외 주식이 원화로 얼마나 출렁였는지", "주가와 환율을 나눠서 한 번 보세요"], "내 계좌의 해외 주식이 원화로 얼마나 출렁였는지, 주가와 환율을 나눠서 한 번 보세요."),
    ], "page": {"head": "내 계좌에서는", "beats": [
        dict(kind="write", text="수익 = 주가 x 환율", x=80, y=200, size=110, line=0, at=.15),
        dict(kind="circle", cx=780, cy=270, rx=220, ry=90, color="red", line=0, at=.7),
        dict(kind="photo", src=LIB + "phone_4915_a.jpg", x=600, y=420, w=400, h=290, rot=4, cap="내 계좌", line=1, at=.0),
        dict(kind="check", text="주가 몫", x=90, y=480, size=88, line=1, at=.3),
        dict(kind="check", text="환율 몫", x=90, y=620, size=88, line=1, at=.6),
        dict(kind="under", x0=90, x1=460, y=740, color="gold", line=1, at=.85),
    ]}},
    cta(["상사 5곳의 정체와 지금 가격은", "9분 풀영상에"], "commons_itochuhq_2.jpg", "일본 종합상사 편"),
]
B["caption"] = ("버크셔 해서웨이는 일본 종합상사 주식을 살 때 미국에서 달러를 보내지 않고 일본에서 엔화 채권을 발행해 돈을 빌렸습니다. "
                "그레그 에이블은 주식에 넣은 원금과 비슷한 만큼을 빌렸고, 엔화로 빌린 돈의 평균 금리는 1.2%였다고 밝혔습니다.\n\n"
                "엔화가 약해지면 주식의 달러 가치는 줄지만 갚을 빚의 달러 가치도 같이 줄어 환율로 잃을 걱정을 크게 덜어 줍니다. "
                "워렌 버핏이 2024년 주주서한에 쓴 2025년 예상치는 배당 약 8억 1,200만 달러, 엔화 빚 이자 약 1억 3,500만 달러로 배당이 이자의 약 6배입니다.\n\n"
                "버크셔는 워렌 버핏이 물러난 뒤인 2026년 4월에도 2,723억 엔어치 엔화 채권을 새로 발행했습니다. "
                + SRC + " 나라 경제는 작아지는데 회사는 왜 커졌는지는 9분 풀영상에 정리했습니다." + CREDIT)
B["subs_en"] = ["When Warren Buffett bought Japanese stocks, he didn't send dollars from the U.S.",
                "He borrowed the money in Japan, in yen. It became a machine earning 6x the interest",
                "Berkshire issued yen IOUs, that is, bonds, to borrow yen",
                "About as much as the money put into the stocks, at an average rate of just 1.2%",
                "If the yen falls, the shares lose dollar value, but so does the debt",
                "Like buying a house abroad with a loan from a local bank",
                "If the house shrinks with the currency, so does the loan: far less currency worry",
                "Warren Buffett's 2024 letter estimated 2025 dividends at about $812 million",
                "Interest on the yen debt: about $135 million. Dividends about six times the interest",
                "Borrow at 1.2%, collect far more in dividends: shopping with others' money and keeping the change",
                "It runs even after Warren Buffett stepped down: ¥272.3 billion of new yen bonds in April",
                "New CEO Greg Abel says the Japan stakes rank with the major U.S. holdings",
                "New boss, same favorite shop",
                "With foreign stocks, returns depend on the currency as well as the company",
                "Split your foreign holdings' won swings into price and currency",
                "Like and subscribe for more. Full video: profile link"]

# ───────────────────────── c. 줄자 눈금 (나라는 작아지는데 회사는 커진 이유) ─────────────────────────
C = dict(BASE, id="Y261029c", scheduled_at="2026-10-29T21:30:00+09:00", mood="tense", broll="city",
         title="일본 월급 30만 엔, 달러로는 반 토막인데 일본 회사 이익은 왜 사상 최대일까? #일본경제",
         title_en="A 300,000-yen salary halved in dollars. So why are Japanese company profits at a record? #JapanEconomy",
         banner=["월급은 그대로인데 달러로 반 토막", "일본 회사 이익은 왜 사상 최대?"], cover_title="달러로 반 토막\n그런데 이익은\n사상 최대?",
         hashtags=["일본경제", "엔화", "엔저", "일본GDP", "밸류노트", "shorts"],
         message="일본 GDP 순위는 달러로 재 엔저에 내려갔지만, 해외에서 달러로 버는 회사는 같은 장사로 엔화 이익이 두 배 가까이 돼 나라와 회사 숫자가 반대로 움직였다.")
C["scenes"] = [
    {"type": "hook", "lines": [
        L(["도쿄 직장인 월급 30만 엔, 2012년엔", "달러로 바꾸면 3,750달러였어요"], "도쿄 직장인 월급 삼십만 엔, 이천십이년엔 달러로 바꾸면 삼천칠백오십 달러였어요."),
        L(["지금은 약 1,900달러, 반 토막이죠", "그런데 일본 회사 이익은 사상 최대입니다"], "지금은 약 천구백 달러, 반 토막이죠. 그런데 일본 회사 이익은 사상 최대입니다."),
    ], "page": {"head": "TOKYO  ·  월급 30만 엔", "beats": [
        dict(kind="photo", src=LIB + "commons_tokyocommute_1.jpg", x=600, y=150, w=400, h=290, rot=4, cap="도쿄 출근길", line=0, at=0),
        dict(kind="write", text="30만 엔", x=80, y=190, size=130, line=0, at=.15),
        dict(kind="print", text="2012 · 1달러 ≈ 80엔", x=84, y=380, size=40, w="ExtraBold", color="gray", line=0, at=.5),
        dict(kind="write", text="3,750달러", x=80, y=440, size=120, line=0, at=.7),
        dict(kind="print", text="2026 · 1달러 ≈ 157엔", x=84, y=620, size=40, w="ExtraBold", color="gray", line=1, at=.0),
        dict(kind="write", text="약 1,900달러", x=80, y=680, size=120, color="red", line=1, at=.1),
        dict(kind="write", text="반 토막", x=650, y=700, size=110, color="red", line=1, at=.4),
        dict(kind="write", rows=["그런데 회사 이익은", "사상 최대?"], x=80, y=900, size=100, color="gold", line=1, at=.7, dur=.9),
    ]}},
    {"type": "statement", "l1": "키는 그대로", "l2": "줄자 눈금만 바뀌었다", "lines": [
        L(["키는 그대로인데 줄자 눈금이 바뀐 셈이죠", "나라도 똑같아요"], "키는 그대로인데, 줄자 눈금이 바뀐 셈이죠. 나라도 똑같아요."),
        L(["달러로 잰 일본 경제는 2012년 6조 3천억 달러에서", "올해 4조 3천억 달러, 3분의 1 가까이 줄었죠"], "달러로 잰 일본 경제는, 이천십이년 육조 삼천억 달러에서 올해 사조 삼천억 달러. 삼분의 일 가까이 줄었죠."),
    ], "page": {"head": "일본 명목 GDP (달러 기준)", "beats": [
        dict(kind="write", rows=["키는 그대로", "줄자 눈금만 바뀜"], x=80, y=180, size=96, line=0, at=.05, dur=1.0),
        dict(kind="under", x0=80, x1=760, y=390, color="gold", line=0, at=.6),
        dict(kind="bars", items=[{"label": "2012년", "v": 6.3, "text": "6.3조$", "color": "ink"},
                                 {"label": "2026년", "v": 4.3, "text": "4.3조$", "color": "red"}], x=120, y=480, w=820, h=420, line=1, at=.05),
        dict(kind="print", text="3분의 1 가까이 줄었다", x=90, y=1010, size=44, w="Bold", line=1, at=.42),
        dict(kind="write", text="-31%", x=660, y=470, size=130, color="red", line=1, at=.7, over=True),
    ]}},
    {"type": "timeline", "title": "일본 경제 규모 세계 순위", "lines": [
        L(["1968년 세계 2위였던 일본은", "2010년 중국에, 2023년 독일에 밀렸고"], "천구백육십팔년 세계 이위였던 일본은, 이천십년 중국에, 이천이십삼년 독일에 밀렸고,"),
        L(["IMF는 내년에 인도와 영국에도 밀려", "6위가 될 거라고 봐요, 1968년 이후 처음이죠"], "아이엠에프는 내년에 인도와 영국에도 밀려 육위가 될 거라고 봐요. 천구백육십팔년 이후 처음이죠."),
    ], "page": {"head": "세계 순위 · IMF 2026년 10월 전망", "beats": [
        dict(kind="write", text="1968 · 2위", x=80, y=190, size=100, line=0, at=.0),
        dict(kind="write", text="2010 · 3위 (중국)", x=80, y=330, size=92, line=0, at=.4),
        dict(kind="write", text="2023 · 4위 (독일)", x=80, y=460, size=92, line=0, at=.75),
        dict(kind="arrow", pts=[[900, 220], [900, 760]], color="red", line=1, at=.0, width=12),
        dict(kind="write", text="2027 · 6위 전망", x=80, y=640, size=110, color="red", line=1, at=.2),
        dict(kind="print", text="인도·영국에 밀릴 전망", x=86, y=800, size=40, w="Bold", color="gray", line=1, at=.45),
        dict(kind="hl", x0=80, y0=880, x1=700, y1=960, color="yellow", line=1, at=.7),
        dict(kind="print", text="1968년 이후 처음", x=90, y=890, size=54, w="ExtraBold", line=1, at=.7),
    ]}},
    {"type": "statement", "l1": "GDP 순위는", "l2": "달러로 잰 성적표", "lines": [
        L(["일본이 금리를 오랫동안 0% 안팎에 묶자", "돈이 미국으로 빠져나가 엔화가 약해졌죠"], "일본이 금리를 오랫동안 영 퍼센트 안팎에 묶자, 돈이 미국으로 빠져나가 엔화가 약해졌죠."),
        L(["GDP 순위는 달러로 잰 성적표라 엔화가 약하면 같이 내려가요", "그런데 이 눈금, 어떤 회사에겐 정반대로 움직였습니다"], "지디피 순위는 달러로 잰 성적표라, 엔화가 약하면 같이 내려가요. 그런데 이 눈금, 어떤 회사에겐 정반대로 움직였습니다."),
    ], "page": {"head": "엔화는 왜 약해졌나", "beats": [
        dict(kind="print", text="일본 금리", x=90, y=180, size=44, w="ExtraBold", line=0, at=.0),
        dict(kind="write", text="0% 안팎", x=80, y=230, size=110, color="blue", line=0, at=.1),
        dict(kind="print", text="미국 금리", x=600, y=180, size=44, w="ExtraBold", line=0, at=.4),
        dict(kind="write", text="훨씬 높다", x=590, y=230, size=110, color="red", line=0, at=.5),
        dict(kind="arrow", pts=[[380, 420], [640, 420]], color="red", line=0, at=.75, width=12),
        dict(kind="write", rows=["GDP 순위 =", "달러로 잰 성적표"], x=80, y=540, size=96, line=1, at=.0, dur=1.0),
        dict(kind="write", text="엔화 약세 = 순위 하락", x=80, y=800, size=92, line=1, at=.3),
        dict(kind="write", text="그런데 회사는?", x=80, y=980, size=110, color="gold", line=1, at=.65),
    ]}},
    {"type": "compare", "title": "해외에서 1억 달러를 벌면", "l": {"label": "1달러 80엔", "v": "80억 엔"}, "r": {"label": "1달러 157엔", "v": "157억 엔"}, "lines": [
        L(["해외에서 1억 달러를 버는 회사라면", "1달러 80엔일 때 일본 장부엔 80억 엔이 찍혀요"], "해외에서 일억 달러를 버는 회사라면, 일 달러 팔십 엔일 때 일본 장부엔 팔십억 엔이 찍혀요."),
        L(["157엔이면 157억 엔이죠", "똑같이 장사했는데 이익이 두 배 가까이 돼요"], "백오십칠 엔이면 백오십칠억 엔이죠. 똑같이 장사했는데, 이익이 두 배 가까이 돼요."),
        L(["올해 4~6월 일본 회사 이익은 24.6% 늘어", "분기 기준 사상 최대였어요"], "올해 사월부터 유월까지 일본 회사 이익은 이십사 점 육 퍼센트 늘어, 분기 기준 사상 최대였어요."),
    ], "page": {"head": "같은 1억 달러, 다른 장부", "beats": [
        dict(kind="photo", src=LIB + "commons_lngcarrier_1.jpg", x=560, y=150, w=440, h=230, rot=3, cap="해외에서 달러로", line=0, at=0),
        dict(kind="write", text="1억 달러", x=80, y=200, size=120, line=0, at=.15),
        dict(kind="write", text="80엔 = 80억 엔", x=80, y=420, size=100, color="gray", line=0, at=.6),
        dict(kind="write", text="157엔 = 157억 엔", x=80, y=560, size=110, color="red", line=1, at=.1),
        dict(kind="write", text="x 2배 가까이", x=600, y=700, size=100, color="red", line=1, at=.55),
        dict(kind="print", text="일본 재무성 · 2026년 4~6월 · 1년 전보다", x=86, y=860, size=34, w="Medium", color="gray", line=2, at=.05),
        dict(kind="write", text="이익 +24.6%", x=80, y=910, size=130, color="red", line=2, at=.2),
        dict(kind="write", text="사상 최대", x=640, y=1080, size=100, color="gold", line=2, at=.65),
    ]}},
    {"type": "statement", "l1": "내 종목은", "l2": "어느 돈으로 버나", "lines": [
        L(["나라 성적은 달러로, 회사 장부는 엔화로 적으니", "두 숫자가 반대로 간 거예요"], "나라 성적은 달러로, 회사 장부는 엔화로 적으니까, 두 숫자가 반대로 간 거예요."),
        L(["내 종목도 확인해 보세요, 전자공시 다트에서 사업보고서의", "'사업의 내용'을 열면 지역별 매출이 나와요"], "내 종목도 확인해 보세요. 전자공시 다트에서 사업보고서의 사업의 내용을 열면, 지역별 매출이 나와요."),
        L(["해외 매출이 크면 원화 약세에 유리하고", "국내 매출이 크면 우리 경기가 더 중요하죠"], "해외 매출이 크면 원화 약세에 유리하고, 국내 매출이 크면 우리 경기가 더 중요하죠."),
    ], "page": {"head": "내 종목은 어느 돈으로 버나", "beats": [
        dict(kind="write", text="나라 성적 = 달러", x=80, y=180, size=96, color="blue", line=0, at=.05),
        dict(kind="write", text="회사 장부 = 엔화", x=80, y=310, size=96, color="red", line=0, at=.45),
        dict(kind="photo", src=LIB + "phone_4915_a.jpg", x=660, y=440, w=340, h=250, rot=4, cap="다트 사업보고서", line=1, at=.0),
        dict(kind="check", text="다트 검색", x=90, y=470, size=84, line=1, at=.2),
        dict(kind="check", text="사업의 내용", x=90, y=590, size=84, line=1, at=.5),
        dict(kind="check", text="지역별 매출", x=90, y=710, size=84, line=1, at=.8),
        dict(kind="write", text="해외 매출 크면: 원화 약세에 유리", x=80, y=880, size=88, color="red", line=2, at=.05),
        dict(kind="write", text="국내 매출 크면: 우리 경기가 중요", x=80, y=1010, size=88, color="blue", line=2, at=.55),
    ]}},
    cta(["워렌 버핏이 고른 상사 5곳은", "9분 풀영상에"], "commons_lawson_1.jpg", "일본 종합상사 편"),
]
C["caption"] = ("도쿄 직장인 월급 30만 엔은 2012년(1달러 약 80엔)엔 3,750달러, 지금(약 157엔)은 약 1,900달러입니다. 키는 그대로인데 줄자 눈금이 바뀐 셈입니다. "
                "달러로 잰 일본 경제도 2012년 6조 3천억 달러에서 2026년 4조 3천억 달러로 줄었고, IMF는 내년 일본이 인도·영국에 밀려 세계 6위가 될 것으로 봅니다(1968년 이후 처음).\n\n"
                "GDP 순위는 번 돈을 달러로 바꿔 잰 숫자라 엔화가 약하면 함께 내려갑니다. 반대로 해외에서 1억 달러를 버는 회사의 엔화 장부는 80억 엔에서 157억 엔이 됩니다. "
                "일본 재무성에 따르면 2026년 4~6월 일본 회사 이익은 1년 전보다 24.6% 늘어 분기 기준 사상 최대였습니다.\n\n"
                "내 종목은 전자공시 다트(DART) 사업보고서 '사업의 내용'의 지역별 매출로 확인할 수 있습니다. "
                + SRC + " 워렌 버핏이 고른 상사 5곳 이야기는 9분 풀영상에 있습니다." + CREDIT)
C["subs_en"] = ["A Tokyo salary of 300,000 yen was $3,750 in 2012",
                "Now about $1,900: same salary, halved. Yet Japanese company profits are at a record",
                "Same height, different tape measure. The whole country too",
                "Japan's economy in dollars: $6.3 trillion in 2012, $4.3 trillion this year, down almost a third",
                "Japan rose to No. 2 in 1968, lost places to China in 2010 and Germany in 2023",
                "The IMF sees it slipping to 6th next year behind India and the U.K., a first since 1968",
                "GDP rankings measure a country's income in dollars",
                "Japan kept rates near zero for years; money flowed to higher U.S. rates and the yen weakened",
                "A weaker yen drags the ranking down. But for some companies it worked the other way",
                "A company earning $100 million abroad: at 80 yen, 8 billion yen on its books",
                "At 157 yen, 15.7 billion yen. Same business, nearly double the profit",
                "Apr-Jun this year, Japanese corporate profits rose 24.6%, a quarterly record",
                "The country is graded in dollars, companies keep books in yen: so the numbers diverged",
                "Check your own stocks: in DART filings, open 'Business overview' for sales by region",
                "Big overseas sales gain when the won is weak; domestic sellers depend more on our economy",
                "Like and subscribe for more. Full video: profile link"]

for s in (A, B, C):
    with open(os.path.join(SPECS, s["id"] + ".json"), "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=1)
    print("wrote", s["id"], sum(len(sc["lines"]) for sc in s["scenes"]), "lines")
