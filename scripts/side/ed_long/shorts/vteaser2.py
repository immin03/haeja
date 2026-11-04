"""황제의 일기 롱폼 소개 쇼츠 (1080x1920) — vteaser.py 를 편마다 쓸 수 있게: ED_SID(세로 조각 spec id), ED_AUD(소리), ED_END1/ED_END2(끝 카드 글)
python3 vshort.py <id> "<제목1>" "<제목2>" chunk:from:to[:cx] ...   (cx = 가로 중심 0~1, 기본 0.5)
- 자막 없이 렌더한 조각(ED_VERT=1)을 9:16 으로 잘라 꽉 채우고, 자막은 세로용으로 크게 다시 얹는다
- 맨 위 훅 제목 고정, 끝 2.6초는 '관련 동영상'으로 본편 유도"""
import sys, os, json, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
L="/home/claude/haeja/_long/"; SID=os.environ.get("ED_SID","edl_ep01v"); AUD=os.environ.get("ED_AUD", "/home/claude/haeja/_long/"+SID+"_a.wav"); CAP=f"/home/claude/haeja/scripts/side/ed_long/caps_{SID}.json"; VER=CAP.replace("caps_","verses_"); F="/root/fonts/"
OUT="/home/claude/shorts2/"; W,H,FPS,END=1080,1920,30,2.6
key,t1,t2=sys.argv[1:4]; segs=[]
for a in sys.argv[4:]:
    p=a.split(":"); segs.append((p[0],float(p[1]),float(p[2]),float(p[3]) if len(p)>3 else 0.5, float(p[4]) if len(p)>4 else 0))
FB=lambda s: ImageFont.truetype(F+"Pretendard-ExtraBold.otf",s); FS=lambda s: ImageFont.truetype(F+"Pretendard-SemiBold.otf",s)
FM=lambda s: ImageFont.truetype(F+"hahmlet-korean-600-normal.ttf",s)
WHITE=(255,255,255); GOLD=(240,196,110); CREAM=(246,234,206)
def shadow_text(img,lines,y,font,fill,gap=1.32,maxw=960):
    d=ImageDraw.Draw(img); sh=Image.new("L",img.size,0); sd=ImageDraw.Draw(sh); pos=[]
    for i,t in enumerate(lines):
        w=d.textlength(t,font=font); x=(W-w)/2; yy=y+i*font.size*gap; pos.append((x,yy,t))
        sd.text((x+2,yy+4),t,font=font,fill=255)
    sh=sh.filter(ImageFilter.GaussianBlur(7)); img.paste((0,0,0,230),(0,0),sh)
    for x,yy,t in pos: d.text((x,yy),t,font=font,fill=fill)
def wrap(t,font,maxw=930):
    d=ImageDraw.Draw(Image.new("L",(1,1))); words=t.split(" "); out=[""]
    for w in words:
        c=(out[-1]+" "+w).strip()
        if d.textlength(c,font=font)<=maxw: out[-1]=c
        else: out.append(w)
    return out
tmp=OUT+key+"_tmp/"; os.makedirs(tmp,exist_ok=True)
# 위 고정층: 위쪽 그라데이션 + 훅 제목 + 아래쪽 그라데이션
top=Image.new("RGBA",(W,H),(0,0,0,0)); g=Image.new("L",(1,H))
for y in range(H):
    a=0
    if y<720: a=int(215*(1-y/720)**1.3)
    if y>1250: a=max(a,int(200*((y-1250)/670)**1.2))
    g.putpixel((0,y),a)
top.paste((0,0,0,255),(0,0),g.resize((W,H)))
d=ImageDraw.Draw(top)
def fit(t,s=104):
    while ImageDraw.Draw(Image.new("L",(1,1))).textlength(t,font=FB(s))>990: s-=4
    return FB(s)
