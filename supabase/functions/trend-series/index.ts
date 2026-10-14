// 메가트렌드 사이클 지수
// 트렌드마다 수혜 기업 묶음을 동일 가중으로 묶어 지수(시작 = 100)를 만든다.
// 5년 일간 종가로 한 번 계산한 뒤 저장만 나눈다 (기간마다 숫자가 어긋나지 않도록)
// - w: 5년, 주 단위로 추림 (5년 차트)   - d: 최근 1년 일간 (3개월·6개월·1년 차트)
// 비교선: 코스피, S&P 500. pg_cron이 평일 아침에 호출하고 trends/series 문서에 저장한다.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
type Pt = [string, number];

async function chart(sym: string, range: string, interval: string): Promise<Pt[] | null> {
  try {
    const r = await fetch(`https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(sym)}?range=${range}&interval=${interval}`, {
      headers: { "User-Agent": "Mozilla/5.0 (haeja-ledger)" },
    });
    if (!r.ok) return null;
    const res = (await r.json())?.chart?.result?.[0];
    const ts: number[] = res?.timestamp || [];
    const cl: (number | null)[] = res?.indicators?.adjclose?.[0]?.adjclose || res?.indicators?.quote?.[0]?.close || [];
    const off = (res?.meta?.gmtoffset ?? 0) * 1000;
    const m = new Map<string, number>();
    ts.forEach((t, i) => { const v = cl[i]; if (typeof v === "number" && isFinite(v) && v > 0) m.set(new Date(t * 1000 + off).toISOString().slice(0, 10), v); });
    const pts = [...m.entries()].sort((a, b) => a[0] < b[0] ? -1 : 1) as Pt[];
    return pts.length > 3 ? pts : null;
  } catch (_) { return null; }
}
async function chartAny(sym: string, range: string, interval: string) {
  let p = await chart(sym, range, interval);
  if (!p && /^\d{6}\.KS$/.test(sym)) p = await chart(sym.replace(".KS", ".KQ"), range, interval);
  return p;
}
async function pool<T>(items: T[], n: number, fn: (x: T) => Promise<void>) {
  let i = 0;
  await Promise.all(Array.from({ length: n }, async () => { while (i < items.length) await fn(items[i++]); }));
}

// "삼성전자 (005930)" → 005930.KS, "NAURA (002371.SZ)" → 002371.SZ, "SMIC (688981.SH/0981.HK)" → 688981.SS
function toSym(s: string): { sym: string; name: string } | null {
  const m = s.match(/^(.*)\(([^)]+)\)\s*$/);
  if (!m) return null;
  const name = m[1].trim();
  let t = m[2].split("/")[0].trim().toUpperCase();
  if (/^\d{6}$/.test(t)) t += ".KS";
  t = t.replace(/\.SH$/, ".SS");
  if (/^\d{1,4}\.HK$/.test(t)) t = t.padStart(7, "0");
  if (!/^[A-Z0-9.\-^=]+$/.test(t)) return null;
  return { sym: t, name };
}

// 동일 가중 연쇄 지수: 각 날짜마다 그날 값이 있는 종목들의 평균 수익률로 이어 붙인다.
function basket(series: Pt[][]): Pt[] {
  const maps = series.map((s) => new Map(s));
  const dates = [...new Set(series.flatMap((s) => s.map((p) => p[0])))].sort();
  const last: (number | null)[] = series.map(() => null);
  const out: Pt[] = [];
  let idx = 100;
  for (const d of dates) {
    const rs: number[] = [];
    maps.forEach((m, i) => {
      const v = m.get(d);
      if (v === undefined) return;
      if (last[i] !== null) { const r = v / (last[i] as number) - 1; if (Math.abs(r) < 0.6) rs.push(r); }
      last[i] = v;
    });
    if (out.length && !rs.length) continue;
    if (rs.length) idx *= 1 + rs.reduce((a, b) => a + b, 0) / rs.length;
    out.push([d, Math.round(idx * 10) / 10]);
  }
  return out;
}

Deno.serve(async (_req: Request) => {
  try {
    const { data: cur } = await sb.from("docs").select("data, owner").eq("collection", "trends").eq("id", "current").maybeSingle();
    if (!cur) return Response.json({ ok: false, msg: "트렌드 문서 없음" });
    const trends: any[] = cur.data?.trends || [];
    const members: Record<string, { sym: string; name: string }[]> = {};
    for (const t of trends) {
      const seen = new Set<string>();
      members[t.key] = Object.values(t.beneficiaries || {}).flat().map((s: any) => toSym(String(s))).filter((x): x is { sym: string; name: string } => !!x && !seen.has(x.sym) && !!seen.add(x.sym));
    }
    const bench: Record<string, { sym: string; label: string }> = { kospi: { sym: "^KS11", label: "코스피" }, spx: { sym: "^GSPC", label: "S&P 500" } };
    const syms = [...new Set([...Object.values(members).flat().map((m) => m.sym), ...Object.values(bench).map((b) => b.sym)])];
    const D: Record<string, Pt[]> = {};
    await pool(syms, 10, async (s) => { const d = await chartAny(s, "5y", "1d"); if (d) D[s] = d; });
    const cut = new Date(Date.now() - 366 * 864e5).toISOString().slice(0, 10);
    const weekly = (p: Pt[]) => { const o: Pt[] = []; let wk = ""; for (const x of p) { const t = new Date(x[0] + "T00:00:00Z"); t.setUTCDate(t.getUTCDate() - ((t.getUTCDay() + 6) % 7)); const k = t.toISOString().slice(0, 10); if (k === wk) o[o.length - 1] = x; else { o.push(x); wk = k; } } return o; };
    const w: Record<string, Pt[]> = {}, d: Record<string, Pt[]> = {}, used: Record<string, string[]> = {};
    const put = (k: string, full: Pt[]) => { w[k] = weekly(full); d[k] = full.filter((x) => x[0] >= cut); };
    for (const t of trends) {
      const ms = members[t.key].filter((m) => D[m.sym]);
      if (!ms.length) continue;
      used[t.key] = ms.map((m) => m.name);
      put(t.key, basket(ms.map((m) => D[m.sym])));
    }
    const norm = (p: Pt[]) => p.map(([k, v]) => [k, Math.round(v / p[0][1] * 1000) / 10] as Pt);
    for (const [k, b] of Object.entries(bench)) if (D[b.sym]) put(k, norm(D[b.sym]));
    const asOf = new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);
    const data = { asOf, w, d, used, bench: Object.fromEntries(Object.entries(bench).map(([k, b]) => [k, b.label])), method: "수혜 기업 동일 가중 지수, 시작 = 100, 수정주가 기준" };
    const { error } = await sb.from("docs").upsert({ collection: "trends", id: "series", owner: cur.owner, data, updated_at: new Date().toISOString() });
    if (error) throw error;
    return Response.json({ ok: true, asOf, symbols: syms.length, fetched: Object.keys(D).length, lines: Object.keys(w).length, used: Object.fromEntries(Object.entries(used).map(([k, v]) => [k, v.length + "/" + members[k]?.length])) });
  } catch (e) {
    return Response.json({ ok: false, error: String((e as Error)?.message || e) }, { status: 500 });
  }
});
