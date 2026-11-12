"""원고 표현 검수 (2026-11-12 대표: "어색한 표현들은 기획하고 스크립트 나온 후 한번 검수를 하고 렌더링")

렌더 전에 내레이션(lines)을 훑어 어색한 말·읽기 실수를 막는다. 롱폼 render2.preflight 와 쇼츠 gate.py 가 같이 쓴다.
새 어색한 표현을 대표님이 짚으면 WORDS 에 한 줄 추가한다.
"""
import re

# 어색한 말 → 바꿀 말
WORDS = {
    "웃돈": "프리미엄",
    "접는 폰": "폴더블폰", "접는 아이폰": "폴더블 아이폰", "접는 화면": "폴더블 화면",
    "석 달": "세 달", "넉 달": "네 달",
    "열에 하나": "10분의 1",
    "일곳": "한 곳",
}
# 읽기 실수: 소수점 달러(331.90달러 → "삼백삼십일 점 구공 달러"로 읽힘) — "약 332달러"처럼 반올림하거나 "331달러 90센트"
DEC_MONEY = re.compile(r"\d+\.\d+\s*(달러|위안|엔|유로|원)")


def check_lines(lines):
    errs = []
    for i, l in lines:
        for w, r in WORDS.items():
            if w in l:
                errs.append(f"장면 {i}: 어색한 말 '{w}' → '{r}'")
        m = DEC_MONEY.search(l)
        if m:
            errs.append(f"장면 {i}: 소수점 금액 '{m.group(0)}' — 읽으면 '점 구공'이 된다. 반올림(약 …) 또는 'N달러 M센트'")
    return errs
