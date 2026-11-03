// 성과 관리 플랫폼 — 공개 리서치 (2026-11-03). 유튜브 공개 페이지 데이터(youtubei)만 쓴다. 로그인·OAuth·LLM 없음(토큰 0).
//  channel : 채널 주소·@핸들 → 구독자·총 조회수·개설일·영상 수, 최근 롱폼·쇼츠 조회수, 평균·중앙값, 터진 영상, 업로드 빈도, 좋아요율
//  topic   : 키워드 → 구독자 대비 조회수가 터진 영상 + 이 주제에서 잘하는 채널을 구독자 구간(1천·1만·10만)별로
//  similar : 채널 → 그 채널의 키워드·최근 제목으로 topic 을 돌려 비슷한 채널·터진 영상
//  video   : 영상 하나의 조회수·좋아요·게시일·하루 평균 조회수·채널 구독자 대비 배수
// 결과는 docs 'studio_cache' 12시간 캐시, 같은 IP 는 시간당 40회(캐시 응답은 횟수에 안 들어감).
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36";
const CORS = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type", "Access-Control-Allow-Methods": "POST, OPTIONS" };
const P_VIDEOS = "EgZ2aWRlb3PyBgQKAjoA", P_SHORTS = "EgZzaG9ydHPyBgUKA5oBAA%3D%3D";

async function yti(path: string, body: any, lang = "ko") {
  const r = await fetch(`https://www.youtube.com/youtubei/v1/${path}?prettyPrint=false`, { method: "POST",
    headers: { "User-Agent": UA, "Content-Type": "application/json", "Accept-Language": lang === "en" ? "en-US" : "ko-KR" },
    body: JSON.stringify({ context: { client: { clientName: "WEB", clientVersion: "2.20251001.00.00", hl: lang === "en" ? "en" : "ko", gl: lang === "en" ? "US" : "KR" } }, ...body }) });
  if (!r.ok) throw new Error("yt " + r.status);
  return await r.json();
}
async function pool<T>(xs: T[], n: number, f: (x: T) => Promise<void>) {
  let i = 0; await Promise.all(Array.from({ length: Math.min(n, xs.length) }, async () => { while (i < xs.length) { const x = xs[i++]; try { await f(x); } catch (_) { /* skip */ } } }));
}
const txt = (o: any): string => o == null ? "" : typeof o === "string" ? o : o.content ?? o.simpleText ?? (o.runs || []).map((r: any) => r.text).join("");
function all(node: any, key: string, out: any[] = [], depth = 0): any[] {
  if (!node || typeof node !== "object" || depth > 40) return out;
  if (Array.isArray(node)) { for (const x of node) all(x, key, out, depth + 1); return out; }
  if (key in node) out.push(node[key]);
  for (const k in node) if (k !== key) all(node[k], key, out, depth + 1);
  return out;
}
const first = (node: any, key: string) => all(node, key)[0];
const UNIT: Record<string, number> = { "천": 1e3, "만": 1e4, "억": 1e8, K: 1e3, M: 1e6, B: 1e9 };
function count(s: string): number | null {
  const m = String(s || "").replace(/,/g, "").match(/([\d.]+)\s*(천|만|억|[KMB])?/i);
  if (!m) return null;
  return Math.round(Number(m[1]) * (UNIT[(m[2] || "").toUpperCase()] || UNIT[m[2] || ""] || 1));
}
function agoDays(s: string): number | null {
  const m = String(s || "").match(/(\d+)\s*(초|분|시간|일|주|개월|년)\s*전/) || String(s || "").match(/(\d+)\s*(second|minute|hour|day|week|month|year)s?\s*ago/i);
  if (!m) return null;
  const k = ({ "초": 0, "분": 0, "시간": 0, "일": 1, "주": 7, "개월": 30.4, "년": 365, second: 0, minute: 0, hour: 0, day: 1, week: 7, month: 30.4, year: 365 } as any)[m[2].toLowerCase()] ?? 1;
  return Math.round(Number(m[1]) * k);
}
const secOf = (t: string) => { const p = String(t || "").split(":").map(Number); return !t || p.some(isNaN) ? 0 : p.reduce((a, b) => a * 60 + b, 0); };
const median = (a: number[]) => { if (!a.length) return 0; const s = [...a].sort((x, y) => x - y); const h = s.length >> 1; return s.length % 2 ? s[h] : Math.round((s[h - 1] + s[h]) / 2); };
const avg = (a: number[]) => a.length ? Math.round(a.reduce((x, y) => x + y, 0) / a.length) : 0;
function isoOf(s: string): string {
  if (!s) return "";
  const m = s.match(/(\d{4})\D+(\d{1,2})\D+(\d{1,2})/);
  if (m) return `${m[1]}-${m[2].padStart(2, "0")}-${m[3].padStart(2, "0")}`;
  const d = Date.parse(s); return isNaN(d) ? "" : new Date(d).toISOString().slice(0, 10);
}
const daysSince = (iso: string) => iso ? Math.max(1, Math.round((Date.now() - Date.parse(iso)) / 864e5)) : null;

