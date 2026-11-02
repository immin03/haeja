// 황제의 일기 성과 수집 (pg_cron emperor-stats: 3시간마다) — LLM 없음, 숫자만 모은다
// 인스타 릴스 · 쓰레드 글 · 유튜브 쇼츠 → ed_stats (하루 1줄씩, 같은 날은 최신값으로 덮어씀)
// 틱톡은 API가 없어 예약 작업(크롬)이 ed_stats 에 직접 넣는다.
// 분석은 매일 아침 예약 작업이 ed_stats 를 읽어 ed_reports 에 쓴다.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const IG = "https://graph.instagram.com/v23.0", TH = "https://graph.threads.net/v1.0", YT = "https://www.googleapis.com/youtube/v3";
const ED_CH = "UCR5ao2RmISHYMmDinRPIaDw";
const kst = () => new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);
const IG_M = ["views", "reach", "saved", "shares", "likes", "comments", "total_interactions", "ig_reels_avg_watch_time", "ig_reels_video_view_total_time"];
const TH_M = ["views", "likes", "replies", "reposts", "quotes", "shares"];

async function getj(url: string, q: Record<string, string> = {}, h: Record<string, string> = {}) {
  const r = await fetch(url + (Object.keys(q).length ? "?" + new URLSearchParams(q) : ""), { headers: h });
  const j = await r.json().catch(() => ({}));
  if (!r.ok || j.error) throw new Error(j?.error?.message || JSON.stringify(j.error || "") || `HTTP ${r.status}`);
  return j;
}
const read = (j: any, out: Record<string, number>) => { for (const m of j.data || []) out[m.name] = Number(m.values?.[0]?.value ?? m.total_value?.value ?? 0); };
async function save(platform: string, ext_id: string, m: Record<string, unknown>, extra: Record<string, unknown> = {}) {
  await sb.from("ed_stats").upsert({ day: kst(), platform, ext_id, m, collected_at: new Date().toISOString(), ...extra });
}
const hoursSince = (t?: string) => t ? Math.round((Date.now() - Date.parse(t)) / 36e5) : null;

async function instagram(acc: any, posts: any[], errs: string[]) {
  for (const p of posts.filter(p => p.ig_media_id)) {
    const out: Record<string, number> = {};
    try { read(await getj(`${IG}/${p.ig_media_id}/insights`, { metric: IG_M.join(","), access_token: acc.access_token }), out); }
    catch { for (const m of IG_M) { try { read(await getj(`${IG}/${p.ig_media_id}/insights`, { metric: m, access_token: acc.access_token }), out); } catch { /* 건너뜀 */ } } }
    if (!Object.keys(out).length) { errs.push("ig " + p.ep); continue; }
    await save("instagram", p.ig_media_id, { ...out, hours: hoursSince(p.ig_at) }, { ep: p.ep, title: p.title, posted_at: p.ig_at });
  }
  try { const me = await getj(`${IG}/me`, { fields: "followers_count,media_count", access_token: acc.access_token }); await save("instagram", "account", { followers: me.followers_count, media: me.media_count }); }
  catch (e) { errs.push("ig account: " + (e as Error).message); }
}

async function threads(acc: any, posts: any[], errs: string[]) {
  for (const p of posts.filter(p => p.th_media_id)) {
    const out: Record<string, number> = {};
    try { read(await getj(`${TH}/${p.th_media_id}/insights`, { metric: TH_M.join(","), access_token: acc.access_token }), out); }
    catch (e) { errs.push(`th ${p.ep}: ${(e as Error).message}`); continue; }
    await save("threads", p.th_media_id, { ...out, hours: hoursSince(p.th_at) }, { ep: p.ep, title: p.title, posted_at: p.th_at });
  }
  try { const o: Record<string, number> = {}; read(await getj(`${TH}/${acc.account_id}/threads_insights`, { metric: "followers_count", access_token: acc.access_token }), o); await save("threads", "account", { followers: o.followers_count }); }
  catch (e) { errs.push("th account: " + (e as Error).message); }
}

// 유튜브 토큰: 황제의 일기 채널 연결(id=2)이 있으면 그것, 없으면 밸류노트 토큰(id=1)으로 공개 통계만 읽는다
// (조회·좋아요·댓글·구독자는 공개 데이터라 어느 계정 토큰으로도 읽힌다. 평균 시청 비율·구독 증가는 id=2 연결 시에만)
async function ytToken(): Promise<{ tok: string; own: boolean } | null> {
  for (const id of [2, 1]) {
    const { data: a } = await sb.from("youtube_account").select("*").eq("id", id).maybeSingle();
    if (!a?.refresh_token) continue;
    const own = a.channel_id === ED_CH;
    if (id === 2 && !own) continue;
    if (a.access_token && Date.parse(a.expires_at) - Date.now() > 120e3) return { tok: a.access_token, own };
    const form = new URLSearchParams({ client_id: Deno.env.get("YOUTUBE_CLIENT_ID")!, client_secret: Deno.env.get("YOUTUBE_CLIENT_SECRET")!, grant_type: "refresh_token", refresh_token: a.refresh_token });
    const t = await (await fetch("https://oauth2.googleapis.com/token", { method: "POST", body: form })).json();
    if (!t.access_token) continue;
    await sb.from("youtube_account").update({ access_token: t.access_token, expires_at: new Date(Date.now() + (t.expires_in || 3600) * 1000).toISOString(), updated_at: new Date().toISOString() }).eq("id", id);
    return { tok: t.access_token, own };
  }
  return null;
}

