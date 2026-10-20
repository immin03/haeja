// 인스타 댓글 → 자동 DM (2026-10-21, 2단계: 자체 발송)
// 흐름: 릴스에 키워드 댓글 → 공개 답글 "DM 보냈어요" + 비공개 답장(DM) "팔로우 확인" 버튼
//       → 버튼을 누르면 팔로우 여부 확인 → 팔로우 중이면 정리본 링크(/g/<릴스 id>), 아니면 팔로우 부탁 + 같은 버튼
// 광고: 인스타 앱 '홍보하기'로 돌린 릴스는 같은 게시물이라 광고 댓글에도 똑같이 동작한다.
//
// Meta 앱 설정 (운영자가 한 번):
//   웹훅 콜백 URL = https://<프로젝트>.supabase.co/functions/v1/ig-dm , 확인 토큰 = 비밀값 IG_WEBHOOK_VERIFY 또는 app_config.ig_webhook_verify
//   구독 필드 = comments, messages, messaging_postbacks
//   권한 = instagram_business_manage_comments, instagram_business_manage_messages (일반 사용자에게 보내려면 고급 접근 심사 필요)
// 켜기: app_config.ig_dm_enabled = true (심사 전에는 false → 앱 역할이 있는 계정만 테스트 가능하도록 ig_dm_testers 목록 사용)
// verify_jwt = false (Meta가 직접 호출). 요청은 앱 비밀키 서명(X-Hub-Signature-256)으로 확인한다.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const IG = "https://graph.instagram.com/v23.0";
const SITE_DEFAULT = "https://www.valuenote.co.kr";
const POSTBACK = "VN_GUIDE";

async function cfg(key: string) { const { data } = await sb.from("app_config").select("value").eq("key", key).maybeSingle(); return data?.value; }
async function acct() { const { data } = await sb.from("social_accounts").select("*").eq("platform", "instagram").maybeSingle(); return data; }

async function verifySig(req: Request, raw: string) {
  const secret = Deno.env.get("META_IG_APP_SECRET"); if (!secret) return false;
  const sig = req.headers.get("x-hub-signature-256") || ""; if (!sig.startsWith("sha256=")) return false;
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(secret), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  const mac = new Uint8Array(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(raw)));
  const hex = Array.from(mac).map(b => b.toString(16).padStart(2, "0")).join("");
  return hex === sig.slice(7);
}

