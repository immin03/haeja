# 롱폼 4편 썸네일 3장 (11/7 대표 확정 양식 v6: 배경에 녹은 큰 주화 + 결과형 문구 + 『명상록』 2장 · 스토아 철학 1장)
# 문구가 길어 흰 줄 2줄 + 노란 큰 줄 1줄로 나눈다
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from make_thumb_v6 import bg
from make_thumb_v5 import draw_rows, GOLD, BOLD
from make_thumb_solution import BLK, WHITE, YEL
OUT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/thumbs/ep04/"
from PIL import Image, ImageOps
G = "/home/claude/haeja/social/side/gen/"
if not os.path.exists(G + "e4_alone_flip.jpeg"): ImageOps.mirror(Image.open(G + "e4_alone.jpeg")).save(G + "e4_alone_flip.jpeg", quality=95)   # 황제를 오른쪽으로, 글자는 왼쪽
MAIN = ("e4_alone_flip.jpeg", 1.0, .5, .45, 2.7, "left"); ALT = ("e4_faustina.jpeg", 1.0, .5, .5, 1.5, "right")
def make(spec, label):
    rows = [(label, BOLD(64 if "명상록" in label else 58), GOLD, 88, -2),
            ("소중한 사람을 잃어도", BLK(84), WHITE, 100, -4), ("무너지지 않는", BLK(84), WHITE, 112, -4),
            ("5가지 방법", BLK(160), YEL, 0, -6)]
    return draw_rows(bg(spec), {"side": spec[5]}, rows, 96)
os.makedirs(OUT, exist_ok=True)
make(MAIN, "『명상록』").save(OUT + "ep04_M1.jpg", quality=92)
make(ALT, "『명상록』").save(OUT + "ep04_M2.jpg", quality=92)
make(MAIN, "스토아 철학").save(OUT + "ep04_S1.jpg", quality=92)
