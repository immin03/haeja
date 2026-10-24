"""자막 문장을 TTS가 정확히 읽도록 한글 발음으로 바꾼다.
예) "1,000만 원" → "천만 원", "-9%" → "마이너스 구 퍼센트", "3배" → "세 배"
"""
import re

D = "영일이삼사오육칠팔구"
NATIVE = {1: "한", 2: "두", 3: "세", 4: "네", 5: "다섯", 6: "여섯", 7: "일곱", 8: "여덟", 9: "아홉", 10: "열",
          11: "열한", 12: "열두", 13: "열세", 14: "열네", 15: "열다섯", 16: "열여섯", 17: "열일곱", 18: "열여덟", 19: "열아홉", 20: "스무"}
WORDS = [("xAI", "엑스에이아이"), ("EBITDA", "에비타"), ("SpaceX", "스페이스엑스"),  # 2026-10-23 스페이스X 편
         ("창신메모리", "창신 메모리"), ("HBM4", "에이치비엠 포"), ("CXMT", "씨엑스엠티"), ("HBM3E", "에이치비엠 쓰리 이"), ("Y1", "와이 원"), ("Y2", "와이 투"), ("ValueNote", "밸유 노트"), ("밸류노트", "밸유 노트"), ("밸류 노트", "밸유 노트"),  # TTS가 "밸류 노트"는 "벨류"로 뭉갠다(음성 인식 검수로 확인)
        ("램리서치", "램 리서치"), ("D램", "디 램"), ("낸드플래시", "낸드 플래시"),  # 붙이면 "디엠", "랜드플랫시"로 뭉갬(검수로 확인)  # 붙여 읽으면 "랩소치"로 뭉갬(음성 인식 검수로 확인)
         ("AI", "에이아이"), ("ETF", "이티에프"), ("PER", "피이알"), ("PBR", "피비알"),
         ("ROE", "알오이"), ("DAY", "데이"), ("S&P", "에스앤피"), ("KOSPI", "코스피"), ("vs", "대"), ("bp", "베이시스 포인트")]


ABC = dict(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", ["에이", "비", "씨", "디", "이", "에프", "지", "에이치", "아이", "제이", "케이", "엘", "엠", "엔", "오", "피", "큐", "알", "에스", "티", "유", "브이", "더블유", "엑스", "와이", "제트"]))


def _group(n):  # 0~9999
    out = ""
    for unit, v in (("천", 1000), ("백", 100), ("십", 10), ("", 1)):
        q = n // v % 10
        if q == 0: continue
        out += ("" if (q == 1 and unit) else D[q]) + unit
    return out


def sino(n):
    n = int(n)
    if n == 0: return "영"
    out = ""
    for unit, v in (("조", 10 ** 12), ("억", 10 ** 8), ("만", 10 ** 4), ("", 1)):
        g = n // v % 10000
        if g == 0: continue
        out += ("" if (g == 1 and unit == "만") else _group(g)) + unit
    return out


def num(s):
    s = s.replace(",", "")
    if "." in s:
        a, b = s.split(".", 1)
        return sino(a) + " 점 " + " ".join(D[int(c)] for c in b)
    return sino(s)


def sign(s):
    return {"+": "플러스 ", "-": "마이너스 ", "−": "마이너스 "}.get(s, "")


# 타입캐스트(사람 성우형 엔진)는 '밸유 노트'처럼 예전 음성용으로 비튼 표기를 그대로 읽어 버린다 → 원래 표기로 둔다
TC_KEEP = {"ValueNote": "밸류노트", "밸류노트": "밸류노트", "밸류 노트": "밸류노트", "D램": "디 램", "창신메모리": "창신 메모리", "낸드플래시": "낸드플래시", "램리서치": "램리서치"}


def to_speech(text):
    import os
    t = text
    tc = bool(os.environ.get("TYPECAST_API_KEY"))
    for a, b in WORDS: t = t.replace(a, TC_KEEP.get(a, b) if tc else b)
    t = re.sub(r"(?<![A-Za-z])([A-Z]{1,5})(?![a-z])", lambda m: "".join(ABC[c] for c in m[1]), t)  # DB손해보험 → 디비손해보험
    t = re.sub(r"(\d)\s*~\s*(\d)", r"\1에서 \2", t)  # 1~2년 → 1에서 2년
    t = t.replace("→", ", ").replace("·", ", ").replace("×", "").replace("\n", " ")
    t = re.sub(r"([+\-−]?)(\d[\d,]*(?:\.\d+)?)\s*%p", lambda m: sign(m[1]) + num(m[2]) + " 퍼센트 포인트", t)
    t = re.sub(r"([+\-−]?)(\d[\d,]*(?:\.\d+)?)\s*%", lambda m: sign(m[1]) + num(m[2]) + " 퍼센트", t)
    t = re.sub(r"(?<![\d.,])(\d+\.\d+)\s*배", lambda m: num(m[1]) + " 배", t)  # 4.4배 → 사 점 사 배 (소수는 먼저)
    t = re.sub(r"(?<![\d.,])(\d+)\s*배(?!럴)", lambda m: (NATIVE[int(m[1])] if int(m[1]) in NATIVE else sino(m[1])) + " 배", t)  # 10배럴은 '십 배럴' (2026-10-24)
    t = re.sub(r"(?<![\d.,])(\d+)\s*월", lambda m: {6: "유월", 10: "시월"}.get(int(m[1])) or sino(m[1]) + "월", t)  # 6월 = 유월, 10월 = 시월 (2026-10-24 '육월'로 읽던 버그)
    t = re.sub(r"(?<![\d.,])(\d+)\s*(주당)", lambda m: (NATIVE.get(int(m[1])) or sino(m[1])) + " " + m[2], t)
    t = re.sub(r"(?<![\d.,])(\d+)\s*(달(?!러)|개(?!월)|가지|번)", lambda m: (NATIVE.get(int(m[1])) or sino(m[1])) + " " + m[2], t)  # 18달러는 '십팔 달러' (2026-10-24 '열여덟 달러'로 읽던 버그)
    t = re.sub(r"([+\-−]?)(\d[\d,]*(?:\.\d+)?)", lambda m: sign(m[1]) + num(m[2]), t)
    return re.sub(r"\s+", " ", t).strip()


if __name__ == "__main__":
    for s in ["지수는 1% 빠졌는데, 3배 상품은 9%", "1,000만 원이 796만 원", "-204만 원", "1억 7,449만 원", "5.8% vs 8.9%",
              "62건 중 60점 이상 27건", "한 달, 1달", "1988년", "PER 40에 산 1,000만 원", "+0.15%p"]:
        print(s, "→", to_speech(s))
