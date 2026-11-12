// node cap.js still|video <mode> <seconds or t> <out>
const { chromium } = require('playwright'); const { spawn } = require('child_process'); const fs = require('fs');
(async () => {
  const [kind, mode, val, out, focus] = process.argv.slice(2);
  const b = await chromium.launch(); const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto('http://127.0.0.1:8765/globe.html'); await p.waitForFunction('window.ready===true', null, { timeout: 60000 }); if (focus) await p.evaluate(f => { const o = JSON.parse(f); if (o.cfg) window.CFG = o.cfg; if (o.HOOK_OFF !== undefined) window.HOOK_OFF = o.HOOK_OFF; if (o.focus) window.FOCUS = o.focus; else if (o.ll) window.FOCUS = o; }, focus);
  const grab = async t => { const d = await p.evaluate(([m, t]) => { draw(m, t); return document.getElementById('c').toDataURL('image/jpeg', 0.92); }, [mode, t]); return Buffer.from(d.split(',')[1], 'base64'); };
  if (kind === 'still') { fs.writeFileSync(out, await grab(+val)); }
  else {
    const fps = 24, n = Math.round(+val * fps);
    const ff = spawn('ffmpeg', ['-v', 'error', '-y', '-f', 'image2pipe', '-r', String(fps), '-i', '-', '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '18', '-pix_fmt', 'yuv420p', out], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let i = 0; i < n; i++) { const buf = await grab(i / fps); if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r)); }
    ff.stdin.end(); await new Promise(r => ff.on('close', r));
  }
  await b.close();
})();
