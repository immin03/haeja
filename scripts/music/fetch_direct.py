"""음악 시안 2차 (2026-11-07) — candidates2.json 의 CDN mp3를 받아 45초 미리듣기 + BPM 추정. 원본도 보관(렌더용)."""
import json, os, subprocess, urllib.request
import numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.abspath(os.path.join(HERE,"..",".."))
OUT=os.path.join(ROOT,"social","music","samples2"); os.makedirs(OUT,exist_ok=True)
UA={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36","Referer":"https://pixabay.com/"}
def bpm(path):
    try:
        raw=subprocess.run(["ffmpeg","-v","error","-i",path,"-t","60","-ac","1","-ar","11025","-f","s16le","-"],capture_output=True).stdout
        x=np.frombuffer(raw,np.int16).astype(np.float32); hop=256
        e=np.array([np.sum(x[i:i+hop]**2) for i in range(0,len(x)-hop,hop)]); o=np.maximum(0,np.diff(np.log1p(e))); o-=o.mean()
        ac=np.correlate(o,o,"full")[len(o)-1:]; fps=11025/hop; lags=np.arange(1,len(ac)); b=60*fps/lags; m=(b>=70)&(b<=150)
        return round(float(b[m][np.argmax(ac[1:][m])]))
    except Exception: return None
meta=[]
for c in json.load(open(os.path.join(HERE,"candidates2.json"),encoding="utf-8"))["tracks"]:
    m=dict(c); raw=os.path.join(OUT,c["key"]+"_full.mp3")
    try:
        open(raw,"wb").write(urllib.request.urlopen(urllib.request.Request(c["mp3"],headers=UA),timeout=60).read())
        dur=float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",raw],capture_output=True,text=True).stdout.strip() or 0)
        st=0 if c["role"]=="인트로" else min(25,max(0,dur-50))
        subprocess.run(["ffmpeg","-y","-v","error","-ss",str(st),"-t","45","-i",raw,"-af","afade=t=in:d=0.4,afade=t=out:st=42:d=3,loudnorm=I=-16:TP=-1.5","-b:a","128k",os.path.join(OUT,c["key"]+".mp3")],check=True)
        m.update(duration=round(dur,1),bpm=bpm(raw),file=f"social/music/samples2/{c['key']}.mp3",full=f"social/music/samples2/{c['key']}_full.mp3")
    except Exception as e: m["error"]=str(e)[:200]
    meta.append(m); print(c["key"], m.get("bpm"), m.get("duration"), m.get("error"), flush=True)
json.dump(meta,open(os.path.join(OUT,"meta.json"),"w",encoding="utf-8"),ensure_ascii=False,indent=1)
