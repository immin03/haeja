// 롱폼용 앱 화면 캡처: 체험 계정으로 로그인해 해당 회사 화면을 찍는다 (렌더 직전에 실행 → 화면 숫자도 최신)
// 사용: node scripts/youtube/long/capture_co.js <회사명> <출력 png> <종목코드>
const { chromium } = require('playwright');
const SITE = process.env.SITE || 'https://www.valuenote.co.kr';
const [name, out, code] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: 'ko-KR', timezoneId: 'Asia/Seoul' });
  const p = await ctx.newPage();
  await p.goto(SITE + '/?login', { waitUntil: 'networkidle' });
  await p.waitForSelector('#lg-email', { timeout: 60000 });
  await p.fill('#lg-email', 'demo@valuenote.app'); await p.fill('#lg-pw', 'valuenote'); await p.click('#lg-go');
  await p.waitForFunction(() => typeof S !== 'undefined' && S.loaded && S.loaded.c && (S2.screen || []).length > 100, null, { timeout: 90000 });
  await p.waitForTimeout(2500);
  await p.addStyleTag({ content: '.demo-bar{display:none!important}' });
  // 목록에서 그 회사를 펼친 상태(앱의 회사 상세)로 만든다
  await p.evaluate(([n, c]) => { S.tab = 'companies'; S.scope = 'all'; S.coMkt = 'ALL'; S.coMin = 0; S.coQ = n; S.coOpen = c; S.coShown = 30; render(); }, [name, code]);
  await p.waitForTimeout(3000);
  await p.evaluate(() => document.querySelectorAll('body *').forEach(e => { const cs = getComputedStyle(e); if (cs.position === 'fixed' || cs.position === 'sticky') e.style.setProperty('display', 'none', 'important'); }));
  const top = await p.evaluate(() => { const t = document.getElementById('coListTop'); return t ? t.getBoundingClientRect().top + window.scrollY : 0; });
  const full = await p.evaluate(() => document.documentElement.scrollHeight);
  await p.screenshot({ path: out, fullPage: true, clip: { x: 0, y: Math.max(0, top - 8), width: 390, height: Math.min(4200, full - top) } });
  console.log('캡처', name, code, out);
  // 밸류노트 소개 장면에서 번갈아 보여 줄 다른 화면들 (실패해도 본 캡처는 그대로 쓴다)
  const hideFixed = () => p.evaluate(() => document.querySelectorAll('body *').forEach(e => { const cs = getComputedStyle(e); if (cs.position === 'fixed' || cs.position === 'sticky') e.style.setProperty('display', 'none', 'important'); }));
  const extra = [
    ['list', () => { S.tab = 'companies'; S.coOpen = null; S.coQ = ''; S.scope = 'all'; S.coMkt = 'ALL'; S.coMin = 0; S.coShown = 30; render(); }],
    ['value', () => { S.tab = 'value'; S.vlSide = 'under'; render(); }],
    ['brief', () => { S.tab = 'briefing'; render(); }],
    ['port', () => { S.tab = 'portfolio'; render(); }],
  ];
  for (const [k, fn] of extra) {
    try {
      await p.evaluate(fn); await p.evaluate(() => window.scrollTo(0, 0)); await p.waitForTimeout(2500); await hideFixed();
      const h = await p.evaluate(() => document.documentElement.scrollHeight);
      if (h < 600) throw new Error('화면이 비어 있음');
      const o = out.replace(/\.png$/, '_' + k + '.png');
      await p.screenshot({ path: o, fullPage: true, clip: { x: 0, y: 0, width: 390, height: Math.min(3000, h) } });
      console.log('캡처', k, o);
    } catch (e) { console.error('추가 화면 실패:', k, e.message); }
  }
  await b.close();
})().catch(e => { console.error('캡처 실패:', e.message); process.exit(1); });
