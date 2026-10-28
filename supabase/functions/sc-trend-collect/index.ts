// 까치 채널(From Korea, With Love) 감성 쇼츠 트렌드 수집 (2026-10-28). 매일 07:40 KST pg_cron 이 부른다.
// 1) sc_hot_queries 검색어마다 유튜브 내부 검색 API로 "이번 달 업로드 · 쇼츠 · 조회수 순" 상위 쇼츠를 받아
//    sc_hot_videos(영상 정보) / sc_hot_snaps(그날 조회수)에 쌓는다. 하루 증가량은 뷰 sc_hot 이 계산한다.
// 2) 오늘 검색에 안 잡힌 최근 큰 영상은 next API 로 조회수만 다시 읽어 증가량을 이어 간다.
// 3) 우리 채널에 올린 영상(sc_videos.youtube_id)의 조회수를 읽어 sc_videos.stats 에 24시간·48시간·7일 값을 남긴다.
// body {"wait": true} 이면 끝날 때까지 기다렸다가 로그를 돌려준다.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36";
const YTV = "2.20251001.00.00";
const today = () => new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);
const num = (s: string | undefined) => { const d = String(s || "").replace(/[^\d]/g, ""); return d ? Number(d) : null; };
const txt = (o: any) => o?.simpleText ?? (o?.runs || []).map((r: any) => r.text).join("") ?? "";
async function pool<T>(xs: T[], n: number, f: (x: T) => Promise<void>) {
  let i = 0; await Promise.all(Array.from({ length: Math.min(n, xs.length) }, async () => { while (i < xs.length) await f(xs[i++]); }));
}
function ago(s: string): string | null {
  const m = s.match(/(\d+)\s*(초|분|시간|일|주|개월|년|second|minute|hour|day|week|month|year)/i);
  if (!m) return null;
  const n = Number(m[1]), u = m[2].toLowerCase();
  const h = /초|second/.test(u) ? 0 : /분|minute/.test(u) ? n / 60 : /시간|hour/.test(u) ? n : /일|day/.test(u) ? n * 24
    : /주|week/.test(u) ? n * 168 : /개월|month/.test(u) ? n * 720 : n * 8760;
  return new Date(Date.now() - h * 3600e3).toISOString();
}
const secs = (s: string) => { const p = String(s || "").split(":").map(Number); if (p.some(isNaN) || !p.length) return null; return p.reduce((a, b) => a * 60 + b, 0); };

async function yti(path: string, lang: string, body: any) {
  const r = await fetch(`https://www.youtube.com/youtubei/v1/${path}?prettyPrint=false`, { method: "POST", headers: { "User-Agent": UA, "Content-Type": "application/json" },
    body: JSON.stringify({ context: { client: { clientName: "WEB", clientVersion: YTV, hl: lang === "ko" ? "ko" : "en", gl: lang === "ko" ? "KR" : "US" } }, ...body }) });
  if (!r.ok) throw new Error("yt " + r.status);
  return await r.json();
}

type Vid = { id: string; title: string; channel: string; channel_id: string; views: number; published: string; length: string };
function collect(node: any, out: Vid[]) {
  if (!node || typeof node !== "object") return;
  if (Array.isArray(node)) { for (const x of node) collect(x, out); return; }
  const v = node.videoRenderer;
  if (v?.videoId) {
    const views = num(txt(v.viewCountText)); const by = v.ownerText?.runs?.[0] || v.longBylineText?.runs?.[0];
    if (views !== null) out.push({ id: v.videoId, title: txt(v.title), channel: by?.text || "", channel_id: by?.navigationEndpoint?.browseEndpoint?.browseId || "",
      views, published: txt(v.publishedTimeText), length: txt(v.lengthText) });
    return;
  }
  for (const k in node) collect(node[k], out);
}
// 쇼츠 선반(shortsLockupViewModel): 채널·업로드일 없이 제목과 "4.2M views" 만 온다
const approx = (s: string) => { const m = String(s || "").replace(/,/g, "").match(/([\d.]+)\s*(K|M|B|천|만|억)?/i); if (!m) return null;
  const k = { k: 1e3, m: 1e6, b: 1e9, "천": 1e3, "만": 1e4, "억": 1e8 } as any; return Math.round(Number(m[1]) * (m[2] ? k[m[2].toLowerCase()] : 1)); };
