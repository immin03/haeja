// 인스타·쓰레드·유튜브 계정 연결 (OAuth)
// 유튜브(2026-10-21): ?start=youtube → 구글 로그인(오프라인 접근) → 갱신 토큰을 youtube_account 에 저장
// 1) 관리자 화면 → GET ?start=instagram|threads&t=<로그인 토큰>&ret=<관리자 페이지 주소>
//    관리자인지 확인하고 Meta 로그인 화면으로 보낸다.
// 2) Meta → GET ?code=...&state=...  토큰을 받아 장기 토큰(60일)으로 바꿔 social_accounts에 저장하고 관리자 화면으로 돌려보낸다.
// 3) Meta 쓰레드 앱의 "제거·삭제 콜백"도 이 주소로 온다(POST). 확인 응답만 준다.
// 4) 황제의 일기(2026-11-02): instagram_ed / threads_ed / youtube_ed.
//    Claude가 SQL로 social_oauth_state에 1회용 nonce를 넣고 ?go=<nonce> 링크를 대표에게 준다(1시간 유효).
//    인스타·쓰레드는 ed_accounts에, 유튜브는 youtube_account id=2 에 저장. 로그인 계정이 emperors.diary 가 아니면 저장하지 않는다.
// verify_jwt = false (Meta가 직접 호출하므로). 관리자 확인은 함수 안에서 한다.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const URL_SELF = Deno.env.get("SUPABASE_URL")! + "/functions/v1/social-oauth";
const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const env = (k: string) => Deno.env.get(k) || "";

const CFG = {
  instagram: {
    id: () => env("META_IG_APP_ID"), secret: () => env("META_IG_APP_SECRET"),
    authorize: "https://www.instagram.com/oauth/authorize",
    // 2026-10-21: 댓글 → 자동 DM(ig-dm)을 위해 댓글·메시지 권한 추가 (다시 연결해야 적용)
    scope: "instagram_business_basic,instagram_business_content_publish,instagram_business_manage_insights,instagram_business_manage_comments,instagram_business_manage_messages",
  },
  threads: {
    id: () => env("META_THREADS_APP_ID"), secret: () => env("META_THREADS_APP_SECRET"),
    authorize: "https://threads.net/oauth/authorize",
    scope: "threads_basic,threads_content_publish,threads_manage_insights",
  },
  youtube: {
    id: () => env("YOUTUBE_CLIENT_ID"), secret: () => env("YOUTUBE_CLIENT_SECRET"),
    authorize: "https://accounts.google.com/o/oauth2/v2/auth",
    // 업로드 · 댓글(고정 댓글) · 채널 분석
    scope: "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.force-ssl https://www.googleapis.com/auth/yt-analytics.readonly",
  },
} as const;
type P = keyof typeof CFG;
const ED_USER = "emperors.diary";
const baseOf = (p: string) => p.replace(/_ed$/, "") as P;
const isEd = (p: string) => p.endsWith("_ed");
const VALID = ["instagram", "threads", "youtube", "instagram_ed", "threads_ed", "youtube_ed"];

async function youtubeConnect(code: string, rowId = 1) {
  const form = new URLSearchParams({ client_id: CFG.youtube.id(), client_secret: CFG.youtube.secret(), grant_type: "authorization_code", redirect_uri: URL_SELF, code });
  const t = await (await fetch("https://oauth2.googleapis.com/token", { method: "POST", body: form })).json();
  if (!t.access_token) throw new Error("구글 토큰 실패: " + JSON.stringify(t));
  const ch = await (await fetch("https://www.googleapis.com/youtube/v3/channels?part=snippet&mine=true", { headers: { Authorization: "Bearer " + t.access_token } })).json();
  const c = ch.items?.[0];
  if (!c) throw new Error("이 구글 계정에 유튜브 채널이 없습니다. 채널을 고르는 화면에서 올바른 채널을 선택해 주세요.");
  if (rowId === 2 && c.id === "UCXh2Zs40HIrLZK5GTrHyYSQ") throw new Error("밸류노트 채널이 선택됐습니다. 채널 선택 화면에서 '황제의 일기'를 골라 다시 연결해 주세요.");
  const { data: old } = await sb.from("youtube_account").select("refresh_token").eq("id", rowId).maybeSingle();
  const refresh = t.refresh_token || old?.refresh_token;
  if (!refresh) throw new Error("갱신 토큰을 받지 못했습니다. myaccount.google.com/permissions 에서 ValueNote 접근을 삭제한 뒤 다시 연결해 주세요.");
  const { error } = await sb.from("youtube_account").upsert({
    id: rowId, channel_id: c.id, channel_title: c.snippet?.title, handle: c.snippet?.customUrl || null,
    refresh_token: refresh, access_token: t.access_token, scopes: t.scope || null,
    expires_at: new Date(Date.now() + (Number(t.expires_in) || 3600) * 1000).toISOString(), updated_at: new Date().toISOString(),
  });
  if (error) throw new Error(error.message);
  return c.snippet?.title as string;
}

