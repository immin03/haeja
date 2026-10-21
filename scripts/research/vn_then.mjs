// 과거 시점 밸류노트 점수: 회사 IR 연간 숫자로 그때의 스크리너 행을 다시 만들고, 지금과 같은 scoreRow 로 채점한다.
// screen-build/index.ts 의 compute() 와 같은 식을 쓴다 (5개 연도 창, EBIT = 세전이익 + 이자비용, 투하자본 = 자기자본 + 차입금).
// 사용: node scripts/research/vn_then.mjs <now.json> <in1.json> [in2.json ...] > out.json
//   in.json = { ticker, fy: { FY2015: {revenue, gross, ni, eps, equity, bps, ocf, capex, debt, ltDebt, interest, pretax, tax, curAssets, curLiab, shares, dps}, ... },
//               prices: { "2019-07-31": {close}, "2020-08-28": {close} } }  (금액은 백만 엔, 주당 값은 엔)
import fs from 'node:fs';
import { scoreRow, setSettings } from '../../supabase/functions/watch-select/scoring.js';
setSettings({});
const rnd = (x, d = 2) => (x === null || x === undefined || !isFinite(x) ? null : Math.round(x * 10 ** d) / 10 ** d);
const cagr = (a, b, y) => (a == null || b == null || a <= 0 || b <= 0 || y <= 0 ? null : (Math.pow(b / a, 1 / y) - 1) * 100);
const isNum = (v) => typeof v === 'number' && isFinite(v);

