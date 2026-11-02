// 황제의 일기(emperors.diary) 인스타 릴스 + 쓰레드 글 자동 게시 (2026-11-02)
// 밸류노트 social-publish 와 완전히 분리: 계정은 ed_accounts, 대기열은 ed_posts.
// {} (5분마다 cron): 토큰 갱신 → 처리 중인 릴스 마무리(게시 + 첫 댓글) → 시간이 된 글을 채널별로 1편씩 시작
// 같은 채널은 최소 60분 간격. app_config.ed_paused = true 면 정기 게시 중지.
// 쓰레드: 글만 (2026-11-02 22:49 사진 붙인 3편 노출 급감 → 기본 글만, th_image=true 일 때만 사진). 따옴표 인용은 별도 문단. 본문 끝 줄 바로 아래 "매일 밤, 황제처럼 생각하라.\n황제의 일기."
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const IG = "https://graph.instagram.com/v23.0", TH = "https://graph.threads.net/v1.0";
const GAP_MIN = 60;
const TH_DELAY_MIN = 30;  // 쓰레드는 영상(scheduled_at)보다 30분 늦게 (2026-11-02 대표 확정: 07:40/12:20/21:30 → 쓰레드 08:10/12:50/22:00)
const TH_TOPIC = "철학"; // 쓰레드 주제(토픽) 태그
const TH_END = "\n\n- 매일 밤, 황제처럼 생각하라. 황제의 일기.";  // 빈 줄 + 대시 서명 한 줄 (2026-11-02 22:44 대표 예시: "마지막에 살짝 티나게")
const json = (o: unknown, status = 200) => new Response(JSON.stringify(o), { status, headers: { "Content-Type": "application/json" } });
type Acc = { platform: string; account_id: string; username: string; access_token: string; expires_at: string };

