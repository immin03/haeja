// 유튜브 채널 공개 숫자(구독자·총 조회·영상 수) 새로고침 — 유튜브 API·스튜디오 없이 채널 공개 페이지에서 읽는다 (2026-11-03 대표님: "브리핑 구독자 수가 업데이트가 안 돼, 새로고침 버튼")
// - POST {t}  : (관리자) 지금 읽어서 docs agent 'yt-channel' 에 subs·views_total·videos·at(source:'public') 로 저장하고 결과를 돌려준다
// - POST {cron:true} : 같은 저장 (지금은 cron 없음 — 버튼을 누를 때만) — 공개 숫자라 인증 없이도 저장만 한다 (social-publish의 {} cron 호출과 같은 방식)
// - GET       : 저장 없이 읽기만 (점검용)
// 공개 페이지의 구독자 수는 1천 명부터 "1.5K"처럼 반올림된다(approx:true). 그 전까지는 정확한 숫자.
// verify_jwt = false (CORS preflight 때문) — 저장은 app_config.admins 에 있는 이메일만.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const cors = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type", "Access-Control-Allow-Methods": "GET, POST, OPTIONS" };
const json = (o: unknown, status = 200) => new Response(JSON.stringify(o), { status, headers: { ...cors, "Content-Type": "application/json" } });
const CHANNEL = "https://www.youtube.com/@valuenote_korea";

async function isAdmin(token: string) {
  const { data } = await sb.auth.getUser(token || "");
  const email = data?.user?.email; if (!email) return null;
  const { data: cfg } = await sb.from("app_config").select("value").eq("key", "admins").maybeSingle();
  return Array.isArray(cfg?.value) && cfg!.value.includes(email) ? data!.user : null;
}

// "1.5K subscribers" → 1500, "150 subscribers" → 150, "2.3M views" → 2300000, "1,234 videos" → 1234
function num(s: string | undefined): { n: number | null; approx: boolean } {
  if (!s) return { n: null, approx: false };
  const m = s.replace(/,/g, "").match(/([\d.]+)\s*([KMB])?/i); if (!m) return { n: null, approx: false };
  const mul = { K: 1e3, M: 1e6, B: 1e9 }[(m[2] || "").toUpperCase() as "K" | "M" | "B"] || 1;
  return { n: Math.round(parseFloat(m[1]) * mul), approx: !!m[2] };
}
function pick(html: string, key: string): string | undefined {
  // 새 형식: "subscriberCountText":"1.5K subscribers"  /  옛 형식: "subscriberCountText":{"simpleText":"150 subscribers"} 또는 {"runs":[{"text":"150 subscribers"}]}
  const a = html.match(new RegExp(`"${key}":"([^"]+)"`)); if (a) return a[1];
  const b = html.match(new RegExp(`"${key}":\\{"simpleText":"([^"]+)"`)); if (b) return b[1];
  const c = html.match(new RegExp(`"${key}":\\{"runs":\\[\\{"text":"([^"]+)"`)); if (c) return c[1];
  // 채널 소개 패널(aboutChannelViewModel)의 표시 문자열
  const d = html.match(new RegExp(`"${key}":"([^"]*)"`, "i")); return d ? d[1] : undefined;
}

