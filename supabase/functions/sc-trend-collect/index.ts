// 까치 채널(From Korea, With Love) 감성 쇼츠 트렌드 수집 (2026-10-28, 10-29 벤치마킹 추가). 매일 07:40 KST pg_cron 이 부른다.
// 1) sc_hot_queries 검색어마다 유튜브 내부 검색 API로 "이번 달 업로드 · 쇼츠 · 조회수 순" 상위 쇼츠를 받아
//    sc_hot_videos(영상 정보) / sc_hot_snaps(그날 조회수)에 쌓는다. 하루 증가량은 뷰 sc_hot 이 계산한다.
// 2) 오늘 검색에 안 잡힌 최근 큰 영상은 next API 로 조회수만 다시 읽어 증가량을 이어 간다.
// 3) (chan) 10만 회 넘은 쇼츠의 채널 구독자·영상 수·쇼츠 조회수 → sc_hot_channels. 뷰 sc_breakout = 작은 채널인데 터진 쇼츠
// 4) (ours) 우리 채널 쇼츠 탭에서 조회수를 읽어 sc_videos 에 youtube_id·stats 를 채운다
// 5) (mine) 우리 올린 영상(sc_videos.youtube_id) 조회수를 6·24·48시간·7일 값으로 남긴다 (3시간마다 {"only":"mine"} → ours+mine)
// body {"wait": true} 이면 끝날 때까지 기다렸다가 로그를 돌려준다. {"probe":"UC..."} 는 채널 하나를 읽어 바로 돌려준다(점검용).
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

// 우리 채널 성과: 공개 6·24·48시간·7일이 지난 첫 측정을 고정 기록, now 는 매번 갱신
async function mine(log: string[]) {
  const { data } = await sb.from("sc_videos").select("id,youtube_id,uploaded_at,scheduled_at,stats").eq("status", "uploaded").not("youtube_id", "is", null);
  let n = 0;
  await pool(data || [], 3, async (v: any) => {
    const pub = Date.parse(v.scheduled_at || v.uploaded_at || new Date().toISOString());
    if (pub > Date.now()) return;
    const views = await viewsOf(v.youtube_id); if (views === null) return;
    const at = new Date().toISOString(), age = (Date.now() - pub) / 3600e3;
    const s = { ...(v.stats || {}) }; s.now = { views, at };
    for (const [k, h] of [["h24", 24], ["h48", 48], ["d7", 168]] as const) if (age >= h && !s[k]) s[k] = { views, at };
    if (!s.h6 && age >= 6) s.h6 = { views, at };
    s.hist = [...(s.hist || []), { views, at }].slice(-80);
    await sb.from("sc_videos").update({ stats: s }).eq("id", v.id); n++;
  });
  log.push(`우리 영상 조회수 ${n}편`);
}
// ── 벤치마킹(2026-10-29): 터진 쇼츠를 올린 채널의 구독자·영상 수·쇼츠 평균, 우리 채널 쇼츠 조회수 ──
// 이 블록은 index.ts 안에서 쓰인다 (yti, lockups, approx, num, txt, pool, sb 가 위에 있다)

type Chan = { channel_id: string; name: string; handle: string; subs: number | null; video_count: number | null; shorts: { id: string; title: string; views: number }[] };
const SHORTS_TAB = "EgZzaG9ydHPyBgUKA5oBAA==";
function strings(node: any, out: string[]) {
  if (node == null) return;
  if (typeof node === "string") { out.push(node); return; }
  if (typeof node !== "object") return;
  if (Array.isArray(node)) { for (const x of node) strings(x, out); return; }
  for (const k in node) strings(node[k], out);
}
async function chanOf(id: string): Promise<Chan | null> {
  try {
    const j = await yti("browse", "en", { browseId: id });
    const ss: string[] = []; strings(j.header, ss);
    const subsS = ss.find((s) => /subscriber/i.test(s)) || "";
    const vidS = ss.find((s) => /^\s*[\d.,]+\s*[KMB]?\s+videos?\s*$/i.test(s)) || "";
    const md = j.metadata?.channelMetadataRenderer || {};
    const handle = (ss.find((s) => /^@[\w.\-]+$/.test(s)) || String(md.vanityChannelUrl || "").split("/").pop() || "").replace(/^@?/, "@");
    const c: Chan = { channel_id: id, name: md.title || "", handle, subs: subsS ? approx(subsS) : (/no subscribers/i.test(ss.join(" ")) ? 0 : null),
      video_count: vidS ? approx(vidS) : null, shorts: [] };
    try {
      const t = await yti("browse", "en", { browseId: id, params: SHORTS_TAB });
      const out: any[] = []; lockups(t, out);
      const seen = new Set<string>();
      c.shorts = out.filter((v) => !seen.has(v.id) && seen.add(v.id)).map((v) => ({ id: v.id, title: v.title, views: v.views })).slice(0, 48);
    } catch (_) { /* 쇼츠 탭 없음 */ }
    return c;
  } catch (_) { return null; }
}
const median = (xs: number[]) => { if (!xs.length) return null; const s = [...xs].sort((a, b) => a - b); return s[Math.floor(s.length / 2)]; };
const chanRow = (c: Chan) => ({ channel_id: c.channel_id, name: c.name, handle: c.handle, subs: c.subs, video_count: c.video_count, shorts: c.shorts,
  shorts_n: c.shorts.length, shorts_median: median(c.shorts.map((s) => s.views)), shorts_max: c.shorts.length ? Math.max(...c.shorts.map((s) => s.views)) : null,
  checked_at: new Date().toISOString() });