function lockups(node: any, out: Vid[]) {
  if (!node || typeof node !== "object") return;
  if (Array.isArray(node)) { for (const x of node) lockups(x, out); return; }
  const l = node.shortsLockupViewModel;
  if (l) {
    const id = l.onTap?.innertubeCommand?.reelWatchEndpoint?.videoId || String(l.entityId || "").replace("shorts-shelf-item-", "");
    const title = l.overlayMetadata?.primaryText?.content || String(l.accessibilityText || "").replace(/,\s*[\d.,]+\s*\S*\s*(views|회).*$/i, "");
    const views = approx(l.overlayMetadata?.secondaryText?.content || (String(l.accessibilityText || "").match(/([\d.,]+\s*(?:thousand|million|billion|K|M|B)?)\s*views/i) || [])[1] || "");
    if (id && views !== null) out.push({ id, title, channel: "", channel_id: "", views, published: "", length: "" });
    return;
  }
  for (const k in node) lockups(node[k], out);
}
// 1차: 조회수 순 + 이번 달 + 쇼츠(CAMSBAgEEAk=) → 채널·업로드일까지 온다. 결과가 없으면 2차: 이번 달 + 쇼츠(EgQIBBAJ) 쇼츠 선반
async function search(q: string, lang: string): Promise<Vid[]> {
  let out: Vid[] = []; collect(await yti("search", lang, { query: q, params: "CAMSBAgEEAk=" }), out);
  if (!out.length) { const j = await yti("search", lang, { query: q, params: "EgQIBBAJ" }); lockups(j, out); if (!out.length) collect(j, out); }
  if (!out.length) throw new Error("empty");
  out = out.filter((v) => { const s = secs(v.length); return s === null || s <= 180; });
  return out.sort((a, b) => b.views - a.views);
}
// 영상 하나의 조회수·업로드일·채널 (next API: 시청 페이지 데이터)
type Meta = { views: number | null; published: string | null; channel: string; channel_id: string };
async function metaOf(id: string): Promise<Meta | null> {
  try {
    const j = await yti("next", "en", { videoId: id });
    const m: Meta = { views: null, published: null, channel: "", channel_id: "" };
    const walk = (n: any) => { if (!n || typeof n !== "object") return; if (Array.isArray(n)) { n.forEach(walk); return; }
      const r = n.videoViewCountRenderer; if (r && m.views === null) { const v = num(txt(r.viewCount)); if (v !== null) m.views = v; }
      const p = n.videoPrimaryInfoRenderer; if (p && !m.published) { const d = txt(p.dateText).replace(/^(Premiered|Streamed live on|Published on)\s*/i, ""); const t = Date.parse(d); m.published = isFinite(t) ? new Date(t + 12 * 3600e3).toISOString() : ago(d); }
      const o = n.videoOwnerRenderer; if (o && !m.channel) { m.channel = txt(o.title); m.channel_id = o.navigationEndpoint?.browseEndpoint?.browseId || ""; }
      for (const k in n) walk(n[k]); };
    walk(j); return m;
  } catch (_) { return null; }
}
const viewsOf = async (id: string) => (await metaOf(id))?.views ?? null;

