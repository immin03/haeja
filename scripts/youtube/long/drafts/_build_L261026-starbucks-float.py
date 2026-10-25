"""스타벅스 롱폼 원고 만들기 (L261026-starbucks-float). 실행: python3 /tmp/sbux_build.py <media-map.json>
미디어 자리표 @이름 → 실제 라이브러리 파일 이름으로 바꾼다."""
import json, sys

FX = "원화는 1달러 1,324.2원 (10월 22일 종가)"
S_10K = "스타벅스 FY2025 연차보고서 (10-K, 2025년 9월 28일 기준)"
S_Q1 = "스타벅스 FY2026 1분기 보고서 (10-Q, 2025년 12월 28일 기준)"
S_Q3 = "스타벅스 FY2026 3분기 실적 발표 (2026년 7월 29일, 6월 28일 기준)"
S_DIG = "스타벅스 디지털 IR 대시보드 (FY2026 3분기, 미국 직영점)"
S_FY25 = "스타벅스 FY2025 실적 발표 (2025년 10월 29일)"

sc = []
def add(v, lines, en, src=None, chapter=None, asof=False, **kw):
    s = {"v": v, "lines": lines, "en": en, "asof": asof}
    if src: s["src"] = src
    if chapter: s["chapter"] = chapter
    s.update(kw); sc.append(s)

# ── 콜드 오픈 (0:00~0:40) ──
add({"type": "media", "lib": "@phone_pay", "caption": "스타벅스 앱 속 충전금, 다 합치면?", "caption_at": "0"},
    ["스타벅스 앱에 충전해 둔 돈, 미국 손님 것만 다 합치면 얼마일까요?"],
    ["Add up all the money Americans have loaded into the Starbucks app. How much is it?"], chapter="스타벅스 충전금은 얼마나 될까")
add({"type": "kinetic", "backdrop": "@coffee_counter", "bd_dim": 0.74, "words": [
        {"t": "약 17억 5천만 달러", "at": "0:17억", "size": 150, "c": "acc", "under": True},
        {"t": "≈ 2조 3천억 원", "at": "0:2조", "size": 90, "c": "muted"}]},
    ["약 17억 5천만 달러, 우리 돈으로 2조 3천억 원이 넘습니다."],
    ["About 1.75 billion dollars."], src=f"{S_10K} · 충전카드·리워드 별 잔액 17억 5,170만 달러 · {FX}")
add({"type": "stat", "kicker": "크리스마스 선물 시즌 직후 · 2025년 12월 28일", "value": "20억 7천만 달러", "label": "손님이 맡겨 둔 충전금·적립 별", "label_en": "Card & Stars balance after the holidays", "at": "0:20억", "count": False, "backdrop": "@gift", "bd_dim": 0.72},
    ["크리스마스 선물 시즌이 지나면, 20억 달러를 훌쩍 넘고요."],
    ["After the holiday gift season, it tops 2 billion dollars."], src=f"{S_Q1} · 20억 7,330만 달러")
add({"type": "media", "lib": "@store", "caption": "스타벅스 주주라면, 또는 관심 있다면", "caption_at": "0"},
    ["스타벅스 주식을 갖고 계시거나 관심 있는 분이라면,", "앞으로 9분이 스타벅스가 진짜 어떻게 돈을 버는지, 큰 그림으로 이해하는 시간이 될 겁니다."],
    ["If you own Starbucks stock or are thinking about it,", "the next nine minutes will show you, in one big picture, how Starbucks really makes money."])
add({"type": "checklist", "title": "이 영상을 보면 알게 되는 것", "title_en": "What you'll take away", "star": 2, "backdrop": "@coffee_cup", "bd_dim": 0.76,
     "items": [["커피 말고 스타벅스를 받쳐 주는 돈", "1:커피"], ["그 돈이 이자보다 더 큰 힘이 되는 이유", "2:이자보다"], ["10월 29일 실적 발표 때 볼 숫자 세 개", "3:10월"]]},
    ["이 영상을 보시면 세 가지를 알게 됩니다.", "하나, 커피 말고 스타벅스를 받쳐 주는 돈.", "둘, 그 돈이 이자보다 더 큰 힘이 되는 이유.", "셋, 10월 29일 실적 발표 때 딱 세 숫자만 보면 되는 이유와, 그 숫자요."],
    ["Here's what you'll take away.", "One: the money behind Starbucks that isn't coffee.", "Two: why that money is worth more than interest.", "Three: the three numbers to watch on October 29 earnings, and why only those three."])
add({"type": "question", "text": "이자 0원, 갚는 날도 없는 돈?", "backdrop": "@bank", "bd_dim": 0.64},
    ["그런데 이 돈, 은행이라면 이자를 줘야 하는 돈이에요. 스타벅스는 한 푼도 안 줍니다.", "이자 0원에 갚는 날짜도 없는 돈. 이런 대출, 저도 받고 싶네요."],
    ["If a bank held this money, it would owe you interest. Starbucks pays none.", "Zero interest, no due date. I'd take a loan like that too."])

