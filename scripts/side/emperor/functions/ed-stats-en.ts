// The Emperor's Diary (EN, @EmperorsDiary-en) 성과 수집 — 한국 채널(ed-stats)과 완전히 분리 (2026-11-15 대표 "영어 채널하고 한국 채널은 별도로 분리, 성과 별도로")
// 결과: ed_stats platform 'youtube_en' — ext_id 'account'(구독·총조회·영상 수) / 영상 id(조회·좋아요·댓글) / 'search_rank'(하루 1번, 목표 검색어 순위)
// 영어 채널 로그인 연결이 없어 공개 숫자만 읽는다(조회·좋아요·댓글·구독은 공개 데이터라 어느 계정 토큰으로도 읽힌다).
// cron emperor-stats-en: 3시간마다. 검색 순위는 emperor-stats-en-rank(KST 10:55) 하루 1번만(search.list 1회 100 단위 → 8개 800 단위/일).
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const YT = "https://www.googleapis.com/youtube/v3";
const EN_CH = "UCRvSvKOjbsEXKY03TCP9I1w";
const PF = "youtube_en";
const kstNow = () => new Date(Date.now() + 9 * 3600e3);
const kst = () => kstNow().toISOString().slice(0, 10);

async function getj(url: string, q: Record<string, string>, H: Record<string, string>) {
  const r = await fetch(url + "?" + new URLSearchParams(q), { headers: H });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(j.error?.message || `HTTP ${r.status}`);
  return j;
}
async function save(ext_id: string, m: Record<string, unknown>, extra: Record<string, unknown> = {}) {
  await sb.from("ed_stats").upsert({ day: kst(), platform: PF, ext_id, m, collected_at: new Date().toISOString(), ...extra });
}
async function token(): Promise<string | null> {
  for (const id of [2, 1]) {
    const { data: a } = await sb.from("youtube_account").select("*").eq("id", id).maybeSingle();
    if (!a?.refresh_token) continue;
    if (a.access_token && Date.parse(a.expires_at) - Date.now() > 120e3) return a.access_token;
    const form = new URLSearchParams({ client_id: Deno.env.get("YOUTUBE_CLIENT_ID")!, client_secret: Deno.env.get("YOUTUBE_CLIENT_SECRET")!, grant_type: "refresh_token", refresh_token: a.refresh_token });
    const t = await (await fetch("https://oauth2.googleapis.com/token", { method: "POST", body: form })).json();
    if (!t.access_token) continue;
    await sb.from("youtube_account").update({ access_token: t.access_token, expires_at: new Date(Date.now() + (t.expires_in || 3600) * 1000).toISOString(), updated_at: new Date().toISOString() }).eq("id", id);
    return t.access_token;
  }
  return null;
}

Deno.serve(async (req: Request) => {
  const body = await req.json().catch(() => ({}));
  const errs: string[] = [];
  try {
    const tok = await token(); if (!tok) return Response.json({ ok: false, error: "유튜브 토큰 없음" }, 500);
    const H = { Authorization: "Bearer " + tok };
    const ch = (await getj(`${YT}/channels`, { part: "statistics,contentDetails", id: EN_CH }, H)).items?.[0];
    await save("account", { subscribers: Number(ch?.statistics?.subscriberCount ?? 0), views: Number(ch?.statistics?.viewCount ?? 0), videos: Number(ch?.statistics?.videoCount ?? 0) });
    const { data: posts } = await sb.from("ed_posts").select("id,ep,title,yt_video_id,duration_sec").in("kind", ["reel_en", "long_en"]).not("yt_video_id", "is", null);
    const ids = (posts || []).map((p: any) => p.yt_video_id);
    // 롱폼 등 ed_posts 에 없는 영상도 채널 업로드 목록에서 함께 읽는다
    try {
      const pl = await getj(`${YT}/playlistItems`, { part: "contentDetails", playlistId: ch.contentDetails.relatedPlaylists.uploads, maxResults: "50" }, H);
      for (const i of pl.items || []) if (!ids.includes(i.contentDetails.videoId)) ids.push(i.contentDetails.videoId);
    } catch (e) { errs.push("uploads: " + (e as Error).message); }
    let n = 0;
    for (let i = 0; i < ids.length; i += 50) {
      const st = await getj(`${YT}/videos`, { part: "statistics,snippet,status,contentDetails", id: ids.slice(i, i + 50).join(",") }, H);
      for (const v of st.items || []) {
        if (v.snippet?.channelId !== EN_CH || v.status?.privacyStatus !== "public") continue;
        const p = (posts || []).find((p: any) => p.yt_video_id === v.id), s = v.statistics || {};
        const pub = v.snippet?.publishedAt;
        await save(v.id, { views: Number(s.viewCount ?? 0), likes: Number(s.likeCount ?? 0), comments: Number(s.commentCount ?? 0),
          hours: pub ? Math.round((Date.now() - Date.parse(pub)) / 3600e3) : null, post: p?.id ?? null, dur: v.contentDetails?.duration ?? null },
          { ep: p?.ep ?? null, title: v.snippet?.title, posted_at: pub });
        n++;
      }
    }
    // 검색 순위 (하루 1번): 목표 검색어에서 우리 영상이 상위 50 안 몇 위인지
    let rank: unknown = null;
    if (body.rank === true) {  // cron emperor-stats-en-rank (KST 10:55) 만 rank:true 로 부른다
      const { data: cfg } = await sb.from("app_config").select("value").eq("key", "ed_en_keywords").maybeSingle();
      const kws: string[] = (cfg?.value?.track || []).slice(0, 8);
      const out: Record<string, unknown> = {};
      for (const q of kws) {
        try {
          const r = await getj(`${YT}/search`, { part: "snippet", q, type: "video", maxResults: "50", regionCode: "US", relevanceLanguage: "en" }, H);
          const hits = (r.items || []).map((x: any, i: number) => ({ i: i + 1, ch: x.snippet?.channelId, id: x.id?.videoId, t: x.snippet?.title })).filter((x: any) => x.ch === EN_CH);
          out[q] = hits.length ? hits.slice(0, 3).map((h: any) => ({ pos: h.i, id: h.id, title: h.t })) : null;
        } catch (e) { errs.push("rank " + q + ": " + (e as Error).message); }
      }
      if (kws.length) { await save("search_rank", out); rank = out; }
    }
    return Response.json({ ok: true, day: kst(), videos: n, rank, errs });
  } catch (e) {
    return Response.json({ ok: false, error: String((e as Error)?.message || e), errs }, 500);
  }
});
