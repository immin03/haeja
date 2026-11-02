"""일기 쓰는 장면(edv02_tablet)에 영어 필기체가 펜 끝을 따라 새겨지게 합성.
카메라 움직임은 판 표면 특징점 추적(호모그래피)으로, 펜 끝은 펜촉 템플릿 추적으로 따라간다.
python3 tablet_script.py in.mp4 out.mp4
"""
import sys, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

SRC, OUT = sys.argv[1], sys.argv[2]
W, H, FPS = 1080, 1920, 30
FONT = "/root/fonts/PinyonScript-Regular.ttf"
# 프레임0 기준 판(밀랍면) 네 꼭짓점: 좌상, 우상, 우하, 좌하
QUAD = np.float32([[150, 975], [750, 860], [980, 1380], [380, 1495]])
TIP0 = (495, 1272)  # 프레임0 펜 끝
LINES = sys.argv[3].split("|") if len(sys.argv) > 3 else ["Begin the morning", "by saying to thyself:", "I shall meet with"]  # 기본: 명상록 2권 1절 (Long 번역)

def read_all(path):
    p = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True)
    a = np.frombuffer(p.stdout, np.uint8); return list(a.reshape(-1, H, W, 3))

frames = read_all(SRC); n = len(frames)
gray = [cv2.cvtColor(f, cv2.COLOR_RGB2GRAY) for f in frames]

# 1) 카메라 추적: 판 위 특징점 (손 쪽 우상단은 제외)
m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [QUAD.astype(np.int32)], 255)
cv2.rectangle(m, (TIP0[0] - 30, 0), (W, TIP0[1] + 40), 0, -1)
Hs = [np.eye(3)]; prev = gray[0]; pts = cv2.goodFeaturesToTrack(prev, 400, 0.01, 8, mask=m); acc = np.eye(3)
for i in range(1, n):
    nxt, st, _ = cv2.calcOpticalFlowPyrLK(prev, gray[i], pts, None, winSize=(21, 21), maxLevel=3)
    good0, good1 = pts[st == 1], nxt[st == 1]
    Hm, _ = cv2.findHomography(good0, good1, cv2.RANSAC, 3.0)
    acc = Hm @ acc; Hs.append(acc.copy())
    prev = gray[i]
    if len(good1) < 150:  # 다시 뽑기
        mi = cv2.warpPerspective(m, acc, (W, H)); pts = cv2.goodFeaturesToTrack(prev, 400, 0.01, 8, mask=mi)
    else:
        pts = good1.reshape(-1, 1, 2)

# 2) 펜 끝 추적 (펜촉 템플릿 매칭)
tx, ty = TIP0; tpl = gray[0][ty - 70:ty + 6, tx - 10:tx + 70]
tips = [TIP0]
for i in range(1, n):
    px, py = tips[-1]; x0, y0 = px - 70, py - 140
    roi = gray[i][y0:y0 + 220, x0:x0 + 220]
    r = cv2.matchTemplate(roi, tpl, cv2.TM_CCOEFF_NORMED); _, _, _, loc = cv2.minMaxLoc(r)
    tips.append((x0 + loc[0] + 10, y0 + loc[1] + 70))
tips = np.array(tips, float)
# 펜 몸통 한 점도 추적해 펜 축 방향을 구함
P2 = (572, 1100); tpl2 = gray[0][P2[1] - 30:P2[1] + 30, P2[0] - 30:P2[0] + 30]; p2s = [P2]
for i in range(1, n):
    px, py = p2s[-1]; x0, y0 = px - 90, py - 90
    r = cv2.matchTemplate(gray[i][y0:y0 + 180, x0:x0 + 180], tpl2, cv2.TM_CCOEFF_NORMED); _, _, _, loc = cv2.minMaxLoc(r)
    p2s.append((x0 + loc[0] + 30, y0 + loc[1] + 30))
p2s = np.array(p2s, float)
k = 9; tips = np.array([tips[max(0, i - k):i + k + 1].mean(0) for i in range(n)])  # 떨림 제거
p2s = np.array([p2s[max(0, i - k):i + k + 1].mean(0) for i in range(n)])