# ── 1막 · 충전 버튼을 누르는 3,580만 명 ──
add({"type": "title", "text": "충전 버튼을 누르는 3,580만 명", "sub": "스타벅스 리워드"}, ["먼저, 이 돈이 어디서 왔는지부터 볼게요."], ["First, where does this money come from?"], chapter="충전 버튼을 누르는 3,580만 명")
add({"type": "media", "lib": "@barista", "caption": "아침 7시 반, 미국 어느 스타벅스", "caption_at": "1"},
    ["스타벅스 매장은 전 세계 4만 1,304곳, 미국에만 1만 6,933곳이 있어요.", "미국 직장인의 아침을 떠올려 보세요. 출근길에 앱으로 미리 주문하고, 매장에선 컵만 집어 들고 나갑니다.", "잔액이 모자라면 앱이 자동으로 25달러씩 채워 주죠."],
    ["Starbucks has 41,304 stores worldwide, 16,933 of them in the U.S.", "Picture a weekday morning in America. You order ahead in the app and just grab your cup.", "When the balance runs low, the app reloads 25 dollars automatically."])
add({"type": "media", "lib": "@phone_pay2", "chips": [{"v": "3,580만 명", "l": "미국 리워드 활성 회원 (90일)", "at": "0:3,580만"}, {"v": "59%", "l": "매출 중 회원 결제 비중", "at": "1:59"}]},
    ["이렇게 앱을 쓰는 미국 리워드 회원이 3,580만 명입니다.", "미국 직영점 매출의 59%를 이 회원들이 냅니다. 손님이 쓰는 돈 열 개 중 여섯 개가 앱에서 나오는 셈이죠.", "회원은 결제할 때마다 별을 모으고, 별로 음료를 받아요. 그래서 또 충전하게 되죠."],
    ["35.8 million active Starbucks Rewards members in the U.S.", "They account for 59% of spending at U.S. company-operated stores. Six in ten dollars come through the app.", "Members earn Stars with every purchase and redeem them for drinks, so they keep reloading."], src=f"{S_DIG} · 90일 활성 회원 3,580만 명 · 회원 결제 비중 59%")
add({"type": "stat", "kicker": "석 달 동안 미국 직영점 카드·앱에 충전된 돈", "value": "31억 달러", "label": "우리 돈 약 4조 원", "label_en": "Loaded to Starbucks Cards in one quarter", "at": "0:31억", "count": False},
    ["석 달 동안 카드와 앱에 새로 충전되는 돈만 31억 달러, 우리 돈 약 4조 원이에요.", "커피를 마시기 전에, 돈부터 먼저 들어오는 구조입니다."],
    ["In one quarter, 3.1 billion dollars were loaded onto cards and the app.", "The money arrives before the coffee is even made."], src=f"{S_DIG} · 충전액 31억 1,500만 달러 (2026년 3~6월) · {FX}")
add({"type": "media", "lib": "@mobile", "chips": [{"v": "33%", "l": "앱으로 미리 들어온 주문", "at": "1:세 건"}, {"v": "42%", "l": "카드·앱 잔액으로 낸 결제", "at": "2:42"}]},
    ["스타벅스가 선불카드를 처음 낸 건 2001년이에요. 20여 년 만에, 커피 회사가 은행 같은 지갑을 갖게 된 거죠.", "지금 미국 직영점 주문 세 건 중 한 건은, 매장에 오기 전에 앱으로 들어온 주문이에요.", "결제 건수로 보면 42%가 카드와 앱 잔액으로 계산됩니다. 거의 절반이죠."],
    ["Starbucks launched its prepaid card in 2001. Two decades later, a coffee company has a bank-like wallet.", "Today one in three orders at U.S. company-operated stores comes in through the app before the customer arrives.", "By transactions, 42% are paid with a Starbucks Card or app balance. Nearly half."], src=f"{S_DIG} · 모바일 주문 비중 33% · 카드 결제 비중 42% (거래 건수 기준)")
add({"type": "media", "lib": "@korea_cafe", "chips": [{"v": "4,275억 원", "l": "한국 사이렌오더 충전금 (2025년 말)", "at": "0:4,275억"}]},
    ["한국도 다르지 않아요. 사이렌오더에 쌓인 충전금이 2025년 말 4,275억 원이었습니다.", "다만 오늘은, 주식으로 사고팔 수 있는 미국 본사 스타벅스 이야기예요."],
    ["Korea is no different: Siren Order balances reached 427.5 billion won at the end of 2025.", "But today is about the U.S. parent, the Starbucks you can actually buy shares in."], src="SCK컴퍼니 2025년 감사보고서 (파이낸셜뉴스 2026년 5월 24일 보도) · 한국 스타벅스는 이마트·싱가포르투자청이 주주인 별도 회사")

# ── 2막 · 손님이 은행이 된 회사 ──
add({"type": "title", "text": "손님이 은행이 된 회사", "sub": "이자 0원, 만기 없음"}, ["그럼 이 돈은, 회계로는 뭘까요?"], ["So what is this money, in accounting terms?"], chapter="손님이 은행이 된 회사")
add({"type": "card", "kicker": "충전금 = 갚아야 할 돈", "title": "손님에게 커피로 돌려줘야 하는 빚", "title_en": "A liability repaid in coffee", "at": "0",
     "rows": [["돈은 먼저 받고", "0:먼저"], ["커피는 나중에 내준다", "1:나중"], ["이자는 0원, 갚는 날도 없다", "2:이자"]]},
    ["손님이 충전한 돈은, 회계로는 스타벅스가 갚아야 할 빚이에요.", "돈은 먼저 받고, 커피는 나중에 내주니까요.", "그런데 이 빚엔 이자도, 갚는 날짜도 없습니다. 손님이 은행이고, 스타벅스가 대출자인 셈이죠.", "커피를 미리 팔아 둔 돈이라, 그 돈으로 매장을 먼저 돌릴 수도 있고요."],
    ["To Starbucks, your loaded balance is a liability.", "It takes the money now and hands over coffee later.", "But this debt has no interest and no due date. Customers are the bank, Starbucks is the borrower.", "It is coffee sold in advance, cash Starbucks can put to work first."], src=f"{S_10K} · 충전카드 잔액은 부채(이연수익)로 기록")