const html = (msg: string, status = 200) => new Response(
  `<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width"><body style="font-family:sans-serif;padding:32px;line-height:1.6">${msg}</body>`,
  { status, headers: { "Content-Type": "text/html; charset=utf-8" } });
const back = (ret: string, q: string) => Response.redirect(ret + (ret.includes("?") ? "&" : "?") + q + "#social", 302);

async function isAdmin(token: string) {
  const { data } = await sb.auth.getUser(token);
  const email = data?.user?.email;
  if (!email) return false;
  const { data: cfg } = await sb.from("app_config").select("value").eq("key", "admins").maybeSingle();
  return Array.isArray(cfg?.value) && cfg!.value.includes(email);
}

async function exchange(p: P, code: string) {
  const c = CFG[p];
  const form = new URLSearchParams({ client_id: c.id(), client_secret: c.secret(), grant_type: "authorization_code", redirect_uri: URL_SELF, code });
  if (p === "instagram") {
    const r1 = await fetch("https://api.instagram.com/oauth/access_token", { method: "POST", body: form });
    const s = await r1.json(); if (!s.access_token) throw new Error("단기 토큰 실패: " + JSON.stringify(s));
    const r2 = await fetch(`https://graph.instagram.com/access_token?grant_type=ig_exchange_token&client_secret=${encodeURIComponent(c.secret())}&access_token=${encodeURIComponent(s.access_token)}`);
    const l = await r2.json(); if (!l.access_token) throw new Error("장기 토큰 실패: " + JSON.stringify(l));
    const me = await (await fetch(`https://graph.instagram.com/v23.0/me?fields=user_id,username&access_token=${encodeURIComponent(l.access_token)}`)).json();
    if (!me.user_id) throw new Error("계정 조회 실패: " + JSON.stringify(me));
    return { account_id: String(me.user_id), username: me.username, access_token: l.access_token, expires_in: l.expires_in };
  }
  const r1 = await fetch("https://graph.threads.net/oauth/access_token", { method: "POST", body: form });
  const s = await r1.json(); if (!s.access_token) throw new Error("단기 토큰 실패: " + JSON.stringify(s));
  const r2 = await fetch(`https://graph.threads.net/access_token?grant_type=th_exchange_token&client_secret=${encodeURIComponent(c.secret())}&access_token=${encodeURIComponent(s.access_token)}`);
  const l = await r2.json(); if (!l.access_token) throw new Error("장기 토큰 실패: " + JSON.stringify(l));
  const me = await (await fetch(`https://graph.threads.net/v1.0/me?fields=id,username&access_token=${encodeURIComponent(l.access_token)}`)).json();
  if (!me.id) throw new Error("계정 조회 실패: " + JSON.stringify(me));
  return { account_id: String(me.id), username: me.username, access_token: l.access_token, expires_in: l.expires_in };
}

function authorizeUrl(platform: string, nonce: string) {
  const b = baseOf(platform);
  const q = new URLSearchParams({ client_id: CFG[b].id(), redirect_uri: URL_SELF, scope: CFG[b].scope, response_type: "code", state: nonce });
  if (b === "youtube") { q.set("access_type", "offline"); q.set("prompt", "consent select_account"); q.set("include_granted_scopes", "true"); }
  return CFG[b].authorize + "?" + q;
}