def occl(i):
    """펜·손 가림 마스크 (1=가려짐)"""
    fr = frames[i].astype(np.int16); R, G, B = fr[..., 0], fr[..., 1], fr[..., 2]
    tx, ty = tips[i]; ax = p2s[i] - tips[i]; ax = ax / np.linalg.norm(ax)
    band = np.zeros((H, W), np.uint8)
    far = tips[i] + ax * 1400; nrm = np.array([-ax[1], ax[0]])
    poly = np.array([tips[i] + nrm * 6, far + nrm * 70, far - nrm * 70, tips[i] - nrm * 6], np.int32)
    cv2.fillPoly(band, [poly], 1)
    skin = ((R > 95) & (R - B > 35) & (G > 55)).astype(np.uint8)
    reg = np.zeros((H, W), np.uint8); reg[: int(ty) + 10, int(tx) - 40:] = 1
    mk = np.maximum(band, skin * reg)
    mk = cv2.morphologyEx(mk, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    mk = cv2.dilate(mk, np.ones((5, 5), np.uint8))
    return cv2.GaussianBlur(mk.astype(np.float32), (0, 0), 1.5)

# 3) 판 좌표계(캔버스 1200x900)에 필기체 렌더
CW, CH = 1200, 900
Hc = cv2.getPerspectiveTransform(np.float32([[0, 0], [CW, 0], [CW, CH], [0, CH]]), QUAD)
def to_canvas(Hf, pt):
    q = np.linalg.inv(Hf @ Hc) @ np.array([pt[0], pt[1], 1.0]); return q[:2] / q[2]
tipc = np.array([to_canvas(Hs[i], tips[i]) for i in range(n)])
f = ImageFont.truetype(FONT, 100)
probe = ImageDraw.Draw(Image.new("L", (10, 10)))
lw = [probe.textlength(s, font=f) for s in LINES]
endx = tipc[-1][0] - 4  # 마지막 줄은 마지막 프레임 펜 끝에서 끝남
base = tipc[-1][1] - 6
lh = 128; left = max(70, endx - lw[2])
def canvas_img(reveal_x):
    """글자 이미지(밝은 획) + 그림자. reveal_x: 마지막 줄을 x까지만 보이게"""
    L = Image.new("L", (CW, CH), 0); d = ImageDraw.Draw(L)
    for j, s in enumerate(LINES):
        y = base - (2 - j) * lh
        d.text((left, y), s, font=f, fill=255, anchor="ls")
    a = np.asarray(L).astype(np.float32) / 255
    y2 = int(base + 40); y1 = int(base - lh * 0.75)
    a[y1:y2, int(reveal_x):] = 0
    return a
# 4) 합성: 밀랍에 새긴 듯 — 밝은 금빛 획 + 아래쪽 어두운 그림자
INK = np.array([228, 196, 140], np.float32); SHD = np.array([10, 7, 4], np.float32)
start_x = tipc[0][0] - 4
out = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                        "-c:v", "libx264", "-crf", "16", "-preset", "veryfast", "-pix_fmt", "yuv420p", OUT], stdin=subprocess.PIPE)
for i in range(n):
    rx = max(start_x, tipc[i][0] - 4)
    rx = left + (rx - left)  # 펜 끝까지 새겨짐
    a = canvas_img(rx)
    # 앞 줄들은 처음부터 있고, 시작 시점에 이미 펜 끝까지 쓴 상태
    M = Hs[i] @ Hc
    am = cv2.warpPerspective(a, M, (W, H), flags=cv2.INTER_LINEAR)
    am = cv2.GaussianBlur(am, (0, 0), 0.8) * (1 - occl(i))
    sh = np.roll(am, 3, axis=0); sh = np.roll(sh, 1, axis=1)
    fr = frames[i].astype(np.float32)
    fr = fr * (1 - 0.55 * sh[..., None]) + SHD * 0.55 * sh[..., None]
    fr = fr * (1 - 0.85 * am[..., None]) + INK * 0.85 * am[..., None]
    out.stdin.write(np.clip(fr, 0, 255).astype(np.uint8).tobytes())
out.stdin.close(); out.wait()
print("frames", n, "tip start/end canvas", tipc[0].round(1), tipc[-1].round(1), "left", round(left, 1))