add({"type": "headline", "items": [{"src": "S&P 글로벌 분석 (모닝스타 보도)", "date": "2016년 6월", "title": "스타벅스 카드 잔액 12억 달러, 웬만한 미국 은행 예금보다 많다", "at": "0"},
                                    {"src": "스타벅스 10-Q", "date": "2025년 12월 28일", "title": "충전금·별 잔액 20억 7천만 달러", "red": True, "at": "1:20억"}], "note": "10년 사이 약 1.7배", "note_at": "1"},
    ["이미 2016년에, 스타벅스 카드에 쌓인 돈이 12억 달러로 웬만한 미국 은행 예금보다 많다는 분석이 나왔어요.", "그게 지금은 연말 기준 20억 달러를 넘었습니다.", "다만 은행 예금엔 이자가 붙지만, 스타벅스 잔액엔 이자가 붙지 않는다는 게 큰 차이죠."],
    ["Back in 2016, analysts noted Starbucks cards held 1.2 billion dollars, more than many U.S. banks had in deposits.", "Today it's over 2 billion after the holidays.", "The difference: bank deposits earn interest, Starbucks balances don't."], src="S&P 글로벌 마켓 인텔리전스 분석 (모닝스타 2016년 6월 13일 보도) · " + S_Q1)
add({"type": "bars", "title": "석 달마다 미국 직영점 카드·앱에 충전된 돈", "title_en": "Dollars loaded per quarter", "unit": "억 달러",
     "items": [["25년\n1분기", 35.2, "0:35억", True, "35.2억"], ["25년\n2분기", 26.3, "0:35억", False, "26.3억"], ["25년\n3분기", 29.6, "0:35억", False, "29.6억"], ["25년\n4분기", 28.0, "0:35억", False, "28.0억"], ["26년\n1분기", 35.6, "0:35억", True, "35.6억"]], "hl": [{"at": "1:선물", "i": 4, "note": "연말 석 달"}]},
    ["충전에도 계절이 있어요. 연말이 낀 석 달에는 35억 달러 넘게 충전됩니다.", "선물로 받은 카드가 연초까지 잔액으로 쌓이니까, 크리스마스 직후 잔액이 1년 중 가장 크죠."],
    ["Loading has seasons: the quarter with the holidays brings in over 3.5 billion dollars.", "Gift cards pile up as balances into the new year, so the balance peaks right after Christmas."], src=f"{S_DIG} · 회계연도 분기 기준 (1분기 = 10~12월)")
add({"type": "equation", "title": "만약 은행에서 빌렸다면 (가정)", "title_en": "If it were a bank loan (hypothetical)",
     "boxes": [{"text": "17.5억 달러", "label": "충전금·별 잔액", "at": "0:17억", "w": 460}, {"text": "4%", "label": "금리를 4%로 가정", "at": "0:4", "w": 300, "kind": "white"}, {"text": "약 7천만 달러", "label": "안 내는 1년 이자", "at": "1:7천만", "w": 480, "kind": "gold"}], "ops": ["×", "="]},
    ["이 돈을 은행에서 빌렸다고 치고, 금리를 4%로만 잡아 볼게요. 계산을 위한 가정이에요.", "1년에 약 7천만 달러, 우리 돈 900억 원이 넘는 이자를 안 내는 셈입니다.", "그럼 스타벅스는 이 돈으로 이자 장사를 하는 회사일까요?"],
    ["Say Starbucks borrowed it from a bank at just 4%, just as an assumption.", "That's about 70 million dollars a year in interest it never pays.", "So is Starbucks really in the interest business?"], src=f"{S_10K} 잔액 17억 5,170만 달러 × 가정 금리 4% (실제 금리와 다를 수 있는 단순 계산) · {FX}")

# ── 반전 · 이자로 버는 돈은 작다 ──
add({"type": "title", "text": "스타벅스는 이자로 돈을 벌까", "sub": "첫 번째 약속"}, ["처음에 말씀드린 첫 번째, 커피 말고 스타벅스를 받쳐 주는 돈이 정말 이자일까요?"], ["Promise one: is the money behind Starbucks really interest?"], chapter="스타벅스는 이자로 돈을 벌까")
add({"type": "question", "text": "17억 달러를 굴리면 1년에 얼마?", "backdrop": "@coffee_counter", "bd_dim": 0.64},
    ["17억 달러를 굴리면, 1년에 얼마나 벌 수 있을까요? 답은, 생각보다 작습니다."], ["How much can 1.75 billion dollars earn in a year? Less than you'd think."])
add({"type": "hbars", "title": "FY2025 · 스타벅스가 1년에 번 돈", "title_en": "Fiscal 2025, in U.S. dollars",
     "items": [["커피 장사로 남긴 돈 (영업이익)", 2936.6, "0:29억", "29억 4천만 달러"], ["이자·기타 수익 (현금 전체)", 113.3, "1:1억", "1억 1천만 달러"]], "hl": [{"at": "2:4%", "i": 1}]},
    ["실제 장부를 열어 볼게요. 2025 회계연도에 스타벅스가 커피 장사로 남긴 돈은 29억 4천만 달러.", "그런데 회사가 가진 현금 전체에서 나온 이자와 기타 수익을 다 합쳐도, 1억 1천만 달러예요.", "영업이익의 약 4%. 스타벅스는 이자로 먹고사는 회사가 아닙니다.", "손님이 언제든 꺼내 쓸 수 있는 돈이라, 오래 묶어 두는 상품에 넣기도 어렵죠. 처음부터 이자로 큰돈을 벌 구조가 아닌 겁니다."],
    ["Let's open the books. In fiscal 2025, Starbucks made 2.94 billion dollars of operating income.", "All its interest and other income, from all its cash combined, was 113 million.", "About 4% of operating income. Starbucks doesn't live on interest.", "Customers can spend it any time, so it can't be locked up for long. The structure was never built for big interest income."], src=f"{S_FY25} · 영업이익 29억 3,660만 달러 · 이자·기타 수익 1억 1,330만 달러")