// 최근 10만 회 이상 쇼츠를 올린 채널 중 7일 안에 안 본 채널 최대 120개
async function chan(log: string[]) {
  const { data: big } = await sb.from("sc_hot").select("video_id,views").gte("views", 100000).order("views", { ascending: false }).limit(800);
  const ids = [...new Set((big || []).map((r: any) => r.video_id))];
  const cids = new Set<string>();
  for (let i = 0; i < ids.length; i += 200) {
    const { data } = await sb.from("sc_hot_videos").select("channel_id").in("video_id", ids.slice(i, i + 200));
    (data || []).forEach((r: any) => r.channel_id && cids.add(r.channel_id));
  }
  const { data: fresh } = await sb.from("sc_hot_channels").select("channel_id").gte("checked_at", new Date(Date.now() - 7 * 864e5).toISOString());
  const skip = new Set((fresh || []).map((r: any) => r.channel_id));
  const todo = [...cids].filter((c) => !skip.has(c)).slice(0, 120);
  const rows: any[] = [];
  await pool(todo, 4, async (id) => { const c = await chanOf(id); if (c) rows.push(chanRow(c)); });
  if (rows.length) await sb.from("sc_hot_channels").upsert(rows, { onConflict: "channel_id" });
  log.push(`채널 ${rows.length}/${todo.length}개 확인 (구독자 확인 ${rows.filter((r) => r.subs !== null).length})`);
}

// 우리 채널: 핸들 → 채널 id → 쇼츠 탭 조회수. 제목이 같은 sc_videos 에 youtube_id 를 채우고 stats 를 쌓는다
async function ours(log: string[]) {
  const { data: s } = await sb.from("sc_settings").select("value").eq("id", 1).maybeSingle();
  const v = s?.value || {};
  let cid = v.channel_id as string | undefined;
  if (!cid && v.handle) {
    const r = await yti("navigation/resolve_url", "en", { url: `https://www.youtube.com/@${String(v.handle).replace(/^@/, "")}` });
    cid = r?.endpoint?.browseEndpoint?.browseId;
  }
  if (!cid) { log.push("우리 채널 id 를 못 찾음 (설정 handle 확인)"); return; }
  const c = await chanOf(cid); if (!c) { log.push("우리 채널 읽기 실패"); return; }
  await sb.from("sc_hot_channels").upsert(chanRow(c), { onConflict: "channel_id" });
  const { data: s2 } = await sb.from("sc_settings").select("value").eq("id", 1).maybeSingle();
  await sb.from("sc_settings").upsert({ id: 1, value: { ...(s2?.value || {}), channel_id: cid, our: { subs: c.subs, video_count: c.video_count, at: new Date().toISOString() } } });
  const norm = (t: string) => String(t || "").toLowerCase().replace(/#\S+/g, "").replace(/[^\p{L}\p{N}]+/gu, "");
  const { data: vids } = await sb.from("sc_videos").select("id,title,youtube_id,stats,scheduled_at,uploaded_at,status").in("status", ["uploaded", "approved"]);
  let n = 0;
  for (const sv of c.shorts) {
    const m = (vids || []).find((x: any) => x.youtube_id === sv.id) || (vids || []).find((x: any) => !x.youtube_id && norm(x.title) && norm(x.title) === norm(sv.title));
    if (!m) continue;
    const at = new Date().toISOString(), st = { ...(m.stats || {}) };
    st.now = { views: sv.views, at }; st.hist = [...(st.hist || []), { views: sv.views, at }].slice(-80);
    const pub = Date.parse(m.scheduled_at || m.uploaded_at || at), age = (Date.now() - pub) / 3600e3;
    for (const [k, h] of [["h6", 6], ["h24", 24], ["h48", 48], ["d7", 168]] as const) if (age >= h && !st[k]) st[k] = { views: sv.views, at };
    await sb.from("sc_videos").update({ youtube_id: sv.id, stats: st, ...(m.status === "approved" ? { status: "uploaded" } : {}) }).eq("id", m.id); n++;
  }
  log.push(`우리 채널 구독자 ${c.subs ?? "?"} · 쇼츠 ${c.shorts.length}편 · 매칭 ${n}편`);
}

// only: "mine" → 우리 채널(ours)+조회수(mine) (3시간마다), "chan" → 채널 확인만, 없으면 전체 (매일 07:40)
async function run(only?: string) {
  const log: string[] = [], t0 = Date.now();
  const all = [["hot", hot], ["chan", chan], ["ours", ours], ["mine", mine]] as const;
  const pick: Record<string, string[]> = { mine: ["ours", "mine"], chan: ["chan"], ours: ["ours"] };
  const steps = all.filter(([n]) => !only || (pick[only] || [only]).includes(n));
  for (const [name, f] of steps) { try { await f(log); } catch (e) { log.push(`${name} 오류: ${String(e).slice(0, 120)}`); } }
  log.push(`${Math.round((Date.now() - t0) / 1000)}초`);
  const { data: s } = await sb.from("sc_settings").select("value").eq("id", 1).maybeSingle();
  await sb.from("sc_settings").upsert({ id: 1, value: { ...(s?.value || {}), [only ? `${only}_log` : "hot_log"]: { at: new Date().toISOString(), log } } });
  return log;
}

Deno.serve(async (req: Request) => {
  const body = await req.json().catch(() => ({}));
  if (body?.probe) return Response.json(await chanOf(body.probe));
  if (body?.wait) return Response.json({ ok: true, log: await run(body?.only) });
  // @ts-ignore EdgeRuntime 은 Supabase 런타임에 있다
  EdgeRuntime.waitUntil(run(body?.only));
  return Response.json({ ok: true, started: true }, { status: 202 });
});