async function youtube(posts: any[], errs: string[]) {
  const t = await ytToken();
  if (!t) { errs.push("youtube: 사용할 유튜브 토큰 없음"); return; }
  const H = { Authorization: "Bearer " + t.tok };
  const ch = (await getj(`${YT}/channels`, { part: "statistics,contentDetails", id: ED_CH }, H)).items?.[0];
  await save("youtube", "account", { subscribers: Number(ch?.statistics?.subscriberCount ?? 0), views: Number(ch?.statistics?.viewCount ?? 0), videos: Number(ch?.statistics?.videoCount ?? 0) });
  const pl = await getj(`${YT}/playlistItems`, { part: "contentDetails,snippet", playlistId: ch.contentDetails.relatedPlaylists.uploads, maxResults: "50" }, H);
  const vids = (pl.items || []).map((i: any) => ({ id: i.contentDetails.videoId, title: i.snippet.title as string, at: i.contentDetails.videoPublishedAt }));
  // ed_posts 와 짝짓기 (제목 앞부분이 같으면 같은 편)
  for (const p of posts) if (!p.yt_video_id) {
    const v = vids.find((v: any) => v.title.startsWith(p.title));
    if (v) { p.yt_video_id = v.id; await sb.from("ed_posts").update({ yt_video_id: v.id }).eq("id", p.id); }
  }
  if (!vids.length) return;
  const st = await getj(`${YT}/videos`, { part: "statistics,snippet", id: vids.map((v: any) => v.id).join(",") }, H);
  // 분석 API: 평균 시청 시간·비율·구독 증가 (영상별, 공개 후 누적)
  const an: Record<string, Record<string, number>> = {};
  if (t.own) try {
    const r = await getj("https://youtubeanalytics.googleapis.com/v2/reports", {
      ids: "channel==" + ED_CH, startDate: "2026-10-01", endDate: kst(), dimensions: "video",
      metrics: "views,averageViewDuration,averageViewPercentage,subscribersGained,shares,likes", filters: "video==" + vids.map((v: any) => v.id).join(","), maxResults: "50",
    }, H);
    const cols = (r.columnHeaders || []).map((c: any) => c.name);
    for (const row of r.rows || []) { const o: Record<string, number> = {}; cols.forEach((c: string, i: number) => { if (i) o[c] = Number(row[i]); }); an[row[0]] = o; }
  } catch (e) { errs.push("yt analytics: " + (e as Error).message); }
  for (const v of st.items || []) {
    const p = posts.find(p => p.yt_video_id === v.id);
    const s = v.statistics || {};
    const a = an[v.id] || {};
    await save("youtube", v.id, {
      views: Number(s.viewCount ?? 0), likes: Number(s.likeCount ?? 0), comments: Number(s.commentCount ?? 0),
      avg_view_sec: a.averageViewDuration, avg_view_pct: a.averageViewPercentage, subs_gained: a.subscribersGained, shares: a.shares,
      hours: hoursSince(v.snippet?.publishedAt),
    }, { ep: p?.ep ?? null, title: v.snippet?.title, posted_at: v.snippet?.publishedAt });
  }
}

Deno.serve(async (req: Request) => {
  await req.json().catch(() => ({}));
  const errs: string[] = [];
  try {
    const { data: posts } = await sb.from("ed_posts").select("id,ep,title,ig_media_id,ig_at,th_media_id,th_at,yt_video_id").order("ep");
    const { data: accs } = await sb.from("ed_accounts").select("*");
    const acc = Object.fromEntries((accs || []).map((a: any) => [a.platform, a]));
    if (acc.instagram) await instagram(acc.instagram, posts || [], errs).catch(e => errs.push("ig: " + e.message));
    if (acc.threads) await threads(acc.threads, posts || [], errs).catch(e => errs.push("th: " + e.message));
    await youtube(posts || [], errs).catch(e => errs.push("yt: " + e.message));
    const { count } = await sb.from("ed_stats").select("*", { count: "exact", head: true }).eq("day", kst());
    return Response.json({ ok: true, day: kst(), rows_today: count, errs });
  } catch (e) {
    return Response.json({ ok: false, error: String((e as Error)?.message || e), errs }, 500);
  }
});