add({"type": "media", "lib": "@drawer", "caption": "그런데 이자보다 큰 돈이 따로 있습니다", "caption_at": "0"},
    ["그런데 장부에는, 이자보다 두 배 큰 돈이 한 줄 더 있어요."],
    ["But the books show another line, twice as big as interest."])

# ── 3막 · 아무도 안 쓰는 돈, 낙전 ──
add({"type": "title", "text": "아무도 안 쓰는 돈, 낙전", "sub": "서랍 속 기프트카드"}, ["서랍 속에 잊고 지낸 기프트카드, 하나쯤 있으시죠?"], ["Got a forgotten gift card in a drawer somewhere?"], chapter="아무도 안 쓰는 돈, 낙전")
add({"type": "card", "kicker": "낙전 (breakage)", "title": "끝내 안 쓰일 것으로 보는 잔액", "title_en": "Breakage: balances never redeemed", "at": "0",
     "rows": [["과거 기록으로 안 쓰일 몫을 추정", "0:추정"], ["그만큼을 매출로 잡는다", "1:매출"]]},
    ["스타벅스는 과거 기록을 보고, 끝내 안 쓰일 잔액이 얼마인지 추정해요.", "그리고 그만큼을 매출로 잡습니다. 이걸 낙전, 영어로 브레이키지라고 해요.", "어디까지나 추정이라, 실제로 쓰인 돈과 차이가 나면 나중에 고쳐 잡습니다."],
    ["From past patterns, Starbucks estimates how much will never be spent.", "It books that as revenue. It's called breakage.", "It's an estimate, adjusted later if actual redemptions differ."], src=f"{S_10K} 회계 정책 (주석 1)")
add({"type": "bars", "title": "스타벅스 낙전 수익 · 1년", "title_en": "Breakage revenue per year", "unit": "백만 달러",
     "items": [["FY2024", 207.6, "0:2억 760만", False, "2억 760만"], ["FY2025", 222.4, "0:2억 2,240만", True, "2억 2,240만"]], "hl": [{"at": "1:이자", "i": 1}]},
    ["2025 회계연도 낙전 수익은 2억 2,240만 달러, 우리 돈 약 2,900억 원이에요.", "아까 이자·기타 수익의 두 배쯤 되죠. 잊힌 잔액이, 이자보다 더 많이 번 셈입니다.", "솔직히 제 서랍에도 잔액 남은 카드가 한 장 있는데, 스타벅스 실적에 조금 보탠 셈이네요.", "그래도 영업이익과 비교하면 8%가 안 돼요. 그러니 스타벅스의 진짜 힘은, 따로 있다는 얘기죠."],
    ["Fiscal 2025 breakage was 222 million dollars.", "About twice the interest and other income. Forgotten balances earned more than interest.", "Honestly, I have a card with a balance in my drawer too. I guess I chipped in.", "Still under 8% of operating income. So the real power lies elsewhere."], src=f"{S_10K} · 낙전 2억 2,240만 달러 (직영 2억 40만 + 라이선스 2,200만), 전년 2억 760만 달러 · {FX}")

# ── 4막 · 다시 오게 만드는 힘 ──
add({"type": "title", "text": "스타벅스는 왜 다시 오게 만들까", "sub": "두 번째 약속"}, ["두 번째 약속, 그 돈이 이자보다 더 큰 힘이 되는 이유입니다."], ["Promise two: why that money beats interest."], chapter="스타벅스는 왜 다시 오게 만들까")
add({"type": "media", "lib": "@queue", "caption": "앱에 12달러가 남아 있다면?", "caption_at": "0"},
    ["앱에 12달러가 남아 있으면, 내일 아침 다른 카페로 가기가 어렵죠.", "충전금의 진짜 힘은 이자가 아니라, 손님을 다시 오게 만드는 끈이에요. 이걸 락인, 붙잡아 두는 효과라고 합니다."],
    ["With 12 dollars left in the app, it's hard to try another cafe tomorrow.", "The real power isn't interest. It's the string that pulls customers back. Lock-in."])
add({"type": "timeline", "title": "브라이언 니콜의 '스타벅스로 돌아가자'", "title_en": "Back to Starbucks",
     "points": [{"x": "FY2025", "text": "미국 동일매장 매출 -2%", "at": "0:마이너스", "color": "red"}, {"x": "2024.9", "text": "브라이언 니콜 CEO 취임", "at": "1:니콜"}, {"x": "FY26 3분기", "text": "미국 동일매장 매출 +7.9%", "at": "2:7.9", "color": "gold"}]},
    ["그런데 이 끈도, 커피가 만족스러울 때만 버팁니다. 2025 회계연도에 미국 매장 매출은 1년 전보다 2% 줄었어요.", "2024년 9월에 온 브라이언 니콜 최고경영자는, 매장 경험부터 다시 고치겠다며 '스타벅스로 돌아가자'를 내걸었죠.", "메뉴를 줄이고 매장 서비스를 다시 손보는 동안, 2025 회계연도 영업이익률은 7.9%까지 내려왔어요. 고치는 비용이 먼저 나간 거죠.", "그리고 올해 3분기, 미국 기존 매장 매출이 7.9% 늘었습니다."],
    ["But the string holds only when the coffee experience does. In fiscal 2025, U.S. comparable sales fell 2%.", "CEO Brian Niccol, who arrived in September 2024, launched Back to Starbucks to fix the store experience first.", "While it trimmed the menu and reworked store service, the fiscal 2025 operating margin fell to 7.9%. The fixing cost came first.", "And last quarter, U.S. comparable store sales rose 7.9%."], src=f"{S_FY25} · {S_Q3}")
