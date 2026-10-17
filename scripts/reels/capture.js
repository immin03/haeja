// 릴스용 앱 화면 캡처 (체험 계정, 모바일 390px, 2배율, 전체 페이지)
// 사용: node scripts/reels/capture.js   → scripts/reels/screens/<이름>.png
// 로컬에서 CDN이 막혀 있으면 LOCAL_SUPA=<supabase.js 경로> 를 준다
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright');
const SITE = process.env.SITE || 'https://www.valuenote.co.kr';
const OUT = path.join(__dirname, 'screens');
const SUIT = path.join(__dirname, '..', '..', 'fonts', 'SUIT-Variable.woff2');

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: 'ko-KR', timezoneId: 'Asia/Seoul' });
  if (process.env.LOCAL_SUPA) {
    const css = `@font-face{font-family:'SUIT Variable';src:url(https://cdn.jsdelivr.net/suit.woff2) format('woff2');font-weight:100 900}@font-face{font-family:'Pretendard Variable';src:url(https://cdn.jsdelivr.net/suit.woff2) format('woff2');font-weight:100 900}`;
    await ctx.route('**/*', r => { const u = r.request().url();
      if (u.includes('supabase.min.js')) return r.fulfill({ path: process.env.LOCAL_SUPA, contentType: 'text/javascript' });
      if (u.endsWith('suit.woff2')) return r.fulfill({ path: SUIT, contentType: 'font/woff2' });
      if (u.includes('SUIT-Variable.css') || u.includes('pretendard') || u.includes('fonts.g')) return r.fulfill({ body: css, contentType: 'text/css' });
      return r.continue(); });
  }
  const p = await ctx.newPage();
  await p.goto(SITE + '/?login', { waitUntil: 'networkidle' });
  await p.waitForSelector('#lg-email', { timeout: 60000 });
  await p.fill('#lg-email', 'demo@valuenote.app'); await p.fill('#lg-pw', 'valuenote'); await p.click('#lg-go');
  await p.waitForFunction(() => typeof S !== 'undefined' && S.loaded && S.loaded.c && (S2.screen || []).length > 100, null, { timeout: 90000 });
  await p.waitForTimeout(3000);
  await p.addStyleTag({ content: '.demo-bar{display:none!important}' });
  const go = async (t) => { await p.evaluate(t => { S.tab = t; render(); window.scrollTo(0, 0); }, t); await p.waitForTimeout(1500); };
  // 화면을 다시 그릴 때 숨긴 고정 요소가 돌아오도록 render 후 새로 그린다
  const shot = async (name) => {
    await p.evaluate(() => document.querySelectorAll('body *').forEach(e => { const cs = getComputedStyle(e); if (cs.position === 'fixed' || cs.position === 'sticky') e.style.setProperty('display', 'none', 'important'); })); await p.screenshot({ path: path.join(OUT, name + '.png'), fullPage: true });
    // 릴스 대본에서 "find"로 강조 위치를 찾을 수 있게 블록별 글자·위치를 저장 (이미지 픽셀 기준, 2배율)
    const boxes = await p.evaluate(() => [...document.querySelectorAll('body *')].map(e => {
      const r = e.getBoundingClientRect(); const t = (e.innerText || '').replace(/\s+/g, ' ').trim();
      if (!t || r.width < 120 || r.height < 24 || r.height > 1400) return null;
      return { t: t.slice(0, 400), b: [r.left + scrollX, r.top + scrollY, r.right + scrollX, r.bottom + scrollY].map(v => Math.round(v * 2)) };
    }).filter(Boolean));
    fs.writeFileSync(path.join(OUT, name + '.json'), JSON.stringify(boxes));
    console.log('저장', name, boxes.length); };
  const clickText = async (txt) => { await p.getByText(txt, { exact: true }).first().click(); await p.waitForTimeout(1500); };

  for (const t of ['portfolio', 'companies', 'briefing', 'radar', 'trends', 'alerts', 'journal']) { await go(t); await shot(t); }
  await go('portfolio'); await clickText('내 등급'); await p.evaluate(() => window.scrollTo(0, 0)); await shot('level');
  await go('companies');
  await p.locator('.co-card, .card').filter({ hasText: '기준 통과' }).first().click().catch(() => {});
  await p.waitForTimeout(2000); await p.evaluate(() => window.scrollTo(0, 0)); await shot('company');
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
