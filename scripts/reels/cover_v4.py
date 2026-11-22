# 쇼츠 표지 v4 (11/22 18:51 대표: 첫 줄 더 크게, 셋째 줄 없앰, 제목은 위로 — 쇼츠 화면 위·아래 가림 여백 고려)
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
F='/tmp/hj/scripts/reels/fonts/'; W,H=1080,1920; PINK=(255,77,109); WH=(255,255,255)
def S(w,s): return ImageFont.truetype(F+f'SUIT-{w}.ttf',s)
def M(w,s): return ImageFont.truetype(F+f'Montserrat-{w}.ttf',s)
def fit(w,t,s,mx):
    while S(w,s).getlength(t)>mx: s-=4
    return S(w,s)
def sh(img,xy,t,f,fill,anchor='ls',blur=12,a=200):
    L=Image.new('RGBA',img.size,(0,0,0,0)); ImageDraw.Draw(L).text(xy,t,font=f,fill=(0,0,0,a),anchor=anchor)
    img.alpha_composite(L.filter(ImageFilter.GaussianBlur(blur))); ImageDraw.Draw(img).text(xy,t,font=f,fill=fill,anchor=anchor)
def make(sp,out):
    py=sp.get('py',560); ph=Image.open(sp['photo']).convert('RGB'); hh=H-py
    s=max(W/ph.width,hh*sp.get('zoom',1)/ph.height); ph=ph.resize((int(ph.width*s)+1,int(ph.height*s)+1))
    ox=int((ph.width-W)*sp.get('fx',.5)); oy=int(max(ph.height-hh,0)*sp.get('fy',0)); ph=ph.crop((ox,oy,ox+W,oy+min(hh,ph.height)))
    a=np.asarray(ph,np.float32); g=a.mean(2,keepdims=True); a=a*.55+g*.45; ph=Image.fromarray(np.clip(a*.92,0,255).astype(np.uint8))
    m=np.full((ph.height,W),255,np.uint8); ft=320; m[:ft]=(np.linspace(0,255,ft)[:,None]).astype(np.uint8)
    fb=min(260,ph.height); m[-fb:]=np.minimum(m[-fb:],(np.linspace(255,0,fb)[:,None]).astype(np.uint8))
    bg=Image.new('RGB',(W,H),(8,8,10)); bg.paste(ph,(0,py),Image.fromarray(m)); img=bg.convert('RGBA'); d=ImageDraw.Draw(img)
    X=70; mx=W-2*X; y=290   # 위 190px 쇼츠 아이콘 가림 → 그 아래부터
    fk=fit('Heavy',sp['kicker'],84,mx-34); d.rectangle([X,y-66,X+12,y+8],fill=PINK); sh(img,(X+36,y),sp['kicker'],fk,WH)
    y+=34
    for t,col in sp['rows']:
        f=fit('Heavy',t,sp.get('size',176),mx); y+=int(f.size*1.03); sh(img,(X-6,y),t,f,col,blur=16,a=220)
    fb2,fl=M('ExtraBold',40),M('Light',40); lw=fb2.getlength('VALUE')+fl.getlength('NOTE')+8; lx=W-X-lw; ly=y+80
    sh(img,(lx,ly),'VALUE',fb2,WH,'lm'); sh(img,(lx+fb2.getlength('VALUE')+8,ly),'NOTE',fl,WH,'lm'); d.rounded_rectangle([lx,ly+27,lx+lw,ly+33],3,fill=PINK)
    img.convert('RGB').save(out,quality=92); return out
L='/tmp/hj/scripts/blog/media/lib/'
SP={
 'Y261121a':{'photo':L+'il_L261121i_thumb_q.jpeg','fx':.62,'zoom':1.25,'py':470,'kicker':'매출 4배인데 주가는 1년 최저','rows':[('아이온큐 주가 전망',WH),('이 3가지만 보세요',PINK)]},
 'Y261122b':{'photo':L+'commons_buffett_2.jpg','fx':.5,'kicker':'나스닥 폭락장에 혼자 신고가','rows':[('워런 버핏',WH),('또 혼자 웃었다',PINK)]},
 'Y261121s':{'photo':'/tmp/pj/mem/th/burry_samsung.png','fx':.55,'zoom':.72,'py':520,'kicker':'빅쇼트 마이클 버리','rows':[('메모리 공매도',WH),('블랙먼데이 오나?',PINK)]},
}
if __name__=='__main__':
    for k,v in SP.items(): make(v,f'/tmp/pj/scv/{k}_v4.jpg')