async function api(path: string, token: string, body?: unknown, method = "POST") {
  const r = await fetch(`${IG}/${path}${method === "GET" ? (path.includes("?") ? "&" : "?") + "access_token=" + token : ""}`, method === "GET"
    ? undefined
    : { method, headers: { "Content-Type": "application/json", Authorization: "Bearer " + token }, body: JSON.stringify(body) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok || j.error) throw new Error((j.error && (j.error.error_user_msg || j.error.message)) || `HTTP ${r.status}`);
  return j;
}

const norm = (s: string) => String(s || "").replace(/\s+/g, "").replace(/['"‘’“”]/g, "").toLowerCase();
const REPLIES = ["DM 보내 드렸어요. 확인 부탁드립니다!", "정리본 DM으로 보내 드렸어요 📩", "메시지 확인해 주세요! 정리본 보내 드렸습니다.", "DM 확인 부탁드려요. 정리본 넣어 두었습니다!"];

function followButton(text: string) {
  return { attachment: { type: "template", payload: { template_type: "button", text, buttons: [{ type: "postback", title: "팔로우 확인 🙌", payload: POSTBACK }] } } };
}
function linkButton(site: string, post: any) {
  const url = `${site}${post?.dm_guide || "/g"}?utm_source=ig-dm&utm_content=${encodeURIComponent(post?.id || "hub")}`;
  return { attachment: { type: "template", payload: { template_type: "button",
    text: `팔로우 확인했습니다. 감사합니다!\n\n${post?.title ? "「" + String(post.title).replace(/^이슈 픽 · /, "") + "」 " : ""}정리본입니다. 릴스에서 다 못 한 숫자와 내 종목에 바로 적용하는 방법까지 담았습니다.\n\n이메일을 넣으면 바로 열리고, 새 정리본이 나오면 같은 메일로 알려 드립니다.`,
    buttons: [{ type: "web_url", url, title: "정리본 보러 가기" }, { type: "web_url", url: `${site}/start?utm_source=ig-dm`, title: "밸류노트 둘러보기" }] } } };
}

// 댓글 하나 처리
async function onComment(v: any, a: any, site: string) {
  const cid = v.id, from = v.from || {}, media = v.media?.id;
  if (!cid || !media || from.id === a.account_id) return "skip-own";
  const { data: post } = await sb.from("social_posts").select("id,title,dm_keyword,dm_guide").eq("ig_media_id", media).maybeSingle();
  const any = (await cfg("ig_dm_any_comment")) === true;   // true면 키워드 없이 아무 댓글에나 반응
  if (!post?.dm_keyword && !any) return "no-keyword-post";
  if (post?.dm_keyword && !any && !norm(v.text).includes(norm(post.dm_keyword))) return "no-match";
  const { error: dup } = await sb.from("ig_dm").insert({ comment_id: cid, media_id: media, post_id: post?.id || null, igsid: from.id || null, username: from.username || null, keyword: post?.dm_keyword || null, status: "new" });
  if (dup) return "dup";
  try {
    const kw = post?.dm_keyword ? `'${post.dm_keyword}'` : "";
    // 비공개 답장 (댓글 7일 안, 1회): 팔로우 확인 버튼
    try {
      await api(`${a.account_id}/messages`, a.access_token, { recipient: { comment_id: cid }, message: followButton(
        `안녕하세요, 밸류노트입니다 🙂\n댓글${kw ? "에 " + kw : ""} 남겨 주셔서 감사합니다.\n\n팔로우 확인을 위해 아래 버튼을 눌러 주세요. 확인되면 바로 정리본을 보내 드립니다.`) });
    } catch (_) {
      // 버튼 템플릿이 거절되면 글로만 보낸다 (답장을 보내 주시면 이어서 링크를 드림)
      await api(`${a.account_id}/messages`, a.access_token, { recipient: { comment_id: cid }, message: { text:
        `안녕하세요, 밸류노트입니다 🙂 댓글 감사합니다.\n이 메시지에 "정리본"이라고 답장해 주시면 팔로우 확인 후 바로 링크를 보내 드립니다.` } });
    }
    await sb.from("ig_dm").update({ status: "asked", updated_at: new Date().toISOString() }).eq("comment_id", cid);
    // 공개 답글 (실패해도 DM은 이미 나감)
    await api(`${cid}/replies`, a.access_token, { message: REPLIES[Math.floor(Math.random() * REPLIES.length)] }).catch(e => console.error("reply", e));
    return "asked";
  } catch (e) {
    await sb.from("ig_dm").update({ status: "failed", error: String((e as Error).message).slice(0, 400), updated_at: new Date().toISOString() }).eq("comment_id", cid);
    return "failed";
  }
}

// 버튼(postback) 또는 답장 처리: 팔로우 확인 → 링크
async function onMessage(m: any, a: any, site: string) {
  const uid = m.sender?.id; if (!uid || uid === a.account_id || m.message?.is_echo) return "skip";
  const isBtn = m.postback?.payload === POSTBACK;
  const isAsk = /정리본|자료|링크|팔로우/.test(String(m.message?.text || ""));
  if (!isBtn && !isAsk) return "ignore";
  const { data: rows } = await sb.from("ig_dm").select("*").eq("igsid", uid).order("created_at", { ascending: false }).limit(1);
  const row = rows?.[0];
  const { data: post } = row?.post_id ? await sb.from("social_posts").select("id,title,dm_guide").eq("id", row.post_id).maybeSingle() : { data: null };
  let follows = true;
  try { follows = !!(await api(`${uid}?fields=is_user_follow_business`, a.access_token, undefined, "GET")).is_user_follow_business; }
  catch (e) { console.error("follow check", e); }   // 확인이 안 되면 막지 않고 보낸다
  if (!follows) {
    await api(`${a.account_id}/messages`, a.access_token, { recipient: { id: uid }, message: followButton(
      "아직 팔로우가 확인되지 않았어요.\n@value.note.korea 를 팔로우하신 뒤 아래 버튼을 다시 눌러 주세요 🙏") });
    return "not-following";
  }
  await api(`${a.account_id}/messages`, a.access_token, { recipient: { id: uid }, message: linkButton(site, post) });
  if (row) await sb.from("ig_dm").update({ status: "sent", updated_at: new Date().toISOString() }).eq("comment_id", row.comment_id);
  return "sent";
}

Deno.serve(async (req: Request) => {
  const u = new URL(req.url);
  if (req.method === "GET") {   // 웹훅 확인
    const want = Deno.env.get("IG_WEBHOOK_VERIFY") || String((await cfg("ig_webhook_verify")) || "");   // 확인 토큰: 비밀값 또는 app_config
    const ok = !!want && u.searchParams.get("hub.mode") === "subscribe" && u.searchParams.get("hub.verify_token") === want;
    return new Response(ok ? (u.searchParams.get("hub.challenge") || "") : "forbidden", { status: ok ? 200 : 403 });
  }
  const raw = await req.text();
  if (!(await verifySig(req, raw))) return new Response("bad signature", { status: 401 });
  const body = JSON.parse(raw || "{}");
  const out: unknown[] = [];
  try {
    const a = await acct(); if (!a) return new Response("no account", { status: 200 });
    const on = (await cfg("ig_dm_enabled")) === true;
    const testers: string[] = (await cfg("ig_dm_testers")) || [];   // 심사 전 테스트용 인스타 아이디 목록
    const site = String((await cfg("site_url")) || SITE_DEFAULT).replace(/\/$/, "");
    for (const e of body.entry || []) {
      for (const c of e.changes || []) {
        if (c.field !== "comments") continue;
        const v = c.value || {};
        if (!on && !testers.includes(v.from?.username)) { out.push("off"); continue; }
        out.push(await onComment(v, a, site));
      }
      for (const m of e.messaging || []) {
        if (!on) { const { data } = await sb.from("ig_dm").select("username").eq("igsid", m.sender?.id || "").limit(1); if (!testers.includes(data?.[0]?.username)) { out.push("off"); continue; } }
        out.push(await onMessage(m, a, site).catch(err => "msg-failed: " + String(err.message || err)));
      }
    }
  } catch (err) { console.error(err); out.push("error"); }
  console.log(JSON.stringify(out));
  return new Response("ok", { status: 200 });   // Meta는 200을 못 받으면 계속 다시 보낸다
});
