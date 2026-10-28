// 벤치마킹 수집 (2026-10-29, 운영자: "구독자는 별로 없는데 영상 몇 개로 조회수가 터진 사람들을 조사해서 벤치마킹할 내용을 전달").
// 매일 새벽 벤치마킹 데스크(예약 작업)가 부른다. 유튜브 API 승인 전이라 트렌드 레이더(trend-collect)와 같은 youtubei 내부 API를 쓴다.
//  action "scan"   : 트렌드 레이더가 모은 최근 영상(trend_videos + 최신 trend_snaps)에 채널 구독자 수를 붙여 "조회수 ÷ 구독자" 이상치를 돌려준다.
//  action "search" : 검색어로 이번 달 영상·쇼츠를 찾아 같은 방식으로 돌려준다 (레이더 검색어 밖의 소재·포맷 탐색용).
//  action "detail" : 영상 하나의 제목·설명·길이·태그·자막 앞부분·썸네일(base64)을 돌려준다 (분석용).
// 채널 구독자 수는 docs(collection 'bench_ch', id = 채널 id)에 7일 캐시한다.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36";
const YTV = "2.20251001.00.00";

async function pool<T>(xs: T[], n: number, f: (x: T) => Promise<void>) {
  let i = 0; await Promise.all(Array.from({ length: Math.min(n, xs.length) }, async () => { while (i < xs.length) await f(xs[i++]); }));
}
const CLIENTS: Record<string, any> = {
  WEB: { clientName: "WEB", clientVersion: YTV },
  ANDROID: { clientName: "ANDROID", clientVersion: "19.09.37", androidSdkVersion: 30 },
  IOS: { clientName: "IOS", clientVersion: "19.09.3", deviceModel: "iPhone14,3" },
};
async function yti(path: string, body: any, lang = "ko", client = "WEB") {
  const c = CLIENTS[client];
  const r = await fetch(`https://www.youtube.com/youtubei/v1/${path}?prettyPrint=false`, { method: "POST",
    headers: { "User-Agent": client === "WEB" ? UA : client === "IOS" ? "com.google.ios.youtube/19.09.3 (iPhone14,3; U; CPU iOS 15_6 like Mac OS X)" : "com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip", "Content-Type": "application/json" },
    body: JSON.stringify({ context: { client: { ...c, hl: lang === "en" ? "en" : "ko", gl: lang === "en" ? "US" : "KR" } }, ...body }) });
  if (!r.ok) throw new Error("yt " + r.status);
  return await r.json();
}
const txt = (o: any) => o?.simpleText ?? (o?.runs || []).map((r: any) => r.text).join("") ?? "";
const num = (s: string | undefined) => { const d = String(s || "").replace(/[^\d]/g, ""); return d ? Number(d) : null; };

