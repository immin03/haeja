"""EP.1 장면 조각(16:9) → 세로 쇼츠 1080x1920. 위: 고정 훅 제목, 가운데: 본편 화면, 아래: 풀영상 안내. 끝 2.6초 = 풀영상 유도 카드
python3 make_short.py <id> "<제목1>" "<제목2>" seg1.mp4:from:to [seg2.mp4:from:to ...]"""
import sys, subprocess, os, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter
L="/home/claude/haeja/_long/"; F="/root/fonts/"; OUT="/home/claude/shorts/"
W,H=1080,1920; FPS=30; VY=664; VH=526; CW,CH,CX,CY=1680,818,120,131; END=2.6
key,t1,t2=sys.argv[1],sys.argv[2],sys.argv[3]; segs=[a.split(":") for a in sys.argv[4:]]
fk=lambda s: ImageFont.truetype(F+"Pretendard-ExtraBold.otf",s); fu=lambda s: ImageFont.truetype(F+"Pretendard-Bold.otf",s)
WHITE=(255,255,255); GOLD=(244,196,92)
def ctext(d,y,t,f,fill,stroke=0):
    w=d.textlength(t,font=f); x=(W-w)/2
    for o in (6,4,2): d.text((x+o/2,y+o),t,font=f,fill=(0,0,0))
    d.text((x,y),t,font=f,fill=fill)
def fit(t,base,maxw=980):
    s=base
    while ImageDraw.Draw(Image.new("RGB",(1,1))).textlength(t,font=fk(s))>maxw: s-=4
    return fk(s)
# 위·아래 고정 레이어 (RGBA)
over=Image.new("RGBA",(W,H),(0,0,0,0)); d=ImageDraw.Draw(over)
ctext(d,250,"2천 년 전 로마 황제의 일기",fu(42),GOLD,3)
f1=fit(t1,100); f2=fit(t2,100)
d.rectangle((W//2-32,316,W//2+32,319),fill=GOLD)
ctext(d,350,t1,f1,WHITE); ctext(d,474,t2,f2,GOLD)
ctext(d,VY+VH+64,"▶ 12분 전체 이야기는 아래 '관련 동영상'",fu(40),(235,228,215),3)
ctext(d,VY+VH+122,"황제의 일기 EP.1",fu(36),GOLD,3)
OV=np.array(over); A=OV[...,3:4].astype(np.float32)/255; OVC=cv2.cvtColor(OV[...,:3],cv2.COLOR_RGB2BGR).astype(np.float32)
def endcard(fr):
    fr=fr[131:949]; bg=cv2.resize(fr,(int(H*fr.shape[1]/fr.shape[0]),H)); x0=(bg.shape[1]-W)//2; bg=cv2.GaussianBlur(bg[:,x0:x0+W],(0,0),24).astype(np.float32)*0.28
    im=Image.fromarray(cv2.cvtColor(bg.astype(np.uint8),cv2.COLOR_BGR2RGB)); d=ImageDraw.Draw(im)
    ctext(d,700,"이 밤의 이야기는",fk(76),WHITE); ctext(d,810,"아직 끝나지 않았다",fk(76),WHITE)
    ctext(d,980,"▼ 아래 '관련 동영상'에서",fu(52),GOLD,3); ctext(d,1055,"12분 전체 이야기 보기",fu(52),GOLD,3)
    ctext(d,1260,"매일 밤, 황제처럼 생각하라.",fu(40),(225,215,200),2)
    return im
over.save(OUT+key+"_ov.png")
# 1) 조각 이어 붙이기 (화면+소리)
ins=[]; fc=""; durs=[]
for i,(f,a,b) in enumerate(segs):
    dd=float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",L+f],capture_output=True,text=True).stdout); durs.append(dd)
    ins+=["-i",L+f,"-ss",a,"-t",f"{dd:.3f}","-i",L+"edl_ep01_a.wav"]
    fc+=f"[{2*i}:v]fps={FPS},setpts=PTS-STARTPTS[v{i}];[{2*i+1}:a]asetpts=PTS-STARTPTS,afade=t=in:d=0.25,afade=t=out:st={dd-0.35:.3f}:d=0.35[a{i}];"
n=len(segs); fc+="".join(f"[v{i}][a{i}]" for i in range(n))+f"concat=n={n}:v=1:a=1[cv][ca]"
cat=OUT+key+"_cat.mp4"
subprocess.run(["ffmpeg","-v","error","-y",*ins,"-filter_complex",fc,"-map","[cv]","-map","[ca]","-c:v","libx264","-preset","ultrafast","-crf","14","-c:a","pcm_s16le",cat.replace(".mp4",".mkv")],check=True)
cat=cat.replace(".mp4",".mkv"); T=sum(durs)
# 끝 카드용 마지막 프레임
c=cv2.VideoCapture(cat); c.set(1,int(T*FPS)-3); ok,last=c.read(); endcard(last).save(OUT+key+"_end.png")
# 2) 세로 합성 + 끝 카드
fc=(f"[0:v]crop={CW}:{CH}:{CX}:{CY},split[a][b];[a]scale=-2:{H},crop={W}:{H},scale=270:480,boxblur=6:2,scale={W}:{H},eq=brightness=-0.22[bg];"
    f"[b]scale={W}:{VH}[fg];[bg][fg]overlay=0:{VY}[m];[m][1:v]overlay=0:0,format=yuv420p[main];"
    f"[2:v]loop=-1:1,fps={FPS},trim=duration={END},format=yuv420p,fade=t=in:d=0.4[endv];[main][endv]concat=n=2:v=1:a=0[vo];"
    f"[0:a]apad=pad_dur={END},afade=t=out:st={T+0.3:.3f}:d={END-0.4}[ao]")
subprocess.run(["ffmpeg","-v","error","-y","-i",cat,"-i",OUT+key+"_ov.png","-loop","1","-i",OUT+key+"_end.png","-filter_complex",fc,"-map","[vo]","-map","[ao]",
    "-c:v","libx264","-preset","veryfast","-crf","21","-c:a","aac","-b:a","192k","-ar","48000","-t",f"{T+END:.3f}","-movflags","+faststart",OUT+key+".mp4"],check=True)
for f in (cat,OUT+key+"_ov.png",OUT+key+"_end.png"): os.remove(f)
print("완성",OUT+key+".mp4",round(T+END,1))
