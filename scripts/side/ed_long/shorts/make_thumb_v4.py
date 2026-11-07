# 롱폼 썸네일 v4 (2026-11-07) — 문구: 대상(작게) → 결과 + N가지 방법(크게) / 큰 주화 시네마틱
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from make_thumb_solution import place, look, shade, logo_coin, put, BLK, SB, WHITE, YEL, MUTE, W, H
from PIL import Image, ImageDraw, ImageFilter
import numpy as np
OUT=sys.argv[1] if len(sys.argv)>1 else "/home/claude/thumbs/"
GOLD=(214,170,92)

EP={
 1:dict(bg=("lp04_eyes.jpeg",1.18,.40,.42,1.6),side="left",
        kick="혼자가 두려운 사람에게", l1="혼자서도 잘 사는", l2="7가지 방법"),
 2:dict(bg=("e2m_holiday.jpeg",1.15,.42,.42,1.7),side="right",
        kick="사람 때문에 지친 당신에게", l1="무례한 사람을 이기는", l2="7가지 방법"),
 3:dict(bg=("e3m_kitchen.jpeg",1.2,.30,.38,1.7),side="left",
        kick="아무도 알아주지 않을 때", l1="인정 없이도 성공하는", l2="7가지 습관"),
}
def fit(d,t,maxw,start,font=BLK):
    s=start
    while d.textlength(t,font=font(s))+len(t)*-4>maxw and s>40: s-=2
    return s
def text_block(im,e,y0=250,maxw=700):
    d=ImageDraw.Draw(im); left=e["side"]=="left"
    s1=fit(d,e["l1"],maxw,104); s2=fit(d,e["l2"],maxw,188)
    rows=[(e["kick"],SB(42),MUTE,62,-1),(e["l1"],BLK(s1),WHITE,s1+22,-4),(e["l2"],BLK(s2),YEL,0,-6)]
    # 그림자
    sh=Image.new("L",(W,H),0); sd=ImageDraw.Draw(sh); out=[]; y=y0
    for t,f,c,dy,tr in rows:
        w=sum(d.textlength(ch,font=f)+tr for ch in t)-tr; x=62 if left else W-58-w
        for ch in t:
            out.append((x,y,ch,f,c)); sd.text((x+3,y+6),ch,font=f,fill=255); x+=d.textlength(ch,font=f)+tr
        y+=dy
    sh=sh.filter(ImageFilter.GaussianBlur(12)); im.paste((0,0,0),(0,0),sh); d=ImageDraw.Draw(im)
    for x,y,ch,f,c in out: d.text((x,y),ch,font=f,fill=c)
    # 대상 문구 위 금색 짧은 선
    xk=62 if left else W-58-120; d.rectangle((xk,y0-22,xk+120,y0-17),fill=GOLD)
    return im
def base(e,k=.97):
    n,z,cx,cy,b=e["bg"]; return shade(look(place(n,z,cx,cy),b),e["side"],k=k,start=.06)

def C(e):
    # 큰 주화: 글자 쪽 위 모서리에 걸쳐 잘리게, 글자 블록보다 위에서 빛남
    im=base(e); S=400; coin=logo_coin(S)
    x=-95 if e["side"]=="left" else W-S+95; y=-110
    im=put(im,coin,x,y,glow=120)
    # 주화 아래쪽을 어둡게 녹여 글자와 분리
    a=np.zeros((H,W),np.float32); yy=np.linspace(0,1,H)[:,None]
    a[:]=np.clip((yy-.30)/.22,0,1)*.0
    return text_block(im,e,y0=300)
def D(e):
    # 금테 프레임 + 위 가운데 주화 휘장
    im=base(e); d=ImageDraw.Draw(im); m=20
    d.rectangle((m,m,W-m,H-m),outline=GOLD,width=3); d.rectangle((m+9,m+9,W-m-9,H-m-9),outline=(120,92,44),width=1)
    S=130; coin=logo_coin(S); cx=62 if e["side"]=="left" else W-58-S
    d.rectangle((cx-10,m-4,cx+S+10,m+12),fill=(0,0,0))
    im=put(im,coin,cx,m-14)
    return text_block(im,e,y0=262)

if __name__=="__main__":
    os.makedirs(OUT,exist_ok=True)
    for k,e in EP.items():
        C(e).save(f"{OUT}v4_ep0{k}_C.jpg",quality=93); D(e).save(f"{OUT}v4_ep0{k}_D.jpg",quality=93)
