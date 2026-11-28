exec(open('/tmp/lgv.py').read().split("V={")[0])
from PIL import Image, ImageDraw
A={'R1 우측 정렬 · 선 없음 · 30':lock(30,align='r',rules=False),
   'R2 우측 정렬 · 한글 금색 · 30':lock(30,align='r',rules=False,ko_col=GOLD),
   'R3 우측 정렬 · 왼쪽 선 · 30':lock(30,align='r',rules=True)}
bg=Image.open('/home/claude/render/bg1.png').convert('RGBA').resize((1920,1080)); lab=fnt('SUIT-Bold.ttf',30); th=Image.open('/home/claude/render/lf01_d1.jpg').convert('RGBA')
sh=Image.new('RGB',(1340+650,3*336),(24,24,24))
for i,(n,lg) in enumerate(A.items()):
    lg.save(f'/home/claude/render/logo_{n[:2]}.png')
    f=bg.copy(); f.alpha_composite(lg,(1920-56-lg.width,max(6,(131-lg.height)//2))); f=f.convert('RGB')
    t=th.copy(); l2=lg.resize((lg.width*2//3,lg.height*2//3),Image.LANCZOS)
    r=Image.new('RGB',(1990,330),(24,24,24)); dd=ImageDraw.Draw(r); dd.text((10,6),n+f' ({lg.width}×{lg.height})',font=lab,fill=(255,220,120))
    r.paste(f.resize((480,270),Image.LANCZOS),(10,48)); r.paste(f.crop((1920-850,0,1920,270)),(500,48))
    # 썸네일: 원래 로고 자리를 덮지 않도록 d1 원본 위에 다시 그림 → 새로 합성
    sh.paste(r,(0,i*336))
sh.save('/home/claude/render/logo_R.jpg',quality=88); print('ok')
