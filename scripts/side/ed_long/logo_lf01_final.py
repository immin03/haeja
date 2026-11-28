import importlib.util as u, sys
sp=u.spec_from_file_location('lg','scripts/side/ed_long/logo_lf01.py'); m=u.module_from_spec(sp); sp.loader.exec_module(m)
from PIL import Image, ImageDraw
fnt,tw,spaced,canvas=m.fnt,m.tw,m.spaced,m.canvas
GOLD,GOLD2,IVO=m.GOLD,m.GOLD2,m.IVO
TE,TK="THE EMPEROR'S DIARY","황제의 일기"
def lock(sz=25, align='c', rules=True, ko_col=IVO, ko_first=False, frame=False, ko_font='hahmlet-korean-600-normal.ttf', ko_scale=1.0, en_track=3):
    k=3; s=lambda v:int(round(v*k))
    fe=fnt('Cinzel-SemiBold.ttf',s(sz)); fk=fnt(ko_font,s(sz*ko_scale))
    we=tw(TE,fe,s(en_track)); wk=tw(TK,fk,s(sz*.28))
    rule=s(sz*1.3) if rules else 0; gap=s(sz*.55) if rules else 0
    Wd=int(max(we+2*(rule+gap), wk))+s(30 if frame else 4); hE=s(sz*1.2); hK=s(sz*ko_scale*1.25); g=s(sz*.35)
    Hd=hE+hK+g+s(30 if frame else 4); im=canvas(Wd,Hd); d=ImageDraw.Draw(im); pad=s(15 if frame else 2)
    rows=[('k',hK),('e',hE)] if ko_first else [('e',hE),('k',hK)]; y=pad
    for kind,h in rows:
        w = we if kind=='e' else wk
        if align=='c': x=Wd/2-w/2
        elif align=='r': x=Wd-pad-w-(rule+gap if kind=='e' and rules else 0)
        else: x=pad+(rule+gap if kind=='e' and rules else 0)
        if kind=='e':
            spaced(d,(x,y),TE,fe,GOLD,s(en_track)); yl=y+s(sz*.68)
            if rules:
                for sg,xi in ((-1,x-gap),(1,x+we+gap)):
                    xo=xi+sg*rule; d.line((min(xi,xo),yl,max(xi,xo),yl),fill=GOLD2+(255,),width=max(1,s(1)))
                    r=s(sz*.16); dx=xi-sg*s(2); d.polygon([(dx-r,yl),(dx,yl-r),(dx+r,yl),(dx,yl+r)],fill=GOLD)
        else: spaced(d,(x,y),TK,fk,ko_col,s(sz*.28))
        y+=h+g
    if frame: d.rectangle((s(2),s(2),Wd-s(3),Hd-s(3)),outline=GOLD2+(230,),width=s(1))
    return im.resize((Wd//k,Hd//k),Image.LANCZOS)
def oneline(sz=24, sep='|'):
    k=3;s=lambda v:int(round(v*k)); fe=fnt('Cinzel-SemiBold.ttf',s(sz)); fk=fnt('hahmlet-korean-600-normal.ttf',s(sz))
    we=tw(TE,fe,s(3)); wk=tw(TK,fk,s(5)); gap=s(22); Wd=int(we+wk+2*gap+s(4)); Hd=s(sz*1.5); im=canvas(Wd,Hd); d=ImageDraw.Draw(im)
    spaced(d,(0,s(3)),TE,fe,GOLD,s(3)); xm=we+gap; d.line((xm,s(sz*.25),xm,s(sz*1.15)),fill=GOLD2+(255,),width=s(1))
    spaced(d,(xm+gap,s(1)),TK,fk,IVO,s(5)); return im.resize((Wd//k,Hd//k),Image.LANCZOS)
V={'1 기본(확정안) 가운데 · 25':lock(),
 '2 작게 · 20':lock(20),
 '3 크게 · 30':lock(30),
 '4 오른쪽 정렬':lock(align='r'),
 '5 선 없이 · 한글 금색':lock(rules=False, ko_col=GOLD),
 '6 한글 위 · 영문 아래':lock(ko_first=True, rules=False, ko_scale=1.25, en_track=4, sz=19),
 '7 가는 금테 상자':lock(22, rules=False, frame=True),
 '8 한 줄':oneline()}
bg=Image.open('/home/claude/render/bg1.png').convert('RGBA').resize((1920,1080))
lab=fnt('SUIT-Bold.ttf',30); rows=[]
for n,lg in V.items():
    f=bg.copy(); f.alpha_composite(lg,(1920-56-lg.width,max(6,(131-lg.height)//2))); f=f.convert('RGB')
    r=Image.new('RGB',(1340,330),(24,24,24)); dd=ImageDraw.Draw(r); dd.text((10,6),n+f'  ({lg.width}×{lg.height})',font=lab,fill=(255,220,120))
    r.paste(f.resize((480,270),Image.LANCZOS),(10,48)); r.paste(f.crop((1920-850,0,1920,270)),(500,48)); rows.append(r)
sh=Image.new('RGB',(1340*2+10,4*336),(24,24,24))
for i,r in enumerate(rows): sh.paste(r,((i%2)*1350,(i//2)*336))
pass

S={24:oneline(24),28:oneline(28),32:oneline(32)}
rows=[]
for z,lg in S.items():
    f=bg.copy(); f.alpha_composite(lg,(1920-56-lg.width,(131-lg.height)//2)); f=f.convert('RGB')
    r=Image.new('RGB',(1340,330),(24,24,24)); dd=ImageDraw.Draw(r); dd.text((10,6),f'{z}px  ({lg.width}×{lg.height})',font=lab,fill=(255,220,120))
    r.paste(f.resize((480,270),Image.LANCZOS),(10,48)); r.paste(f.crop((1920-850,0,1920,270)),(500,48)); rows.append(r)
    lg.save(f'/home/claude/render/logo8_{z}.png')
    f.resize((390,219),Image.LANCZOS).save(f'/home/claude/render/logo8_{z}_phone.jpg')
sh=Image.new('RGB',(1340,3*336+240),(24,24,24))
for i,r in enumerate(rows): sh.paste(r,(0,i*336))
for i,z in enumerate(S): sh.paste(Image.open(f'/home/claude/render/logo8_{z}_phone.jpg'),(10+i*440,3*336+10))
ImageDraw.Draw(sh).text((10,3*336+225),'',font=lab)
sh.save('/home/claude/render/logo8_sizes.jpg',quality=90)
exec(open('/tmp/lgv.py').read().split("V={")[0])
from PIL import Image, ImageDraw
def cn(d0, ring=True):
    c=canvas(d0,d0); inner=m.coin(d0-(8 if ring else 0)); c.alpha_composite(inner,((d0-inner.width)//2,)*2)
    if ring: ImageDraw.Draw(c).ellipse((1,1,d0-2,d0-2),outline=GOLD+(255,),width=2)
    return c
def P(textlg, coin_d, side='L', divider=True, gap=16):
    h=max(textlg.height,coin_d); dv=(gap*2+2) if divider else gap
    out=canvas(coin_d+dv+textlg.width,h); c=cn(coin_d)
    if side=='L':
        out.alpha_composite(c,(0,(h-coin_d)//2)); out.alpha_composite(textlg,(coin_d+dv,(h-textlg.height)//2)); xd=coin_d+gap
    else:
        out.alpha_composite(textlg,(0,(h-textlg.height)//2)); out.alpha_composite(c,(textlg.width+dv,(h-coin_d)//2)); xd=textlg.width+gap
    if divider: ImageDraw.Draw(out).line((xd,h*0.12,xd,h*0.88),fill=GOLD2+(255,),width=2)
    return out
tl=lock(28,align='l',rules=False); tr=lock(28,align='r',rules=False)
A={'P1 주화 왼쪽 · 세로 금선 · 글 왼쪽 정렬':P(tl,70,'L'),
   'P2 글 오른쪽 정렬 · 세로 금선 · 주화 오른쪽':P(tr,70,'R'),
   'P3 주화 왼쪽 · 선 없이 붙임':P(tl,66,'L',divider=False,gap=14),
   'P4 글 위아래 높이에 꼭 맞춘 작은 주화':P(tl,int(tl.height*0.92),'L',divider=True,gap=12)}
bg=Image.open('/home/claude/render/bg1.png').convert('RGBA').resize((1920,1080)); lab=fnt('SUIT-Bold.ttf',30)
sh=Image.new('RGB',(1350,4*336),(24,24,24))
for i,(n,lg) in enumerate(A.items()):
    lg.save(f'/home/claude/render/logo_{n[:2]}.png')
    f=bg.copy(); f.alpha_composite(lg,(1920-56-lg.width,max(6,(131-lg.height)//2))); f=f.convert('RGB')
    r=Image.new('RGB',(1350,330),(24,24,24)); dd=ImageDraw.Draw(r); dd.text((10,6),n+f' ({lg.width}×{lg.height})',font=lab,fill=(255,220,120))
    r.paste(f.resize((480,270),Image.LANCZOS),(10,48)); r.paste(f.crop((1920-850,0,1920,270)),(500,48)); sh.paste(r,(0,i*336))
sh.save('/home/claude/render/logo_coin2.jpg',quality=88); print('ok')
exec(open('/tmp/lg4.py').read().split("tl=lock")[0])
from PIL import Image, ImageDraw
def en_only(sz):
    k=3;s=lambda v:int(round(v*k)); fe=fnt('Cinzel-SemiBold.ttf',s(sz)); we=tw(TE,fe,s(3.5)); im=canvas(int(we)+s(4),s(sz*1.25)); d=ImageDraw.Draw(im)
    spaced(d,(0,s(sz*.08)),TE,fe,GOLD,s(3.5)); bb=im.getbbox(); im=im.crop((0,bb[1]-s(2),im.width,bb[3]+s(2)))
    return im.resize((im.width//k,im.height//k),Image.LANCZOS)
A={'F1 주화 60 · 영문 32':P(en_only(32),60,'L',gap=16),'F2 주화 68 · 영문 36':P(en_only(36),68,'L',gap=18),'F3 주화 52 · 영문 28':P(en_only(28),52,'L',gap=14)}
bg=Image.open('/home/claude/render/bg1.png').convert('RGBA').resize((1920,1080)); lab=fnt('SUIT-Bold.ttf',30)
sh=Image.new('RGB',(1350,3*336),(24,24,24))
for i,(n,lg) in enumerate(A.items()):
    lg.save(f'/home/claude/render/logo_{n[:2]}.png')
    f=bg.copy(); f.alpha_composite(lg,(1920-56-lg.width,max(6,(131-lg.height)//2))); f=f.convert('RGB')
    r=Image.new('RGB',(1350,330),(24,24,24)); dd=ImageDraw.Draw(r); dd.text((10,6),n+f' ({lg.width}×{lg.height})',font=lab,fill=(255,220,120))
    r.paste(f.resize((480,270),Image.LANCZOS),(10,48)); r.paste(f.crop((1920-850,0,1920,270)),(500,48)); sh.paste(r,(0,i*336))
sh.save('/home/claude/render/logo_final.jpg',quality=88); print('ok')