add({"type": "stat", "kicker": "FY2026 3분기 · 미국 기존 매장", "value": "+4.2%", "label": "손님 수(거래 건수) 증가", "label_en": "U.S. comparable transactions", "at": "0", "count": False,
     "tags": [{"text": "객단가 +3.6%보다 큰 몫", "at": "1:가격", "kind": "gold"}], "backdrop": "@store2", "bd_dim": 0.72},
    ["눈여겨볼 건 늘어난 이유예요. 손님 수가 4.2% 늘었습니다.", "리워드 활성 회원도 2년 전 3,380만 명에서 3,580만 명으로 늘었고요. 가격만 올려서가 아니라, 사람이 다시 돌아오고 있다는 뜻이죠. 처음에 말씀드린 두 번째, 다시 오게 만드는 힘이 숫자로 보이는 순간이에요."],
    ["What matters is why: transactions rose 4.2%.", "Active Rewards members also grew from 33.8 to 35.8 million in two years. Not just higher prices, but people coming back. That's promise two, the pull-back power, showing up in the numbers."], src=f"{S_Q3} · 거래 +4.2%, 객단가 +3.6%")

# ── 5막 · 또 하나의 선불, 네슬레 ──
add({"type": "title", "text": "네슬레가 미리 낸 71억 5천만 달러", "sub": "또 하나의 선불"}, ["그런데 스타벅스가 미리 받아 둔 돈은, 손님 충전금만이 아니에요."], ["And customer balances aren't the only money Starbucks got up front."], chapter="네슬레가 미리 낸 71억 달러")
add({"type": "media", "lib": "@supermarket", "chips": [{"v": "71.5억 달러", "l": "2018년 네슬레 선불", "at": "0:71억"}, {"v": "40년", "l": "나눠서 매출로", "at": "1:40년"}]},
    ["2018년, 네슬레는 마트에서 스타벅스 원두와 캡슐을 팔 권리를 사면서, 71억 5천만 달러를 한 번에 냈어요.", "왜 이렇게 큰돈을 미리 냈을까요? 마트와 캡슐 커피 시장에서, 스타벅스라는 이름을 쓰는 값이에요.", "스타벅스는 이 돈을 40년에 나눠서 매출로 잡습니다. 40년 할부로 받는 월급 같은 거죠."],
    ["In 2018, Nestle paid 7.15 billion dollars up front for the right to sell Starbucks beans and capsules in stores.", "Why so much up front? It's the price of using the Starbucks name in grocery aisles and coffee capsules.", "Starbucks spreads it as revenue over 40 years. Like a salary paid out over four decades."], src="스타벅스 FY2019 1분기 보고서 (10-Q) · 네슬레 계약 선불 약 70억 달러를 40년 정액으로 매출 인식 · 네슬레 발표 (2018년 5월 7일)")
add({"type": "stat", "kicker": "2026년 6월 28일 · 장부에 남은 장기 선수 매출", "value": "56억 달러", "label": "대부분이 네슬레가 미리 낸 돈", "label_en": "Long-term deferred revenue", "at": "0:56억", "count": False},
    ["그래서 지금도 장부에는, 앞으로 매출이 될 장기 선수금이 56억 달러 남아 있어요.", "손님 충전금 17억 달러에 이 돈까지, 스타벅스는 남의 돈을 먼저 받아 두는 데 정말 능한 회사입니다."],
    ["So the books still carry 5.6 billion dollars of long-term deferred revenue.", "Add the 1.75 billion in customer balances: Starbucks is very good at getting paid first."], src=f"{S_Q3} 재무상태표 · 장기 이연수익 56억 3,250만 달러")

# ── 6막 · 주식으로는 ──
add({"type": "title", "text": "스타벅스 주가, 숫자로 보면", "sub": "워렌 버핏의 스승의 계산법"}, ["그럼 주식으로는, 어떻게 봐야 할까요?"], ["So how should we look at the stock?"], chapter="스타벅스 주가, 숫자로 보면")
add({"type": "card", "kicker": "벤저민 그레이엄의 계산법", "title": "아주 깐깐한 바닥 계산", "title_en": "Benjamin Graham's floor value", "at": "0",
     "rows": [["여러 해 평균으로 번 돈", "0:평균"], ["× 최대 10배까지만", "1:10배"], ["앞으로의 성장은 0으로", "2:0으로"]]},
    ["워렌 버핏의 스승, 벤저민 그레이엄의 계산법을 빌려 볼게요.", "여러 해 평균으로 번 돈에, 최대 10배까지만 값을 쳐 줍니다.", "앞으로 더 클 거라는 기대는 0으로 놓아요. 그래서 아주 깐깐한, 바닥 계산이에요."],
    ["Let's borrow the method of Warren Buffett's teacher, Benjamin Graham.", "Take average earnings over several years, and pay at most 10 times that.", "Count future growth as zero. A strict floor."])
