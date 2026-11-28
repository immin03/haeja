exec(open('/tmp/lgv.py').read().split("V={")[0])
from PIL import Image, ImageDraw
def with_coin(lg, gold=True, ring=True):
    h=lg.height; d0=h; c=canvas(d0,d0); dr=ImageDraw.Draw(c)
    inner=m.coin(d0-(10 if ring else 0), gold=gold); c.alpha_composite(inner,((d0-inner.width)//2,)*2)
    if ring: dr.ellipse((1,1,d0-2,d0-2),outline=GOLD+(255,),width=2)
    out=canvas(d0+18+lg.width,h); out.alpha_composite(c,(0,0)); out.alpha_composite(lg,(d0+18,0)); return out
base=lock(30,align='r',rules=False)
A={'R1 기본(현재)':base,'C1 금빛 주화 + 금테':with_coin(base),'C2 금빛 주화(테 없음)':with_coin(base,ring=False),'C3 원본 주화 + 금테':with_coin(base,gold=False)}
bg=Image.open('/home/claude/render/bg1.png').convert('RGBA').resize((1920,1080)); lab=fnt('SUIT-Bold.ttf',30)
sh=Image.new('RGB',(1350,4*336),(24,24,24))
for i,(n,lg) in enumerate(A.items()):
    lg.save(f'/home/claude/render/logo_{n[:2]}.png')
    f=bg.copy(); f.alpha_composite(lg,(1920-56-lg.width,max(6,(131-lg.height)//2))); f=f.convert('RGB')
    r=Image.new('RGB',(1350,330),(24,24,24)); dd=ImageDraw.Draw(r); dd.text((10,6),n+f' ({lg.width}×{lg.height})',font=lab,fill=(255,220,120))
    r.paste(f.resize((480,270),Image.LANCZOS),(10,48)); r.paste(f.crop((1920-850,0,1920,270)),(500,48)); sh.paste(r,(0,i*336))
sh.save('/home/claude/render/logo_coin.jpg',quality=88); print('ok')
