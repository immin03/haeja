"""라이브러리 영상의 펼친 책 종이에 '얼룩 같은 잉크 자국' 대신 실제 필기체 글씨를 입혀 새 영상으로 굽는다 (2026-11-05 대표: 노트는 얼룩 대신 글자가 써진 것으로).

python3 page_ink.py candle_diary [--test]
 · 종이마다 네 모서리(첫 프레임)를 정해 두면, 종이 위 특징점으로 카메라 움직임을 따라가며
   ① 영상 모델이 그린 굵은 얼룩을 종이 색으로 지우고 ② 원근에 맞춰 영어 필기체(『명상록』 영역본)를 얹는다.
 · 결과: social/side/gen/libv_<이름>_ink.mp4 (library.py 가 있으면 이걸 먼저 쓴다)
"""
import os, sys, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
FONT = "/root/fonts/PinyonScript-Regular.ttf"
TXT = ("Begin the morning by saying to thyself, I shall meet with the busy-body, the ungrateful, arrogant, deceitful, envious, unsocial. "
       "All these things happen to them by reason of their ignorance of what is good and evil. But I who have seen the nature of the good that it is beautiful, "
       "and of the bad that it is ugly, can neither be injured by any of them, for no one can fix on me what is ugly. "
       "When thou hast done a good act and another has received it, why dost thou still look for a third thing besides these, as fools do, "
       "either to have the reputation of having done a good act or to obtain a return. A man when he has done a good act does not call out for others to come and see, "
       "but he goes on to another act, as a vine goes on to produce again the grapes in season.")

# 종이: 네 모서리 [안쪽 위, 바깥 위, 바깥 아래, 안쪽 아래] (첫 프레임 픽셀), 글씨 영역(u0,u1,v0,v1 비율), 줄 수
PAGES = {
    "candle_diary": {
        "pages": [
            {"quad": [[505, 306], [764, 269], [990, 401], [668, 489]], "area": [0.10, 0.92, 0.10, 0.90], "lines": 7, "seed": 0},
            {"quad": [[118, 384], [497, 303], [662, 492], [233, 558]], "area": [0.42, 0.94, 0.22, 0.92], "lines": 8, "seed": 1},
        ],
        "erase": 21, "ink": [30, 18, 10], "strength": 1.0,
        # 지우면 안 되는 것(첫 프레임 다각형, 가장 가까운 종이의 움직임을 따라감): 펜, 촛대 접시
        "keep": [[[278, 462], [710, 333], [722, 352], [292, 486]], [[165, 120], [405, 120], [405, 420], [165, 420]]],
    },
}


def text_plane(n_lines, seed, Wp=1600, Hp=1000, area=(0.1, 0.9, 0.1, 0.9)):
    """종이 평면(가로 Wp, 세로 Hp)에 글씨 줄을 채운 알파 이미지"""
    u0, u1, v0, v1 = area; x0, x1, y0, y1 = int(u0 * Wp), int(u1 * Wp), int(v0 * Hp), int(v1 * Hp)
    gap = (y1 - y0) / n_lines; f = ImageFont.truetype(FONT, int(gap * 0.7))
    im = Image.new("L", (Wp, Hp), 0); d = ImageDraw.Draw(im)
    words = TXT.split(); k = (seed * 37) % len(words); words = words[k:] + words[:k]
    y = y0 + gap * 0.8; wi = 0
    for li in range(n_lines):
        line = ""; lim = (x1 - x0) * (0.55 if li == n_lines - 1 else 1.0)
        while d.textlength((line + " " + words[wi % len(words)]).strip(), font=f) < lim: line = (line + " " + words[wi % len(words)]).strip(); wi += 1
        d.text((x0, y), line, font=f, fill=255, anchor="ls"); y += gap
    return np.array(im).astype(np.float32) / 255.0


def track(gray, quad):
    """종이 위 특징점으로 프레임마다 첫 프레임 → 현재 프레임 호모그래피"""
    h, w = gray[0].shape; m = np.zeros((h, w), np.uint8); cv2.fillPoly(m, [np.int32(quad)], 255)
    m = cv2.erode(m, np.ones((9, 9), np.uint8))
    acc = np.eye(3); Hs = [acc.copy()]; prev = gray[0]; pts = cv2.goodFeaturesToTrack(prev, 400, 0.005, 6, mask=m)
    for i in range(1, len(gray)):
        if pts is not None and len(pts) >= 8:
            nxt, st, _ = cv2.calcOpticalFlowPyrLK(prev, gray[i], pts, None, winSize=(25, 25), maxLevel=3)
            g0, g1 = pts[st == 1], nxt[st == 1]
            Hm = cv2.findHomography(g0, g1, cv2.RANSAC, 2.5)[0] if len(g0) >= 8 else None
            if Hm is not None: acc = Hm @ acc
            pts = g1.reshape(-1, 1, 2) if len(g1) >= 150 else cv2.goodFeaturesToTrack(gray[i], 400, 0.005, 6, mask=cv2.warpPerspective(m, acc, (w, h)))
        Hs.append(acc.copy()); prev = gray[i]
    # 흔들림 줄이기: 호모그래피 원소를 앞뒤 프레임과 평균
    A = np.array(Hs); A = A / A[:, 2:3, 2:3]; k = 4
    return [A[max(0, i - k):i + k + 1].mean(0) for i in range(len(A))]


