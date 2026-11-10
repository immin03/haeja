import os
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageEnhance,ImageChops
import numpy as np
G='social/side/gen/';O=os.environ.get('OUT','_long/')   # 저장소 루트에서 실행: python3 scripts/side/ed_long/thumb_cep01.py (SUIT: scripts/reels/fonts → /root/fonts)
W,H=1280,720
F=lambda s:ImageFont.truetype('/root/fonts/hahmlet-korean-700-normal.ttf',s)
P=lambda s:ImageFont.truetype('/root/fonts/Pretendard-SemiBold.otf',s)
def fit(p,box,cx=.5,cy=.4,scale=1.0):
    im=Image.open(G+p).convert('RGB');bw,bh=box;k=max(bw/im.width,bh/im.height)*scale
    im=im.resize((int(im.width*k)+1,int(im.height*k)+1),Image.LANCZOS)
    x=int((im.width-bw)*cx);y=int((im.height-bh)*cy);return im.crop((x,y,x+bw,y+bh))
def grad(w,h,x0,x1,a0,a1):
    g=np.zeros((h,w),np.float32);xs=np.clip((np.arange(w)-x0)/max(x1-x0,1),0,1);g[:]=a0+(a1-a0)*xs;return Image.fromarray((g*255).astype(np.uint8))