// "구독자 1.2만명" "3.4천명" "123명" "1.2M subscribers" → 숫자
function parseCount(s: string): number | null {
  let m = s.match(/구독자\s*([\d.,]+)\s*(천|만|억)?\s*명/);
  if (m) { const n = Number(m[1].replace(/,/g, "")); return Math.round(n * (({ "천": 1e3, "만": 1e4, "억": 1e8 } as any)[m[2] || ""] || 1)); }
  m = s.match(/([\d.,]+)\s*([KMB])?\s*subscribers/i);
  if (m) { const n = Number(m[1].replace(/,/g, "")); return Math.round(n * (({ K: 1e3, M: 1e6, B: 1e9 } as any)[(m[2] || "").toUpperCase()] || 1)); }
  return null;
}
async function channelInfo(id: string): Promise<{ subs: number | null; title: string; handle: string }> {
  const j = await yti("browse", { browseId: id });
  const s = JSON.stringify(j?.header || {}).slice(0, 200000);
  const m = s.match(/구독자\s*[\d.,]+\s*(?:천|만|억)?\s*명/) || s.match(/[\d.,]+\s*[KMB]?\s*subscribers/i);
  const handle = (s.match(/"(@[A-Za-z0-9._-]{2,40})"/) || [])[1] || "";
  const title = j?.metadata?.channelMetadataRenderer?.title || "";
  return { subs: m ? parseCount(m[0]) : null, title, handle };
}
async function subsFor(ids: string[], maxNew = 80): Promise<Map<string, any>> {
  const out = new Map<string, any>();
  const { data: pub } = await sb.rpc("publisher_id");
  for (let i = 0; i < ids.length; i += 200) {
    const { data } = await sb.from("docs").select("id,data,updated_at").eq("owner", pub).eq("collection", "bench_ch").in("id", ids.slice(i, i + 200));
    (data || []).forEach((r: any) => { if (Date.parse(r.updated_at) > Date.now() - 7 * 864e5 && r.data?.subs != null) out.set(r.id, r.data); });
  }
  const need = ids.filter((x) => x && !out.has(x)).slice(0, maxNew);
  const save: any[] = [];
  await pool(need, 4, async (id) => {
    try { const c = await channelInfo(id); if (c.subs != null) { out.set(id, c); save.push({ owner: pub, collection: "bench_ch", id, data: c, updated_at: new Date().toISOString() }); } } catch (_) { /* skip */ }
  });
  for (let i = 0; i < save.length; i += 200) await sb.from("docs").upsert(save.slice(i, i + 200), { onConflict: "owner,collection,id" });
  return out;
}
// 조회수 글자 → 숫자: "조회수 12만회" "조회수 123,456회" "1.2M views" "12K views"
function viewsOf(t: string): number | null {
  const m = String(t || "").replace(/,/g, "").match(/([\d.]+)\s*(천|만|억|K|M|B)?/i);
  if (!m) return null;
  return Math.round(Number(m[1]) * (({ "천": 1e3, "만": 1e4, "억": 1e8, K: 1e3, M: 1e6, B: 1e9 } as any)[(m[2] || "").toUpperCase()] || ({ "천": 1e3, "만": 1e4, "억": 1e8 } as any)[m[2] || ""] || 1));
}
const secOf = (t: string) => { const p = String(t || "").split(":").map(Number); return p.some(isNaN) ? 0 : p.reduce((a, b) => a * 60 + b, 0); };
async function oembed(id: string) {
  const r = await fetch(`https://www.youtube.com/oembed?format=json&url=${encodeURIComponent("https://www.youtube.com/shorts/" + id)}`, { headers: { "User-Agent": UA } });
  if (!r.ok) throw new Error("oembed " + r.status);
  return await r.json();
}
async function channelIdOf(authorUrl: string): Promise<string> {
  const j = await yti("navigation/resolve_url", { url: authorUrl });
  return j?.endpoint?.browseEndpoint?.browseId || "";
}
// 시청 페이지 HTML (API가 막혀도 열리는 경우가 많다): 설명·길이·조회수·채널
async function watchPage(id: string) {
  const r = await fetch(`https://www.youtube.com/watch?v=${id}&hl=ko&gl=KR`, { headers: { "User-Agent": UA, "Accept-Language": "ko-KR,ko;q=0.9" } });
  if (!r.ok) throw new Error("watch " + r.status);
  const h = await r.text();
  const m = h.match(/ytInitialPlayerResponse\s*=\s*(\{.+?\});(?:var|<\/script>)/s);
  const j = m ? JSON.parse(m[1]) : null;
  return j;
}
async function player(id: string) {
  let j: any = null, how = "";
  try { const x = await yti("player", { videoId: id }, "ko", "ANDROID"); if (x?.videoDetails?.videoId) { j = x; how = "player"; } } catch (_) { /* blocked */ }
  if (!j) { try { const x = await watchPage(id); if (x?.videoDetails?.videoId) { j = x; how = "watch"; } } catch (_) { /* blocked */ } }
  if (j) {
    const d = j.videoDetails || {}, mf = j?.microformat?.playerMicroformatRenderer || {};
    return { j, how, id, title: d.title || "", channel: d.author || "", channel_id: d.channelId || "", views: Number(d.viewCount) || 0, length_s: Number(d.lengthSeconds) || 0,
      keywords: (d.keywords || []).slice(0, 20), description: String(d.shortDescription || "").slice(0, 1500), published: mf.publishDate || mf.uploadDate || "",
      is_short: Number(d.lengthSeconds) > 0 && Number(d.lengthSeconds) <= 180 };
  }
  const o = await oembed(id);
  return { j: null, how: "oembed", id, title: o.title || "", channel: o.author_name || "", channel_id: await channelIdOf(o.author_url).catch(() => ""), views: 0, length_s: 0,
    keywords: [], description: "", published: "", is_short: false };
}
const shape = (v: any, ch: any) => {
  const subs = ch?.subs ?? null;
  return { video_id: v.video_id || v.id, url: (v.is_short ? "https://www.youtube.com/shorts/" : "https://www.youtube.com/watch?v=") + (v.video_id || v.id), title: v.title, channel: v.channel || ch?.title || "", channel_id: v.channel_id,
    handle: ch?.handle || "", subs, views: v.views, ratio: subs ? Math.round((v.views / Math.max(subs, 1)) * 10) / 10 : null, published: v.published || v.published_est || "", length: v.length_text || (v.length_s ? `${Math.floor(v.length_s / 60)}:${String(v.length_s % 60).padStart(2, "0")}` : ""),
    is_short: !!v.is_short, thumb: `https://i.ytimg.com/vi/${v.video_id || v.id}/hqdefault.jpg`, cats: v.cats || [], lang: v.lang || "" };
};
const filt = (rows: any[], p: any) => rows.filter((r) => r.subs != null && r.views >= (p.min_views ?? 30000) && r.subs <= (p.max_subs ?? 100000) && (r.ratio ?? 0) >= (p.min_ratio ?? 5))
  .sort((a, b) => (b.ratio - a.ratio) || (b.views - a.views)).slice(0, p.limit ?? 40);