function rowAt(base, fy, years, px) {
  const Y = years.map((y) => fy[y] || {});
  const s = (k) => Y.map((o) => (isNum(o[k]) ? o[k] : null));
  const nz = (xs) => xs.filter((x) => x !== null);
  const last = (xs) => { for (let i = xs.length - 1; i >= 0; i--) if (xs[i] !== null) return xs[i]; return null; };
  const ni = s('ni'), rev = s('revenue'), gp = s('gross'), eps = s('eps'), eq = s('equity'), sh = s('shares');
  const ebit = Y.map((o) => (isNum(o.pretax) ? o.pretax + (isNum(o.interest) ? Math.abs(o.interest) : 0) : null));
  const ie = s('interest'), debt = s('debt'), ltd = Y.map((o) => (isNum(o.ltDebt) ? o.ltDebt : isNum(o.debt) ? o.debt : null));
  const taxr = Y.map((o) => (isNum(o.tax) && isNum(o.pretax) && o.pretax > 0 ? Math.abs(o.tax) / o.pretax : null));
  const invcap = Y.map((o) => (isNum(o.equity) && isNum(o.debt) ? o.equity + o.debt : null));
  const fcf = Y.map((o) => (isNum(o.ocf) && isNum(o.capex) ? o.ocf - Math.abs(o.capex) : null));
  const capex = Y.map((o) => (isNum(o.capex) ? -Math.abs(o.capex) : null));
  const ca = s('curAssets'), cl = s('curLiab');
  const f = {};
  const roes = []; for (let i = 0; i < Y.length; i++) { if (ni[i] === null || eq[i] === null) continue; const prev = i > 0 && eq[i - 1] !== null ? eq[i - 1] : null; const b = prev !== null ? (eq[i] + prev) / 2 : eq[i]; if (b > 0) roes.push(ni[i] / b * 100); }
  if (roes.length) { f.roeAvg = rnd(roes.reduce((a, b) => a + b, 0) / roes.length); f.roeMin = rnd(Math.min(...roes)); }
  const eLast = last(ebit), icLast = last(invcap); let t = last(taxr); t = t !== null && t >= 0 && t <= 0.5 ? t : 0.22;
  if (eLast !== null && icLast && icLast > 0) f.roic = rnd(eLast * (1 - t) / icLast * 100);
  if (last(gp) !== null && last(rev)) f.gpm = rnd(last(gp) / last(rev) * 100);
  if (last(ni) !== null && last(rev)) f.npm = rnd(last(ni) / last(rev) * 100);
  const epsN = nz(eps); if (epsN.length >= 3) f.epsCagr = rnd(cagr(epsN[0], epsN.at(-1), epsN.length - 1));
  const revN = nz(rev); const revCagr = revN.length >= 3 ? cagr(revN[0], revN.at(-1), revN.length - 1) : null;
  const niN = nz(ni); if (niN.length) f.lossYears = niN.filter((x) => x < 0).length;
  const fcfN = nz(fcf); const sumNi = fcfN.length && niN.length ? niN.slice(-fcfN.length).reduce((a, b) => a + b, 0) : null;
  if (fcfN.length && sumNi && sumNi > 0) { f.fcfConv = rnd(fcfN.reduce((a, b) => a + b, 0) / sumNi * 100); const capN = nz(capex); if (capN.length) f.capexNi = rnd(Math.abs(capN.slice(-fcfN.length).reduce((a, b) => a + b, 0)) / sumNi * 100); }
  const niLast = last(ni); const l = last(ltd);
  if (l !== null && niLast !== null) f.ltdNi = niLast > 0 ? rnd(l / niLast) : (l <= 0 ? 0 : 99); else if (l === null) f.ltdNi = 0;
  const ieL = last(ie); if (eLast !== null) f.icr = eLast <= 0 ? (ieL ? rnd(eLast / Math.abs(ieL)) : null) : (!ieL ? 99 : rnd(Math.min(eLast / Math.abs(ieL), 99)));
  if (last(ca) && last(cl)) f.currentRatio = rnd(last(ca) / last(cl));
  const shN = nz(sh); if (shN.length >= 2 && shN[0] > 0) f.shareChg = rnd((shN.at(-1) / shN[0] - 1) * 100);
  for (const k of Object.keys(f)) if (f[k] === null || f[k] === undefined) delete f[k];
  const shares = last(sh); const val = {};
  if (shares) {
    // 금액은 백만 엔, 주식 수는 주 → 주당 값 = 백만 엔 × 1e6 / 주
    const k = 1e6;
    if (niLast !== null) val.eps = rnd(niLast * k / shares, 4);
    if (last(eq)) val.bps = rnd(last(eq) * k / shares, 4);
    const f3 = fcfN.slice(-3); if (f3.length) val.oeps = rnd(f3.reduce((a, b) => a + b, 0) / f3.length * k / shares, 4);
    if (last(rev)) val.sps = rnd(last(rev) * k / shares, 4);
  }
  if (revCagr !== null) val.revCagr = rnd(revCagr, 1);
  const gs = [f.epsCagr, revCagr].filter((g) => g !== null && g !== undefined);
  val.growth = rnd(gs.length ? Math.max(0, Math.min(Math.min(...gs) * 0.5, 8)) : 2, 1);
  if (epsN.length >= 3) val.epsAvg = rnd(epsN.reduce((a, b) => a + b, 0) / epsN.length, 4);
  const revYoY = revN.length >= 2 ? revN.slice(1).map((v, i) => rnd((v / revN[i] - 1) * 100, 1)).slice(-3) : null; if (revYoY) val.revYoY = revYoY;
  return { ...base, px, fin: f, val, mcap: null, fy: years.at(-1), yrs: niN.length, dataConf: 'medium' };
}

const now = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const out = {};
for (const p of process.argv.slice(3)) {
  const d = JSON.parse(fs.readFileSync(p, 'utf8'));
  const base = { ...now[d.ticker].row }; delete base.fin; delete base.val;
  const res = {};
  for (const [date, yrs] of [['2019-07-31', ['FY2015', 'FY2016', 'FY2017', 'FY2018', 'FY2019']], ['2020-08-28', ['FY2016', 'FY2017', 'FY2018', 'FY2019', 'FY2020']]]) {
    const px = d.prices?.[date]?.close; if (!isNum(px)) { res[date] = { error: 'no price' }; continue; }
    const r = rowAt(base, d.fy, yrs, px); const sc = scoreRow(r, null, 30);
    res[date] = { px, q: sc.q, v: sc.v, b: sc.b, iv: sc.iv && rnd(sc.iv, 0), per: rnd(px / r.val.eps, 1), pbr: rnd(px / r.val.bps, 2), flags: sc.flags, fin: r.fin, val: r.val };
  }
  const n = now[d.ticker];
  res.now = { px: n.px, q: n.q, v: n.v, b: n.b, total: n.total, iv: n.iv && rnd(n.iv, 0), per: rnd(n.px / n.row.val.eps, 1), pbr: rnd(n.px / n.row.val.bps, 2) };
  out[d.ticker] = { n: n.n, ...res };
}
console.log(JSON.stringify(out, null, 1));