Deno.serve(async (req: Request) => {
  const u = new URL(req.url);
  // 쓰레드 앱 제거·삭제 콜백 (저장하는 사용자 데이터가 없으므로 확인만)
  if (req.method === "POST") {
    return new Response(JSON.stringify({ url: "https://haeja.vercel.app/privacy", confirmation_code: "vn-" + Date.now() }), { headers: { "Content-Type": "application/json" } });
  }
  try {
    // 황제의 일기: Claude가 만든 1회용 링크
    const go = u.searchParams.get("go");
    if (go) {
      const { data: st } = await sb.from("social_oauth_state").select("*").eq("nonce", go).maybeSingle();
      if (!st || !isEd(st.platform) || Date.now() - new Date(st.created_at).getTime() > 3600e3) return html("연결 링크가 만료됐습니다. Claude에게 새 링크를 요청해 주세요.", 400);
      if (!CFG[baseOf(st.platform)].id()) return html("앱 시크릿이 아직 없습니다.", 500);
      return Response.redirect(authorizeUrl(st.platform, go), 302);
    }

    const start = u.searchParams.get("start") as P | null;
    if (start) {
      if (!(start in CFG)) return html("알 수 없는 채널입니다.", 400);
      const ret = u.searchParams.get("ret") || "";
      if (!/^https:\/\/[a-z0-9.-]+(:\d+)?\/[^\s#]*$/i.test(ret)) return html("돌아갈 주소가 올바르지 않습니다.", 400);
      if (!(await isAdmin(u.searchParams.get("t") || ""))) return html("관리자 계정으로 로그인한 상태에서 눌러 주세요.", 403);
      if (!CFG[start].id() || !CFG[start].secret()) return back(ret, `social_err=${encodeURIComponent((start === "instagram" ? "META_IG_APP_ID / META_IG_APP_SECRET" : start === "threads" ? "META_THREADS_APP_ID / META_THREADS_APP_SECRET" : "YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET") + " 시크릿이 아직 없습니다.")}`);
      const nonce = crypto.randomUUID();
      await sb.from("social_oauth_state").delete().lt("created_at", new Date(Date.now() - 3600e3).toISOString());
      await sb.from("social_oauth_state").insert({ nonce, platform: start, ret });
      return Response.redirect(authorizeUrl(start, nonce), 302);
    }

    const state = u.searchParams.get("state") || "";
    const { data: st } = await sb.from("social_oauth_state").select("*").eq("nonce", state).maybeSingle();
    if (!st || !VALID.includes(st.platform)) return html("연결 요청이 만료됐습니다. 관리자 화면에서 다시 눌러 주세요.", 400);
    await sb.from("social_oauth_state").delete().eq("nonce", state);
    const ed = isEd(st.platform); const base = baseOf(st.platform);
    const err = u.searchParams.get("error_description") || u.searchParams.get("error");
    if (err) return ed ? html("연결이 취소됐습니다: " + err.replace(/</g, "&lt;"), 400) : back(st.ret, `social_err=${encodeURIComponent(err)}`);
    const code = (u.searchParams.get("code") || "").replace(/#_$/, "");
    if (base === "youtube") {
      const title = await youtubeConnect(code, ed ? 2 : 1);
      return ed ? html(`✅ 유튜브 '${title}' 채널 연결 완료. 이 창을 닫으셔도 됩니다.`) : back(st.ret, "social_ok=youtube");
    }
    const t = await exchange(base, code);
    // 다른 계정(개인 계정 등)으로 로그인돼 있으면 저장하지 않는다: 게시물이 엉뚱한 계정에 올라가는 것을 막는다
    const want = ed ? ED_USER : (env(base === "instagram" ? "IG_EXPECT_USERNAME" : "TH_EXPECT_USERNAME") || "value.note.korea");
    if (t.username && t.username.toLowerCase() !== want.toLowerCase()) {
      const m = `@${t.username} 계정으로 로그인돼 있습니다. @${want} 계정으로 다시 로그인한 뒤 연결해 주세요. 기존 연결은 그대로 유지됩니다.`;
      return ed ? html("⚠️ " + m, 400) : back(st.ret, `social_err=${encodeURIComponent(m)}`);
    }
    const row = { platform: base, account_id: t.account_id, username: t.username, access_token: t.access_token,
      expires_at: new Date(Date.now() + (Number(t.expires_in) || 5184000) * 1000).toISOString(), updated_at: new Date().toISOString() };
    const { error } = await sb.from(ed ? "ed_accounts" : "social_accounts").upsert(row);
    if (error) throw new Error(error.message);
    if (ed) return html(`✅ @${t.username} ${base === "instagram" ? "인스타그램" : "쓰레드"} 연결 완료. 이 창을 닫으셔도 됩니다.`);
    // 인스타: 댓글·메시지 웹훅을 이 계정에 구독 (권한이 아직 없으면 조용히 넘어간다)
    if (base === "instagram") {
      await fetch(`https://graph.instagram.com/v23.0/${t.account_id}/subscribed_apps?subscribed_fields=comments,messages,messaging_postbacks&access_token=${encodeURIComponent(t.access_token)}`, { method: "POST" })
        .then(r => r.json()).then(j => console.log("subscribed_apps", JSON.stringify(j))).catch(e => console.error("subscribed_apps", e));
    }
    return back(st.ret, `social_ok=${base}`);
  } catch (e) {
    return html("연결 중 오류가 났습니다: " + String((e as Error).message || e).replace(/</g, "&lt;"), 500);
  }
});