def run(name, test=False):
    cfg = PAGES[name]; src = os.path.join(ROOT, "social/side/gen", f"libv_{name}.mp4")
    cap = cv2.VideoCapture(src); fps = cap.get(cv2.CAP_PROP_FPS) or 24; fr = []
    while True:
        ok, f = cap.read()
        if not ok: break
        fr.append(f)
    h, w = fr[0].shape[:2]; gray = [cv2.cvtColor(f, cv2.COLOR_BGR2GRAY) for f in fr]
    ink = np.array(cfg["ink"][::-1], np.float32)
    out = [f.astype(np.float32) for f in fr]
    for pg in cfg["pages"]:
        quad = np.float32(pg["quad"]); Hs = track(gray, quad)
        Wp, Hp = 1600, 1000
        plane = text_plane(pg["lines"], pg["seed"], Wp, Hp, pg["area"])
        Hq = cv2.getPerspectiveTransform(np.float32([[0, 0], [Wp, 0], [Wp, Hp], [0, Hp]]), quad)
        for i, f in enumerate(fr):
            Hi = Hs[i] @ Hq
            km = np.zeros((h, w), np.uint8)
            for poly in cfg.get("keep", []): cv2.fillPoly(km, [np.int32(cv2.perspectiveTransform(np.float32([poly]), Hs[i])[0])], 1)
            km = cv2.GaussianBlur(cv2.dilate(km, np.ones((9, 9), np.uint8)).astype(np.float32), (0, 0), 3)
            pm = cv2.warpPerspective(np.ones((Hp, Wp), np.float32), Hi, (w, h))
            pm = cv2.erode(pm, np.ones((5, 5), np.uint8))
            # ① 얼룩 지우기: 종이 안에서 주변(닫힘 연산)보다 확 어두운 작은 덩어리 → 종이 색으로
            g = gray[i].astype(np.float32); k = cfg["erase"]
            bg = cv2.morphologyEx(f, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))).astype(np.float32)
            bgg = cv2.cvtColor(bg.astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
            dk = np.clip((bgg - g - 10) / 22, 0, 1)
            big = cv2.morphologyEx((bgg - g > 45).astype(np.uint8), cv2.MORPH_OPEN, np.ones((k, k), np.uint8))   # 펜처럼 큰 물체는 남김
            dk = dk * (1 - cv2.dilate(big, np.ones((7, 7), np.uint8)))
            dk = cv2.GaussianBlur(cv2.dilate(dk, np.ones((3, 3), np.uint8)), (0, 0), 1.5) * pm * (1 - km)
            bg = cv2.GaussianBlur(bg, (0, 0), 1.5)
            base = out[i] * (1 - dk[..., None]) + bg * dk[..., None]
            # ② 글씨: 원근 맞춰 얹고, 펜·그림자 같은 어두운 곳은 빼기
            a = cv2.warpPerspective(plane, Hi, (w, h)); a = cv2.GaussianBlur(a, (0, 0), 0.7)
            lum = cv2.cvtColor(np.clip(base, 0, 255).astype(np.uint8), cv2.COLOR_BGR2GRAY).astype(np.float32)
            lv = np.percentile(lum[pm > 0.5], 70) if (pm > 0.5).any() else 150
            vis = np.clip((lum - lv * 0.32) / (lv * 0.2), 0, 1); vis = cv2.erode(vis, np.ones((5, 5), np.uint8))
            al = (a * vis * pm * (1 - km) * cfg["strength"])[..., None]
            out[i] = base * (1 - al) + (base * 0.18 + ink * 0.82) * al
    if test:
        D = "/tmp/claude-0/-home-claude/f2ab3a6f-63d3-5eff-9968-28e72facdd87/scratchpad/pg"
        for j, f in [(0, out[0]), (1, out[len(out) // 2]), (2, out[-1])]: cv2.imwrite(f"{D}/{name}_t{j}.jpg", np.clip(f, 0, 255).astype(np.uint8))
        return
    dst = os.path.join(ROOT, "social/side/gen", f"libv_{name}_ink.mp4")
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgr24", "-s", f"{w}x{h}", "-r", str(fps), "-i", "-",
                            "-c:v", "libx264", "-preset", "slow", "-crf", "14", "-pix_fmt", "yuv420p", dst], stdin=subprocess.PIPE)
    for f in out: enc.stdin.write(np.clip(f, 0, 255).astype(np.uint8).tobytes())
    enc.stdin.close(); enc.wait(); print(dst)


if __name__ == "__main__":
    run(sys.argv[1], "--test" in sys.argv)
