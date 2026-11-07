# 롱폼 썸네일 v3 — 해결책형(N가지) + 주화 브랜드 표시 (2026-11-07)
# 변형: cur=현재 / B=로고 주화 왼쪽 위 / A=숫자 주화 / C=시네마틱 큰 주화
import sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import numpy as np
G="/home/claude/haeja/social/side/gen/"; F="/root/fonts/"; W,H=1280,720
OUT=sys.argv[1] if len(sys.argv)>1 else "/home/claude/thumbs/"
def place(n,zoom,cx,cy):
    im=Image.open(G+n).convert("RGB"); s=max(W/im.width,H/im.height)*zoom; im=im.resize((int(im.width*s),int(im.height*s)),Image.LANCZOS)
    x=max(0,min(int(im.width*cx-W/2),im.width-W)); y=max(0,min(int(im.height*cy-H/2),im.height-H)); return im.crop((x,y,x+W,y+H))
def look(im,b=1.5,c=1.25,sat=.7):
    return ImageEnhance.Color(ImageEnhance.Brightness(ImageEnhance.Contrast(im).enhance(c)).enhance(b)).enhance(sat)
def shade(im,side,k=.96,start=.0):
    xs=np.linspace(0,1,W); g=(1-xs) if side=="left" else xs
    a=np.tile(np.clip((g-start)*1.9-0.2,0,1)**0.9*k,(H,1)); a=np.maximum(a,np.linspace(0,1,H)[:,None]**3*.5)
    return Image.fromarray((np.array(im).astype(np.float32)*(1-a[...,None])).clip(0,255).astype(np.uint8))
BLK=lambda s: ImageFont.truetype(F+"Pretendard-ExtraBold.otf",s); BLACK=lambda s: ImageFont.truetype(F+"Pretendard-Black.otf",s)
SB=lambda s: ImageFont.truetype(F+"Pretendard-SemiBold.otf",s)
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

# ── 주화 ──
GOLD_D=np.array([42,28,8]); GOLD_M=np.array([176,128,52]); GOLD_L=np.array([255,228,150])
def gold_map(L):
    t=(L/255.0)[...,None]
    lo=GOLD_D+(GOLD_M-GOLD_D)*np.clip(t*2,0,1); hi=GOLD_M+(GOLD_L-GOLD_M)*np.clip(t*2-1,0,1)
    return np.where(t<.5,lo,hi).clip(0,255).astype(np.uint8)
def logo_coin(size):
    src=Image.open(G+"lg3_coin_engraved.jpeg").convert("L").crop((96,74,926,925)).resize((size,size),Image.LANCZOS)
    L=np.array(ImageEnhance.Contrast(src).enhance(1.15)).astype(np.float32)
    # 바탕(검정)도 금속판처럼 살짝 띄움
    L=L*.82+38
    yy,xx=np.mgrid[0:size,0:size]; r=np.hypot(xx-size/2,yy-size/2)/(size/2)
    L=L*(1.08-.22*r)  # 가운데 밝고 가장자리 어둡게
    rgb=gold_map(L.clip(0,255))
    mask=Image.fromarray((np.clip((1.0-r)*size*.5,0,1)*255).astype(np.uint8))
    coin=Image.fromarray(rgb).convert("RGBA"); coin.putalpha(mask); return coin
def num_coin(size,n):
    yy,xx=np.mgrid[0:size,0:size]; r=np.hypot(xx-size/2,yy-size/2)/(size/2)
    # 비스듬한 빛
    lx=(xx/size-.3); ly=(yy/size-.25); L=200-90*np.hypot(lx,ly)
    L=np.where((r>.86)&(r<.93),L+45,L)            # 테두리 띠
    L=np.where(r>.93,L-30,L)
    rgb=gold_map(L.clip(0,255)); im=Image.fromarray(rgb).convert("RGBA")
    d=ImageDraw.Draw(im)
    for i in range(64):                                # 점 테두리
        a=i/64*2*np.pi; px=size/2+np.cos(a)*size*.79; py=size/2+np.sin(a)*size*.79; rr=size*.012
        d.ellipse((px-rr,py-rr,px+rr,py+rr),fill=(120,84,30,255))
    f=BLACK(int(size*.62)); bb=d.textbbox((0,0),n,font=f); tw,th=bb[2]-bb[0],bb[3]-bb[1]
    tx=(size-tw)/2-bb[0]; ty=(size-th)/2-bb[1]-size*.04
    d.text((tx+3,ty+4),n,font=f,fill=(255,236,170,255))  # 하이라이트(양각)
    d.text((tx,ty),n,font=f,fill=(70,46,12,255))
    f2=BLK(int(size*.13)); w2=d.textlength("가지",font=f2); d.text(((size-w2)/2,size*.70),"가지",font=f2,fill=(70,46,12,255))
    mask=Image.fromarray((np.clip((1.0-r)*size*.5,0,1)*255).astype(np.uint8)); im.putalpha(mask); return im