add({"type": "versus", "title": "{px_label} 기준 · 스타벅스 한 주", "title_en": "One Starbucks share",
     "left": {"name": "계산기가 매긴 값", "value": "{iv_short}", "label": "지금까지 번 돈 기준", "at": "0"},
     "right": {"name": "시장이 매긴 값", "value": "{px_short}", "label": "{px_label}", "at": "0:{px_short}", "win": "1:{mult}", "win_text": "계산기 값의 {mult}"}},
    ["이 계산으로 스타벅스 한 주는 {iv_short}. {px_label} 주가는 {px_short}이에요.", "시장이 계산기보다 {mult}를 쳐 주고 있는 거죠. 2025 회계연도 주당순이익이 1년 새 절반 넘게 줄어든 탓도 커요.", "시장은 니콜의 회복이 계속된다는 데 돈을 건 셈입니다."],
    ["By this math, one Starbucks share is worth {iv_short}. At {px_label} it traded at {px_short}.", "The market pays {mult} the calculator, partly because fiscal 2025 earnings per share fell by more than half.", "The market is betting Niccol's turnaround keeps going."], src="밸류노트 스타벅스 데이터 ({asof} 기준) · 적정 주가 = 여러 해 평균 이익 × 최대 10배 · " + S_FY25 + " (GAAP 주당순이익 1.63달러, -51%)", asof=True)
add({"type": "stat", "kicker": "스타벅스 FY2026 전망 · 조정 주당순이익", "value": "2.55~2.65달러", "label": "2025 회계연도 2.13달러에서 20% 넘게 회복", "label_en": "FY2026 adjusted EPS guidance", "at": "0", "count": False},
    ["회사도 회복을 자신하고 있어요. 올해 조정 주당순이익을 2.55달러에서 2.65달러로 내다봤습니다.", "작년 2.13달러보다 20% 넘게 많은 숫자죠. 이번 실적이 그 말을 지키는지가, 첫 시험대예요."],
    ["The company sounds confident: it guided fiscal 2026 adjusted EPS to 2.55 to 2.65 dollars.", "That's over 20% above last year's 2.13. This report is the first test of that promise."], src=f"{S_Q3} · FY2026 조정 EPS 전망 2.55~2.65달러 · {S_FY25} · FY2025 조정 EPS 2.13달러")
add({"type": "twocol", "title": "같은 주식, 두 가지 앞날", "title_en": "Two possible paths",
     "left": {"title": "회복이 이어지면", "gold": True, "at": "0", "items": [["손님 수 증가가 이익으로", "0:손님"], ["평균 이익도 다시 올라간다", "0:평균"]]},
     "right": {"title": "회복이 멈추면", "at": "1:멈추면", "items": [["줄어든 이익이 평균을 끌어내림", "1:평균"], ["시장 기대와 차이가 커진다", "1:기대"]]}},
    ["회복이 이어지면, 늘어난 손님이 이익이 되고, 여러 해 평균 이익도 다시 올라가요. 그럼 바닥 값도 함께 올라가죠.", "반대로 회복이 멈추면, 이익이 줄어든 해가 평균을 끌어내려서, 시장 기대와의 차이가 더 벌어집니다."],
    ["If the recovery continues, more customers become profit and the multi-year average rises, lifting the floor value.", "If it stalls, the weak years drag the average down and the gap with market hopes widens."])
add({"type": "phone", "layout": "trio", "img": "capture:SBUX", "title": "밸류노트", "sub": "워렌 버핏의 기준을 담은 앱", "trio": [{"key": "capture:SBUX", "label": "기업 상세", "at": "0"}, {"key": "capture:SBUX:list", "label": "기업 목록 · 매일 계산", "at": "0:600여"}, {"key": "capture:SBUX:value", "label": "저평가 우량주", "at": "1:바닥"}]},
    ["밸류노트에는 스타벅스를 포함해 600여 곳이, 이 기준으로 매일 계산돼 있어요. 스타벅스의 밸류노트 점수는 {score}점입니다.", "다만 이건 미래 기대를 0으로 놓은 바닥 계산이라, 목표 주가도 아니고 사라 팔라는 신호도 아니에요."],
    ["ValueNote runs this calculator daily on over 600 companies, Starbucks included. Its ValueNote score is {score}.", "It's a floor that counts growth as zero, not a target price or a buy or sell signal."], src="밸류노트 앱 화면 ({asof} 기준)", asof=True)

# ── 엔딩 · 10월 29일에 볼 숫자 3개 ──
add({"type": "title", "text": "10월 29일 실적에서 볼 숫자 3개", "sub": "세 번째 약속"}, ["마지막, 세 번째 약속이에요. 10월 29일, 미국 장 마감 뒤 실적이 나옵니다."], ["Finally, promise three. Results come out after the U.S. close on October 29."], chapter="10월 29일 실적에서 볼 숫자 3개")
add({"type": "question", "text": "그럼 주주라면, 무엇을 봐야 할까?", "backdrop": "@store2", "bd_dim": 0.64},
    ["그럼 스타벅스 주식을 가졌거나 사 볼까 고민하는 분이라면, 무엇을 봐야 할까요? 딱 세 숫자면 됩니다."], ["So if you own or are eyeing Starbucks, what should you watch? Just three numbers."])