async function call(url: string, params: Record<string, string>, method = "POST") {
  const q = new URLSearchParams(params);
  const r = method === "GET" ? await fetch(url + "?" + q) : await fetch(url, { method, body: q });
  const j = await r.json().catch(() => ({}));
  if (!r.ok || j.error) throw new Error((j.error && (j.error.error_user_msg || j.error.message)) || `HTTP ${r.status}`);
  return j;
}
async function cfg(key: string) { const { data } = await sb.from("app_config").select("value").eq("key", key).maybeSingle(); return data?.value; }
async function accounts(): Promise<Record<string, Acc>> {
  const { data } = await sb.from("ed_accounts").select("*");
  return Object.fromEntries((data || []).map((a: Acc) => [a.platform, a]));
}
async function refresh(acc: Record<string, Acc>) {
  for (const a of Object.values(acc)) {
    if (!a.expires_at || new Date(a.expires_at).getTime() - Date.now() > 10 * 864e5) continue;
    try {
      const j = a.platform === "instagram"
        ? await call("https://graph.instagram.com/refresh_access_token", { grant_type: "ig_refresh_token", access_token: a.access_token }, "GET")
        : await call("https://graph.threads.net/refresh_access_token", { grant_type: "th_refresh_token", access_token: a.access_token }, "GET");
      a.access_token = j.access_token;
      a.expires_at = new Date(Date.now() + (Number(j.expires_in) || 5184000) * 1000).toISOString();
      await sb.from("ed_accounts").update({ access_token: a.access_token, expires_at: a.expires_at, updated_at: new Date().toISOString() }).eq("platform", a.platform);
    } catch (e) { console.error("refresh", a.platform, e); }
  }
}
// 쓰레드 본문: 따옴표 인용은 반드시 자기 줄에 (2026-11-02 22:44 대표 예시). 빈 줄(문단)은 글쓴이가 넣은 그대로 둔다
function fmtTH(t: string) {
  return t.replace(/[ \t]*([“"][^“”"\n]{8,}[”"])[ \t]*/g, "\n$1\n")
    .split("\n").map(l => l.trim()).join("\n").replace(/\n{3,}/g, "\n\n").trim();
}
const thText = (p: any) => fmtTH(String(p.th_text || "")).slice(0, 500 - TH_END.length) + TH_END;

async function upd(id: string, o: Record<string, unknown>) { await sb.from("ed_posts").update(o).eq("id", id); }

// 처리 중인 릴스 → 끝났으면 게시 + 첫 댓글
async function finishIG(a: Acc) {
  const out: unknown[] = [];
  const { data: rows } = await sb.from("ed_posts").select("*").eq("ig_status", "processing");
  for (const p of rows || []) {
    try {
      const st = (await call(`${IG}/${p.ig_container}`, { fields: "status_code", access_token: a.access_token }, "GET")).status_code;
      if (st === "ERROR" || st === "EXPIRED") throw new Error("영상 처리 실패 (" + st + ")");
      if (st !== "FINISHED") { if (Date.now() - new Date(p.ig_at).getTime() > 40 * 60e3) throw new Error("영상 처리 40분 초과"); continue; }
      const pub = await call(`${IG}/${a.account_id}/media_publish`, { creation_id: p.ig_container, access_token: a.access_token });
      const link = await call(`${IG}/${pub.id}`, { fields: "permalink", access_token: a.access_token }, "GET").catch(() => ({}));
      await upd(p.id, { ig_status: "posted", ig_media_id: pub.id, ig_permalink: link.permalink || null, ig_at: new Date().toISOString(), ig_error: null });
      if (p.ig_comment) {
        try { await call(`${IG}/${pub.id}/comments`, { message: p.ig_comment, access_token: a.access_token }); await upd(p.id, { ig_comment_status: "posted" }); }
        catch (e) { await upd(p.id, { ig_comment_status: "failed: " + String((e as Error).message).slice(0, 200) }); }
      }
      out.push({ id: p.id, ig: pub.id });
    } catch (e) {
      const msg = String((e as Error).message || e).slice(0, 500);
      await upd(p.id, { ig_status: "failed", ig_error: msg, ig_at: new Date().toISOString() }); out.push({ id: p.id, error: msg });
    }
  }
  return out;
}

async function startIG(a: Acc, p: any, site: string) {
  const { data: lock } = await sb.from("ed_posts").update({ ig_status: "publishing", ig_error: null }).eq("id", p.id).in("ig_status", ["pending", "failed"]).select("id");
  if (!lock?.length) return { skipped: "locked" };
  try {
    const url = /^https?:/.test(p.video_path) ? p.video_path : site + p.video_path;
    const prm: Record<string, string> = { media_type: "REELS", video_url: url, share_to_feed: "true", caption: p.ig_caption || "", access_token: a.access_token };
    if (p.cover_path) prm.cover_url = /^https?:/.test(p.cover_path) ? p.cover_path : site + p.cover_path;  // 표지 = 첫 화면(훅) 양식
    const c = await call(`${IG}/${a.account_id}/media`, prm);
    await upd(p.id, { ig_status: "processing", ig_container: c.id, ig_at: new Date().toISOString() });
    return { processing: c.id };
  } catch (e) {
    const msg = String((e as Error).message || e).slice(0, 500);
    await upd(p.id, { ig_status: "failed", ig_error: msg, ig_at: new Date().toISOString() }); return { error: msg };
  }
}

async function postTH(a: Acc, p: any, site = "") {
  const { data: lock } = await sb.from("ed_posts").update({ th_status: "publishing", th_error: null }).eq("id", p.id).in("th_status", ["pending", "failed"]).select("id");
  if (!lock?.length) return { skipped: "locked" };
  try {
    const prm: Record<string, string> = { media_type: "TEXT", text: thText(p), topic_tag: p.th_topic || TH_TOPIC, access_token: a.access_token };
    if (p.th_image === true && p.cover_path) { prm.media_type = "IMAGE"; prm.image_url = /^https?:/.test(p.cover_path) ? p.cover_path : site + p.cover_path; }  // 쓰레드 = 표지 사진 1장 + 글
    const c = await call(`${TH}/${a.account_id}/threads`, prm);
    for (let i = 0; i < 15; i++) { const st = (await call(`${TH}/${c.id}`, { fields: "status", access_token: a.access_token }, "GET").catch(() => ({}))).status; if (st === "FINISHED" || !st) break; if (st === "ERROR") throw new Error("이미지 처리 실패"); await new Promise(r => setTimeout(r, 2000)); }
    await new Promise(r => setTimeout(r, 2000));
    const pub = await call(`${TH}/${a.account_id}/threads_publish`, { creation_id: c.id, access_token: a.access_token });
    const link = await call(`${TH}/${pub.id}`, { fields: "permalink", access_token: a.access_token }, "GET").catch(() => ({}));
    await upd(p.id, { th_status: "posted", th_media_id: pub.id, th_permalink: link.permalink || null, th_at: new Date().toISOString() });
    return { posted: pub.id };
  } catch (e) {
    const msg = String((e as Error).message || e).slice(0, 500);
    await upd(p.id, { th_status: "failed", th_error: msg, th_at: new Date().toISOString() }); return { error: msg };
  }
}

async function lastAt(ch: "ig" | "th") {
  const { data } = await sb.from("ed_posts").select(`${ch}_at`).eq(`${ch}_status`, "posted").order(`${ch}_at`, { ascending: false }).limit(1);
  return data?.[0]?.[`${ch}_at`] ? new Date(data[0][`${ch}_at`]).getTime() : 0;
}

Deno.serve(async (req: Request) => {
  const body = await req.json().catch(() => ({}));
  try {
    const site = String((await cfg("site_url")) || "").replace(/\/$/, "");
    const acc = await accounts();
    if (body.action === "preview_th") return json({ text: thText(body) });
    if (body.action === "check") {
      const out: Record<string, unknown> = { accounts: Object.values(acc).map(a => ({ platform: a.platform, username: a.username, expires_at: a.expires_at })) };
      if (acc.instagram) out.ig_limit = await call(`${IG}/${acc.instagram.account_id}/content_publishing_limit`, { fields: "quota_usage,config", access_token: acc.instagram.access_token }, "GET").catch(e => ({ error: String(e.message) }));
      if (acc.threads) out.th_limit = await call(`${TH}/${acc.threads.account_id}/threads_publishing_limit`, { fields: "quota_usage,config", access_token: acc.threads.access_token }, "GET").catch(e => ({ error: String(e.message) }));
      if (body.url) out.head = await fetch(body.url, { method: "HEAD" }).then(r => ({ status: r.status, type: r.headers.get("content-type"), len: r.headers.get("content-length") })).catch(e => ({ error: String(e) }));
      return json(out);
    }
    await refresh(acc);
    const res: Record<string, unknown> = {};
    if (acc.instagram) res.finished = await finishIG(acc.instagram);
    if ((await cfg("ed_paused")) === true && !body.force) return json({ ...res, idle: "paused" });
    const now = new Date().toISOString();
    const thCut = new Date(Date.now() - TH_DELAY_MIN * 60e3).toISOString();
    for (const ch of ["ig", "th"] as const) {
      const a = acc[ch === "ig" ? "instagram" : "threads"]; if (!a) continue;
      if (ch === "ig") { const { count } = await sb.from("ed_posts").select("id", { count: "exact", head: true }).eq("ig_status", "processing"); if (count) continue; }
      if (!body.force && Date.now() - (await lastAt(ch)) < GAP_MIN * 60e3) continue;
      const { data: due } = await sb.from("ed_posts").select("*").eq(ch === "ig" ? "to_ig" : "to_th", true).eq(`${ch}_status`, "pending")
        .eq("paused", false).lte("scheduled_at", ch === "th" && !body.force ? thCut : now).order("scheduled_at").limit(1);
      const p = due?.[0]; if (!p) continue;
      res[ch] = { id: p.id, ...(ch === "ig" ? await startIG(a, p, site) : await postTH(a, p, site)) };
    }
    return json(res);
  } catch (e) {
    return json({ error: String((e as Error).message || e) }, 500);
  }
});
