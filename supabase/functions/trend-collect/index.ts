// 트렌드 레이더 수집 (2026-10-26). 매일 07:25 KST pg_cron 이 부른다. 바로 202를 돌려주고 뒤에서 일한다.
// 1) 핫비디오: trend_queries 의 검색어마다 유튜브 내부 검색 API(이번 달 업로드)로 영상·조회수 스냅샷을 쌓는다.
//    어제 이후 검색에 안 잡힌 최근 급등 영상은 영상 페이지에서 조회수만 다시 읽어 증가량을 이어 간다.
//    급등 판단은 DB 뷰 trend_hot 이 한다 (하루 증가량 ÷ 그 전 평균, 새 영상은 조회수 ÷ 올린 지 며칠).
// 2) 종목 관심도: 네이버 증권 검색 상위 30, 야후 미국 트렌딩 20 → trend_stocks
// 3) 실적 일정: 많이 찾는 회사들의 다음 실적 발표일을 야후에서 받아 issue_events(kind earnings, auto) 에 넣는다.
// 유튜브 API 승인이 나면 1)의 검색·조회수 읽기만 API로 바꾸면 된다 (테이블은 그대로).
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36";
const today = () => new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);
async function pool<T>(xs: T[], n: number, f: (x: T) => Promise<void>) {
  let i = 0; await Promise.all(Array.from({ length: Math.min(n, xs.length) }, async () => { while (i < xs.length) await f(xs[i++]); }));
}
const num = (s: string | undefined) => { const d = String(s || "").replace(/[^\d]/g, ""); return d ? Number(d) : null; };
const txt = (o: any) => o?.simpleText ?? (o?.runs || []).map((r: any) => r.text).join("") ?? "";

// "3일 전" "2주 전" "1개월 전" "5시간 전" "2 days ago" "Streamed 3 weeks ago" → 대략의 업로드 시각
function ago(s: string): string | null {
  const m = s.match(/(\d+)\s*(초|분|시간|일|주|개월|년|second|minute|hour|day|week|month|year)/i);
  if (!m) return null;
  const n = Number(m[1]), u = m[2].toLowerCase();
  const h = /초|second/.test(u) ? 0 : /분|minute/.test(u) ? n / 60 : /시간|hour/.test(u) ? n : /일|day/.test(u) ? n * 24
    : /주|week/.test(u) ? n * 168 : /개월|month/.test(u) ? n * 720 : n * 8760;
  return new Date(Date.now() - h * 3600e3).toISOString();
}

type Vid = { id: string; title: string; channel: string; channel_id: string; views: number; published: string; length: string };
function collect(node: any, out: Vid[]) {
  if (!node || typeof node !== "object") return;
  if (Array.isArray(node)) { for (const x of node) collect(x, out); return; }
  const v = node.videoRenderer;
  if (v?.videoId) {
    const views = num(txt(v.viewCountText));
    const by = v.ownerText?.runs?.[0];
    if (views !== null && !txt(v.badges?.[0]?.metadataBadgeRenderer?.label).match(/LIVE|실시간/))
      out.push({ id: v.videoId, title: txt(v.title), channel: by?.text || "", channel_id: by?.navigationEndpoint?.browseEndpoint?.browseId || "",
        views, published: txt(v.publishedTimeText), length: txt(v.lengthText) });
    return;
  }
  for (const k in node) collect(node[k], out);
}