f1,f2=fit(t1),fit(t2); fs=min(f1.size,f2.size); f1=f2=FB(fs)
shadow_text(top,[t1],250,f1,WHITE); shadow_text(top,[t2],250+fs*1.22,f2,GOLD)
top.save(tmp+"top.png")
# 자막 조각
caps=json.load(open(CAP)); ov=[]; vov=[]; T=0; parts=[]
for i,(ch,a,b,cx,mx) in enumerate(segs):
    f=f"{L}{SID}_{ch}_v.mp4"
    dd=float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout)
    if b>a: dd=min(dd-a,b-a)
    if mx: dd=min(dd,mx)
    parts.append((f,a,dd,cx))
    for (ca,cb,txt,kind) in caps:
        if cb<=a or ca>=a+dd: continue
        s0=max(ca,a)-a+T; s1=min(cb,a+dd)-a+T
        im=Image.new("RGBA",(W,520),(0,0,0,0))
        if kind=="emph": fnt=FB(74); col=GOLD
        elif kind=="mono": fnt=FM(66); col=CREAM
        else: fnt=FB(66); col=WHITE
        lines=wrap(txt,fnt); shadow_text(im,lines,(520-len(lines)*fnt.size*1.32)/2,fnt,col)
        if kind=="mono":   # 황제의 목소리 표시
            dd2=ImageDraw.Draw(im); m="— 황제 —"; mf=FS(30); dd2.text(((W-dd2.textlength(m,font=mf))/2,(520-len(lines)*fnt.size*1.32)/2-50),m,font=mf,fill=(220,200,160))
        p=f"{tmp}c{len(ov):03d}.png"; im.save(p); ov.append((p,s0,s1))
    for v in json.load(open(VER)):
        if v["t1"]<=a or v["t0"]>=a+dd: continue
        s0=max(v["t0"],a)-a+T; s1=min(v["t1"],a+dd)-a+T
        im=Image.new("RGBA",(W,H),(0,0,0,0)); im.paste((0,0,0,95),(0,560,W,1380))
        vf=FM(76); ls=[]
        for ln in v["lines"]: ls+=wrap(ln,vf,900)
        y0=960-len(ls)*vf.size*1.4/2-40
        shadow_text(im,ls,y0,vf,GOLD,gap=1.4)
        shadow_text(im,["- "+v["src"]+" -"],y0+len(ls)*vf.size*1.4+30,FS(38),CREAM)
        pth=f"{tmp}v{len(vov):02d}.png"; im.save(pth); vov.append((pth,s0,s1))
    T+=dd
# 끝 카드
end=Image.new("RGBA",(W,H),(0,0,0,0)); de=ImageDraw.Draw(end)
end.paste((0,0,0,242),(0,0,W,H))
shadow_text(end,os.environ.get("ED_END1","그 밤의 일기는|본편에서 이어집니다").split("|"),720,FB(78),WHITE)
shadow_text(end,os.environ.get("ED_END2","▼ 아래 링크에서|12분 풀버전 보기").split("|"),990,FB(58),GOLD)
shadow_text(end,["매일 밤, 황제처럼 생각하라."],1250,FS(40),CREAM)
end.save(tmp+"end.png")
# 합성
ins=[]; fc=""
for i,(f,a,dd,cx) in enumerate(parts):
    ins+=["-i",f,"-ss",f"{a:.3f}","-t",f"{dd:.3f}","-i",AUD]
    x=int(max(0,min(1920-608,1920*cx-304)))
    if cx<0:   # 글자가 넓은 화면(인트로 타이틀 등): 자르지 않고 통째로, 뒤는 검정
        fc+=(f"[{2*i}:v]trim={a:.3f}:{a+dd:.3f},fps={FPS},crop=1200:1080:360:0,scale={W}:-2:flags=lanczos,pad={W}:{H}:0:(oh-ih)/2:black,setsar=1,setpts=PTS-STARTPTS[v{i}];")
    else:
        fc+=(f"[{2*i}:v]trim={a:.3f}:{a+dd:.3f},fps={FPS},crop=608:1080:{x}:0,scale={W}:{H}:flags=lanczos,setsar=1,setpts=PTS-STARTPTS[v{i}];")
    fc+=(""
         f"[{2*i+1}:a]asetpts=PTS-STARTPTS,afade=t=in:d=0.2,afade=t=out:st={dd-0.3:.3f}:d=0.3[a{i}];")
n=len(parts); k=2*n
fc+="".join(f"[v{i}][a{i}]" for i in range(n))+f"concat=n={n}:v=1:a=1[cv][ca];"
ins+=["-i",tmp+"top.png"]; fc+=f"[cv][{k}:v]overlay=0:0[o0];"; k+=1; last="o0"
for j,(p,s0,s1) in enumerate(ov):
    ins+=["-i",p]; fc+=f"[{last}][{k}:v]overlay=0:1150:enable='between(t,{s0:.3f},{s1:.3f})'[o{j+1}];"; last=f"o{j+1}"; k+=1
for j,(pth,s0,s1) in enumerate(vov):
    ins+=["-i",pth]; fc+=f"[{last}][{k}:v]overlay=0:0:enable='between(t,{s0:.3f},{s1:.3f})'[w{j}];"; last=f"w{j}"; k+=1
ins+=["-loop","1","-t",str(END),"-i",tmp+"end.png"]; e=k; k+=1
fc+=(f"[{last}]tpad=stop_mode=clone:stop_duration={END}[pad];[{e}:v]fps={FPS},format=rgba,fade=t=in:d=0.4:alpha=1,setpts=PTS+{T:.3f}/TB[endv];"
     f"[pad][endv]overlay=0:0:eof_action=pass,format=yuv420p[vo];[ca]apad=pad_dur={END},afade=t=out:st={T+0.2:.3f}:d={END-0.3}[ao]")
subprocess.run(["ffmpeg","-v","error","-y",*ins,"-filter_complex",fc,"-map","[vo]","-map","[ao]","-c:v","libx264","-preset","veryfast","-crf","20",
    "-c:a","aac","-b:a","192k","-ar","48000","-t",f"{T+END:.3f}","-movflags","+faststart",OUT+key+".mp4"],check=True)
subprocess.run(["rm","-rf",tmp]); print("완성",OUT+key+".mp4",round(T+END,1))
