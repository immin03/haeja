"""자막 문장을 TTS가 정확히 읽도록 한글 발음으로 바꾼다.
예) "1,000만 원" → "천만 원", "-9%" → "마이너스 구 퍼센트", "3배" → "세 배"
"""
import re

D = "영일이삼사오육칠팔구"
NATIVE = {1: "한", 2: "두", 3: "세", 4: "네", 5: "다섯", 6: "여섯", 7: "일곱", 8: "여덟", 9: "아홉", 10: "열"}
WORDS = [("ValueNote", "밸류 노트"), ("밸류노트", "밸류 노트"), ("ETF", "이티에프"), ("PER", "퍼"), ("PBR", "피비알"),
         ("ROE", "알오이"), ("DAY", "데이"), ("S&P", "에스앤피"), ("KOSPI", "코스피"), ("vs", "대"), ("bp", "베이시스 포인트")]


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


def to_speech(text):
    t = text
    for a, b in WORDS: t = t.replace(a, b)
    t = t.replace("→", ", ").replace("·", ", ").replace("×", "").replace("\n", " ")
    t = re.sub(r"([+\-−]?)(\d[\d,]*(?:\.\d+)?)\s*%p", lambda m: sign(m[1]) + num(m[2]) + " 퍼센트 포인트", t)
    t = re.sub(r"([+\-−]?)(\d[\d,]*(?:\.\d+)?)\s*%", lambda m: sign(m[1]) + num(m[2]) + " 퍼센트", t)
    t = re.sub(r"(\d+)\s*배", lambda m: (NATIVE[int(m[1])] if int(m[1]) in NATIVE else sino(m[1])) + " 배", t)
    t = re.sub(r"(\d+(?:\.\d+)?)\s*배", lambda m: num(m[1]) + " 배", t)
    t = re.sub(r"(\d+)\s*(달|개|가지|번)", lambda m: (NATIVE.get(int(m[1])) or sino(m[1])) + " " + m[2], t)
    t = re.sub(r"([+\-−]?)(\d[\d,]*(?:\.\d+)?)", lambda m: sign(m[1]) + num(m[2]), t)
    return re.sub(r"\s+", " ", t).strip()


if __name__ == "__main__":
    for s in ["지수는 1% 빠졌는데, 3배 상품은 9%", "1,000만 원이 796만 원", "-204만 원", "1억 7,449만 원", "5.8% vs 8.9%",
              "62건 중 60점 이상 27건", "한 달, 1달", "1988년", "PER 40에 산 1,000만 원", "+0.15%p"]:
        print(s, "→", to_speech(s))
