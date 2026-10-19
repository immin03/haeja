# 소개 페이지(/start)에 쓰는 실제 앱 화면을 릴스 캡처에서 잘라 만든다.
# 사용: node scripts/reels/capture.js 로 캡처를 새로 찍은 뒤 → python3 scripts/start-shots.py
# 결과: start-img/portfolio.webp, start-img/radar.webp (2배율, 폭 780px)
import json, os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'scripts', 'reels', 'screens')
OUT = os.path.join(ROOT, 'start-img')
os.makedirs(OUT, exist_ok=True)

def bottom_of(name, starts, n):
    """캡처 옆 json에서 글자가 starts로 시작하는 블록의 n번째 아래 끝을 찾는다 (없으면 None)"""
    boxes = json.load(open(os.path.join(SRC, name + '.json')))
    hits = sorted({b['b'][3] for b in boxes if b['t'].startswith(starts) and b['b'][2] - b['b'][0] > 500})
    return hits[n] if len(hits) > n else None

def cut(name, bottom, default):
    im = Image.open(os.path.join(SRC, name + '.png')).convert('RGB')
    y = bottom or default
    im = im.crop((0, 0, im.width, min(y + 24, im.height)))
    im.save(os.path.join(OUT, name + '.webp'), 'WEBP', quality=82, method=6)
    print('저장', name, im.size)

# 포트폴리오: 맨 위 ~ 보유 종목 6개까지 (총 평가액·30일 추이·종목 목록)
boxes = json.load(open(os.path.join(SRC, 'portfolio.json')))
rows = sorted({b['b'][3] for b in boxes if '비중' in b['t'] and b['b'][3] - b['b'][1] < 160 and b['b'][2] - b['b'][0] > 600})
cut('portfolio', rows[5] if len(rows) > 5 else None, 1700)
# 경제 레이더: 맨 위 ~ 지표 10개 레이더 차트까지
cut('radar', bottom_of('radar', '지표 10개', 0), 1640)
