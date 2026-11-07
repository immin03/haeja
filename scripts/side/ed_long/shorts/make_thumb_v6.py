# 롱폼 썸네일 v6 (2026-11-07 확정) — 편당 3장 A/B 테스트용
#   M1: 『명상록』 + 기본 배경 / M2: 『명상록』 + 다른 배경 / S1: 스토아 철학 + 기본 배경
#   배경 큰 주화(은은하게), 문구 = 결과 + 7가지(대본 '오늘 밤에는' 실천 7개와 일치)
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from make_thumb_v5 import draw_rows, fit, GOLD, BOLD
from make_thumb_solution import place, look, shade, logo_coin, put, BLK, WHITE, YEL, W, H
from PIL import Image, ImageDraw
import numpy as np
OUT=sys.argv[1] if len(sys.argv)>1 else "/home/claude/thumbs/v6/"

EP={
 1:dict(l1="배신당해도 무너지지 않는", l2="7가지 방법",
        main=("lp04_eyes.jpeg",1.18,.36,.42,1.6,"left"), alt=("lp05_phone.jpeg",1.12,.38,.5,1.75,"right")),
 2:dict(l1="무례한 사람을 이기는", l2="7가지 방법",
        main=("e2m_holiday.jpeg",1.15,.42,.42,1.7,"right"), alt=("e2_eyes.jpeg",1.3,.36,.38,1.75,"left")),
 3:dict(l1="인정에 목매지 않는", l2="7가지 습관",
        main=("e3m_kitchen.jpeg",1.2,.34,.38,1.7,"left"), alt=("e3_watch.jpeg",1.12,.66,.30,1.6,"right")),
}
def bg(spec):
    n,z,cx,cy,b,side=spec; im=shade(look(place(n,z,cx,cy),b),side,k=.95,start=.08)
    big=logo_coin(560); big.putalpha(Image.fromarray((np.array(big.split()[3])*.32).astype(np.uint8)))
    x=-120 if side=="left" else W-440
    return put(im,big,x,80,glow=70)
def make(e,spec,label):
    side=spec[5]; d=ImageDraw.Draw(Image.new("RGB",(10,10)))
    s1=fit(d,e["l1"],700,104); s2=fit(d,e["l2"],700,180)
    rows=[(label,BOLD(66 if "명상록" in label else 60),GOLD,92,-2),(e["l1"],BLK(s1),WHITE,s1+20,-4),(e["l2"],BLK(s2),YEL,0,-6)]
    return draw_rows(bg(spec),{"side":side},rows,170)

if __name__=="__main__":
    os.makedirs(OUT,exist_ok=True)
    for k,e in EP.items():
        make(e,e["main"],"『명상록』").save(f"{OUT}ep0{k}_M1.jpg",quality=92)
        make(e,e["alt"],"『명상록』").save(f"{OUT}ep0{k}_M2.jpg",quality=92)
        make(e,e["main"],"스토아 철학").save(f"{OUT}ep0{k}_S1.jpg",quality=92)
