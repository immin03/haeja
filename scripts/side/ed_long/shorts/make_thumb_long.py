from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import cv2, numpy as np
G="/home/claude/haeja/social/side/gen/"; F="/root/fonts/"; W,H=1280,720
def src(n): return Image.open(G+n).convert("RGB")
def place(im,zoom,cx,cy):
    s=max(W/im.width,H/im.height)*zoom; im=im.resize((int(im.width*s),int(im.height*s)),Image.LANCZOS)
    x=max(0,min(int(im.width*cx-W/2),im.width-W)); y=max(0,min(int(im.height*cy-H/2),im.height-H)); return im.crop((x,y,x+W,y+H))
def shade(im,side,k=.9,start=.15):
    xs=np.linspace(0,1,W); g=(1-xs) if side=="left" else xs
    a=np.clip((g-start)/(1-start)*1.6,0,1)**1.1*k; a=np.tile(a,(H,1))
    a=np.maximum(a,(np.linspace(0,1,H)[:,None]**2.5*.55))
    return Image.fromarray((np.array(im).astype(np.float32)*(1-a[...,None])).clip(0,255).astype(np.uint8))
def grade(im,b=1.5,c=1.12,sat=.85):
    im=ImageEnhance.Contrast(im).enhance(c); im=ImageEnhance.Brightness(im).enhance(b); return ImageEnhance.Color(im).enhance(sat)
SER=lambda s: ImageFont.truetype(F+"hahmlet-korean-700-normal.ttf",s)
SANS=lambda s,w="ExtraBold": ImageFont.truetype(F+f"Pretendard-{w}.otf",s)
EN=lambda s: ImageFont.truetype(F+"cormorant-sc-latin-600-normal.ttf",s)
WHITE=(250,246,238); GOLD=(226,184,104); MUTE=(205,196,182)
class T:
    def __init__(s,im): s.im=im; s.sh=Image.new("L",(W,H),0); s.txt=[]
    def line(s,x,y,segs,font,anchor="l",track=-2):
        d=ImageDraw.Draw(Image.new("L",(1,1)))
        ws=[sum(d.textlength(ch,font=font)+track for ch in t) for t,_ in segs]; tot=sum(ws)
        if anchor=="r": x-=tot
        for (t,c) in segs:
            for ch in t:
                s.txt.append((x,y,ch,font,c)); x+=d.textlength(ch,font=font)+track
    def rule(s,x,y,w,anchor="l"): s.txt.append(("rule",x if anchor=="l" else x-w,y,w))
    def done(s):
        sd=ImageDraw.Draw(s.sh)
        for t in s.txt:
            if t[0]=="rule": continue
            x,y,ch,f,c=t; sd.text((x+2,y+5),ch,font=f,fill=235)
        sh=s.sh.filter(ImageFilter.GaussianBlur(9)); black=Image.new("RGB",(W,H),(0,0,0))
        im=Image.composite(black,s.im,sh); d=ImageDraw.Draw(im)
        for t in s.txt:
            if t[0]=="rule": _,x,y,w=t; d.rectangle((x,y,x+w,y+3),fill=GOLD); continue
            x,y,ch,f,c=t; d.text((x,y),ch,font=f,fill=c)
        return im

def emperor():   # 1) 황제 버전
    im=shade(grade(place(src("lp04_eyes.jpeg"),1.15,.38,.42),1.55),"left",.93); t=T(im)
    t.line(64,92,[("THE EMPEROR'S DIARY",GOLD)],EN(30),track=3)
    t.rule(66,140,64)
    t.line(60,176,[("가장 믿던 장군이",WHITE)],SER(84))
    t.line(60,284,[("나를 ",WHITE),("죽었다고",GOLD)],SER(108))
    t.line(60,412,[("선언한 밤",WHITE)],SER(108))
    t.line(64,566,[("로마 황제가 일기에 남긴 일곱 문장",MUTE)],SANS(34,"SemiBold"),track=-1)
    return t.done()
def cut50():     # 2) 50대 표적 — 끊어야 할 사람
    im=shade(grade(place(src("e3b_sofa.jpeg"),1.12,.5,.45),1.7),"right",.92,.1); t=T(im)
    R=W-64
    t.line(R,92,[("50대 이후 인간관계",GOLD)],SANS(36,"Bold"),"r",-1)
    t.rule(R,146,64,"r")
    t.line(R,180,[("이런 사람은",WHITE)],SANS(96),"r",-4)
    t.line(R,298,[("조용히 ",WHITE),("끊어라",GOLD)],SANS(118),"r",-5)
    t.line(R,470,[("만나고 오면 더 지치는 사람",MUTE)],SANS(40,"SemiBold"),"r",-1)
    t.line(R,526,[("2천 년 전 황제의 답",MUTE)],SANS(40,"SemiBold"),"r",-1)
    return t.done()
def betray():    # 3) 배신 — 화내지 마라
    im=shade(grade(place(src("e6c_car.jpeg"),1.1,.62,.45),1.6),"left",.93,.05); t=T(im)
    t.line(64,92,[("나를 배신한 사람에게",GOLD)],SANS(38,"Bold"),track=-1)
    t.rule(66,148,64)
    t.line(58,180,[("“화내지",WHITE)],SANS(124),track=-5)
    t.line(58,318,[("마라”",WHITE)],SANS(124),track=-5)
    t.line(64,486,[("그 화가 ",MUTE),("나를 먼저",GOLD),(" 무너뜨린다",MUTE)],SANS(42,"SemiBold"),track=-1)
    return t.done()
for k,fn in [("A_emperor",emperor),("B_50s",cut50),("C_betrayal",betray)]:
    fn().save(f"/home/claude/thumbs/ep01_thumb_{k}.jpg",quality=93)
ims=[Image.open(f"/home/claude/thumbs/ep01_thumb_{k}.jpg") for k in ("A_emperor","B_50s","C_betrayal")]
c=Image.new("RGB",(1280,2180),"white")
for i,im in enumerate(ims): c.paste(im,(0,i*730))
c.save("/tmp/claude-0/-home-claude/2f808af9-8d53-543d-a222-ade3a04962ab/scratchpad/th2.jpg")
