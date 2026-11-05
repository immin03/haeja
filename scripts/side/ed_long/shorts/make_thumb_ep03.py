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
# EP3 「아무도 알아주지 않을 때」 (2026-11-05)
def A():
    im=shade(look(place("e3_watch.jpeg",1.12,.66,.30),1.6),"right",k=.95,start=.18)
    R=W-56
    return lines(im,R,140,[("아무도",BLK(140),WHITE,160,-5),("알아주지 않을 때",BLK(112),YEL,190,-5),("2천 년 전 황제가 궁전 보물을 판 이유",SB(36),MUTE,0,-1)],"r")
def B():
    im=shade(look(place("e3m_kitchen.jpeg",1.2,.34,.38),1.7),"left",k=.95,start=.08)
    return lines(im,60,128,[("고맙다는 말",BLK(132),WHITE,160,-5),("못 들어도",BLK(150),YEL,214,-6),("30년 차린 밥상이 가족을 살렸다",SB(36),MUTE,0,-1)])
def C():
    im=shade(look(place("e3m_promotion.jpeg",1.25,.3,.36),1.7),"right",k=.95,start=.05)
    R=W-56
    return lines(im,R,128,[("내 이름이",BLK(150),WHITE,172,-6),("빠져도 괜찮다",BLK(128),YEL,206,-5),("일을 해낸 사람은, 나다",SB(36),MUTE,0,-1)],"r")
for k,fn in [("A_emperor",A),("B_kitchen",B),("C_name",C)]:
    fn().save(f"/home/claude/thumbs/ep03_{k}.jpg",quality=93)
ims=[Image.open(f"/home/claude/thumbs/ep03_{k}.jpg").resize((640,360)) for k in ("A_emperor","B_kitchen","C_name")]
c=Image.new("RGB",(640,1100),"white")
for i,im in enumerate(ims): c.paste(im,(0,i*370))
c.save("/tmp/claude-0/-home-claude/f2ab3a6f-63d3-5eff-9968-28e72facdd87/scratchpad/th3.jpg")
