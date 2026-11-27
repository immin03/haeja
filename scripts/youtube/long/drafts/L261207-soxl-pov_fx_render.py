"""povshot.py still name:t ...  |  povshot.py render outdir name ..."""
import sys, os, json, subprocess
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__)); FPS = 30; DUR = 8.0
CL = json.load(open('/home/claude/haeja/scripts/youtube/long/drafts/L261207-soxl-pov_clips.json', encoding='utf-8'))
def main():
    mode = sys.argv[1]
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox', '--force-device-scale-factor=1'])
        pg = b.new_page(viewport={'width': 1280, 'height': 720}); pg.goto('file://' + os.path.join(HERE, 'pov.html'))
        pg.evaluate('document.fonts.ready'); pg.wait_for_timeout(400); pg.evaluate('c=>setClips(c)', CL)
        if mode == 'still':
            os.makedirs('pst', exist_ok=True)
            for a in sys.argv[2:]:
                n, t = a.split(':'); pg.evaluate('([n,t])=>render(n,t)', [n, float(t)]); pg.screenshot(path=f'pst/{n}.jpg', type='jpeg', quality=80)
        else:
            out = sys.argv[2]; os.makedirs(out, exist_ok=True)
            for n in sys.argv[3:]:
                tmp = os.path.join(out, n + '.tmp.mp4')
                ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(FPS), '-c:v', 'mjpeg', '-i', '-', '-c:v', 'libx264', '-crf', '20', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', tmp], stdin=subprocess.PIPE)
                for f in range(int(DUR * FPS)):
                    pg.evaluate('([n,t])=>render(n,t)', [n, f / FPS]); ff.stdin.write(pg.screenshot(type='jpeg', quality=90))
                ff.stdin.close()
                if ff.wait() == 0: os.replace(tmp, os.path.join(out, n + '.mp4'))
        b.close()
main()
