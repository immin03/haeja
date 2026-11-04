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

def A():
    im=shade(look(place("e2_eyes.jpeg",1.3,.36,.38),1.75),"left",k=.95,start=.08)
    return lines(im,62,140,[("무례한 사람에게",BLK(116),WHITE,148,-5),("흔들리지 마라",BLK(132),YEL,196,-5),("2천 년 전 황제가 매일 아침 한 말",SB(36),MUTE,0,-1)])
def B():
    im=shade(look(place("e2m_holiday.jpeg",1.15,.42,.42),1.7),"right")
    R=W-60
    return lines(im,R,128,[("똑같이",BLK(168),WHITE,196,-6),("갚지 마라",BLK(168),YEL,232,-6),("무례한 사람을 이기는 단 하나의 방법",SB(36),MUTE,0,-1)],"r")
def C():
    im=shade(look(place("e2m_friend.jpeg",1.25,.52,.34),1.75),"right")
    R=W-60
    return lines(im,R,128,[("그 사람 말에",BLK(124),WHITE,156,-5),("상처받지 마라",BLK(124),YEL,196,-5),("상처는 말이 아니라 내 해석에서 온다",SB(36),MUTE,0,-1)],"r")
from PIL import Image
for k,fn in [("A_emperor",A),("B_repay",B),("C_words",C)]:
    fn().save(f"/home/claude/thumbs/ep02_{k}.jpg",quality=93)
ims=[Image.open(f"/home/claude/thumbs/ep02_{k}.jpg").resize((640,360)) for k in ("A_emperor","B_repay","C_words")]
c=Image.new("RGB",(640,1100),"white")
for i,im in enumerate(ims): c.paste(im,(0,i*370))
c.save("/tmp/claude-0/-home-claude/f2ab3a6f-63d3-5eff-9968-28e72facdd87/scratchpad/th2.jpg")
