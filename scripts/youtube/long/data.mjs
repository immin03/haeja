// 롱폼 원고의 숫자를 "렌더하는 순간의 최신 데이터"로 채운다 (앱과 같은 계산: scoring.js + vnscore.mjs)
// 사용: node scripts/youtube/long/data.mjs <spec.json>  →  같은 폴더에 <id>.data.json
// 원고의 {px} {iv} {mult} 같은 자리는 여기서 계산한 값으로만 채운다. 원고에 현재가·적정 주가를 직접 적지 않는다.
import fs from 'node:fs';
import path from 'node:path';
import { scoreRow } from '../../../supabase/functions/watch-select/scoring.js';
import { makeVN } from '../../vnscore.mjs';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..', '..', '..');
const cfg = fs.readFileSync(path.join(ROOT, 'config.js'), 'utf8');
const U = cfg.match(/SUPABASE_URL:\s*'([^']+)'/)[1], K = cfg.match(/SUPABASE_ANON_KEY:\s*'([^']+)'/)[1];
const H = { headers: { apikey: K, Authorization: 'Bearer ' + K } };

// 1,294,000 → "129만 4천 원" / 295,282 → "29만 5천 원" (만 단위 아래는 천 단위까지만)
export function won(n) {
  n = Math.round(n);
  const eok = Math.floor(n / 1e8), man = Math.floor((n % 1e8) / 1e4), cheon = Math.floor((n % 1e4) / 1e3);
  let s = '';
  if (eok) s += eok.toLocaleString('ko-KR') + '억 ';
  if (man) s += man.toLocaleString('ko-KR') + '만 ';
  if (cheon && !eok) s += cheon + '천 ';
  return (s.trim() || n.toLocaleString('ko-KR')) + ' 원';
}
const comma = (n) => Math.round(n).toLocaleString('ko-KR') + '원';
const x1 = (v) => (Math.round(v * 10) / 10).toFixed(1).replace(/\.0$/, '') + '배';
const pct = (v) => Math.round(v * 100) + '%';
const vs = (a, b) => { const r = a / b; return r < 1 ? `약 ${Math.round(r * 100)}%` : `약 ${x1(r)}`; };

// 1,443,000,000 → "14억 4천만 원" (천만 단위 반올림)
export function eokman(n) {
  const c = Math.round(n / 1e7); const eok = Math.floor(c / 10), r = c % 10;
  return (eok ? eok + '억 ' : '') + (r ? r + '천만 ' : '') + '원';
}

export async function companyData(code, spec = {}) {
  const docs = await (await fetch(`${U}/rest/v1/docs?collection=eq.screen&select=id,data`, H)).json();
  const meta = docs.find((d) => d.id === 'meta')?.data || {};
  const rows = docs.filter((d) => d.id.startsWith('chunk-')).flatMap((d) => d.data?.rows || []);
  const r = rows.find((x) => x.code === code || x.t === code);
  if (!r) throw new Error('회사 데이터 없음: ' + code);
  // 가격은 렌더하는 순간 야후에서 다시 받는다 (실패하면 매일 갱신되는 스크리너 가격과 그 날짜)
  let asofIso = (docs.find((d) => d.id.startsWith('chunk-') && (d.data?.rows || []).includes(r))?.data?.pxAt) || meta.generatedAt || new Date().toISOString();
  try {
    const j = await (await fetch(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(r.t)}?range=5d&interval=1d`, { headers: { 'User-Agent': 'Mozilla/5.0' } })).json();
    const res = j.chart.result[0], ts = res.timestamp, cl = res.indicators.quote[0].close;
    let i = cl.length - 1; while (i >= 0 && cl[i] == null) i--;
    const live = res.meta.regularMarketPrice || cl[i];
    if (live > 0) { r.px = live; asofIso = new Date((res.meta.regularMarketTime || ts[i]) * 1000).toISOString(); }
  } catch (e) { console.error('야후 가격 실패, 스크리너 가격 사용:', String(e).slice(0, 120)); }
  // 최근 1년 최고가 (원고에서 "?"로 시작하는 문장에만 쓴다: 못 받으면 그 문장을 뺀다)
  let hi = {};
  try {
    const j = await (await fetch(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(r.t)}?range=1y&interval=1d`, { headers: { 'User-Agent': 'Mozilla/5.0' } })).json();
    const res = j.chart.result[0], cl = res.indicators.quote[0].high || res.indicators.quote[0].close; let k = -1, mx = 0;  // 장중 최고가 (앱의 52주 범위와 같은 기준)
    cl.forEach((v, i) => { if (v != null && v > mx) { mx = v; k = i; } });
    if (mx > 0) { const hd = new Date(res.timestamp[k] * 1000 + 9 * 3600e3); hi = { hi52: comma(mx), hi52_short: won(mx), hi52_when: `${hd.getUTCFullYear()}년 ${hd.getUTCMonth() + 1}월`, from_hi: Math.round((1 - r.px / mx) * 100) + '%' }; }
  } catch (e) { console.error('1년 최고가 실패:', String(e).slice(0, 120)); }
  const sc = scoreRow(r, null, 30);
  const px = r.px, iv = sc.iv, E = sc.E;
  // 앱과 같은 종합 점수 (숫자 65% + 정성 20% + 트렌드 15%)
  const tr = (await (await fetch(`${U}/rest/v1/docs?collection=eq.trends&id=eq.current&select=data`, H)).json())[0]?.data;
  const pf = Object.fromEntries((await (await fetch(`${U}/rest/v1/docs?collection=eq.profiles&select=id,data`, H)).json()).map((d) => [d.id, d.data]));
  const vn = makeVN(tr, pf)(r, sc);
  const d = new Date(new Date(asofIso).getTime() + 9 * 3600e3);
  const asof = `${d.getUTCMonth() + 1}월 ${d.getUTCDate()}일`;
  const hm = d.getUTCHours() * 60 + d.getUTCMinutes(), wd = d.getUTCDay();
  const intraday = String(asofIso).length > 10 && wd >= 1 && wd <= 5 && hm >= 9 * 60 && hm < 15 * 60 + 30 && (r.m === 'KR' || /\.K[SQ]$/.test(r.t));
  const px_label = intraday ? `${asof} 장중 주가` : `${asof} 종가`;
  const bt = spec.backtest; let btv = {};
  if (bt) { const mult = (r.px + (bt.div_per_share || 0)) / bt.then_px; btv = { bt_won: eokman(1e8 * mult), bt_mult: x1(mult), bt_asof: asof, bt_rise: Math.floor(r.px / bt.then_px) + '배' }; }
  const normal = iv / 10;                 // 적정 주가에 쓰인 정상 이익(주당)
  const need = px / 10 / E;               // 지금 주가가 맞으려면 필요한 정상 이익 비율
  const v30 = E * 0.3 * 10, v100 = E * 10;
  return {
    raw: { code, ticker: r.t, name: r.n, px, iv, eps: E, score: vn.total, q: sc.q, v: sc.v, asof_iso: asofIso, ivSrc: sc.ivSrc },
    vars: {
      asof, px_label, ...btv, ...hi, score: String(vn.total), q_score: String(sc.q), v_score: String(sc.v), px: comma(px), px_short: won(px), iv: comma(iv), iv_short: won(iv),
      mult: x1(px / iv), per_now: x1(px / E), per_avg: x1(px / normal), eps: won(E),
      need: pct(need), iv_pct: pct(iv / 10 / E), iv_vs: vs(iv, px),
      v30: won(v30), v30_vs: vs(v30, px), v100: won(v100), v100_vs: vs(v100, px),
    },
  };
}

export function fill(s, vars) {
  return String(s).replace(/\{(\w+)\}/g, (m, k) => { if (!(k in vars)) throw new Error('원고 자리 값 없음: ' + k); return vars[k]; });
}

if (process.argv[2]) {
  const specPath = process.argv[2];
  const spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
  const data = await companyData(spec.company, spec);
  const out = specPath.replace(/\.json$/, '.data.json');
  fs.writeFileSync(out, JSON.stringify(data, null, 1));
  console.log(JSON.stringify(data.vars, null, 1));
}