// ───────── 영상 하나: 시청 다음(next) 응답 = 제목·조회수·좋아요·게시일·채널 ─────────
async function watchInfo(id: string) {
  const j = await yti("next", { videoId: id });
  const pri = first(j?.contents, "videoPrimaryInfoRenderer") || {}, sec = first(j?.contents, "videoSecondaryInfoRenderer") || {};
  const s = JSON.stringify(pri).slice(0, 200000);
  const lk = s.match(/사용자\s*([\d.,]+\s*(?:천|만|억)?)\s*명과 함께 이 동영상에 좋아요/) || s.match(/along with ([\d,]+) other/i);
  const owner = sec?.owner?.videoOwnerRenderer || {};
  const vc = first(pri, "videoViewCountRenderer") || {};
  let channel_id = owner?.navigationEndpoint?.browseEndpoint?.browseId || all(sec, "browseEndpoint").map((b: any) => b?.browseId).find((x: string) => /^UC/.test(x || "")) || "";
  let channel = txt(owner.title), title = txt(pri.title);
  if (!channel_id) { // 쇼츠 등 다른 형식: oembed 로 채널 주소를 받아 채널 id 로 바꾼다
    try {
      const r = await fetch(`https://www.youtube.com/oembed?format=json&url=${encodeURIComponent("https://www.youtube.com/watch?v=" + id)}`, { headers: { "User-Agent": UA } });
      if (r.ok) { const o = await r.json(); title ||= o.title || ""; channel ||= o.author_name || "";
        const rj = await yti("navigation/resolve_url", { url: o.author_url }); channel_id = rj?.endpoint?.browseEndpoint?.browseId || ""; }
    } catch (_) { /* 없음 */ }
  }
  return { title, views: count(txt(vc.viewCount)), likes: lk ? (count(lk[1]) ?? 0) + 1 : null, published: isoOf(txt(pri.dateText)), channel_id, channel };
}

