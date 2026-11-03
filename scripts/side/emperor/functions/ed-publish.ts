// 황제의 일기(emperors.diary) 인스타 릴스·카드뉴스(kind='carousel', images[]) + 쓰레드 글 자동 게시 (2026-11-02, 카드뉴스 2026-11-03)
// 밸류노트 social-publish 와 완전히 분리: 계정은 ed_accounts, 대기열은 ed_posts.
// {} (5분마다 cron): 토큰 갱신 → 처리 중인 릴스 마무리(게시 + 첫 댓글) → 시간이 된 글을 채널별로 1편씩 시작
// 같은 채널은 최소 60분 간격. app_config.ed_paused = true 면 정기 게시 중지.
// 유튜브 댓글(2026-11-03 대표 "댓글 안 달리던데 재발하지 않게"): yt_video_id 가 공개되면 yt_comment 를 채널 이름으로 한 번 단다 (youtube_account id=2, 황제의 일기 채널일 때만)
// 쓰레드: 글만 (2026-11-02 22:49 사진 붙인 3편 노출 급감 → 기본 글만, th_image=true 일 때만 사진). 따옴표 인용은 자기 줄에, 끝에 빈 줄 + "- 매일 밤, 황제처럼 생각하라. 황제의 일기."
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const IG = "https://graph.instagram.com/v23.0", TH = "https://graph.threads.net/v1.0";
const GAP_MIN = 60;
const TH_DELAY_MIN = 0;  // 2026-11-03 12:32 대표: 쓰레드는 이미지 없이 글만 올리므로 영상과 같은 시각에 (이전: 30분 뒤)
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

// 처리 중인 릴스·카드뉴스 → 끝났으면 게시 + 첫 댓글
async function finishIG(a: Acc) {
  const out: unknown[] = [];
  const { data: rows } = await sb.from("ed_posts").select("*").eq("ig_status", "processing");
  for (const p of rows || []) {
    try {
      const st = (await call(`${IG}/${p.ig_container}`, { fields: "status_code", access_token: a.access_token }, "GET")).status_code;
      if (st === "ERROR" || st === "EXPIRED") throw new Error("처리 실패 (" + st + ")");
      if (st !== "FINISHED") { if (Date.now() - new Date(p.ig_at).getTime() > 40 * 60e3) throw new Error("처리 40분 초과"); continue; }
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
    const abs = (u: string) => /^https?:/.test(u) ? u : site + u;
    let c: { id: string };
    if (p.kind === "carousel") {  // 카드뉴스 (2026-11-03): 사진 2~10장 → 캐러셀
      const imgs: string[] = (p.images || []).slice(0, 10);
      if (imgs.length < 2) throw new Error("카드뉴스 사진이 2장 미만");
      const kids: string[] = [];
      for (const u of imgs) kids.push((await call(`${IG}/${a.account_id}/media`, { image_url: abs(u), is_carousel_item: "true", access_token: a.access_token })).id);
      c = await call(`${IG}/${a.account_id}/media`, { media_type: "CAROUSEL", children: kids.join(","), caption: p.ig_caption || "", access_token: a.access_token });
    } else {
      const prm: Record<string, string> = { media_type: "REELS", video_url: abs(p.video_path), share_to_feed: "true", caption: p.ig_caption || "", access_token: a.access_token };
      if (p.cover_path) prm.cover_url = abs(p.cover_path);  // 표지 = 첫 화면(훅) 양식
      c = await call(`${IG}/${a.account_id}/media`, prm);
    }
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
    if (p.th_image === true && p.cover_path) { prm.media_type = "IMAGE"; prm.image_url = /^https?:/.test(p.cover_path) ? p.cover_path : site + p.cover_path; }  // 사진은 th_image=true 일 때만
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

// 유튜브 첫 댓글 (2026-11-03): 공개된 쇼츠에 yt_comment 를 단다. 고정(pin)은 API 로 안 돼서 댓글만.
const ED_CH = "UCR5ao2RmISHYMmDinRPIaDw";
async function ytTok(): Promise<string | null> {
  const { data: a } = await sb.from("youtube_account").select("*").eq("id", 2).maybeSingle();
  if (!a?.refresh_token || a.channel_id !== ED_CH) return null;
  if (a.access_token && Date.parse(a.expires_at) - Date.now() > 120e3) return a.access_token;
  const form = new URLSearchParams({ client_id: Deno.env.get("YOUTUBE_CLIENT_ID")!, client_secret: Deno.env.get("YOUTUBE_CLIENT_SECRET")!, grant_type: "refresh_token", refresh_token: a.refresh_token });
  const t = await (await fetch("https://oauth2.googleapis.com/token", { method: "POST", body: form })).json();
  if (!t.access_token) return null;
  await sb.from("youtube_account").update({ access_token: t.access_token, expires_at: new Date(Date.now() + (t.expires_in || 3600) * 1000).toISOString(), updated_at: new Date().toISOString() }).eq("id", 2);
  return t.access_token;
}
async function ytComments() {
  const { data: rows } = await sb.from("ed_posts").select("id,yt_video_id,yt_comment").eq("yt_comment_status", "pending").not("yt_video_id", "is", null).lte("scheduled_at", new Date().toISOString()).limit(5);
  if (!rows?.length) return [];
  const tok = await ytTok(); if (!tok) return [{ error: "황제의 일기 유튜브 연결 없음(youtube_account id=2)" }];
  const H = { Authorization: "Bearer " + tok, "Content-Type": "application/json" };
  const out: unknown[] = [];
  for (const p of rows) {
    if (!p.yt_comment) { await upd(p.id, { yt_comment_status: "skip" }); continue; }
    try {
      const v = await (await fetch(`https://www.googleapis.com/youtube/v3/videos?part=status&id=${p.yt_video_id}`, { headers: H })).json();
      if (v.items?.[0]?.status?.privacyStatus !== "public") continue;  // 예약 중이면 공개될 때까지 기다린다
      const r = await fetch("https://www.googleapis.com/youtube/v3/commentThreads?part=snippet", { method: "POST", headers: H,
        body: JSON.stringify({ snippet: { videoId: p.yt_video_id, topLevelComment: { snippet: { textOriginal: p.yt_comment } } } }) });
      const j = await r.json();
      if (!r.ok) throw new Error(j.error?.message || `HTTP ${r.status}`);
      await upd(p.id, { yt_comment_status: "posted", yt_comment_id: j.id, yt_comment_error: null }); out.push({ id: p.id, yt_comment: j.id });
    } catch (e) {
      const msg = String((e as Error).message || e).slice(0, 300);
      await upd(p.id, { yt_comment_status: "failed", yt_comment_error: msg }); out.push({ id: p.id, error: msg });
    }
  }
  return out;
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
    res.yt_comments = await ytComments().catch(e => [{ error: String(e) }]);  // 공개된 영상 댓글은 일시정지와 무관하게
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
