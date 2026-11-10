import os
from PIL import Image,ImageDraw,ImageFont,ImageFilter,ImageEnhance,ImageChops
import numpy as np
G='social/side/gen/';O=os.environ.get('OUT','_long/')   # 저장소 루트에서 실행: python3 scripts/side/ed_long/thumb_cep01.py
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
def text(im,lines,x,y,size,gold=None,tag='『명상록』',lh=1.14):
    # 11/10 대표: 40·50대 — 글자 크게, 세련되게(금빛 그라데이션 + 부드러운 그림자), 태그도 크게
    f=F(size);n=len(lines);bot=H-46;y=bot-int(size*lh*(n-1))-size-8
    for i,l in enumerate(lines):
        yy=y+int(i*size*lh)
        m=Image.new('L',(W,H),0);ImageDraw.Draw(m).text((x,yy),l,font=f,fill=255)
        st=Image.new('L',(W,H),0);ImageDraw.Draw(st).text((x,yy),l,font=f,fill=255,stroke_width=4,stroke_fill=255)
        sh=st.filter(ImageFilter.GaussianBlur(14));im.paste((0,0,0),(10,14),sh.point(lambda v:min(255,int(v*1.6))))
        im.paste((10,8,6),(0,0),st)
        if gold is not None and i==gold:
            g=np.zeros((H,W,3),np.uint8);t=np.clip((np.arange(H)-yy)/(size*1.1),0,1)[:,None]
            top=np.array([255,236,170]);btm=np.array([212,150,58]);g[:]=(top*(1-t)+btm*t)[:,None,:].astype(np.uint8)
            im.paste(Image.fromarray(g),(0,0),m)
        else: im.paste((252,247,236),(0,0),m)
    tf=P(64);d=ImageDraw.Draw(im);tw=d.textlength(tag,font=tf);ty=y-112
    d.rounded_rectangle((x,ty,x+tw+56,ty+92),12,fill=(150,22,24),outline=(232,190,110),width=3)
    d.text((x+28,ty+8),tag,font=tf,fill=(255,240,214))
    return im
def fin(im):
    im=ImageEnhance.Contrast(im).enhance(1.12);im=ImageEnhance.Color(im).enhance(1.12)
    v=np.array(im).astype(np.float32);yy,xx=np.mgrid[0:H,0:W];r=((xx-W/2)/(W/2))**2+((yy-H/2)/(H/2))**2
    v*=np.clip(1.08-0.3*r,0,1.1)[...,None];return Image.fromarray(np.clip(v,0,255).astype(np.uint8))
# A: 황제 vs 카시우스
a=Image.new('RGB',(W,H));L=fit('cep1i_spk.jpeg',(700,H),.55,.2,1.15);R=fit('cep1i_ctalk.jpeg',(840,H),.5,.15,1.2)
a.paste(R,(440,0));a.paste(L,(0,0),grad(700,H,470,690,1,0))
a=fin(a);a=coin(a,640,150,420,.22)
dk=Image.new('RGB',(W,H),(0,0,0));a=Image.composite(a,dk,Image.fromarray((np.clip(1.0-np.clip((np.mgrid[0:H,0:W][0]-330)/390,0,1)*.78,0,1)*255).astype(np.uint8)))
text(a,['뒤통수 친 사람을','이기는 3가지 방법'],52,0,132,gold=1).save(O+'thumb_A.jpg',quality=93)
# B: 불타는 상자
b=fit('c1_burn.jpeg',(W,H),.5,.5,1.0);e=fit('c1_emp_fire.jpeg',(620,H),.5,.2,1.25)
b.paste(e,(660,0),grad(620,H,0,260,0,1));b=fin(b);b=coin(b,330,250,520,.25)
dk=Image.new('RGB',(W,H),(0,0,0));b=Image.composite(b,dk,grad(W,H,0,760,.42,1))
text(b,['등 돌린 사람에게','하지 말 것 3가지'],52,0,128,gold=1).save(O+'thumb_B.jpg',quality=93)
# C: 스토아 철학
c=fit('cep1i_sback.jpeg',(W,H),.5,.3,1.0);c=fin(c);c=coin(c,960,250,560,.3)
dk=Image.new('RGB',(W,H),(0,0,0));c=Image.composite(c,dk,Image.fromarray((np.clip(1.0-np.clip((np.mgrid[0:H,0:W][0]-300)/420,0,1)*.8,0,1)*255).astype(np.uint8)))
text(c,['믿었던 사람에게','무너지지 않는 법'],52,0,128,gold=1,tag='스토아 철학').save(O+'thumb_C.jpg',quality=93)
s=Image.new('RGB',(W*3//2+40,H//2+20),(20,20,20))
for i,n in enumerate('ABC'): s.paste(Image.open(O+f'thumb_{n}.jpg').resize((W//2,H//2)),(10+i*(W//2+10),10))
s.save(O+'thumbs.jpg')
