import sys, os
sys.path.insert(0, 'scripts')
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import brand
W,H=2560,1440
NAVY=(13,27,52); NAVY2=(22,40,72); IVORY=(246,241,232); GOLD=(240,208,140); GREY=(176,186,206); GREEN=(61,245,160); RED=(255,77,109)
F=lambda w,s: ImageFont.truetype(f'scripts/reels/fonts/SUIT-{w}.ttf', s)
im=Image.new('RGBA',(W,H),NAVY+(255,))
d=ImageDraw.Draw(im)
# soft vertical gradient + faint grid
for y in range(H):
    t=y/H; c=tuple(int(NAVY[i]*(1-t)+NAVY2[i]*t) for i in range(3)); d.line([(0,y),(W,y)],fill=c)
g=Image.new('RGBA',(W,H),(0,0,0,0)); gd=ImageDraw.Draw(g)
for x in range(0,W,80): gd.line([(x,0),(x,H)],fill=(255,255,255,10))
for y in range(0,H,80): gd.line([(0,y),(W,y)],fill=(255,255,255,10))
im.alpha_composite(g)
# subtle rising line chart on right (decor, outside safe text area mostly)
pts=[(1700,980),(1860,900),(1980,940),(2120,800),(2260,830),(2420,640),(2560,600)]
ln=Image.new('RGBA',(W,H),(0,0,0,0)); ld=ImageDraw.Draw(ln)
ld.line(pts,fill=GOLD+(70,),width=8,joint='curve')
im.alpha_composite(ln.filter(ImageFilter.GaussianBlur(1)))
# safe area 1546x423 centered
sx=(W-1546)//2+50; sy=(H-423)//2+18; SW=1546-100
logo=brand.logo_image(size=70,theme="dark",ko=True)[0]
im.alpha_composite(logo,(sx, sy+8))
lx=sx+logo.width+40
d=ImageDraw.Draw(im)
d.line([(lx, sy+30),(lx, sy+190)],fill=GOLD+(160,),width=3)
tx=lx+44
d.text((tx, sy+18),'돈이 움직이는 이야기',font=F('Heavy',96),fill=IVORY)
d.text((tx, sy+138),'기업 · 돈 · 경제를 이야기로 풀고, 마지막에 숫자로 정리합니다',font=F('SemiBold',36),fill=GREY)
# three pillars row
labels=[('기업 분석','상장사 이야기 · 주가 전망 3가지'),('돈과 기업 이야기','생활 속 돈은 어디로 가나'),('경제 · 금융','금리 · 환율 · 금 · 채권')]
y0=sy+250; colw=SW//3
for i,(a,b) in enumerate(labels):
    x=sx+i*colw
    d.ellipse([x, y0+8, x+22, y0+30], fill=GOLD)
    d.text((x+38, y0-6), a, font=F('ExtraBold',50), fill=IVORY)
    d.text((x+38, y0+62), b, font=F('Medium',32), fill=GREY)
im.convert('RGB').save(sys.argv[1],quality=92)
# preview: safe area box + mobile/tv crops
pv=im.copy(); pd=ImageDraw.Draw(pv); pd.rectangle([(W-1546)//2,(H-423)//2,(W+1546)//2,(H+423)//2],outline=(255,0,0,255),width=4)
pd.rectangle([(W-2560)//2,(H-423)//2,(W+2560)//2,(H+423)//2],outline=(0,255,0,255),width=3)
pv.convert('RGB').resize((1280,720)).save(sys.argv[2],quality=85)