// ───────── 채널 ─────────
async function resolveChannel(q: string): Promise<string> {
  q = String(q || "").trim();
  const id = q.match(/(UC[\w-]{22})/); if (id) return id[1];
  let url = q;
  if (/^@/.test(q)) url = "https://www.youtube.com/" + q;
  else if (!/^https?:/.test(q)) url = /youtu/.test(q) ? "https://" + q.replace(/^\/+/, "") : "https://www.youtube.com/@" + q.replace(/\s+/g, "");
  const v = url.match(/(?:v=|youtu\.be\/|shorts\/)([\w-]{11})/);
  if (v) { const w = await watchInfo(v[1]).catch(() => null); if (w?.channel_id) return w.channel_id; }
  const j = await yti("navigation/resolve_url", { url }).catch(() => null);
  const b = j?.endpoint?.browseEndpoint?.browseId;
  if (b && /^UC/.test(b)) return b;
  throw new Error("채널을 찾지 못했습니다. 채널 주소나 @핸들을 확인해 주세요.");
}
function lockups(j: any) {
  const out: any[] = [];
  for (const l of all(j, "lockupViewModel")) {
    const id = l?.contentId; if (!id || l?.contentType && !/VIDEO/.test(l.contentType)) continue;
    const md = l?.metadata?.lockupMetadataViewModel || {};
    const parts = all(md, "metadataParts").flat().map((p: any) => txt(p?.text));
    const vt = parts.find((p: string) => /조회수|views?/i.test(p)) || "";
    const at = parts.find((p: string) => /전$|ago$/.test(p)) || "";
    const badge = all(l?.contentImage, "thumbnailBadgeViewModel").map((b: any) => b?.text).find((t: string) => /^\d+:\d+/.test(t || "")) || "";
    out.push({ id, title: txt(md.title), views: /조회수 없음|No views/i.test(vt) ? 0 : count(vt) ?? 0, ago: at, days: agoDays(at), length: badge, length_s: secOf(badge), short: false });
  }
  for (const v of all(j, "videoRenderer")) {
    if (!v?.videoId || out.some((x) => x.id === v.videoId)) continue;
    const len = txt(v.lengthText), at = txt(v.publishedTimeText);
    out.push({ id: v.videoId, title: txt(v.title), views: count(txt(v.viewCountText)) ?? 0, ago: at, days: agoDays(at), length: len, length_s: secOf(len), short: false });
  }
  return out;
}
function shortsOf(j: any) {
  return all(j, "shortsLockupViewModel").map((s: any) => ({
    id: s?.onTap?.innertubeCommand?.reelWatchEndpoint?.videoId || String(s?.entityId || "").replace(/^shorts-shelf-item-/, ""),
    title: txt(s?.overlayMetadata?.primaryText), views: count(txt(s?.overlayMetadata?.secondaryText)) ?? 0, short: true,
  })).filter((s: any) => s.id);
}
async function aboutOf(home: any) {
  const tokens = all(home?.header, "continuationCommand").map((c: any) => c?.token).filter(Boolean);
  for (const t of tokens.slice(0, 2)) {
    try {
      const a = first(await yti("browse", { continuation: t }), "aboutChannelViewModel");
      if (a) return { joined: isoOf(txt(a.joinedDateText)), total_views: count(txt(a.viewCountText)), videos: count(txt(a.videoCountText)), country: txt(a.country) };
    } catch (_) { /* next */ }
  }
  return null;
}
async function channelBasics(id: string, full = true) {
  const home = await yti("browse", { browseId: id });
  const h = first(home?.header, "pageHeaderViewModel") || {};
  const rows = all(h?.metadata, "metadataParts").flat().map((p: any) => txt(p?.text)).filter(Boolean);
  const meta = home?.metadata?.channelMetadataRenderer || {};
  const subsT = rows.find((r: string) => /구독자|subscriber/i.test(r)) || "";
  const vidT = rows.find((r: string) => /동영상|video/i.test(r)) || "";
  const handle = rows.find((r: string) => /^@/.test(r)) || "";
  const avatar = (all(h?.image, "sources")[0] || []).slice(-1)[0]?.url || "";
  const base: any = { id, title: meta.title || txt(h?.title?.dynamicTextViewModel?.text), handle, url: `https://www.youtube.com/${handle || "channel/" + id}`,
    subs: /숨김|hidden/i.test(subsT) ? null : count(subsT), videos: count(vidT), keywords: String(meta.keywords || "").slice(0, 300), avatar, description: String(meta.description || "").slice(0, 300) };
  if (full) {
    const about = await aboutOf(home);
    if (about) { base.joined = about.joined; base.total_views = about.total_views; base.country = about.country; if (about.videos) base.videos = about.videos; }
  }
  return base;
}