// 유튜브 웹이 쓰는 내부 검색 API (youtubei). 검색 페이지 HTML보다 가볍고, 동의 페이지 리디렉션에 걸리지 않는다.
const YTV = "2.20251001.00.00";
async function yti(path: string, lang: string, body: any) {
  const r = await fetch(`https://www.youtube.com/youtubei/v1/${path}?prettyPrint=false`, { method: "POST", headers: { "User-Agent": UA, "Content-Type": "application/json" },
    body: JSON.stringify({ context: { client: { clientName: "WEB", clientVersion: YTV, hl: lang === "en" ? "en" : "ko", gl: lang === "en" ? "US" : "KR" } }, ...body }) });
  if (!r.ok) throw new Error("yt " + r.status);
  return await r.json();
}
async function search(q: string, lang: string): Promise<Vid[]> {
  // params EgIIBA== : 이번 달 업로드
  const data = await yti("search", lang, { query: q, params: "EgIIBA==" });
  const out: Vid[] = []; collect(data, out);
  if (!out.length) throw new Error("empty");
  return out;
}

async function watchViews(id: string): Promise<number | null> {
  try {
    const j = await yti("player", "ko", { videoId: id });
    const v = Number(j?.videoDetails?.viewCount);
    return isFinite(v) && v > 0 ? v : null;
  } catch (_) { return null; }
}

async function videos(log: string[]) {
  const { data: qs } = await sb.from("trend_queries").select("q,cat,lang").eq("active", true);
  const day = today(), seen = new Map<string, { v: Vid; cats: Set<string>; qs: Set<string>; lang: string }>();
  let fails = 0; const why = new Map<string, number>();
  // 3개씩 동시에, 실패하면 1.5초 쉬고 한 번 더
  await pool(qs || [], 3, async (q: any) => {
    for (let k = 0; k < 2; k++) {
      try {
        for (const v of await search(q.q, q.lang)) {
          const e = seen.get(v.id) || { v, cats: new Set<string>(), qs: new Set<string>(), lang: q.lang };
          e.cats.add(q.cat); e.qs.add(q.q); seen.set(v.id, e);
        }
        break;
      } catch (e) {
        if (k === 1) { fails++; const m = String((e as Error).message || e).slice(0, 40); why.set(m, (why.get(m) || 0) + 1); }
        await new Promise((r) => setTimeout(r, 1500));
      }
    }
  });
  log.push(`검색어 ${qs?.length || 0}개 (실패 ${fails}${why.size ? ': ' + [...why].map(([m, n]) => `${m} ${n}`).join(', ') : ''}) · 영상 ${seen.size}개`);
  const ids = [...seen.keys()];
  const old = new Map<string, any>();
  for (let i = 0; i < ids.length; i += 200) {
    const { data } = await sb.from("trend_videos").select("video_id,cats,queries,first_seen,published_est").in("video_id", ids.slice(i, i + 200));
    (data || []).forEach((r: any) => old.set(r.video_id, r));
  }
  const now = new Date().toISOString();
  const rows = [...seen.values()].map(({ v, cats, qs, lang }) => {
    const o = old.get(v.id);
    return { video_id: v.id, title: v.title, channel: v.channel, channel_id: v.channel_id, length_text: v.length, published_text: v.published,
      published_est: o?.published_est || ago(v.published), lang,
      cats: [...new Set([...(o?.cats || []), ...cats])], queries: [...new Set([...(o?.queries || []), ...qs])].slice(0, 12), last_seen: now };
  });
  for (let i = 0; i < rows.length; i += 300) await sb.from("trend_videos").upsert(rows.slice(i, i + 300), { onConflict: "video_id" });
  const snaps = [...seen.values()].map(({ v }) => ({ video_id: v.id, day, views: v.views, taken_at: now }));
  for (let i = 0; i < snaps.length; i += 500) await sb.from("trend_snaps").upsert(snaps.slice(i, i + 500), { onConflict: "video_id,day" });

  // 오늘 검색엔 안 잡혔지만 최근 7일 안에 보였고 조회수가 큰 영상: 영상 페이지에서 조회수만 다시 읽는다 (최대 120개)
  const { data: miss } = await sb.from("trend_videos").select("video_id").gte("last_seen", new Date(Date.now() - 7 * 864e5).toISOString())
    .lt("last_seen", new Date(Date.now() - 12 * 3600e3).toISOString()).order("last_seen", { ascending: false }).limit(400);
  const missIds = (miss || []).map((r: any) => r.video_id);
  let refetch: string[] = [];
  if (missIds.length) {
    const { data: lastSnaps } = await sb.from("trend_snaps").select("video_id,views").in("video_id", missIds.slice(0, 400)).order("day", { ascending: false });
    const best = new Map<string, number>(); (lastSnaps || []).forEach((s: any) => { if (!best.has(s.video_id)) best.set(s.video_id, s.views); });
    refetch = [...best.entries()].filter(([, v]) => v >= 20000).sort((a, b) => b[1] - a[1]).slice(0, 120).map(([k]) => k);
  }
  const extra: any[] = [];
  await pool(refetch, 4, async (id) => { const v = await watchViews(id); if (v !== null) extra.push({ video_id: id, day, views: v, taken_at: new Date().toISOString() }); });
  if (extra.length) await sb.from("trend_snaps").upsert(extra, { onConflict: "video_id,day" });
  log.push(`다시 읽은 영상 ${extra.length}/${refetch.length}개`);
}