def coin(base,cx,cy,d,op):
    c=Image.open('docs/emperor/profile_final.png').convert('RGBA').resize((d,d),Image.LANCZOS)
    m=Image.new('L',(d,d),0);ImageDraw.Draw(m).ellipse((0,0,d,d),fill=255);m=m.filter(ImageFilter.GaussianBlur(d//14))
    lay=Image.new('RGB',base.size,(0,0,0));lay.paste(c.convert('RGB'),(cx-d//2,cy-d//2),m)
    return Image.blend(base,ImageChops.screen(base,lay),op)
S_=lambda w,s:ImageFont.truetype(f'/root/fonts/SUIT-{w}.ttf',s)
def track(d,xy,t,f,fill,sp):
    x,y=xy
    for ch in t: d.text((x,y),ch,font=f,fill=fill); x+=d.textlength(ch,font=f)+sp
    return x
def tw_(d,t,f,sp): return sum(d.textlength(c,font=f)+sp for c in t)-sp
def text(im,lines,x,y,size,gold=None,tag='명상록',lh=1.12):
    # 11/10 대표: 테두리 없이, SUIT 고딕, 절제된 크림슨 태그
    f=S_('ExtraBold',size);n=len(lines);bot=H-52;y=bot-int(size*lh*(n-1))-size
    m=Image.new('L',(W,H),0);dm=ImageDraw.Draw(m)
    for i,l in enumerate(lines): track(dm,(x,y+int(i*size*lh)),l,f,255,-3)
    sh=m.filter(ImageFilter.GaussianBlur(18));im.paste((0,0,0),(0,6),sh.point(lambda v:min(255,int(v*1.3))))
    for i,l in enumerate(lines):
        mm=Image.new('L',(W,H),0);track(ImageDraw.Draw(mm),(x,y+int(i*size*lh)),l,f,255,-3)
        im.paste((236,196,118) if i==gold else (250,248,244),(0,0),mm)
    d=ImageDraw.Draw(im);tf=S_('Bold',62);tw=tw_(d,tag,tf,4);ty=y-112
    d.rectangle((x,ty,x+tw+48,ty+86),fill=(138,24,28))
    track(d,(x+24,ty+8),tag,tf,(255,246,236),4)
    d.rectangle((x+tw+64,ty+42,x+tw+64+100,ty+44),fill=(236,196,118))
    brand(im)
    return im
def brand(im):
    # 11/10 대표: 오른쪽 위에 채널 이름을 작고 세련되게
    d=ImageDraw.Draw(im);ef=ImageFont.truetype('/root/fonts/cormorant-sc-latin-600-normal.ttf',30);kf=S_('SemiBold',22)
    en="THE EMPEROR'S DIARY";ko='황제의 일기';ew=tw_(d,en,ef,3);kw=tw_(d,ko,kf,6);r=W-40;cd=58
    bw=max(ew,kw);x0=r-bw;cx=int(x0-14-cd)
    sh=Image.new('L',(W,H),0);ImageDraw.Draw(sh).rectangle((cx-10,24,r+10,24+cd+12),fill=150);im.paste((0,0,0),(0,0),sh.filter(ImageFilter.GaussianBlur(22)))
    c=Image.open('docs/emperor/profile_final.png').convert('RGBA').resize((cd,cd),Image.LANCZOS);mk=Image.new('L',(cd,cd),0);ImageDraw.Draw(mk).ellipse((0,0,cd-1,cd-1),fill=255)
    im.paste(c.convert('RGB'),(cx,30),mk)
    track(d,(int(r-ew),30),en,ef,(236,206,140),3);track(d,(int(r-kw),68),ko,kf,(240,234,224),6)
def fin(im):
    im=ImageEnhance.Contrast(im).enhance(1.12);im=ImageEnhance.Color(im).enhance(1.12)
    v=np.array(im).astype(np.float32);yy,xx=np.mgrid[0:H,0:W];r=((xx-W/2)/(W/2))**2+((yy-H/2)/(H/2))**2
    v*=np.clip(1.08-0.3*r,0,1.1)[...,None];return Image.fromarray(np.clip(v,0,255).astype(np.uint8))
# A: 황제 vs 카시우스
a=Image.new('RGB',(W,H));L=fit('cep1i_spk.jpeg',(700,H),.55,.2,1.15);R=fit('cep1i_ctalk.jpeg',(840,H),.5,.15,1.2)
a.paste(R,(440,0));a.paste(L,(0,0),grad(700,H,470,690,1,0))
a=fin(a);a=coin(a,640,150,420,.22)
dk=Image.new('RGB',(W,H),(0,0,0));a=Image.composite(a,dk,Image.fromarray((np.clip(1.0-np.clip((np.mgrid[0:H,0:W][0]-330)/390,0,1)*.78,0,1)*255).astype(np.uint8)))
text(a,['뒤통수 친 사람을','이기는 3가지 방법'],52,0,140,gold=1).save(O+'thumb_A.jpg',quality=93)
# B: 불타는 상자
b=fit('c1_burn.jpeg',(W,H),.5,.5,1.0);e=fit('c1_emp_fire.jpeg',(620,H),.5,.2,1.25)
b.paste(e,(660,0),grad(620,H,0,260,0,1));b=fin(b);b=coin(b,330,250,520,.25)
dk=Image.new('RGB',(W,H),(0,0,0));b=Image.composite(b,dk,grad(W,H,0,760,.42,1))
text(b,['등 돌린 사람에게','하지 말 것 3가지'],52,0,134,gold=1).save(O+'thumb_B.jpg',quality=93)
# C: 스토아 철학
c=fit('cep1i_sback.jpeg',(W,H),.5,.3,1.0);c=fin(c);c=coin(c,960,250,560,.3)
dk=Image.new('RGB',(W,H),(0,0,0));c=Image.composite(c,dk,Image.fromarray((np.clip(1.0-np.clip((np.mgrid[0:H,0:W][0]-300)/420,0,1)*.8,0,1)*255).astype(np.uint8)))
text(c,['믿었던 사람에게','무너지지 않는 법'],52,0,134,gold=1,tag='스토아 철학').save(O+'thumb_C.jpg',quality=93)
s=Image.new('RGB',(W*3//2+40,H//2+20),(20,20,20))
for i,n in enumerate('ABC'): s.paste(Image.open(O+f'thumb_{n}.jpg').resize((W//2,H//2)),(10+i*(W//2+10),10))
s.save(O+'thumbs.jpg')