async function channel(p: any) {
  const id = await resolveChannel(p.q);
  const base = await channelBasics(id);
  const [vj, sj] = await Promise.all([yti("browse", { browseId: id, params: P_VIDEOS }).catch(() => null), yti("browse", { browseId: id, params: P_SHORTS }).catch(() => null)]);
  const longs = vj ? lockups(vj).slice(0, 30) : [];
  const shorts = sj ? shortsOf(sj).slice(0, 30) : [];
  const subs = base.subs || 0;
  const lv = longs.map((v) => v.views), sv = shorts.map((v) => v.views);
  const lmed = median(lv), smed = median(sv);
  const mark = (v: any, med: number) => ({ ...v, x_median: med ? Math.round(v.views / med * 10) / 10 : null, x_subs: subs ? Math.round(v.views / subs * 10) / 10 : null });
  const L = longs.map((v) => mark(v, lmed)), S = shorts.map((v) => mark(v, smed));
  const days = longs.map((v) => v.days).filter((d): d is number => d != null);
  const age = daysSince(base.joined);
  const top = [...L].sort((a, b) => b.views - a.views).slice(0, 4).concat([...S].sort((a, b) => b.views - a.views).slice(0, 4));
  await pool(top, 4, async (v) => { const w = await watchInfo(v.id); v.likes = w.likes; v.published = w.published; });
  const er = top.filter((v) => v.likes != null && v.views).map((v) => v.likes / v.views * 100);
  const span = days.length ? Math.max(...days) : 0;
  return {
    channel: { ...base, age_days: age, age_months: age ? Math.round(age / 30.4 * 10) / 10 : null,
      subs_per_month: age && subs ? Math.round(subs / (age / 30.4)) : null, views_per_video: base.total_views && base.videos ? Math.round(base.total_views / base.videos) : null },
    stats: {
      long: { n: L.length, avg: avg(lv), median: lmed, best: lv.length ? Math.max(...lv) : 0, x_subs_median: subs ? Math.round(lmed / subs * 100) / 100 : null, avg_len_s: avg(longs.map((v) => v.length_s).filter(Boolean)) },
      short: { n: S.length, avg: avg(sv), median: smed, best: sv.length ? Math.max(...sv) : 0, x_subs_median: subs ? Math.round(smed / subs * 100) / 100 : null },
      uploads_30d: days.filter((d) => d <= 30).length, uploads_90d: days.filter((d) => d <= 90).length,
      per_week: days.length >= 2 && span > 0 ? Math.round(days.length / (span / 7) * 10) / 10 : null,
      like_rate: er.length ? Math.round(er.reduce((a, b) => a + b, 0) / er.length * 100) / 100 : null,
    },
    breakouts: [...L, ...S].filter((v) => (v.x_median ?? 0) >= 3 || (v.x_subs ?? 0) >= 3).sort((a, b) => (b.x_median ?? 0) - (a.x_median ?? 0)).slice(0, 10),
    longs: L, shorts: S,
  };
}

