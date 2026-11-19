# r180 ④ (대표 2026-11-19 16:40): 렌더 뒤 8초 간격 장면 시트로 코드 화면 고정·여백·이름표·자막 겹침·빈 화면을 눈으로 확인한다.
# 사용: python3 scripts/youtube/long/sheet.py <video.mp4> <out_dir> [간격초=8]
#  → out_dir/sheet_01.jpg … (한 장에 4×4 = 16칸, 칸마다 왼쪽 위에 영상 시각) · 안내선: 노란 가로선 = 자막 영역(아래 18%) 윗선, 세로선 = 좌우 6%
import os, subprocess, sys


def main():
    v, out = sys.argv[1], sys.argv[2]; step = float(sys.argv[3]) if len(sys.argv) > 3 else 8.0
    os.makedirs(out, exist_ok=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", v], capture_output=True, text=True).stdout.strip())
    n = int(dur // step) + 1; per = 16
    for k in range(0, n, per):
        t0 = k * step; frames = min(per, n - k)
        vf = (f"fps=1/{step},drawtext=text='%{{pts\\:hms\\:{t0:.2f}}}':x=12:y=12:fontsize=34:fontcolor=yellow:box=1:boxcolor=black@0.6:boxborderw=6,"
              "drawbox=x=0:y=ih*0.82:w=iw:h=3:color=yellow@0.7:t=fill,drawbox=x=iw*0.06:y=0:w=2:h=ih:color=yellow@0.5:t=fill,"
              "drawbox=x=iw*0.94:y=0:w=2:h=ih:color=yellow@0.5:t=fill,scale=640:-1,tile=4x4")
        o = os.path.join(out, f"sheet_{k // per + 1:02d}.jpg")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t0:.2f}", "-i", v, "-t", f"{frames * step:.2f}", "-vf", vf, "-frames:v", "1", o], check=True)
        print(o)


if __name__ == "__main__":
    main()