async function scan(p: any) {
  const since = new Date(Date.now() - (p.days ?? 30) * 864e5).toISOString();
  const { data: vids } = await sb.from("trend_videos").select("video_id,title,channel,channel_id,length_text,published_est,cats,lang").gte("published_est", since).limit(3000);
  const ids = (vids || []).map((v: any) => v.video_id);
  const views = new Map<string, number>();
  for (let i = 0; i < ids.length; i += 300) {
    const { data } = await sb.from("trend_snaps").select("video_id,views,day").in("video_id", ids.slice(i, i + 300)).order("day", { ascending: false });
    (data || []).forEach((s: any) => { if (!views.has(s.video_id)) views.set(s.video_id, s.views); });
  }
  const cand = (vids || []).map((v: any) => ({ ...v, views: views.get(v.video_id) || 0, is_short: /^0:[0-5]\d$|^1:00$/.test(v.length_text || "") })).filter((v: any) => v.views >= (p.min_views ?? 30000));
  const all = [...new Set(cand.sort((a: any, b: any) => b.views - a.views).map((v: any) => v.channel_id))] as string[];
  const ch = await subsFor(all, p.max_new ?? 80);
  const rows = cand.map((v: any) => shape(v, ch.get(v.channel_id)));
  return { checked: cand.length, channels: ch.size, channels_total: all.length, pending_channels: all.length - ch.size, items: filt(rows, p) };
}

function collectVids(node: any, out: Map<string, any>) {
  if (!node || typeof node !== "object") return;
  if (Array.isArray(node)) { for (const x of node) collectVids(x, out); return; }
  const v = node.videoRenderer;
  if (v?.videoId) {
    const by = v.ownerText?.runs?.[0];
    const len = txt(v.lengthText);
    out.set(v.videoId, { id: v.videoId, title: txt(v.title), channel: by?.text || "", channel_id: by?.navigationEndpoint?.browseEndpoint?.browseId || "",
      views: viewsOf(txt(v.viewCountText)) || 0, length_s: secOf(len), length_text: len, published: txt(v.publishedTimeText), is_short: secOf(len) > 0 && secOf(len) <= 180 });
    return;
  }
  const sl = node.shortsLockupViewModel;
  const sid = sl?.onTap?.innertubeCommand?.reelWatchEndpoint?.videoId;
  if (sid && !out.has(sid)) {
    out.set(sid, { id: sid, title: sl?.overlayMetadata?.primaryText?.content || "", channel: "", channel_id: "", views: viewsOf(sl?.overlayMetadata?.secondaryText?.content || "") || 0,
      length_s: 0, length_text: "", published: "", is_short: true });
    return;
  }
  for (const k in node) collectVids(node[k], out);
}
async function search(p: any) {
  const qs: string[] = (p.queries || (p.q ? [p.q] : [])).slice(0, 12);
  const found = new Map<string, any>();
  await pool(qs, 3, async (q) => { try { collectVids(await yti("search", { query: q, params: p.params || "EgIIBA==" }, p.lang || "ko"), found); } catch (_) { /* skip */ } });
  const minV = p.min_views ?? 30000;
  const vids = [...found.values()].filter((v) => v.views >= minV);
  // 쇼츠 칸에는 채널이 없다 → oembed 로 채널 주소를 받아 채널 id 로 바꾼다 (최대 30개)
  await pool(vids.filter((v) => !v.channel_id).slice(0, 30), 4, async (v) => {
    try { const o = await oembed(v.id); v.channel = o.author_name || ""; v.channel_id = await channelIdOf(o.author_url); } catch (_) { /* skip */ }
  });
  const ok = vids.filter((v) => v.channel_id);
  const ch = await subsFor([...new Set(ok.map((v) => v.channel_id))], p.max_new ?? 60);
  return { queries: qs, found: found.size, checked: ok.length, items: filt(ok.map((v) => shape(v, ch.get(v.channel_id))), p) };
}