def put(im,coin,x,y,glow=0):
    im=im.convert("RGBA"); a=coin.split()[3]
    sh=Image.new("RGBA",im.size,(0,0,0,0)); sh.paste((0,0,0,200),(x+6,y+10),a); sh=sh.filter(ImageFilter.GaussianBlur(12))
    im=Image.alpha_composite(im,sh)
    if glow:
        gl=Image.new("RGBA",im.size,(0,0,0,0)); big=a.resize((int(coin.width*1.25),)*2)
        gl.paste((255,196,90,int(glow)),(x-int(coin.width*.125),y-int(coin.width*.125)),big); gl=gl.filter(ImageFilter.GaussianBlur(40))
        im=Image.alpha_composite(im,gl)
    im.alpha_composite(coin,(x,y)); return im.convert("RGB")

# ── 편별 설정 ──
EP={
 1:dict(bg=("lp04_eyes.jpeg",1.18,.36,.42,1.6),side="left",
        cur=[("혼자인 걸",150,WHITE,178),("두려워 마라",150,YEL,206),("2천 년 전 황제가 매일 밤 쓴 일기",36,MUTE,0)],
        new=[("혼자여도",148,WHITE,172),("흔들리지 않는 법",112,YEL,190),("2천 년 전 황제가 매일 밤 지킨 처방",38,MUTE,0)],
        num=[("혼자여도",148,WHITE,172),("흔들리지 않는",112,YEL,190),("2천 년 전 황제가 매일 밤 지킨 처방",38,MUTE,0)]),
 2:dict(bg=("e2m_holiday.jpeg",1.15,.42,.42,1.7),side="right",
        cur=[("똑같이",168,WHITE,196),("갚지 마라",168,YEL,224),("무례한 사람을 이기는 단 하나의 방법",44,MUTE,0)],
        new=[("무례한 사람",140,WHITE,168),("이기는 7가지",150,YEL,196),("똑같이 갚지 않고 이기는 황제의 방법",38,MUTE,0)],
        num=[("무례한 사람",140,WHITE,168),("이기는 법",160,YEL,206),("똑같이 갚지 않고 이기는 황제의 방법",38,MUTE,0)]),
 3:dict(bg=("e3m_kitchen.jpeg",1.2,.34,.38,1.7),side="left",
        cur=[("고맙다는 말",132,WHITE,160),("못 들어도",150,YEL,214),("30년 차린 밥상이 가족을 살렸다",36,MUTE,0)],
        new=[("알아주지 않아도",120,WHITE,150),("버티는 7가지",150,YEL,196),("2천 년 전 황제가 남몰래 지킨 습관",38,MUTE,0)],
        num=[("알아주지 않아도",120,WHITE,150),("버티는 법",160,YEL,206),("2천 년 전 황제가 남몰래 지킨 습관",38,MUTE,0)]),
}
EP[1]["new"][1]=("흔들리지 않는 7가지",104,YEL,180)
def rows(spec):
    return [(t,(SB(s) if s<60 else BLK(s)),c,dy,(-1 if s<60 else -5)) for t,s,c,dy in spec]
def base(e):
    n,z,cx,cy,b=e["bg"]; return shade(look(place(n,z,cx,cy),b),e["side"],k=.95,start=.08)
def text(im,e,spec,y0):
    if e["side"]=="left": return lines(im,62,y0,rows(spec))
    return lines(im,W-56,y0,rows(spec),"r")
def render(k):
    e=EP[k]; out={}
    out["cur"]=text(base(e),e,e["cur"],128)
    # B: 로고 주화 — 글자 반대쪽 위가 아니라 글자 쪽 위 모서리(텍스트 블록의 '머리')
    c=logo_coin(172); im=text(base(e),e,e["new"],206)
    x=54 if e["side"]=="left" else W-54-172
    out["B"]=put(im,c,x,30)
    # A: 숫자 주화 — 7가지를 주화 안에
    nc=num_coin(200,"7"); spec=e["num"][:2]; im=text(base(e),e,spec,96)
    x=56 if e["side"]=="left" else W-56-200
    out["A"]=put(im,nc,x,96+sum(r[3] for r in spec)+6)
    return out
def render_C(k):
    # C: 시네마틱 — 큰 주화가 인물 반대편 어둠 속에서 빛남
    e=EP[k]; im=base(e); big=logo_coin(560)
    big.putalpha(Image.fromarray((np.array(big.split()[3])*.32).astype(np.uint8)))
    x=-120 if e["side"]=="left" else W-440
    im=put(im,big,x,80,glow=70)
    return text(im,e,e["new"],196)

if __name__=="__main__":
    import os; os.makedirs(OUT,exist_ok=True)
    for k in (1,2,3):
        o=render(k); o["C"]=render_C(k)
        for v,im in o.items(): im.save(f"{OUT}ep0{k}_{v}.jpg",quality=93)
