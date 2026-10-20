// 성과 수집 (pg_cron: 3시간마다, 토큰 0) — 밸류노트 비서의 '눈'
// 1) 최근 21일 안에 올라간 인스타 릴스마다 조회수·도달·저장·공유·평균 시청 시간을 받아 social_posts.ig_insights 에 저장
// 2) 인스타 계정 팔로워 수를 하루 한 줄씩 metrics_daily 에 저장
// LLM 은 쓰지 않는다. 해석은 비서(예약 작업)가 public.agent_snapshot() 한 번으로 읽어 간다.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const IG = "https://graph.instagram.com/v23.0";
const kst = () => new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);
const METRICS = ["views", "reach", "saved", "shares", "likes", "comments", "total_interactions", "ig_reels_avg_watch_time", "ig_reels_video_view_total_time"];

async function get(path: string, q: Record<string, string>) {
  const r = await fetch(`${IG}/${path}?${new URLSearchParams(q)}`);
  const j = await r.json().catch(() => ({}));
  if (!r.ok || j.error) throw new Error(j?.error?.message || `HTTP ${r.status}`);
  return j;
}

async function insights(id: string, token: string) {
  const out: Record<string, number> = {};
  const read = (j: any) => { for (const m of j.data || []) out[m.name] = Number(m.values?.[0]?.value ?? m.total_value?.value ?? 0); };
  try { read(await get(`${id}/insights`, { metric: METRICS.join(","), access_token: token })); }
  catch { // 지원하지 않는 지표가 섞이면 하나씩 다시 받는다
    for (const m of METRICS) { try { read(await get(`${id}/insights`, { metric: m, access_token: token })); } catch { /* 건너뜀 */ } }
  }
  // 인사이트 권한이 없을 때(재연결 전)도 좋아요·댓글 수는 기본 권한으로 받는다
  if (!("views" in out)) {
    try { const b = await get(id, { fields: "like_count,comments_count", access_token: token });
      out.likes = Number(b.like_count ?? 0); out.comments = Number(b.comments_count ?? 0); out.noInsights = 1; } catch { /* 건너뜀 */ }
  }
  return out;
}

Deno.serve(async (req: Request) => {
  const body = await req.json().catch(() => ({}));
  try {
    const { data: acc } = await sb.from("social_accounts").select("account_id,access_token").eq("platform", "instagram").maybeSingle();
    if (!acc?.access_token) return Response.json({ ok: false, msg: "인스타 계정 없음" });
    if (body.debug) { // 진단: 한 게시물의 원래 응답·오류를 그대로 돌려준다
      const out: Record<string, string> = {};
      for (const m of METRICS) { try { out[m] = JSON.stringify(await get(`${body.debug}/insights`, { metric: m, access_token: acc.access_token })).slice(0, 200); } catch (e) { out[m] = "ERR " + (e as Error).message; } }
      return Response.json(out);
    }
    const since = new Date(Date.now() - 21 * 864e5).toISOString();
    const { data: posts, error } = await sb.from("social_posts").select("id,ig_media_id,ig_at")
      .eq("ig_status", "posted").not("ig_media_id", "is", null).gte("ig_at", since);
    if (error) throw error;
    let done = 0; const errs: string[] = [];
    for (const p of posts || []) {
      try {
        const m = await insights(p.ig_media_id, acc.access_token);
        if (Object.keys(m).length) {
          const hours = Math.round((Date.now() - Date.parse(p.ig_at)) / 36e5);
          await sb.from("social_posts").update({ ig_insights: { ...m, hours }, ig_insights_at: new Date().toISOString() }).eq("id", p.id);
          done++;
        }
      } catch (e) { errs.push(`${p.id}: ${(e as Error).message}`); }
    }
    let followers: number | null = null;
    try {
      const me = await get("me", { fields: "followers_count,media_count", access_token: acc.access_token });
      followers = Number(me.followers_count ?? 0);
      await sb.from("metrics_daily").upsert({ day: kst(), k: "ig_account", v: { followers, media: Number(me.media_count ?? 0) } });
    } catch (e) { errs.push(`account: ${(e as Error).message}`); }
    return Response.json({ ok: true, posts: posts?.length || 0, updated: done, followers, errs: errs.slice(0, 5) });
  } catch (e) {
    return Response.json({ ok: false, error: String((e as Error)?.message || e) }, 500);
  }
});