async function probe(p: any) {
  const id = p.id || "dQw4w9WgXcQ", out: any = {};
  for (const c of ["ANDROID", "IOS", "WEB"]) { try { const x = await yti("player", { videoId: id }, "ko", c); out["player_" + c] = x?.videoDetails ? "ok" : (x?.playabilityStatus?.status || "empty"); } catch (e) { out["player_" + c] = String(e); } }
  try { const x = await yti("next", { videoId: id }); out.next = x?.contents ? "ok" : "empty"; } catch (e) { out.next = String(e); }
  try { const x = await watchPage(id); out.watch = x?.videoDetails ? "ok" : "no data"; } catch (e) { out.watch = String(e); }
  try { const o = await oembed(id); out.oembed = o?.author_url || "ok"; out.resolve = await channelIdOf(o.author_url); } catch (e) { out.oembed = String(e); }
  try { const r = await fetch(`https://i.ytimg.com/vi/${id}/hqdefault.jpg`); out.thumb = r.status; } catch (e) { out.thumb = String(e); }
  return out;
}

async function detail(p: any) {
  const v: any = await player(p.id);
  let captions = "";
  try {
    const tracks = v.j?.captions?.playerCaptionsTracklistRenderer?.captionTracks || [];
    const t = tracks.find((x: any) => /^ko/.test(x.languageCode)) || tracks.find((x: any) => /^en/.test(x.languageCode)) || tracks[0];
    if (t?.baseUrl) {
      const r = await fetch(t.baseUrl + "&fmt=json3", { headers: { "User-Agent": UA } });
      const j = await r.json().catch(() => null);
      captions = (j?.events || []).map((e: any) => (e.segs || []).map((s: any) => s.utf8).join("")).join(" ").replace(/\s+/g, " ").slice(0, 6000);
    }
  } catch (_) { /* no captions */ }
  let thumb_b64 = "";
  for (const q of ["maxresdefault", "hqdefault", "hq720"]) {
    try { const r = await fetch(`https://i.ytimg.com/vi/${p.id}/${q}.jpg`); if (r.ok) { const b = new Uint8Array(await r.arrayBuffer()); if (b.length > 3000) { let s = ""; for (let i = 0; i < b.length; i += 8192) s += String.fromCharCode(...b.subarray(i, i + 8192)); thumb_b64 = btoa(s); break; } } } catch (_) { /* next */ }
  }
  const ch = (await subsFor([v.channel_id])).get(v.channel_id);
  delete (v as any).j;
  return { ...shape(v, ch), source: (v as any).how, keywords: v.keywords, description: v.description, length_s: v.length_s, captions, thumb_b64 };
}

Deno.serve(async (req: Request) => {
  try {
    const p = await req.json().catch(() => ({}));
    const out = p.action === "search" ? await search(p) : p.action === "detail" ? await detail(p) : p.action === "probe" ? await probe(p) : await scan(p);
    return Response.json({ ok: true, ...out });
  } catch (e) { return Response.json({ ok: false, error: String(e).slice(0, 300) }, { status: 500 }); }
});
