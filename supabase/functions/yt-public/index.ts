// 유튜브 채널 공개 숫자(구독자·총 조회·영상 수) 새로고침 — 유튜브 API·스튜디오 없이 채널 공개 페이지에서 읽는다 (2026-11-03 대표님: "브리핑 구독자 수가 업데이트가 안 돼, 새로고침 버튼")
// - POST {t}  : (관리자) 지금 읽어서 docs agent 'yt-channel' 에 subs·views_total·videos·at(source:'public') 로 저장하고 결과를 돌려준다
// - POST {cron:true} : (pg_cron, 3시간마다) 같은 저장 — 공개 숫자라 인증 없이도 저장만 한다 (social-publish의 {} cron 호출과 같은 방식)
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
    return json({ ok: true, ...now, prev_subs: prev.subs ?? null, prev_at: prev.at ?? null });
  } catch (e) { return json({ error: String((e as Error).message || e) }, 500); }
});