async function stocks(log: string[]) {
  const day = today(), rows: any[] = [];
  try {
    const r = await fetch("https://m.stock.naver.com/api/stocks/searchTop?page=1&pageSize=30", { headers: { "User-Agent": UA } });
    const j = await r.json();
    (j?.stocks || []).forEach((s: any, i: number) => rows.push({ day, src: "naver_search", rank: i + 1, name: s.stockName, code: s.itemCode,
      price: s.closePrice, change: s.fluctuationsRatio != null ? `${s.fluctuationsRatio}%` : null }));
  } catch (_) { log.push("네이버 검색 상위 실패"); }
  try {
    const r = await fetch("https://query1.finance.yahoo.com/v1/finance/trending/US?count=25", { headers: { "User-Agent": UA } });
    const j = await r.json();
    const syms: string[] = (j?.finance?.result?.[0]?.quotes || []).map((x: any) => x.symbol).filter((s: string) => !s.startsWith("^")).slice(0, 20);
    syms.forEach((s, i) => rows.push({ day, src: "yahoo_us", rank: i + 1, name: s, code: s }));
  } catch (_) { log.push("야후 트렌딩 실패"); }
  if (rows.length) { await sb.from("trend_stocks").delete().eq("day", day); await sb.from("trend_stocks").insert(rows); }
  log.push(`종목 관심도 ${rows.length}줄`);
}

