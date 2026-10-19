// 매일 아침 이슈 카드뉴스 자동 생성 (GitHub Actions에서 실행)
// 1) 실서비스를 체험 계정으로 열어, 앱이 계산한 경제 레이더·기업 점수를 읽는다
// 2) 어제 대비 '적정 매수가 아래'로 새로 들어온 좋은 회사 수를 센다 (종목명은 카드에 쓰지 않음)
// 3) 레이더·브리핑 화면을 모바일 크기로 캡처하고 카드 5장을 그린다
// 4) social/daily/<날짜>/NN.jpg, social/daily/queue.json, social/daily/state.json 을 쓴다
//    → 커밋되면 Vercel이 배포하고, Supabase 예약 작업이 queue.json을 읽어 게시 대기열에 넣는다 (승인 후 게시)
// 로컬 테스트: LOCAL_SUPA=<supabase.js 경로> node scripts/daily_cards.js
const fs = require('fs'), path = require('path');
const { chromium } = require('playwright');

const SITE = process.env.SITE || 'https://www.valuenote.co.kr';
const ROOT = path.join(__dirname, '..');
const OUT = path.join(ROOT, 'social', 'daily');
const SUIT = path.join(ROOT, 'fonts', 'SUIT-Variable.woff2');
const HANDLE = '@value.note.korea';
const DISC = '*본 콘텐츠는 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아닙니다.';
const kst = new Date(Date.now() + 9 * 3600e3);
const ymd = kst.toISOString().slice(0, 10), tag = ymd.replace(/-/g, '');
const md = `${kst.getUTCMonth() + 1}월 ${kst.getUTCDate()}일`;
const MKT = { KR: '한국', US: '미국', JP: '일본', CN: '중국', HK: '홍콩' };
const SEC = { Technology: 'IT', 'Financial Services': '금융', Financials: '금융', Industrials: '산업재', 'Consumer Cyclical': '경기소비재', 'Consumer Defensive': '필수소비재', Healthcare: '헬스케어', 'Communication Services': '통신·미디어', Energy: '에너지', 'Basic Materials': '소재', Utilities: '유틸리티', 'Real Estate': '부동산' };

async function openApp() {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true, hasTouch: true, locale: 'ko-KR', timezoneId: 'Asia/Seoul' });
  if (process.env.LOCAL_SUPA) {   // 로컬 테스트용: CDN을 로컬 파일로 대체
    const css = `@font-face{font-family:'SUIT Variable';src:url(https://cdn.jsdelivr.net/suit.woff2) format('woff2');font-weight:100 900}`;
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
  await p.waitForFunction(() => typeof S !== 'undefined' && S.loaded && S.loaded.c && typeof scoredRows === 'function' && (S2.screen || []).length > 100, null, { timeout: 90000 });
  await p.waitForTimeout(3000);
  await p.addStyleTag({ content: '.demo-bar{display:none!important}' });
  return { b, p };
}

async function readData(p) {
  return p.evaluate(() => {
    const req = cfg().reqMOS ?? 30;
    const rows = scoredRows();
    const good = rows.filter(r => isNum(r.b) && r.b >= 75 && isNum(r.mos));
    const pass = good.filter(r => r.mos >= req), near = good.filter(r => r.mos >= req - 10 && r.mos < req);
    const R = S.radar || {}, lv = rdLevel(R);
    const ind = Object.values(R.ind || {});
    return {
      pass: pass.map(r => ({ c: r.code, m: r.m, s: r.s })), near: near.length, total: rows.length,
      radar: { headline: R.headline || '', level: lv == null ? null : RD_LV[lv].n, levelNote: lv == null ? '' : RD_LV[lv].s, warn: ind.filter(o => (o.lv || 0) >= 3).length, n: ind.length }
    };
  });
}

async function capture(p, dir) {
  const go = (t) => p.evaluate(t => { S.tab = t; render(); window.scrollTo(0, 0); }, t);
  await go('radar'); await p.waitForTimeout(1500); await p.screenshot({ path: path.join(dir, '_radar.png') });
  await go('briefing'); await p.waitForTimeout(1500); await p.screenshot({ path: path.join(dir, '_briefing.png') });
}

