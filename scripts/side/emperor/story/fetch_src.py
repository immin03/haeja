"""python3 fetch_src.py <epid> — 장면 원본을 src/ 로 모은다 (저장소 → 없으면 Storage)"""
import os, subprocess, sys, shutil, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from specs import EP
HERE = os.path.dirname(os.path.abspath(__file__)); SRC = HERE + "/src/"; os.makedirs(SRC, exist_ok=True)
ROOT = "/home/claude/haeja"; PX = ROOT + "/_long/px2/src/"
def want(e):
    out = []
    for k, line, src, img, mv in EP[e]["sc"]:
        if src.startswith("@"): out.append([src[1:]])
        else: out.append([src + "_v.mp4"] if mv else [src + ".jpeg", src + ".png"])
    return out
def get(name):
    if os.path.exists(SRC + name) and os.path.getsize(SRC + name) > 5000: return True
    if os.path.exists(PX + name): shutil.copy(PX + name, SRC + name); return True
    r = subprocess.run(["git", "-C", ROOT, "show", f"origin/main:social/side/gen/{name}"], capture_output=True)
    if r.returncode == 0 and len(r.stdout) > 5000: open(SRC + name, "wb").write(r.stdout); return True
    for base in ("https://msjbrwyzkiueqnzjeicm.supabase.co/storage/v1/object/public/media/social/side/gen/", "https://www.valuenote.co.kr/social/side/gen/"):
        try:
            d = urllib.request.urlopen(base + name, timeout=60).read()
            if len(d) > 5000: open(SRC + name, "wb").write(d); return True
        except Exception: pass
    return False
miss = []
for alts in want(sys.argv[1]):
    if not any(get(a) for a in alts): miss.append(alts[0])
print("missing:", miss or "none")