// 사람들이 많이 찾는 회사들 (실적일을 캘린더에 자동으로)
const EARN: [string, string, string][] = [
  ["005930.KS", "삼성전자", "반도체"], ["000660.KS", "SK하이닉스", "반도체"], ["005380.KS", "현대차", "자동차"], ["000270.KS", "기아", "자동차"],
  ["035420.KS", "네이버", "플랫폼"], ["035720.KS", "카카오", "플랫폼"], ["373220.KS", "LG에너지솔루션", "2차전지"], ["207940.KS", "삼성바이오로직스", "바이오"],
  ["NVDA", "엔비디아", "반도체"], ["AAPL", "애플", "빅테크"], ["MSFT", "마이크로소프트", "빅테크"], ["GOOGL", "알파벳(구글)", "빅테크"],
  ["AMZN", "아마존", "빅테크"], ["META", "메타", "빅테크"], ["TSLA", "테슬라", "자동차"], ["NFLX", "넷플릭스", "미디어"],
  ["COST", "코스트코", "소비·유통"], ["SBUX", "스타벅스", "소비·유통"], ["NKE", "나이키", "소비·유통"], ["MCD", "맥도날드", "소비·유통"],
  ["KO", "코카콜라", "소비·유통"], ["DIS", "디즈니", "미디어"], ["BRK-B", "버크셔 해서웨이", "지주"], ["TSM", "TSMC", "반도체"],
  ["AVGO", "브로드컴", "반도체"], ["LULU", "룰루레몬", "소비·유통"], ["WMT", "월마트", "소비·유통"], ["PLTR", "팔란티어", "소프트웨어"],
];
async function yahooAuth(): Promise<{ cookie: string; crumb: string } | null> {
  try {
    const r = await fetch("https://fc.yahoo.com", { headers: { "User-Agent": UA }, redirect: "manual" });
    const cookie = (r.headers.get("set-cookie") || "").split(/,(?=[^;]+=)/).map((s) => s.split(";")[0].trim()).filter(Boolean).join("; ");
    if (!cookie) return null;
    const c = await fetch("https://query2.finance.yahoo.com/v1/test/getcrumb", { headers: { "User-Agent": UA, Cookie: cookie } });
    const crumb = (await c.text()).trim();
    return c.ok && crumb && crumb.length < 40 && !/[<{ ]/.test(crumb) ? { cookie, crumb } : null;
  } catch (_) { return null; }
}
async function earnings(log: string[]) {
  const auth = await yahooAuth(); if (!auth) { log.push("실적 일정: 야후 인증 실패"); return; }
  const u = `https://query2.finance.yahoo.com/v7/finance/quote?symbols=${encodeURIComponent(EARN.map((e) => e[0]).join(","))}&fields=earningsTimestamp,earningsTimestampStart,earningsTimestampEnd,isEarningsDateEstimate&crumb=${encodeURIComponent(auth.crumb)}`;
  const rows = (await (await fetch(u, { headers: { "User-Agent": UA, Cookie: auth.cookie } })).json())?.quoteResponse?.result || [];
  const t = today(), ins: any[] = [];
  for (const q of rows) {
    const ts = q.earningsTimestampStart || q.earningsTimestamp; if (!ts) continue;
    const d = new Date(ts * 1000 + (q.gmtOffSetMilliseconds ?? 0)).toISOString().slice(0, 10);
    if (d < t) continue;
    const e = EARN.find((x) => x[0] === String(q.symbol).toUpperCase()); if (!e) continue;
    ins.push({ id: `E-${e[0]}`, day: d, title: `${e[1]} 실적 발표`, kind: "earnings", cat: e[2], companies: [e[1]], lead_days: 7, auto: true,
      est: !!q.isEarningsDateEstimate || (!!q.earningsTimestampEnd && q.earningsTimestampEnd !== q.earningsTimestampStart), source: "Yahoo Finance", updated_at: new Date().toISOString() });
  }
  // 회사당 한 줄(E-심볼): 다음 실적일로 덮어쓴다. 지난 실적 줄은 날짜가 바뀌며 자연히 갱신된다.
  if (ins.length) await sb.from("issue_events").upsert(ins, { onConflict: "id" });
  log.push(`실적 일정 ${ins.length}곳`);
}

async function run() {
  const log: string[] = [], t0 = Date.now();
  for (const [name, f] of [["stocks", stocks], ["earnings", earnings], ["videos", videos]] as const) {
    try { await f(log); } catch (e) { log.push(`${name} 오류: ${String(e).slice(0, 120)}`); }
  }
  log.push(`${Math.round((Date.now() - t0) / 1000)}초`);
  const { data: pub } = await sb.rpc("publisher_id");
  if (pub) await sb.from("docs").upsert({ owner: pub, collection: "trends", id: "radar_log", data: { at: new Date().toISOString(), log }, updated_at: new Date().toISOString() }, { onConflict: "owner,collection,id" });
  return log;
}

Deno.serve(async (req: Request) => {
  const body = await req.json().catch(() => ({}));
  if (body?.wait) return Response.json({ ok: true, log: await run() });
  // @ts-ignore EdgeRuntime 은 Supabase 런타임에 있다
  EdgeRuntime.waitUntil(run());
  return Response.json({ ok: true, started: true }, { status: 202 });
});