async function hot(log: string[]) {
  const { data: qs } = await sb.from("sc_hot_queries").select("q,cat,lang").eq("active", true);
  const day = today(), seen = new Map<string, { v: Vid; cats: Set<string>; qs: Set<string>; lang: string }>();
  let fails = 0;
  await pool(qs || [], 2, async (q: any) => {
    for (let k = 0; k < 2; k++) {
      try {
        for (const v of (await search(q.q, q.lang)).slice(0, 15)) {
          const e = seen.get(v.id) || { v, cats: new Set<string>(), qs: new Set<string>(), lang: q.lang };
          e.cats.add(q.cat); e.qs.add(q.q); if (v.views > e.v.views) e.v = v; seen.set(v.id, e);
        }
        break;
      } catch (_) { if (k === 1) fails++; await new Promise((r) => setTimeout(r, 1500)); }
    }
  });
  log.push(`검색어 ${qs?.length || 0}개 (실패 ${fails}) · 쇼츠 ${seen.size}개`);
  const ids = [...seen.keys()], old = new Map<string, any>();
  for (let i = 0; i < ids.length; i += 200) {
    const { data } = await sb.from("sc_hot_videos").select("video_id,cats,queries,published_est,channel,channel_id,length_sec").in("video_id", ids.slice(i, i + 200));
    (data || []).forEach((r: any) => old.set(r.video_id, r));
  }
  const now = new Date().toISOString();
  const rows = [...seen.values()].map(({ v, cats, qs, lang }) => { const o = old.get(v.id);
    return { video_id: v.id, title: v.title, channel: v.channel || o?.channel || "", channel_id: v.channel_id || o?.channel_id || "", lang, length_sec: v.length ? secs(v.length) : (o?.length_sec ?? null),
      published_est: o?.published_est || ago(v.published), cats: [...new Set([...(o?.cats || []), ...cats])],
      queries: [...new Set([...(o?.queries || []), ...qs])].slice(0, 12), last_seen: now }; });
  // 쇼츠 선반으로만 잡혀 업로드일·채널을 모르는 영상: 시청 페이지에서 채운다 (최대 150개)
  const need = rows.filter((r) => !r.published_est || !r.channel).slice(0, 150);
  let filled = 0;
  await pool(need, 4, async (r: any) => { const m = await metaOf(r.video_id); if (!m) return;
    if (!r.published_est && m.published) r.published_est = m.published; if (!r.channel && m.channel) { r.channel = m.channel; r.channel_id = m.channel_id; } filled++; });
  log.push(`업로드일·채널 보충 ${filled}/${need.length}개`);
  for (let i = 0; i < rows.length; i += 300) await sb.from("sc_hot_videos").upsert(rows.slice(i, i + 300), { onConflict: "video_id" });
  const snaps = [...seen.values()].map(({ v }) => ({ video_id: v.id, day, views: v.views, taken_at: now }));
  for (let i = 0; i < snaps.length; i += 500) await sb.from("sc_hot_snaps").upsert(snaps.slice(i, i + 500), { onConflict: "video_id,day" });

  // 오늘 검색엔 없지만 최근 10일 안에 보였던 큰 영상(5만 회 이상) 최대 80개: 조회수만 다시 읽는다
  const { data: miss } = await sb.from("sc_hot").select("video_id,views").lt("day", day).gte("views", 50000).order("views", { ascending: false }).limit(80);
  const extra: any[] = [];
  await pool((miss || []).map((r: any) => r.video_id), 4, async (id) => { const v = await viewsOf(id); if (v !== null) extra.push({ video_id: id, day, views: v, taken_at: new Date().toISOString() }); });
  if (extra.length) await sb.from("sc_hot_snaps").upsert(extra, { onConflict: "video_id,day" });
  log.push(`다시 읽은 영상 ${extra.length}/${miss?.length || 0}개`);
}

// 우리 채널 성과: 올린 지 24·48시간·7일이 지난 첫 측정을 고정 기록, now 는 매번 갱신
async function mine(log: string[]) {
  const { data } = await sb.from("sc_videos").select("id,youtube_id,uploaded_at,stats").eq("status", "uploaded").not("youtube_id", "is", null);
  let n = 0;
  await pool(data || [], 3, async (v: any) => {
    const views = await viewsOf(v.youtube_id); if (views === null) return;
    const at = new Date().toISOString(), age = (Date.now() - Date.parse(v.uploaded_at || at)) / 3600e3;
    const s = { ...(v.stats || {}) }; s.now = { views, at };
    for (const [k, h] of [["h24", 24], ["h48", 48], ["d7", 168]] as const) if (age >= h && !s[k]) s[k] = { views, at };
    s.hist = [...(s.hist || []), { views, at }].slice(-60);
    await sb.from("sc_videos").update({ stats: s }).eq("id", v.id); n++;
  });
  log.push(`우리 영상 조회수 ${n}편`);
}

async function run() {
  const log: string[] = [], t0 = Date.now();
  for (const [name, f] of [["hot", hot], ["mine", mine]] as const) { try { await f(log); } catch (e) { log.push(`${name} 오류: ${String(e).slice(0, 120)}`); } }
  log.push(`${Math.round((Date.now() - t0) / 1000)}초`);
  const { data: s } = await sb.from("sc_settings").select("value").eq("id", 1).maybeSingle();
  await sb.from("sc_settings").upsert({ id: 1, value: { ...(s?.value || {}), hot_log: { at: new Date().toISOString(), log } } });
  return log;
}

Deno.serve(async (req: Request) => {
  const body = await req.json().catch(() => ({}));
  if (body?.wait) return Response.json({ ok: true, log: await run() });
  // @ts-ignore EdgeRuntime 은 Supabase 런타임에 있다
  EdgeRuntime.waitUntil(run());
  return Response.json({ ok: true, started: true }, { status: 202 });
});
