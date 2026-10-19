# 소개 페이지(/start)에 쓰는 실제 앱 화면을 릴스 캡처에서 잘라 만든다.
# 사용: node scripts/reels/capture.js 로 캡처를 새로 찍은 뒤 → python3 scripts/start-shots.py
# 결과: start-img/portfolio.webp (현황 요약 + 성격별 대표 종목 4줄 + 지금 할 일 첫 줄), start-img/radar.webp
import json, os
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'scripts', 'reels', 'screens')
OUT = os.path.join(ROOT, 'start-img')
os.makedirs(OUT, exist_ok=True)

def boxes(name):
    return json.load(open(os.path.join(SRC, name + '.json')))

def save(im, name):
    im.save(os.path.join(OUT, name + '.webp'), 'WEBP', quality=82, method=6)
    print('저장', name, im.size)

# ---------- 포트폴리오: 실제 화면에서 필요한 줄만 이어 붙인다 ----------
im = Image.open(os.path.join(SRC, 'portfolio.png')).convert('RGB')
B = boxes('portfolio')
wide = [b for b in B if b['b'][2] - b['b'][0] > 600]
def first(pred):
    for b in sorted(wide, key=lambda b: b['b'][1]):
        if pred(b): return b['b']
    return None
row = lambda b: '비중' in b['t'] and b['b'][3] - b['b'][1] < 260 and b['b'][1] > 700
top = first(lambda b: b['t'].startswith('총 평가액') and b['b'][3] - b['b'][1] < 400)
picks = [first(lambda b: row(b) and '가치주 유지' in b['t']),
         first(lambda b: row(b) and '고평가' in b['t']),
         first(lambda b: row(b) and '관찰주' in b['t']),
         first(lambda b: row(b) and '투기주' in b['t'])]
picks = [p for p in picks if p]
cash = first(lambda b: b['t'].startswith('현금'))
todo_h = first(lambda b: b['t'].startswith('지금 할 일') and b['b'][3] - b['b'][1] < 90)
todo_1 = first(lambda b: (b['t'].startswith('우선') or b['t'].startswith('조정')) and b['b'][3] - b['b'][1] < 160)

parts = [(0, top[3] + 18)]                          # 앱 머리·탭·총 평가액
parts += [(p[1], p[3]) for p in picks]              # 대표 종목 줄
if cash: parts.append((cash[3], cash[3] + 46))      # 카드 아래 둥근 끝
if todo_h and todo_1:
    parts.append((todo_h[1] - 34, todo_1[1]))       # '지금 할 일' 제목 + 카드 위 끝
    parts.append((todo_1[1], todo_1[3]))            # 첫 줄 (우선 정리)
H = sum(b - a for a, b in parts) + 60
bg = im.getpixel((10, todo_h[1] if todo_h else im.height - 10))
out = Image.new('RGB', (im.width, H), bg)
y = 0
for a, b in parts:
    out.paste(im.crop((0, a, im.width, b)), (0, y)); y += b - a
if todo_1:
    # 첫 줄 아래로 흰 카드를 닫는다: 둥근 끝을 그린 뒤 안쪽 글자는 원본으로 다시 덮는다
    from PIL import ImageDraw
    d = ImageDraw.Draw(out)
    x0, x1 = 32, im.width - 32
    card = im.getpixel((im.width // 2, todo_1[1] + 6)); line = im.getpixel((x0, todo_1[1] + 6))
    h1 = todo_1[3] - todo_1[1]
    top_y = y - 70  # 첫 줄 아래쪽 70px만 다시 그려 카드 위쪽은 원본 그대로 둔다
    d.rounded_rectangle((x0, top_y - 40, x1, y + 34), radius=30, fill=card, outline=line, width=2)
    out.paste(im.crop((x0, todo_1[3] - 110, x1, todo_1[3] - 72)), (x0, top_y - 40))
    out.paste(im.crop((x0 + 3, todo_1[3] - 72, x1 - 3, todo_1[3] - 2)), (x0 + 3, top_y - 2))
    d.rectangle((x0 + 3, y - 2, x1 - 3, y + 4), fill=card)
    y += 34
save(out.crop((0, 0, im.width, y + 16)), 'portfolio')

# ---------- 경제 레이더: 맨 위 ~ 위험 신호등(게이지) 카드까지 ----------
im = Image.open(os.path.join(SRC, 'radar.png')).convert('RGB')
g = next((b['b'] for b in sorted(boxes('radar'), key=lambda b: b['b'][1])
          if b['t'].startswith('안정 양호 유의 경계 위험') and b['b'][2] - b['b'][0] > 600), None)
y = (g[3] if g else 976) + 30
save(im.crop((0, 0, im.width, min(y, im.height))), 'radar')
