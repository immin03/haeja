# 사례(STOP FEARING BEING ALONE) 방식: 짧은 명령형 한 문장, 흰색+노랑 두 톤, 아주 굵게, 강한 인물 한 명
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
G="/home/claude/haeja/social/side/gen/"; F="/root/fonts/"; W,H=1280,720
def place(n,zoom,cx,cy):
    im=Image.open(G+n).convert("RGB"); s=max(W/im.width,H/im.height)*zoom; im=im.resize((int(im.width*s),int(im.height*s)),Image.LANCZOS)
    x=max(0,min(int(im.width*cx-W/2),im.width-W)); y=max(0,min(int(im.height*cy-H/2),im.height-H)); return im.crop((x,y,x+W,y+H))
def look(im,b=1.5,c=1.25,sat=.7):
    return ImageEnhance.Color(ImageEnhance.Brightness(ImageEnhance.Contrast(im).enhance(c)).enhance(b)).enhance(sat)
def shade(im,side,k=.96,start=.0):
    xs=np.linspace(0,1,W); g=(1-xs) if side=="left" else xs
    a=np.tile(np.clip((g-start)*1.9-0.2,0,1)**0.9*k,(H,1)); a=np.maximum(a,np.linspace(0,1,H)[:,None]**3*.5)
    return Image.fromarray((np.array(im).astype(np.float32)*(1-a[...,None])).clip(0,255).astype(np.uint8))
BLK=lambda s: ImageFont.truetype(F+"Pretendard-ExtraBold.otf",s); SB=lambda s: ImageFont.truetype(F+"Pretendard-SemiBold.otf",s)
WHITE=(255,255,255); YEL=(255,206,48); MUTE=(200,192,180)
def lines(im,x,y,rows,anchor="l"):
    d=ImageDraw.Draw(im); sh=Image.new("L",(W,H),0); sd=ImageDraw.Draw(sh); out=[]
    for (t,f,c,dy,tr) in rows:
        w=sum(d.textlength(ch,font=f)+tr for ch in t)-tr; xx=x-w if anchor=="r" else x
        for ch in t:
            out.append((xx,y,ch,f,c)); sd.text((xx+3,y+6),ch,font=f,fill=255); xx+=d.textlength(ch,font=f)+tr
        y+=dy
    sh=sh.filter(ImageFilter.GaussianBlur(10)); im.paste((0,0,0),(0,0),sh); d=ImageDraw.Draw(im)
    for xx,yy,ch,f,c in out: d.text((xx,yy),ch,font=f,fill=c)
    return im


# v2 (11/5): 제목 중복 제거(A), 부제는 재생시간 배지(오른쪽 아래) 구역 밖으로·크게, 글자 덩어리를 위로
OUT="/mnt/user-data/outputs/"
def A():
    im=shade(look(place("e2_eyes.jpeg",1.3,.36,.38),1.75),"left",k=.95,start=.08)
    return lines(im,62,118,[("황제는",BLK(132),WHITE,160,-5),("화내지 않았다",BLK(132),YEL,200,-5),("무례한 사람 앞에서 그가 한 일",SB(46),MUTE,0,-1)])
def B():
    im=shade(look(place("e2m_holiday.jpeg",1.15,.42,.42),1.7),"right")
    R=W-60
    return lines(im,R,92,[("똑같이",BLK(168),WHITE,196,-6),("갚지 마라",BLK(168),YEL,224,-6),("무례한 사람을 이기는 단 하나의 방법",SB(44),MUTE,0,-1)],"r")
def C():
    im=shade(look(place("e2m_friend.jpeg",1.25,.52,.34),1.75),"right")
    R=W-60
    return lines(im,R,104,[("그 사람 말에",BLK(124),WHITE,156,-5),("상처받지 마라",BLK(124),YEL,192,-5),("상처는 말이 아니라 해석에서 온다",SB(44),MUTE,0,-1)],"r")
from PIL import Image, ImageDraw
names=[("A_emperor",A),("B_repay",B),("C_words",C)]
for k,fn in names: fn().save(OUT+f"ep02_v2_{k}.jpg",quality=93)
# QA: 배지 모의(오른쪽 아래) + 모바일 크기
qa=Image.new("RGB",(1300,3*380+10),"white")
for i,(k,_) in enumerate(names):
    im=Image.open(OUT+f"ep02_v2_{k}.jpg").copy(); d=ImageDraw.Draw(im)
    d.rounded_rectangle((1280-150,720-74,1280-16,720-16),12,fill=(0,0,0)); d.text((1280-138,720-70),"12:16",font=SB(40),fill=WHITE)
    qa.paste(im.resize((640,360)),(0,i*380)); qa.paste(im.resize((320,180)),(660,i*380)); qa.paste(im.resize((168,94)),(1000,i*380))
qa.save("/tmp/claude-0/-home-claude/b3bb3450-f4f4-5f54-9098-40ef46fd6495/scratchpad/qa.jpg",quality=90)