add({"type": "table", "title": "스타벅스 주주가 볼 숫자 3개", "title_en": "Three numbers to watch", "cols": ["숫자", "회사가 내건 기준"], "cw": [620, 520],
     "rows": [["① 미국 기존 매장 매출", "4분기 +6.5% 이상", "0:6.5"], ["② 손님 수 (거래 건수)", "계속 늘어나는가", "1:손님"], ["③ 영업이익률 (조정)", "1년 11% 이상", "2:11"]], "hl": 1},
    ["첫째, 미국 기존 매장 매출. 회사는 이번 분기 6.5% 이상을 내걸었어요.", "둘째, 손님 수. 가격이 아니라 사람이 계속 돌아오는지가, 충전금이라는 끈이 튼튼한지를 보여 줘요.", "셋째, 영업이익률. 회사는 1년 기준 11% 이상을 예상했습니다. 매장을 고치는 데 쓴 돈이, 이익으로 돌아오기 시작했는지 보는 숫자죠."],
    ["One: U.S. comparable sales. The company guided to 6.5% or more this quarter.", "Two: transactions. Whether people, not prices, keep coming back shows if the string is holding.", "Three: operating margin. The company expects above 11% for the year, showing whether the store fixes are paying off."], src=f"{S_Q3} · FY2026 전망 (4분기 미국 동일매장 매출 +6.5% 이상, 연간 조정 영업이익률 11% 초과) · 실적 발표 2026년 10월 29일 장 마감 후")
add({"type": "kinetic", "backdrop": "@coffee_cup2", "bd_dim": 0.74, "words": [
        {"t": "이자 4%", "at": "0", "size": 110, "c": "muted"}, {"t": "낙전 8% 미만", "at": "0:낙전은", "size": 110, "c": "muted"}, {"t": "다시 오게 하는 힘", "at": "1:다시", "size": 120, "c": "acc", "under": True}]},
    ["정리하면, 충전금이 버는 이자는 이익의 4%, 낙전은 8%가 안 됩니다.", "스타벅스를 받쳐 주는 진짜 힘은, 내일 아침 또 오게 만드는 그 앱 잔액이에요.", "그리고 내 돈에 쓰는 법 하나. 충전은 한 달에 쓸 만큼만 해 두세요. 이자는 어차피 스타벅스 몫이니까요."],
    ["To sum up: interest is 4% of profit, breakage under 8%.", "What really holds Starbucks up is that app balance that brings you back tomorrow morning.", "One tip for your own money: load only what you'll spend in a month. The interest goes to Starbucks anyway."])
add({"type": "end", "title": "더 현명한 투자를 위해", "sub": "밸류노트가 함께하겠습니다", "btn_at": ["0:구독", "0:좋아요", "0:알림"],
     "next": {"thumb": "/social/youtube/L261025-tesla-faucet/thumb.jpg", "label": "함께 보면 좋은 영상", "title": "테슬라 주가 전망, 한 대 팔면 195만 원 남는데 몸값은 1,950조?", "at": "1:테슬라"}, "backdrop": "@store", "bd_dim": 0.74},
    ["10월 29일, 세 숫자가 어떻게 나올지 궁금하시다면 구독과 좋아요, 알림 설정 부탁드려요.", "차 한 대에 남는 돈으로 본 테슬라 편도 함께 보시면, 회사가 돈 버는 구조를 보는 눈이 하나 더 생길 거예요.", "여러분 앱엔 지금 얼마가 남아 있나요? 댓글로 알려 주세요. 밸류노트가 더 현명한 투자를 돕겠습니다. 감사합니다."],
    ["Curious how the three numbers land on October 29? Subscribe, like and turn on notifications.", "Watch our Tesla episode too, and you'll have one more way to read how a company makes money.", "How much is left in your app right now? Tell us in the comments. Thanks for watching."])

