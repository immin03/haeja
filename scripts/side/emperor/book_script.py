"""촛불 일기장(libv_candle_diary)의 오른쪽 페이지에 필기체 글을 얹는다 — 카메라 움직임은 책 표면 특징점 추적(호모그래피)"""
import sys, subprocess, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
SRC, OUT = sys.argv[1], sys.argv[2]; W, H = 1280, 720
QUAD = np.float32([[492, 312], [760, 266], [988, 400], [676, 484]])      # 프레임0 오른쪽 페이지
LQUAD = np.float32([[255, 352], [490, 312], [676, 484], [262, 518]])   # 프레임0 왼쪽 페이지
CANDLE = np.int32([[165, 120], [330, 110], [405, 330], [405, 400], [165, 405]])
QUILL = np.int32([[280, 466], [713, 331], [720, 345], [290, 480]])       # 펜대(글 위로 다시 덮음)
raw = subprocess.run(["ffmpeg","-v","error","-i",SRC,"-f","rawvideo","-pix_fmt","rgb24","-"],capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3); n = len(fr)
gray = [cv2.cvtColor(f, cv2.COLOR_RGB2GRAY) for f in fr]
m = np.zeros((H, W), np.uint8); cv2.fillPoly(m, [np.int32([[300,330],[770,260],[1000,400],[1040,470],[650,520],[250,560]])], 255)
acc = np.eye(3); Hs = [acc.copy()]; pts = cv2.goodFeaturesToTrack(gray[0], 500, 0.01, 6, mask=m)
for i in range(1, n):
    nx, st, _ = cv2.calcOpticalFlowPyrLK(gray[i-1], gray[i], pts, None, winSize=(21, 21), maxLevel=3)
    g0, g1 = pts[st == 1], nx[st == 1]
    Hm, _ = cv2.findHomography(g0, g1, cv2.RANSAC, 2.5); acc = Hm @ acc; Hs.append(acc.copy())
    if len(g1) < 200: pts = cv2.goodFeaturesToTrack(gray[i], 500, 0.01, 6, mask=cv2.warpPerspective(m, acc, (W, H)))
    else: pts = g1.reshape(-1, 1, 2)
# 페이지 공간(900x600)에 필기체 줄
PW, PH = 900, 600; f = ImageFont.truetype("/root/fonts/PinyonScript-Regular.ttf", 62)
TXT = ["Quid me contemnit aliquis? Ipse viderit.", "Ego vero curabo ne quid contemptu", "dignum aut faciam aut dicam.", "Odit me aliquis? Ipse viderit.",
       "Ego autem mitis ero erga omnes", "et benignus, et paratus ipsi illi", "errorem ostendere, non cum convicio,", "sed candide et ingenue."]
pg = Image.new("L", (PW, PH), 0); d = ImageDraw.Draw(pg)
for k, ln in enumerate(TXT): d.text((60 + (k % 3) * 8, 30 + k * 70), ln, font=f, fill=255)
pg = np.array(pg)
TXL = ["Mane dic tibi ipsi: occurram", "homini curioso, ingrato, insolenti,", "doloso, invido, insociabili.", "Haec omnia illis accidunt", "propter ignorantiam boni et mali.", "Ego vero, qui naturam boni vidi,", "nec laedi ab ullo eorum possum."]
pl = Image.new("L", (PW, PH), 0); d = ImageDraw.Draw(pl)
for k, ln in enumerate(TXL): d.text((70 + (k % 2) * 10, 40 + k * 76), ln, font=f, fill=255)
pl = np.array(pl)
src = np.float32([[0, 0], [PW, 0], [PW, PH], [0, PH]])
P0 = cv2.getPerspectiveTransform(src, QUAD); PL0 = cv2.getPerspectiveTransform(src, LQUAD)
enc = subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-r","24","-i","-","-c:v","libx264","-preset","veryfast","-crf","14","-pix_fmt","yuv420p",OUT], stdin=subprocess.PIPE)
INK = np.array([38, 24, 12], np.float32)
for i in range(n):
    Hm = Hs[i] @ P0
    a = np.maximum(cv2.warpPerspective(pg, Hm, (W, H), flags=cv2.INTER_LINEAR), cv2.warpPerspective(pl, Hs[i] @ PL0, (W, H), flags=cv2.INTER_LINEAR)).astype(np.float32) / 255
    a = cv2.GaussianBlur(a, (0, 0), 0.8) * 0.82
    img = fr[i].astype(np.float32)
    # 페이지의 흐린 얼룩 글씨를 지우고(크게 흐린 바탕 + 원래 종이결) 새 글을 쓴다
    pm = np.zeros((H, W), np.uint8)
    for Q in (QUAD, LQUAD): cv2.fillPoly(pm, [cv2.perspectiveTransform(Q.reshape(-1, 1, 2), Hs[i]).astype(np.int32)], 255)
    pm = cv2.erode(pm, np.ones((9, 9), np.uint8)); pm = cv2.GaussianBlur(pm, (0, 0), 6).astype(np.float32)[..., None] / 255
    lo = cv2.GaussianBlur(img, (0, 0), 14); fine = img - cv2.GaussianBlur(img, (0, 0), 1.6)
    clean = lo * 1.04 + fine * 0.8
    base = img * (1 - pm) + clean * pm
    out = base * (1 - a[..., None]) + INK * a[..., None]
    qm = np.zeros((H, W), np.uint8); q = cv2.perspectiveTransform(QUILL.reshape(-1, 1, 2).astype(np.float32), Hs[i]).astype(np.int32); cv2.fillPoly(qm, [q], 255)
    cv2.fillPoly(qm, [cv2.perspectiveTransform(CANDLE.reshape(-1, 1, 2).astype(np.float32), Hs[i]).astype(np.int32)], 255)
    qm = cv2.GaussianBlur(qm, (0, 0), 1.2).astype(np.float32)[..., None] / 255
    out = out * (1 - qm) + img * qm
    enc.stdin.write(np.clip(out, 0, 255).astype(np.uint8).tobytes())
enc.stdin.close(); enc.wait(); print("ok", n)
