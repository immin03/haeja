// 사용: node scripts/research/vn_now.mjs <out.json> [티커,티커,...]
// 오늘 데이터로 밸류노트 점수를 다시 계산해 사이트 값과 맞는지 확인한다 (일본 상사 시점 비교용 하네스)
import fs from 'node:fs';
import { scoreRow, setSettings } from '../../supabase/functions/watch-select/scoring.js';
import { makeVN } from '../vnscore.mjs';
const cfg = fs.readFileSync('config.js', 'utf8');
const U = cfg.match(/SUPABASE_URL:\s*'([^']+)'/)[1], K = cfg.match(/SUPABASE_ANON_KEY:\s*'([^']+)'/)[1];
const h = { headers: { apikey: K, Authorization: 'Bearer ' + K } };
const get = async (q) => (await (await fetch(`${U}/rest/v1/docs?${q}`, h)).json());
setSettings({});
const rows = (await get('collection=eq.screen&select=id,data')).filter((d) => d.id.startsWith('chunk-')).flatMap((d) => d.data.rows || []);
const tr = (await get('collection=eq.trends&id=eq.current&select=data'))[0]?.data;
const pf = Object.fromEntries((await get('collection=eq.profiles&select=id,data')).map((d) => [d.id, d.data]));
const VN = makeVN(tr, pf);
const T = (process.argv[3] ? process.argv[3].split(',') : ['8001.T', '8053.T', '8002.T', '8058.T', '8031.T']);
const out = {};
for (const t of T) {
  const r = rows.find((x) => x.t === t); const sc = scoreRow(r, null, 30); const v = VN(r, sc);
  out[t] = { n: r.n, px: r.px, q: sc.q, v: sc.v, b: sc.b, qual: v.qual, trend: v.trend, total: v.total, iv: sc.iv, flags: sc.flags, row: r, qualObj: pf[t]?.qual || null, trendLinks: pf[t]?.trendLinks || null };
  console.log(t, r.n, 'px', r.px, 'q', sc.q, 'v', sc.v, 'b', sc.b, 'qual', v.qual, 'trend', v.trend, 'TOTAL', v.total, 'iv', sc.iv && Math.round(sc.iv), sc.flags);
}
fs.writeFileSync(process.argv[2] || '/dev/null', JSON.stringify(out, null, 1));
