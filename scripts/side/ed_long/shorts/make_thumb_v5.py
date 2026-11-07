# 롱폼 썸네일 v5 (2026-11-07) — 대표 선택: v3 C(배경에 녹은 큰 주화) + v4 결과형 문구 + 『명상록』 표기
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from make_thumb_solution import place, look, shade, logo_coin, put, BLK, SB, WHITE, YEL, MUTE, W, H
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import numpy as np
OUT=sys.argv[1] if len(sys.argv)>1 else "/home/claude/thumbs/"
GOLD=(226,184,104); F="/root/fonts/"
BOLD=lambda s: ImageFont.truetype(F+"Pretendard-ExtraBold.otf",s)

EP={
 1:dict(bg=("lp04_eyes.jpeg",1.18,.36,.42,1.6),side="left",  l1="혼자서도 잘 사는",     l2="7가지 방법"),
 2:dict(bg=("e2m_holiday.jpeg",1.15,.42,.42,1.7),side="right",l1="무례한 사람을 이기는", l2="7가지 방법"),
 3:dict(bg=("e3m_kitchen.jpeg",1.2,.34,.38,1.7),side="left",  l1="인정 없이도 성공하는", l2="7가지 습관"),
}
def fit(d,t,maxw,start):
    s=start
    while d.textlength(t,font=BLK(s))+len(t)*-4>maxw and s>40: s-=2
    return s
def bg(e):
    n,z,cx,cy,b=e["bg"]; im=shade(look(place(n,z,cx,cy),b),e["side"],k=.95,start=.08)
    big=logo_coin(560); big.putalpha(Image.fromarray((np.array(big.split()[3])*.32).astype(np.uint8)))
    x=-120 if e["side"]=="left" else W-440
    return put(im,big,x,80,glow=70)
def draw_rows(im,e,rows,y0):
    d=ImageDraw.Draw(im); left=e["side"]=="left"
    sh=Image.new("L",(W,H),0); sd=ImageDraw.Draw(sh); out=[]; y=y0
    for t,f,c,dy,tr in rows:
        w=sum(d.textlength(ch,font=f)+tr for ch in t)-tr; x=62 if left else W-58-w
        for ch in t:
            out.append((x,y,ch,f,c)); sd.text((x+3,y+6),ch,font=f,fill=255); x+=d.textlength(ch,font=f)+tr
        y+=dy
    sh=sh.filter(ImageFilter.GaussianBlur(12)); im.paste((0,0,0),(0,0),sh); d=ImageDraw.Draw(im)
    for x,y,ch,f,c in out: d.text((x,y),ch,font=f,fill=c)
    return im
def X(e):
    # 『명상록』을 금색 제목처럼 위에 크게
    d=ImageDraw.Draw(Image.new("RGB",(10,10))); s1=fit(d,e["l1"],700,104); s2=fit(d,e["l2"],700,180)
    rows=[("『명상록』",BOLD(66),GOLD,92,-2),(e["l1"],BLK(s1),WHITE,s1+20,-4),(e["l2"],BLK(s2),YEL,0,-6)]
    return draw_rows(bg(e),e,rows,170)
def Y(e):
    # 문구 먼저, 아래에 '마르쿠스 아우렐리우스 『명상록』' 서명처럼
    d=ImageDraw.Draw(Image.new("RGB",(10,10))); s1=fit(d,e["l1"],700,104); s2=fit(d,e["l2"],700,180)
    rows=[(e["l1"],BLK(s1),WHITE,s1+20,-4),(e["l2"],BLK(s2),YEL,s2+26,-6),("마르쿠스 아우렐리우스 『명상록』",BOLD(44),GOLD,0,-1)]
    return draw_rows(bg(e),e,rows,150)

if __name__=="__main__":
    os.makedirs(OUT,exist_ok=True)
    for k,e in EP.items():
        X(e).save(f"{OUT}v5_ep0{k}_X.jpg",quality=93); Y(e).save(f"{OUT}v5_ep0{k}_Y.jpg",quality=93)
    from PIL import ImageFont as IF
    T=IF.truetype(F+"Pretendard-ExtraBold.otf",30); S=IF.truetype(F+"Pretendard-SemiBold.otf",22)
    cols=[("X","X · 『명상록』 위에 크게 (추천)"),("Y","Y · 『명상록』 아래 서명처럼")]
    eps=[(1,"1편 혼자인 걸 두려워하지 마라"),(2,"2편 무례한 사람에게 흔들리지 마라"),(3,"3편 아무도 알아주지 않을 때")]
    cw,ch=800,450; c=Image.new("RGB",(40+2*(cw+20),90+3*(ch+70)+250),"white"); dd=ImageDraw.Draw(c)
    for i,(v,l) in enumerate(cols): dd.text((20+i*(cw+20),30),l,font=T,fill=(176,120,20) if v=="X" else (20,20,20))
    for r,(k,l) in enumerate(eps):
        y=90+r*(ch+70); dd.text((20,y),l,font=S,fill=(90,90,90))
        for i,(v,_) in enumerate(cols): c.paste(Image.open(f"{OUT}v5_ep0{k}_{v}.jpg").resize((cw,ch),Image.LANCZOS),(20+i*(cw+20),y+32))
    y=90+3*(ch+70); dd.text((20,y),"휴대폰 피드 실제 크기(약 320px)",font=S,fill=(90,90,90)); x=20
    for k in (1,2,3):
        for v in ("X","Y"):
            c.paste(Image.open(f"{OUT}v5_ep0{k}_{v}.jpg").resize((260,146),Image.LANCZOS),(x,y+40)); x+=275
    c.save(f"{OUT}longform_thumb_v5.jpg",quality=88)