spec = {
 "id": "L261026-starbucks-float", "series": "돈 버는 구조", "plan": "P261026-starbucks-prepaid", "company": "SBUX", "events": [], "fx": 1324.2,
 "format": 2, "look": {"paper": "dots", "dark": "forest", "accent": "gold"}, "scheduled_at": "2026-10-26T19:00:00+09:00",
 "title": "스타벅스는 어떻게 돈을 벌까? 손님이 맡긴 돈만 17억 달러, 이자는 0원",
 "title_en": "How does Starbucks make money? Customers hold $1.75 billion in its app, interest-free",
 "thumb": {"photo": "@thumb_b", "focus_x": 0.6, "l1": "스타벅스 앱 속 충전금", "l2": "17억 달러, 이자는 0원?", "pos": "left"},
 "ab_sets": [
   {"key": "b", "default": True, "title": "스타벅스는 어떻게 돈을 벌까? 손님이 맡긴 돈만 17억 달러, 이자는 0원", "thumb": {"photo": "@thumb_b", "focus_x": 0.6, "l1": "스타벅스 앱 속 충전금", "l2": "17억 달러, 이자는 0원?", "pos": "left"}, "file": "thumb_b.jpg"},
   {"key": "a", "title": "스타벅스 주가, 10월 29일 실적 전 볼 숫자 3개 · 충전금 17억 달러의 비밀", "thumb": {"photo": "@thumb_a", "focus_x": 0.5, "l1": "스타벅스 주주라면", "l2": "10월 29일 이 숫자 3개", "pos": "left"}, "file": "thumb_a.jpg"},
   {"key": "c", "title": "스타벅스 적정주가는? 워렌 버핏 스승의 계산으론 {iv_short}", "thumb": {"photo": "@thumb_c", "focus_x": 0.6, "l1": "스타벅스 적정주가가", "l2": "{iv_short}이라고?", "pos": "left"}, "file": "thumb_c.jpg"}],
 "tags": ["스타벅스", "스타벅스 주가", "스타벅스 실적", "스타벅스 충전금", "Starbucks", "SBUX", "낙전", "브라이언 니콜", "네슬레", "워렌 버핏", "적정 주가", "미국주식"],
 "search_keywords": ["스타벅스 주가", "스타벅스는 어떻게 돈을 벌까", "스타벅스 실적", "스타벅스 충전금", "Starbucks stock"],
 "sources": [S_10K, S_Q1, S_Q3, S_DIG, S_FY25, "스타벅스 FY2019 1분기 보고서 (10-Q) · 네슬레 계약 회계 처리", "S&P 글로벌 마켓 인텔리전스 (모닝스타 2016년 6월 13일 보도)", "SCK컴퍼니 2025년 감사보고서 (파이낸셜뉴스 2026년 5월 24일 보도)", "밸류노트 스타벅스 데이터 ({asof} 기준)", "서울 외환시장 원·달러 환율 1,324.2원 (10월 22일 종가)"],
 "description_head": "스타벅스 주가와 실적이 궁금한 분, 스타벅스는 어떻게 돈을 버는지 궁금한 분을 위한 영상입니다. 미국 손님이 스타벅스 앱과 카드에 맡겨 둔 돈은 약 17억 5천만 달러, 크리스마스 직후엔 20억 달러가 넘습니다. 이자도 만기도 없는 이 돈으로 스타벅스는 정말 이자 장사를 할까요?\n\n실제 장부로 확인하면 이자·기타 수익은 영업이익의 약 4%, 잊힌 잔액을 매출로 잡는 낙전은 2억 2,240만 달러입니다. 진짜 힘은 손님을 다시 오게 만드는 앱 잔액이고, 브라이언 니콜의 '스타벅스로 돌아가자' 이후 미국 손님 수는 다시 늘고 있습니다. 네슬레가 2018년에 미리 낸 71억 5천만 달러 이야기, 그레이엄식 바닥 계산, 그리고 10월 29일 실적 발표 때 볼 숫자 세 개까지 정리했습니다.\n\n사진: 위키미디어 공용 — Shixart1985 (CC BY 2.0) · Infrogmation of New Orleans (CC BY 2.0) · Donald_Trung (CC BY-SA 4.0) · GoToVan from Vancouver, Canada (CC BY 2.0) · Another Believer (CC BY-SA 4.0) · Hiro - Kokoro☆Photo from Kyoto, Japan (CC BY-SA 2.0) · m01229 from USA (CC BY 2.0) · JimmyStardust (CC BY-SA 4.0) · Christian Bolz (CC BY-SA 4.0) · Pike Place Market (CC BY 2.0) · 그 밖의 영상: Mixkit\n\n#스타벅스 #스타벅스주가 #미국주식 #실적발표 #워렌버핏",
 "description_en": "Starbucks stock and earnings, explained: how does Starbucks really make money? U.S. customers keep about $1.75 billion in the Starbucks app and cards, topping $2 billion after the holidays, with no interest and no due date. Does Starbucks live off that float? The books say interest and other income is about 4% of operating income, and breakage, unspent balances booked as revenue, was $222 million. The real power is lock-in: the balance that brings you back. We also cover Nestle's $7.15 billion up-front payment, Benjamin Graham's floor value, and the three numbers to watch on the October 29 earnings release.\n\n#Starbucks #SBUX #stocks #earnings",
 "pinned_comment": "10월 29일 스타벅스 실적, 세 숫자 중 무엇이 가장 궁금하신가요? ① 미국 기존 매장 매출(전망 6.5% 이상) ② 손님 수 ③ 영업이익률(연간 11% 이상 전망). 실적이 나오면 이 댓글에 결과를 정리해 드릴게요.\n\n참고: 그레이엄식 계산(여러 해 평균 이익 × 최대 10배)으로 스타벅스 적정 주가는 {iv_short}, 밸류노트 점수는 {score}점입니다 ({asof} 기준). 목표 주가가 아니라 성장을 0으로 놓은 바닥 계산입니다.\n\n내 종목도 같은 기준으로: https://valuenote.co.kr/yt",
 "hook_promises": ["커피 말고 받쳐 주는 돈 → '스타벅스는 이자로 돈을 벌까'(약 2분대 회수)", "이자보다 큰 힘 → '스타벅스는 왜 다시 오게 만들까'", "10월 29일 볼 숫자 3개 → '10월 29일 실적에서 볼 숫자 3개'"],
 "viewer_question": "스타벅스 주식을 가진 사람·관심 있는 사람: 스타벅스는 진짜 어디서 돈을 벌고, 10월 29일 실적 때 무엇을 보면 되나?",
 "scenes": sc,
}

if __name__ == "__main__":
    mp = json.load(open(sys.argv[1])) if len(sys.argv) > 1 else {}
    txt = json.dumps(spec, ensure_ascii=False, indent=1)
    for k, v in mp.items(): txt = txt.replace('"@' + k + '"', json.dumps(v))
    import re
    left = sorted(set(re.findall(r'"@(\w+)"', txt)))
    if left: print("미디어 자리표 남음:", left)
    open("/tmp/haeja/scripts/youtube/long/specs/L261026-starbucks-float.json", "w").write(txt)
    n = sum(len(s["lines"]) for s in sc); print("장면", len(sc), "문장", n, "글자", sum(len(l) for s in sc for l in s["lines"]))
    for s in sc: assert len(s["lines"]) == len(s["en"]), s["v"]["type"]