async function video(p: any) {
  const id = (String(p.q || "").trim().match(/(?:v=|youtu\.be\/|shorts\/|^)([\w-]{11})(?:$|[?&/#])/) || [])[1];
  if (!id) throw new Error("영상 주소를 확인해 주세요.");
  const w = await watchInfo(id);
  if (!w.channel_id) throw new Error("영상을 찾지 못했습니다.");
  const base = await channelBasics(w.channel_id, false);
  const days = daysSince(w.published);
  const views = w.views || 0;
  return { video: { id, title: w.title, views, likes: w.likes, published: w.published, days, views_per_day: days ? Math.round(views / days) : null,
    like_rate: w.likes && views ? Math.round(w.likes / views * 10000) / 100 : null, thumb: `https://i.ytimg.com/vi/${id}/hqdefault.jpg`, url: `https://www.youtube.com/watch?v=${id}` },
    channel: base, x_subs: base.subs ? Math.round(views / base.subs * 10) / 10 : null };
}

// ───────── 주제 ─────────
const FILTER: Record<string, string> = { week: "EgQIAxAB", month: "EgQIBBAB", year: "EgQIBRAB", any: "EgIQAQ%3D%3D", channels: "EgIQAg%3D%3D" };
function searchVideos(j: any) {
  const out = new Map<string, any>();
  for (const v of all(j, "videoRenderer")) {
    if (!v?.videoId) continue;
    const by = v.ownerText?.runs?.[0], len = txt(v.lengthText), at = txt(v.publishedTimeText);
    out.set(v.videoId, { id: v.videoId, title: txt(v.title), channel: by?.text || "", channel_id: by?.navigationEndpoint?.browseEndpoint?.browseId || "",
      views: count(txt(v.viewCountText)) ?? 0, length: len, length_s: secOf(len), ago: at, days: agoDays(at), short: secOf(len) > 0 && secOf(len) <= 180 });
  }
  for (const s of all(j, "shortsLockupViewModel")) {
    const id = s?.onTap?.innertubeCommand?.reelWatchEndpoint?.videoId; if (!id || out.has(id)) continue;
    out.set(id, { id, title: txt(s?.overlayMetadata?.primaryText), channel: "", channel_id: "", views: count(txt(s?.overlayMetadata?.secondaryText)) ?? 0, length: "", length_s: 0, ago: "", days: null, short: true });
  }
  return [...out.values()];
}
function searchChannels(j: any) {
  return all(j, "channelRenderer").map((c: any) => {
    const a = txt(c.subscriberCountText), b = txt(c.videoCountText);
    const subsT = /구독자|subscriber/i.test(a) ? a : /구독자|subscriber/i.test(b) ? b : "";
    return { id: c.channelId, title: txt(c.title), handle: /^@/.test(a) ? a : "", subs: subsT ? count(subsT) : null };
  }).filter((c: any) => c.id);
}
const TIERS: [string, number, number][] = [["1천 미만", 0, 1e3], ["1천~1만", 1e3, 1e4], ["1만~10만", 1e4, 1e5], ["10만 이상", 1e5, 1e12]];
const tierOf = (s: number | null) => s == null ? "알 수 없음" : (TIERS.find(([, a, b]) => s >= a && s < b) || TIERS[3])[0];

async function topic(p: any) {
  const q = String(p.q || "").trim(); if (!q) throw new Error("키워드를 넣어 주세요.");
  const queries: string[] = [...new Set<string>((p.queries || [q]).map((x: string) => String(x).trim()).filter(Boolean))].slice(0, 4);
  const period = FILTER[p.period] ? p.period : "month";
  const vids = new Map<string, any>(); const chs = new Map<string, any>();
  await pool(queries, 3, async (qq) => {
    const [vj, cj] = await Promise.all([yti("search", { query: qq, params: FILTER[period] }, p.lang), yti("search", { query: qq, params: FILTER.channels }, p.lang)]);
    for (const v of searchVideos(vj)) if (!vids.has(v.id)) vids.set(v.id, v);
    for (const c of searchChannels(cj)) if (!chs.has(c.id)) chs.set(c.id, c);
  });
  // 쇼츠 칸에는 채널이 없다 → 시청 정보로 채널을 붙인다 (최대 12개)
  await pool([...vids.values()].filter((v) => !v.channel_id).sort((a, b) => b.views - a.views).slice(0, 12), 4, async (v) => { const w = await watchInfo(v.id); v.channel_id = w.channel_id; v.channel = w.channel; });
  const need = [...new Set([...vids.values()].sort((a, b) => b.views - a.views).map((v) => v.channel_id).filter(Boolean))].filter((id) => !chs.has(id)).slice(0, 40);
  await pool(need, 6, async (id) => { const b = await channelBasics(id, false); chs.set(id, { id, title: b.title, handle: b.handle, subs: b.subs, videos: b.videos }); });
  const videos = [...vids.values()].filter((v) => v.channel_id).map((v) => { const c = chs.get(v.channel_id) || {}; return { ...v, channel: v.channel || c.title || "", subs: c.subs ?? null, x_subs: c.subs ? Math.round(v.views / Math.max(c.subs, 1) * 10) / 10 : null, tier: tierOf(c.subs ?? null) }; });
  const breakouts = videos.filter((v) => v.subs != null && v.views >= (p.min_views ?? 5000) && (v.x_subs ?? 0) >= (p.min_x ?? 1.5)).sort((a, b) => (b.x_subs - a.x_subs) || (b.views - a.views)).slice(0, 30);
  const byTier: Record<string, any[]> = {};
  for (const c of chs.values()) if (c.subs != null) (byTier[tierOf(c.subs)] ||= []).push(c);
  const pick: any[] = [];
  for (const [t] of TIERS) {
    const hot = videos.filter((v) => v.tier === t);
    const score = (c: any) => Math.max(0, ...hot.filter((v) => v.channel_id === c.id).map((v) => v.x_subs || 0));
    pick.push(...(byTier[t] || []).sort((a, b) => score(b) - score(a) || b.subs - a.subs).slice(0, p.per_tier ?? 5));
  }
  await pool(pick, 5, async (c) => {
    const b = await channelBasics(c.id, true);
    const vj = await yti("browse", { browseId: c.id, params: P_VIDEOS }).catch(() => null);
    const L = vj ? lockups(vj).slice(0, 12) : [];
    const age = daysSince(b.joined);
    Object.assign(c, { title: b.title || c.title, handle: b.handle || c.handle, url: b.url, avatar: b.avatar, videos: b.videos ?? c.videos, joined: b.joined || "", total_views: b.total_views ?? null,
      age_months: age ? Math.round(age / 30.4 * 10) / 10 : null, subs_per_month: age && c.subs ? Math.round(c.subs / (age / 30.4)) : null,
      recent_avg: avg(L.map((v) => v.views)), recent_median: median(L.map((v) => v.views)), recent_best: L.length ? [...L].sort((a, b) => b.views - a.views)[0] : null,
      uploads_30d: L.filter((v) => (v.days ?? 999) <= 30).length });
  });
  const tiers = TIERS.map(([t]) => ({ tier: t, channels: pick.filter((c) => tierOf(c.subs) === t),
    videos: videos.filter((v) => v.tier === t).sort((a, b) => (b.x_subs ?? 0) - (a.x_subs ?? 0)).slice(0, 6) }));
  return { q, queries, period, found_videos: vids.size, found_channels: chs.size, breakouts, tiers };
}

async function similar(p: any) {
  const id = await resolveChannel(p.q);
  const base = await channelBasics(id, false);
  const vj = await yti("browse", { browseId: id, params: P_VIDEOS }).catch(() => null);
  const titles = vj ? lockups(vj).slice(0, 15).map((v) => v.title) : [];
  const kw = String(base.keywords || "").replace(/"/g, "").split(/\s+/).filter((w) => w.length >= 2 && !base.title.includes(w)).slice(0, 4);
  const freq: Record<string, number> = {};
  const STOP = /^(the|and|for|with|you|how|what|why|이것|진짜|이유|방법|모든|그리고|하는|있는|없는|우리|오늘|정말|영상|이렇게|결국|지금|shorts)$/i;
  for (const t of titles) for (const w of t.replace(/[^\p{L}\p{N}\s]/gu, " ").split(/\s+/)) if (w.length >= 2 && !STOP.test(w)) freq[w] = (freq[w] || 0) + 1;
  const top = Object.entries(freq).sort((a, b) => b[1] - a[1]).map(([w]) => w).filter((w) => !kw.includes(w)).slice(0, 4);
  const words = [...kw, ...top];
  const queries = (p.queries || [words.slice(0, 2).join(" "), words.slice(2, 4).join(" "), top.slice(0, 2).join(" ")]).filter((x: string) => x && x.trim()).slice(0, 3);
  if (!queries.length) queries.push(base.title);
  const r: any = await topic({ ...p, q: queries[0], queries });
  for (const t of r.tiers) t.channels = t.channels.filter((c: any) => c.id !== id);
  r.breakouts = r.breakouts.filter((v: any) => v.channel_id !== id);
  return { base: { ...base, keywords_used: words }, ...r };
}

// ───────── 캐시·횟수 제한 ─────────
async function sha(s: string) { const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s)); return [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("").slice(0, 32); }
let PUB: string | null = null;
async function pub() { if (!PUB) { const { data } = await sb.rpc("publisher_id"); PUB = data; } return PUB; }
async function limited(req: Request) {
  const ip = (req.headers.get("x-forwarded-for") || "").split(",")[0].trim() || "x";
  const key = "rl-" + (await sha(ip + new Date().toISOString().slice(0, 13)));
  const owner = await pub();
  const { data } = await sb.from("docs").select("data").eq("owner", owner).eq("collection", "studio_rl").eq("id", key).maybeSingle();
  const n = (data?.data?.n || 0) + 1;
  await sb.from("docs").upsert({ owner, collection: "studio_rl", id: key, data: { n }, updated_at: new Date().toISOString() }, { onConflict: "owner,collection,id" });
  return n > 40;
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });
  const json = (o: any, s = 200) => Response.json(o, { status: s, headers: CORS });
  try {
    const p = await req.json().catch(() => ({}));
    const act = ["channel", "topic", "similar", "video"].includes(p.action) ? p.action : "channel";
    const ck = "c-" + (await sha(JSON.stringify([act, String(p.q || "").trim().toLowerCase(), p.period || "", p.lang || "", p.queries || ""])));
    const owner = await pub();
    if (!p.fresh) {
      const { data } = await sb.from("docs").select("data,updated_at").eq("owner", owner).eq("collection", "studio_cache").eq("id", ck).maybeSingle();
      if (data && Date.parse(data.updated_at) > Date.now() - 12 * 3600e3) return json({ ok: true, cached: data.updated_at, ...data.data });
    }
    if (await limited(req)) return json({ ok: false, error: "요청이 많습니다. 한 시간 뒤에 다시 시도해 주세요." }, 429);
    const out = act === "topic" ? await topic(p) : act === "similar" ? await similar(p) : act === "video" ? await video(p) : await channel(p);
    await sb.from("docs").upsert({ owner, collection: "studio_cache", id: ck, data: out, updated_at: new Date().toISOString() }, { onConflict: "owner,collection,id" });
    return json({ ok: true, ...out });
  } catch (e) { return json({ ok: false, error: String((e as Error)?.message || e).slice(0, 300) }); }
});
