// 은퇴 배당 비교 릴스 (2026-10-20 운영자 요청)
// "N년 전 은퇴하며 3억·5억을 배당주에 넣고 배당을 생활비로 썼다면 지금 매달 얼마를 받을까?"
// 실제 주가·배당 기록(야후)과 그때 환율로 계산한다. 결과가 밋밋한 묶음은 만들지 않는다(interest).
//
// 사용
//   node scripts/reels/div_race.mjs scan                  모든 후보를 계산해 divrace/scan.json 에 기록 (재미 판정 포함)
//   node scripts/reels/div_race.mjs pick YYYY-MM-DD HH:MM 그 칸이 비어 있으면, 아직 안 쓴 재미있는 묶음 하나로 대본 specs/D<yymmdd>.json
//   node scripts/reels/div_race.mjs one <key> [YYYY-MM-DD HH:MM]   특정 묶음 하나로 대본 (미리보기용, 기록 안 남김)
// 묶음 목록: scripts/reels/divrace/sets.json, 쓴 기록: scripts/reels/divrace/state.json
import fs from 'node:fs';
import path from 'node:path';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..', '..');
const DIR = path.join(ROOT, 'scripts', 'reels', 'divrace');
const SPECS = path.join(ROOT, 'scripts', 'reels', 'specs');
const YEARS = 5;
const FX = { USD: 'KRW=X', JPY: 'JPYKRW=X', CNY: 'CNYKRW=X', HKD: 'HKDKRW=X' };