// ---------- 카드 그리기 (v2 템플릿과 같은 디자인, SUIT 단일 글꼴) ----------
const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const br = s => esc(s).replace(/\n/g, '<br>').replace(/\*\*(.+?)\*\*/g, '<em>$1</em>');
const CSS = `@font-face{font-family:SUIT;src:url(data:font/woff2;base64,${fs.readFileSync(SUIT).toString('base64')}) format('woff2');font-weight:100 900}
*{box-sizing:border-box;margin:0;padding:0}html,body{width:1080px;height:1350px}
body{font-family:SUIT,sans-serif;word-break:keep-all;overflow-wrap:break-word;-webkit-font-smoothing:antialiased}
.s{position:relative;width:1080px;height:1350px;overflow:hidden;background:radial-gradient(120% 80% at 50% 0%,#17283F 0%,#0E1B2E 55%,#0A1322 100%);color:#F3EEE3}
.top{position:absolute;left:84px;right:84px;top:64px;display:flex;justify-content:space-between;align-items:center;z-index:5}
.wm{font-weight:700;font-size:30px;letter-spacing:-.02em}.wm .ko{font-weight:600;font-size:24px;color:#8F9AAB;margin-left:14px;letter-spacing:.04em}.cta .wm .ko{color:#7A8394}.wm i{font-style:normal;color:#E2C489}.pg{color:#8F9AAB;font-size:26px}
em{font-style:normal;color:#E2C489}
.hook .body,.cta .body{position:absolute;left:84px;right:84px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:center}
.k{color:#E2C489;font-size:34px;font-weight:700;margin-bottom:34px}
.hook h1{font-size:84px;line-height:1.22;font-weight:800;letter-spacing:-.045em}
.hook .sub{margin-top:44px;font-size:40px;line-height:1.55;color:#C7CEDA;font-weight:500}
.swipe{position:absolute;left:84px;bottom:64px;font-size:28px;color:#E2C489;font-weight:700}
.chips{margin-top:40px;display:flex;flex-wrap:wrap;gap:16px}.chip{border:2px solid rgba(226,196,137,.5);border-radius:999px;padding:14px 26px;font-size:32px;font-weight:700;color:#F3EEE3}
.shot .head{position:absolute;left:84px;right:84px;top:140px;z-index:4}
.shot h2{font-size:58px;line-height:1.25;font-weight:800;letter-spacing:-.04em}
.shot .sub{margin-top:18px;font-size:34px;line-height:1.5;color:#C7CEDA;font-weight:500}
.phone{position:absolute;left:50%;transform:translateX(-50%);width:720px;border-radius:72px;background:#05080F;padding:20px;box-shadow:0 0 0 2px #2A3A52,0 40px 90px rgba(0,0,0,.55)}
.screen{position:relative;width:680px;border-radius:54px;overflow:hidden;background:#fff}.screen img{display:block;width:680px}
.cta{background:#F3EEE3;color:#0A1322}.cta .wm{color:#0A1322}.cta .wm i{color:#A8823F}.cta .pg{color:#7A8394}
.cta h2{font-size:76px;line-height:1.25;font-weight:800;letter-spacing:-.04em}.cta em{color:#A8823F}
.cta .sub{margin-top:36px;font-size:38px;line-height:1.55;color:#3A4558;font-weight:500}
.btn{margin-top:56px;display:inline-flex;align-self:flex-start;background:#0A1322;color:#F3EEE3;border-radius:999px;padding:26px 40px;font-size:34px;font-weight:700}
.handle{margin-top:28px;font-size:30px;color:#7A8394;font-weight:600}
.disc{position:absolute;left:84px;right:84px;bottom:60px;font-size:22px;color:#7A8394;line-height:1.5}`;
function cardHtml(c, i, n) {
  const top = `<div class="top"><span class="wm">Value<i>Note</i><b class="ko">밸류노트</b></span><span class="pg">${i + 1} / ${n}</span></div>`;
  if (c.kind === 'hook') return `<section class="s hook">${top}<div class="body">${c.k ? `<div class="k">${esc(c.k)}</div>` : ''}<h1>${br(c.t)}</h1>${c.s ? `<div class="sub">${br(c.s)}</div>` : ''}${c.chips ? `<div class="chips">${c.chips.map(x => `<span class="chip">${esc(x)}</span>`).join('')}</div>` : ''}</div>${i === 0 ? '<div class="swipe">넘겨서 보기 →</div>' : ''}</section>`;
  if (c.kind === 'cta') return `<section class="s cta">${top}<div class="body"><h2>${br(c.t)}</h2>${c.s ? `<div class="sub">${br(c.s)}</div>` : ''}<div class="btn">프로필 링크에서 확인하기</div><div class="handle">밸류노트 · ${HANDLE}</div></div><div class="disc">${esc(DISC)}</div></section>`;
  const sc = 680 / 390, headH = c.s ? 300 : 230, src = 'data:image/png;base64,' + fs.readFileSync(c.img).toString('base64');
  return `<section class="s shot">${top}<div class="head"><h2>${br(c.t)}</h2>${c.s ? `<div class="sub">${br(c.s)}</div>` : ''}</div>
    <div class="phone" style="top:${140 + headH}px"><div class="screen" style="height:${(c.h || 600) * sc}px"><img src="${src}" style="margin-top:${-(c.y || 0) * sc}px"></div></div></section>`;
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const dir = path.join(OUT, tag); fs.mkdirSync(dir, { recursive: true });
  const statePath = path.join(OUT, 'state.json');
  const state = fs.existsSync(statePath) ? JSON.parse(fs.readFileSync(statePath, 'utf8')) : {};
  const { b, p } = await openApp();
  const d = await readData(p);
  await capture(p, dir);
  await b.close();

  const prev = new Set(state.pass || []);
  const fresh = state.pass ? d.pass.filter(x => !prev.has(x.c)) : [];
  const left = state.pass ? state.pass.filter(c => !d.pass.some(x => x.c === c)).length : 0;
  const byMkt = Object.entries(fresh.reduce((a, x) => (a[MKT[x.m] || x.m] = (a[MKT[x.m] || x.m] || 0) + 1, a), {})).sort((a, b) => b[1] - a[1]);
  const bySec = Object.entries(fresh.reduce((a, x) => { const k = SEC[x.s]; if (k) a[k] = (a[k] || 0) + 1; return a; }, {})).sort((a, b) => b[1] - a[1]).slice(0, 3);
  const R = d.radar, head = (R.headline || '').replace(/\s+/g, ' ').trim();

  const cards = [
    { kind: 'hook', k: `${md} 아침 시장 브리핑`, t: head ? head.replace(/,\s*/, ',\n') : '오늘 시장,\n무엇이 바뀌었을까요?', s: R.level ? `지금 경기 신호는 **${R.level}**입니다.\n${R.levelNote}` : '' },
    { kind: 'shot', t: `경제 레이더 · ${R.level || '확인 중'}`, s: `지표 ${R.n}개 중 경고 이상 ${R.warn}개`, img: path.join(dir, '_radar.png'), y: 105, h: 580 },
    fresh.length
      ? { kind: 'hook', k: '어제와 비교하면', t: `적정 매수가 아래로\n**새로 들어온 좋은 회사 ${fresh.length}곳**`, s: '밸류노트 점수 75점 이상 회사 중, 어제는 비쌌고 오늘은 적정 주가보다 30% 이상 싸진 곳입니다.', chips: [...byMkt.map(([k, v]) => `${k} ${v}`), ...bySec.map(([k, v]) => `${k} ${v}`)] }
      : { kind: 'hook', k: '좋은 회사의 가격', t: `적정 매수가 아래\n좋은 회사 **${d.pass.length}곳**`, s: `근처까지 온 곳은 ${d.near}곳입니다.${left ? `\n어제보다 ${left}곳이 다시 비싸졌습니다.` : ''}` },
    { kind: 'shot', t: `적정 매수가 아래 ${d.pass.length}곳, 근처 ${d.near}곳`, s: '5개 시장 620개 기업을 매일 같은 기준으로 다시 봅니다.', img: path.join(dir, '_briefing.png'), y: 105, h: 580 },
    { kind: 'cta', t: '어떤 회사인지는\n**앱에서 확인**하세요', s: '종목 이름과 적정 가격, 점수 근거까지\n로그인 없이 볼 수 있습니다.' },
  ];
  const b2 = await chromium.launch(); const pg = await b2.newPage({ viewport: { width: 1080, height: 1350 } });
  const images = [];
  for (let i = 0; i < cards.length; i++) {
    await pg.setContent(`<!doctype html><html lang="ko"><head><meta charset="utf-8"><style>${CSS}</style></head><body>${cardHtml(cards[i], i, cards.length)}</body></html>`);
    await pg.evaluate(() => document.fonts.ready);
    const f = String(i + 1).padStart(2, '0') + '.jpg';
    await pg.screenshot({ path: path.join(dir, f), type: 'jpeg', quality: 92 });
    images.push(`/social/daily/${tag}/${f}`);
  }
  await b2.close();
  for (const f of fs.readdirSync(dir)) if (f.startsWith('_')) fs.unlinkSync(path.join(dir, f));

  const lines = [`${md} 아침 시장 브리핑입니다.`, ''];
  if (head) lines.push(`밤사이 가장 큰 소식은 "${head}"입니다.`);
  if (R.level) lines.push(`경제 레이더는 지금 '${R.level}' 단계입니다. 지표 ${R.n}개 중 ${R.warn}개에서 경고 이상의 신호가 나왔습니다.`);
  lines.push('');
  if (fresh.length) lines.push(`어제와 비교하면 좋은 회사 ${fresh.length}곳이 적정 매수가 아래로 새로 들어왔습니다.`, `시장별로는 ${byMkt.map(([k, v]) => `${k} ${v}곳`).join(', ')}입니다.` + (bySec.length ? ` 업종은 ${bySec.map(([k, v]) => `${k} ${v}곳`).join(', ')}이 많습니다.` : ''));
  else lines.push(`지금 적정 매수가 아래에 있는 좋은 회사는 ${d.pass.length}곳, 근처까지 온 곳은 ${d.near}곳입니다.`);
  lines.push('', '어떤 회사인지는 밸류노트에서 로그인 없이 확인할 수 있습니다.');
  const caption = lines.join('\n').slice(0, 430);

  const item = { id: 'D' + tag, seq: Number(tag), title: `${md} 시장 브리핑`, scheduled_at: `${ymd}T08:30:00+09:00`, caption,
    hashtags: ['주식뉴스', '오늘의시장', '가치투자', '주식공부', '밸류노트'], threads_tag: '주식뉴스', images, to_ig: false, music: '차분한 뉴스 브리핑 비트', approved: false };
  const qPath = path.join(OUT, 'queue.json');
  const q = (fs.existsSync(qPath) ? JSON.parse(fs.readFileSync(qPath, 'utf8')) : []).filter(x => x.id !== item.id).slice(-6);
  q.push(item); fs.writeFileSync(qPath, JSON.stringify(q, null, 1));
  fs.writeFileSync(statePath, JSON.stringify({ date: ymd, pass: d.pass.map(x => x.c) }));
  // 30일 지난 날짜 폴더는 지운다
  for (const f of fs.readdirSync(OUT)) if (/^\d{8}$/.test(f) && f < (new Date(Date.now() - 30 * 864e5 + 9 * 3600e3).toISOString().slice(0, 10).replace(/-/g, ''))) fs.rmSync(path.join(OUT, f), { recursive: true });
  console.log(JSON.stringify({ id: item.id, fresh: fresh.length, pass: d.pass.length, near: d.near, radar: R }, null, 1));
})();