async function read() {
  const r = await fetch(CHANNEL + "/about?hl=en&gl=US", { headers: {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9", "Cookie": "CONSENT=YES+1; SOCS=CAI" } });
  if (!r.ok) throw new Error("youtube HTTP " + r.status);
  const html = await r.text();
  const subsT = pick(html, "subscriberCountText"), viewsT = pick(html, "viewCountText"), vidT = pick(html, "videoCountText");
  const subs = num(subsT), views = num(viewsT), videos = num(vidT);
  if (subs.n == null) throw new Error("구독자 수를 페이지에서 찾지 못했습니다 (페이지 형식이 바뀐 듯)");
  const id = (html.match(/"channelId":"(UC[^"]+)"/) || [])[1] || null;
  return { subs: subs.n, subs_approx: subs.approx, subs_text: subsT, views_total: views.n, videos: videos.n, channel_id: id, at: new Date().toISOString(), source: "public" };
}

// 2026-11-06 대표님: "쇼츠 조회 이거보다 많이 되었는데", "여전히 안 바뀌는데"
// 공개 영상 페이지는 조회수를 빼고 내려오는 때가 많아(60편 중 9편만) 믿을 수 없다 → 채널에 연결된 구글 로그인(youtube_account)으로 유튜브 API를 읽는다.
//  - Data API videos.list(statistics): 최근 90일 영상별 정확한 조회수 → youtube_posts.stats.public
//  - Analytics API: 쇼츠 유효 조회(engagedViews, 최근 90일)·롱폼 시청시간(최근 365일) → docs agent 'yt-channel'.api (수익 창출 조건 숫자)
const VN_HANDLE = "@valuenote_korea";
async function ytToken(): Promise<string> {
  const { data: a } = await sb.from("youtube_account").select("id,access_token,refresh_token,expires_at").eq("handle", VN_HANDLE).maybeSingle();
  if (!a?.refresh_token) throw new Error("밸류노트 유튜브 계정 연결이 없습니다");
  if (a.access_token && a.expires_at && Date.parse(a.expires_at) > Date.now() + 120e3) return a.access_token as string;
  const form = new URLSearchParams({ client_id: Deno.env.get("YOUTUBE_CLIENT_ID") || "", client_secret: Deno.env.get("YOUTUBE_CLIENT_SECRET") || "", grant_type: "refresh_token", refresh_token: a.refresh_token as string });
  const t = await (await fetch("https://oauth2.googleapis.com/token", { method: "POST", body: form })).json();
  if (!t.access_token) throw new Error("유튜브 로그인 갱신 실패(" + (t.error || "?") + ") — 관리자에서 유튜브 다시 연결 필요");
  await sb.from("youtube_account").update({ access_token: t.access_token, expires_at: new Date(Date.now() + (t.expires_in || 3600) * 1000).toISOString(), updated_at: new Date().toISOString() }).eq("id", a.id);
  return t.access_token;
}
async function gget(url: string, tok: string) {
  const r = await fetch(url, { headers: { Authorization: "Bearer " + tok } });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error((j?.error?.message || "HTTP " + r.status).slice(0, 160));
  return j;
}
const ymd = (ms: number) => new Date(ms + 9 * 3600e3).toISOString().slice(0, 10);
async function apiRefresh() {
  const tok = await ytToken(), at = new Date().toISOString();
  const since = new Date(Date.now() - 90 * 864e5).toISOString();
  const { data: rows } = await sb.from("youtube_posts").select("id,youtube_id,kind").not("youtube_id", "is", null).or(`uploaded_at.gte.${since},uploaded_at.is.null`);
  const list = rows || [], views: Record<string, number> = {};
  for (let i = 0; i < list.length; i += 50) {
    const ids = list.slice(i, i + 50).map((r) => r.youtube_id).join(",");
    const j = await gget(`https://www.googleapis.com/youtube/v3/videos?part=statistics&id=${ids}`, tok);
    for (const it of j.items || []) views[it.id] = Number(it.statistics?.viewCount ?? 0);
  }
  let done = 0, shorts = 0, longs = 0;
  for (const row of list) {
    const v = views[row.youtube_id as string]; if (v == null) continue;
    const { error } = await sb.rpc("yt_set_public_views", { p_id: row.id, p_views: v, p_at: at, p_by: "YouTube API" });
    if (!error) { done++; if (row.kind === "short") shorts += v; else longs += v; }
  }
  // 수익 창출 조건 숫자 (분석 데이터는 보통 1~2일 늦게 잡힌다)
  let mon: Record<string, unknown> | null = null, mon_error: string | null = null;
  try {
    const end = ymd(Date.now() - 864e5), s90 = ymd(Date.now() - 90 * 864e5), s365 = ymd(Date.now() - 365 * 864e5);
    const base = "https://youtubeanalytics.googleapis.com/v2/reports?ids=channel==MINE";
    const sh = await gget(`${base}&startDate=${s90}&endDate=${end}&metrics=views,engagedViews&filters=creatorContentType==shorts`, tok);
    const lg = await gget(`${base}&startDate=${s365}&endDate=${end}&metrics=views,estimatedMinutesWatched&filters=creatorContentType==videoOnDemand`, tok);
    const r1 = (sh.rows || [[0, 0]])[0], r2 = (lg.rows || [[0, 0]])[0];
    mon = { at, end_date: end, shorts_views_90d: Number(r1[0] || 0), shorts_engaged_90d: Number(r1[1] || 0), long_views_12m: Number(r2[0] || 0), long_watch_h_12m: Math.round(Number(r2[1] || 0) / 60 * 10) / 10 };
  } catch (e) { mon_error = String((e as Error).message || e); }
  return { videos_checked: list.length, videos_updated: done, shorts_views: shorts, long_views: longs, videos_at: at, api: mon, api_error: mon_error };
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  try {
    if (req.method === "GET") return json(await read());
    const body = await req.json().catch(() => ({}));
    const user = body.cron === true ? null : await isAdmin(body.t || ""); if (!user && body.cron !== true) return json({ error: "관리자만 쓸 수 있습니다" }, 403);
    const now = await read();
    const { data: row } = await sb.from("docs").select("owner,data").eq("collection", "agent").eq("id", "yt-channel").maybeSingle();
    const prev = (row?.data || {}) as Record<string, unknown>;
    let owner = row?.owner as string | undefined;
    if (!owner) { const { data: cfg } = await sb.from("app_config").select("value").eq("key", "publisher").maybeSingle(); owner = (cfg?.value as string) || user?.id; if (!owner) return json({ error: "publisher 설정이 없습니다" }, 500); }
    const hist = Array.isArray(prev.history) ? (prev.history as unknown[]) : [];
    const data = { ...prev, subs: now.subs, subs_approx: now.subs_approx, subs_text: now.subs_text, views_total: now.views_total, videos: now.videos, channel_id: now.channel_id || prev.channel_id || null, at: now.at, source: "public",
      history: [...hist, { at: now.at, subs: now.subs, views_total: now.views_total, source: "public" }].slice(-90) };
    const { error } = await sb.from("docs").upsert({ owner, collection: "agent", id: "yt-channel", data, updated_at: now.at }, { onConflict: "owner,collection,id" });
    if (error) return json({ error: error.message }, 500);
    const vids = await apiRefresh().catch((e) => ({ videos_error: String((e as Error).message || e) })) as Record<string, unknown>;
    if (vids.api) await sb.from("docs").update({ data: { ...data, api: vids.api } }).eq("owner", owner).eq("collection", "agent").eq("id", "yt-channel");
    return json({ ok: true, ...now, prev_subs: prev.subs ?? null, prev_at: prev.at ?? null, ...vids });
  } catch (e) { return json({ error: String((e as Error).message || e) }, 500); }
});