// ── 데이터 ──────────────────────────────────────────────
const cache = {};
async function yahoo(sym, p1, p2) {
  const k = sym + p1;
  if (cache[k]) return cache[k];
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?period1=${p1}&period2=${p2}&interval=1d&events=div`;
  for (let a = 0; a < 3; a++) {
    try {
      const r = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0 (valuenote)' } });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      const res = (await r.json())?.chart?.result?.[0];
      if (!res) throw new Error('no result');
      const off = (res.meta?.gmtoffset ?? 0) * 1000;
      const day = (t) => new Date(t * 1000 + off).toISOString().slice(0, 10);
      const q = res.indicators?.quote?.[0]?.close || [];
      const px = [];
      (res.timestamp || []).forEach((t, i) => { if (typeof q[i] === 'number' && isFinite(q[i]) && q[i] > 0) px.push([day(t), q[i]]); });
      const dv = Object.values(res.events?.dividends || {}).map((e) => [day(e.date), e.amount]).filter((e) => e[1] > 0).sort((a, b) => (a[0] < b[0] ? -1 : 1));
      return (cache[k] = { px, dv, cur: res.meta?.currency });
    } catch (e) {
      if (a === 2) throw new Error(`${sym}: ${e.message}`);
      await new Promise((r) => setTimeout(r, 1500 * (a + 1)));
    }
  }
}
const at = (px, d) => { // d 이전(포함) 마지막 값
  let lo = 0, hi = px.length - 1, r = null;
  while (lo <= hi) { const m = (lo + hi) >> 1; if (px[m][0] <= d) { r = px[m][1]; lo = m + 1; } else hi = m - 1; }
  return r ?? px[0][1];
};
const addMonths = (ym, k) => { const [y, m] = ym.split('-').map(Number); const t = y * 12 + m - 1 + k; return `${Math.floor(t / 12)}-${String(t % 12 + 1).padStart(2, '0')}`; };
const monthEnd = (ym) => { const [y, m] = ym.split('-').map(Number); return new Date(Date.UTC(y, m, 0)).toISOString().slice(0, 10); };
const minusYear = (d) => `${Number(d.slice(0, 4)) - 1}${d.slice(4)}`;

async function simulate(set, today) {
  const startYm = addMonths(today.slice(0, 7), -12 * YEARS);
  const p1 = Math.floor(Date.parse(addMonths(startYm, -14) + '-01') / 1000), p2 = Math.floor(Date.now() / 1000) + 86400;
  const money = set.money; // 만 원
  const months = [];
  for (let ym = startYm; ym <= today.slice(0, 7); ym = addMonths(ym, 1)) months.push(ym);
  const out = [];
  for (const it of set.items) {
    const d = await yahoo(it.sym, p1, p2);
    const fx = it.cur === 'KRW' ? null : await yahoo(FX[it.cur], p1, p2);
    if (d.cur && d.cur !== it.cur) throw new Error(`${it.sym}: 통화 ${d.cur} ≠ ${it.cur}`);
    const rate = (day) => (fx ? at(fx.px, day) : 1);
    const first = d.px.find((p) => p[0] >= startYm + '-01');
    if (!first || first[0] > monthEnd(startYm)) throw new Error(`${it.sym}: ${startYm} 주가 없음`);
    const buy = first[0], p0 = first[1];
    const shares = (money * 1e4) / (p0 * rate(buy));
    // 1년 배당 = 최근 '1년에 주는 횟수'만큼의 배당 합 (지급일이 며칠 밀려 1년 창에 5번·3번 잡히는 들쭉날쭉을 없앤다)
    const ttm = (day) => {
      const past = d.dv.filter((e) => e[0] <= day);
      const two = past.filter((e) => e[0] > minusYear(minusYear(day))).length;
      const freq = Math.max(1, Math.min(12, Math.round(two / 2) || past.filter((e) => e[0] > minusYear(day)).length));
      const recent = past.filter((e) => e[0] > minusYear(minusYear(day)));
      return recent.slice(-freq).reduce((s, e) => s + e[1], 0);
    };
    const inc = [], val = [], cum = [], x = [];
    months.forEach((ym, i) => {
      const day = i === 0 ? buy : (i === months.length - 1 ? today : monthEnd(ym));
      x.push(ym.replace('-', '.'));
      inc.push(shares * ttm(day) * rate(day) / 12 / 1e4);
      val.push(shares * at(d.px, day) * rate(day) / 1e4);
      cum.push(d.dv.filter((e) => e[0] > buy && e[0] <= day).reduce((s, e) => s + shares * e[1] * rate(e[0]), 0) / 1e4);
    });
    const yStart = ttm(buy) / p0, last = at(d.px, today), yEnd = ttm(today) / last;
    const nDiv = d.dv.filter((e) => e[0] > buy).length;
    out.push({ ...it, buy, x, inc, val, cum, yStart, yEnd, growth: ttm(buy) > 0 ? ttm(today) / ttm(buy) : null, priceRet: last / p0 - 1, nDiv });
  }
  return { key: set.key, theme: set.theme, money, start: startYm, today, series: out, ...judge(out) };
}

// ── 재미 판정: 운영자 "드라마틱하지 않은 결과는 하지 마" ──
function judge(S) {
  const f = (k) => S.map((s) => s[k][s[k].length - 1]);
  const inc = f('inc'), val = f('val'), cum = f('cum');
  const bad = S.filter((s) => s.nDiv < 3 || (s.growth && (s.growth < 0.5 || s.growth > 6)) || !(s.yEnd > 0.003 && s.yEnd < 0.2) || !(s.yStart > 0.003 && s.yStart < 0.25)).map((s) => s.name);
  const r = (a) => Math.max(...a) / Math.max(1e-9, Math.min(...a));
  const iMax = inc.indexOf(Math.max(...inc)), vMax = val.indexOf(Math.max(...val));
  const incR = r(inc), valR = r(val), cumR = r(cum), reversal = iMax !== vMax;
  const interest = !bad.length && (incR >= 1.7 || (valR >= 1.5 && incR >= 1.3) || (reversal && incR >= 1.4 && valR >= 1.3));
  const score = Math.round((Math.max(incR - 1, valR - 1, (cumR - 1) * 0.6) + (reversal ? 0.3 : 0)) * 100) / 100;
  return { incR: +incR.toFixed(2), valR: +valR.toFixed(2), cumR: +cumR.toFixed(2), reversal, interest, score, bad };
}

// ── 한국어 도우미 ────────────────────────────────────────
const LAT_B = new Set(['L', 'M', 'N', 'R']), DIG_B = new Set(['0', '1', '3', '6', '7', '8']);
function batchim(w) {
  const c = w.trim().slice(-1);
  const code = c.charCodeAt(0);
  if (code >= 0xac00 && code <= 0xd7a3) return (code - 0xac00) % 28 !== 0;
  if (/[A-Za-z]/.test(c)) return LAT_B.has(c.toUpperCase());
  if (/\d/.test(c)) return DIG_B.has(c);
  return false;
}
const jo = (w, a, b) => w + (batchim(w) ? a : b); // jo('KB금융','은','는')
const ro = (w) => w + (batchim(w) && !/[ㄹ]$/.test(w) && !w.endsWith('일') ? '으로' : '로');
function won(v) { // 만 원 → "1억 5,300만 원" / "418만 원"
  v = Math.round(v);
  if (Math.abs(v) >= 10000) {
    const e = Math.floor(v / 10000), m = Math.round((v % 10000) / 100) * 100;
    return `${e}억` + (m ? ` ${m.toLocaleString('en-US')}만` : '') + ' 원';
  }
  return `${v.toLocaleString('en-US')}만 원`;
}
const wonBar = (v) => (Math.abs(v) >= 10000 ? `${(Math.round(v / 1000) / 10).toFixed(1).replace(/\.0$/, '')}억 원` : `${Math.round(v).toLocaleString('en-US')}만 원`);
const eok = (money) => `${money / 10000}억`;
const pct = (x) => (Math.round(x * 1000) / 10).toFixed(1).replace(/\.0$/, '');
const times = (x) => (Math.round(x * 10) / 10).toFixed(1).replace(/\.0$/, '');
const sayName = (s) => s.say || s.name;
const readLen = (t) => t.replace(/\s/g, '').length * 0.17 / 1.1 + 0.12;

// ── 대본 ────────────────────────────────────────────────
function buildSpec(R, id, when) {
  const S = R.series, N = YEARS, M = eok(R.money), n = S[0].x.length;
  const last = (s, k) => s[k][s[k].length - 1];
  const byInc = [...S].sort((a, b) => last(b, 'inc') - last(a, 'inc'));
  const A = byInc[0], Z = byInc[byInc.length - 1];
  const V = [...S].sort((a, b) => last(b, 'val') - last(a, 'val'))[0];
  const C = [...S].sort((a, b) => last(b, 'cum') - last(a, 'cum'))[0];
  const order = [A, ...S.filter((s) => s !== A)]; // 금색 = 1등
  const L0 = [...S].sort((a, b) => b.inc[0] - a.inc[0])[0];
  // 말풍선: 1등이 앞지른 달, 또는 둥근 금액을 넘은 달
  const events = [];
  let cross = -1;
  if (L0 !== A) for (let i = 1; i < n; i++) if (A.inc[i] > L0.inc[i] && A.inc[i - 1] <= L0.inc[i - 1]) cross = i;
  if (cross > 0) events.push({ i: cross, j: 0, text: `${A.name}, ${L0.name} 추월!` });
  const mile = [50, 100, 200, 300, 500, 1000, 2000].filter((m) => A.inc[0] < m && last(A, 'inc') >= m).pop();
  if (mile) { const i = A.inc.findIndex((v) => v >= mile); if (i > 0 && Math.abs(i - cross) > 10) events.push({ i, j: 0, text: `${A.name} 월 ${mile}만 원 돌파!` }); }

  const ln = (cap, say) => (say ? { cap, say } : { cap });
  const scenes = [];
  scenes.push({ type: 'hook', top: `은퇴하며 ${M},\n${R.theme}에 넣었다면?`, num: { to: Math.round(last(A, 'inc')), fmt: 'won' }, tone: 'gold',
    label: `${A.name}, ${N}년 뒤 매달 받는 배당`, lines: [
      ln([`${N}년 전 ${M} 원을`, `${R.theme}에 넣었다면?`]),
      ln([`${jo(A.name, '은', '는')} 지금`, `매달 ${won(last(A, 'inc'))}을 줍니다`], `${jo(sayName(A), '은', '는')} 지금 매달 ${won(last(A, 'inc'))}을 줍니다`)] });

  const raceLines = [ln([`회사마다 ${M} 원씩 넣고`, '배당은 생활비로 썼습니다'])];
  const gA = A.growth;
  let twist = null;
  if (cross > 0) twist = ln([`처음엔 ${jo(L0.name, '이', '가')} 가장 많았지만`, `${jo(A.name, '이', '가')} 앞질렀습니다`], `처음엔 ${jo(sayName(L0), '이', '가')} 가장 많았지만 ${jo(sayName(A), '이', '가')} 앞질렀습니다`);
  else if (gA && gA >= 1.3) twist = ln([`${A.name}의 1주당 배당은`, `${N}년 동안 ${times(gA)}배가 됐습니다`], `${sayName(A)}의 1주당 배당은 ${N}년 동안 ${times(gA)}배가 됐습니다`);
  if (twist) raceLines.push(twist);
  raceLines.push(ln([`${jo(Z.name, '은', '는')} 같은 돈으로`, `매달 ${won(last(Z, 'inc'))}입니다`], `${jo(sayName(Z), '은', '는')} 같은 돈으로 매달 ${won(last(Z, 'inc'))}입니다`));
  scenes.push({ type: 'race', x: S[0].x, money: R.money, ylab: '매달 받는 배당 (세전)', events,
    series: order.map((s) => ({ name: s.name, inc: s.inc.map((v) => +v.toFixed(1)), val: s.val.map((v) => Math.round(v)), cum: s.cum.map((v) => Math.round(v)) })), lines: raceLines });

  const tone = (s, k) => (s === order[0] ? 'gold' : (k === 'val' && last(s, 'val') < R.money ? 'loss' : 'gray'));
  if (C !== A || V !== A) scenes.push({ type: 'bars', title: `${N}년 동안 받은 배당`, items: [...S].sort((a, b) => last(b, 'cum') - last(a, 'cum')).map((s) => ({ label: s.name, v: Math.round(last(s, 'cum')), text: wonBar(last(s, 'cum')), tone: tone(s, 'cum') })),
    lines: [ln([`${N}년 동안 가장 많이 받은 곳은`, `${C.name}, ${won(last(C, 'cum'))}입니다`], `${N}년 동안 가장 많이 받은 곳은 ${sayName(C)}, ${won(last(C, 'cum'))}입니다`)] });

  const valLines = V === A
    ? [ln([`${jo(A.name, '은', '는')} 원금도 1등으로`, `${jo(won(last(A, 'val')), '이', '가')} 됐습니다`], `${jo(sayName(A), '은', '는')} 원금도 1등으로 ${jo(won(last(A, 'val')), '이', '가')} 됐습니다`)]
    : [ln([`원금은 ${jo(V.name, '이', '가')}`, `${ro(won(last(V, 'val')))} 가장 많습니다`], `원금은 ${jo(sayName(V), '이', '가')} ${ro(won(last(V, 'val')))} 가장 많습니다`),
       ln(['배당이 가장 많은 회사가', '원금까지 이기지는 않았습니다'])];
  scenes.push({ type: 'bars', title: `${M} 원은 지금 얼마일까`, items: [...S].sort((a, b) => last(b, 'val') - last(a, 'val')).map((s) => ({ label: s.name, v: Math.round(last(s, 'val')), text: wonBar(last(s, 'val')), tone: tone(s, 'val') })), lines: valLines });

  // 전: 차이를 만든 원리 하나 (처음 산 가격 = 배당수익률 / 배당이 자라는 속도)
  const yTop = [...S].sort((a, b) => b.yStart - a.yStart)[0];
  const gTop = [...S].filter((s) => s.growth).sort((a, b) => b.growth - a.growth)[0];
  const byPrice = yTop === A || !(gTop === A && gA >= 1.3);
  if (byPrice) {
    scenes.push({ type: 'statement', l1: '차이를 만든 건', l2: '처음 산 가격', tone: 'gold', say: '차이를 만든 것은 처음 산 가격이었습니다.' });
    scenes.push({ type: 'compare', title: `${N}년 전 배당수익률`, l: { label: A.name, v: pct(A.yStart) + '%', sub: '1년 배당 나누기 주가', tone: 'gold' }, r: { label: Z.name, v: pct(Z.yStart) + '%', sub: '1년 배당 나누기 주가', tone: 'gray' },
      lines: [ln(['배당수익률은 1년 배당을', '주가로 나눈 값입니다']), ln(['같은 회사도 싸게 살수록', '매달 받는 돈이 커집니다'])] });
  } else {
    scenes.push({ type: 'statement', l1: '차이를 만든 건', l2: '배당이 늘어난 속도', tone: 'gold', say: '차이를 만든 것은 배당이 늘어난 속도였습니다.' });
    scenes.push({ type: 'compare', title: `${N}년 동안 1주당 배당`, l: { label: A.name, v: times(gA) + '배', sub: `${N}년 전보다`, tone: 'gold' }, r: { label: Z.name, v: times(Z.growth || 1) + '배', sub: `${N}년 전보다`, tone: 'gray' },
      lines: [A.yStart < Z.yStart ? ln(['처음 배당수익률이 낮아도', '배당이 자라면 결과가 바뀝니다']) : ln(['같은 돈을 넣어도 배당이 늘면', '매달 받는 돈이 계속 커집니다']), ln(['그래서 배당이 자랄 회사를', '적정한 가격에 사야 합니다'])] });
  }
  scenes.push({ type: 'cta', l1: '배당주의 적정 주가는', l2: '밸류노트에서', lines: [{ say: '배당주의 적정 주가는 밸류노트에서 확인하세요.' }] });

  // 길이: 40초를 넘지 않게 덜 중요한 문장부터 뺀다
  const est = () => scenes.reduce((t, sc) => t + (sc.lines || [{ say: sc.say }]).reduce((u, l) => u + readLen(l.say || (l.cap || []).join(' ')), 0.1) + (sc.type === 'statement' ? 0.6 : 0.25), 0);
  if (est() > 36 && valLines.length > 1) valLines.pop();
  if (est() > 36 && twist) raceLines.splice(1, 1);

  const dots = ['🟡', '🟢', '🔵', '🟣'];
  const caption = [
    `은퇴하며 ${M} 원을 ${R.theme}에 넣었다면, 지금 매달 얼마를 받을까요?`,
    `${R.start.replace('-', '년 ').replace(/^(\d+년 )0?/, '$1')}월에 ${M} 원씩 사서 배당은 매달 생활비로 썼다고 계산했습니다 (${N}년).`,
    order.map((s, i) => `${dots[i]} ${s.name}: 지금 매달 ${won(last(s, 'inc'))} · ${N}년간 받은 배당 ${won(last(s, 'cum'))} · 원금 ${M} 원이 ${won(last(s, 'val'))}`).join('\n'),
    V === A ? `${jo(A.name, '은', '는')} 매달 받는 배당도, 원금도 가장 많이 불었습니다.` : `매달 받는 배당은 ${A.name}, 원금을 가장 키운 건 ${jo(V.name, '이었', '였')}습니다.`,
    byPrice
      ? `차이를 만든 건 처음 산 가격이었습니다. ${A.name}의 ${N}년 전 배당수익률(1년 배당 ÷ 주가)은 ${pct(A.yStart)}%, ${jo(Z.name, '은', '는')} ${pct(Z.yStart)}%였습니다. 같은 회사도 싸게 살수록 매달 받는 돈이 커집니다.`
      : `차이를 만든 건 배당이 늘어난 속도였습니다. ${A.name}의 1주당 배당은 ${N}년 동안 ${times(gA)}배, ${jo(Z.name, '은', '는')} ${times(Z.growth || 1)}배가 됐습니다.`,
    '밸류노트는 버핏·그레이엄 방식으로 배당주의 적정 주가를 계산하고, 적정 매수가에 오면 알려 드립니다. 은퇴 계좌에 담을 배당주가 지금 적당한 가격인지 프로필 링크에서 확인하세요.',
    `※ ${S[0].buy} 매수 가정, 실제 주가·배당 기록으로 계산한 시뮬레이션입니다. 세전 기준, 배당 재투자 없음, 해외 주식은 그때 환율로 원화 환산. 매달 받는 배당은 그 시점 1년 배당 ÷ 12입니다.`,
  ].join('\n\n');

  return { id, title: `은퇴 배당 비교 · ${R.theme}에 ${M} 넣었다면`, tag: '은퇴 배당 비교', scheduled_at: when, mood: 'calm', broll: 'money', cover: 'race',
    caption, hashtags: ['배당주', '은퇴', '월배당', R.theme.replace(/[\s·]/g, ''), '밸류노트'], threads_tag: '배당주', scenes,
    data: { key: R.key, start: S[0].buy, today: R.today, method: 'yahoo v8 chart close + dividends, FX at date', judge: { incR: R.incR, valR: R.valR, reversal: R.reversal, score: R.score } } };
}

// ── 실행 ────────────────────────────────────────────────
const kst = () => new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);
const sets = JSON.parse(fs.readFileSync(path.join(DIR, 'sets.json'), 'utf8')).sets;
const statePath = path.join(DIR, 'state.json');
const state = fs.existsSync(statePath) ? JSON.parse(fs.readFileSync(statePath, 'utf8')) : { used: [] };
const [cmd, a1, a2] = process.argv.slice(2);

if (cmd === 'scan') {
  const rows = [];
  for (const set of sets) {
    try {
      const R = await simulate(set, kst());
      const last = (s, k) => Math.round(s[k][s[k].length - 1]);
      rows.push({ key: set.key, theme: set.theme, money: set.money, interest: R.interest, score: R.score, incR: R.incR, valR: R.valR, reversal: R.reversal, bad: R.bad,
        series: R.series.map((s) => ({ name: s.name, buy: s.buy, inc: last(s, 'inc'), val: last(s, 'val'), cum: last(s, 'cum'), yStart: pct(s.yStart), yEnd: pct(s.yEnd), growth: s.growth && times(s.growth), nDiv: s.nDiv })) });
      fs.mkdirSync(path.join(DIR, 'data'), { recursive: true });
      fs.writeFileSync(path.join(DIR, 'data', set.key + '.json'), JSON.stringify(R));
      console.log(set.key, R.interest ? '재미있음' : '밋밋함', R.score, JSON.stringify(R.bad));
    } catch (e) { rows.push({ key: set.key, error: e.message }); console.log(set.key, '오류', e.message); }
  }
  fs.writeFileSync(path.join(DIR, 'scan.json'), JSON.stringify({ date: kst(), rows }, null, 1));
} else if (cmd === 'pick' || cmd === 'one') {
  const ymd = (cmd === 'pick' ? a1 : a2) || kst(), hm = (cmd === 'pick' ? a2 : process.argv[5]) || '18:00';
  const when = `${ymd}T${hm}:00+09:00`, id = 'D' + ymd.replace(/-/g, '').slice(2);
  if (cmd === 'pick') {
    const taken = fs.readdirSync(SPECS).filter((f) => f.endsWith('.json')).some((f) => { try { return JSON.parse(fs.readFileSync(path.join(SPECS, f), 'utf8')).scheduled_at === when; } catch (_) { return false; } });
    if (taken) { console.log('이미 릴스 있음', when); process.exit(0); }
  }
  const cand = cmd === 'one' ? sets.filter((s) => s.key === a1) : sets.filter((s) => !state.used.some((u) => u.key === s.key));
  let made = null;
  for (const set of cand) {
    try {
      const cached = path.join(DIR, 'data', set.key + '.json');
      const R = process.env.DIVRACE_CACHE && fs.existsSync(cached) ? { ...JSON.parse(fs.readFileSync(cached, 'utf8')), ...judge(JSON.parse(fs.readFileSync(cached, 'utf8')).series) } : await simulate(set, kst());  // DIVRACE_CACHE=1: 점검 때 받아 둔 기록으로 (로컬 미리보기)
      R.series = R.series.map((x) => ({ ...x, ...set.items.find((i) => i.sym === x.sym) }));
      if (cmd === 'pick' && !R.interest) { console.log('밋밋해서 건너뜀', set.key, R.score); continue; }
      const spec = buildSpec(R, id, when);
      fs.writeFileSync(path.join(SPECS, id + '.json'), JSON.stringify(spec, null, 1));
      made = { id, key: set.key, score: R.score, interest: R.interest };
      break;
    } catch (e) { console.log('오류', set.key, e.message); }
  }
  if (!made) {
    console.log('만들 묶음 없음');
    if (cmd === 'pick') fs.writeFileSync(path.join(ROOT, 'social', 'reels', 'low_divrace.txt'), `은퇴 배당 비교: 남은 재미있는 묶음이 없습니다 (${ymd}). sets.json 에 새 묶음을 넣거나 기간을 바꿔 주세요.\n`);
    process.exit(0);
  }
  if (cmd === 'pick') {
    state.used.push({ key: made.key, id, date: ymd, score: made.score });
    fs.writeFileSync(statePath, JSON.stringify(state, null, 1));
    const left = sets.filter((s) => !state.used.some((u) => u.key === s.key)).length;
    if (left <= 2) fs.writeFileSync(path.join(ROOT, 'social', 'reels', 'low_divrace.txt'), `은퇴 배당 비교 후보가 ${left}개 남았습니다 (${ymd})\n`);
  }
  console.log(JSON.stringify(made));
} else {
  console.log('사용: node scripts/reels/div_race.mjs scan | pick YYYY-MM-DD HH:MM | one <key> [YYYY-MM-DD HH:MM]');
}
