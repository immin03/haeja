// 카카오 "나에게 보내기" 공통 모듈 (2026-11-10)
// 카카오 로그인 회원이 '카카오톡 메시지 전송(talk_message)'에 동의하면 kakao_tokens 에 토큰을 두고,
// 알림을 그 회원 본인의 카톡(나와의 채팅)으로 보낸다. 비용 0원, 정보성 메시지만.
// 필요한 비밀값: KAKAO_REST_KEY(카카오 개발자 콘솔 REST API 키 = OAuth client_id), KAKAO_CLIENT_SECRET(보안 탭에서 켰을 때만)
import type { SupabaseClient } from "npm:@supabase/supabase-js@2.45.4";

export const SITE = "https://www.valuenote.co.kr";
export const KAKAO_REST_KEY = Deno.env.get("KAKAO_REST_KEY") || "";
export const KAKAO_CLIENT_SECRET = Deno.env.get("KAKAO_CLIENT_SECRET") || "";

export type KakaoToken = {
  uid: string; refresh_token: string | null; access_token: string | null;
  access_expires_at: string | null; refresh_expires_at: string | null; scopes: string[] | null;
  linked_at: string; last_sent_at: string | null; fail_count: number; last_error: string | null;
};
export type SendResult = { ok: boolean; skip?: boolean; reason?: string };

const form = (o: Record<string, string>) => new URLSearchParams(o).toString();
export const absUrl = (u?: string) => !u ? SITE + "/" : /^https?:/.test(u) ? u : SITE + (u.startsWith("/") ? u : "/" + u);

/* 카카오 사용자 토큰으로 동의한 scope 목록을 읽는다 */
export async function kakaoScopes(accessToken: string): Promise<{ ok: boolean; agreed: string[]; error?: string }> {
  const r = await fetch("https://kapi.kakao.com/v2/user/scopes", { headers: { Authorization: `Bearer ${accessToken}` } });
  const j = await r.json().catch(() => ({}));
  if (!r.ok) return { ok: false, agreed: [], error: j?.msg || `HTTP ${r.status}` };
  return { ok: true, agreed: (j?.scopes || []).filter((s: { agreed?: boolean }) => s.agreed).map((s: { id: string }) => s.id) };
}

/* 만료된 액세스 토큰을 리프레시 토큰으로 갱신해 저장. 실패하면 null */
async function refresh(sb: SupabaseClient, t: KakaoToken): Promise<string | null> {
  if (!KAKAO_REST_KEY) { await sb.from("kakao_tokens").update({ last_error: "KAKAO_REST_KEY 없음" }).eq("uid", t.uid); return null; }
  if (!t.refresh_token) return null;
  const body: Record<string, string> = { grant_type: "refresh_token", client_id: KAKAO_REST_KEY, refresh_token: t.refresh_token };
  if (KAKAO_CLIENT_SECRET) body.client_secret = KAKAO_CLIENT_SECRET;
  const r = await fetch("https://kauth.kakao.com/oauth/token", { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded;charset=utf-8" }, body: form(body) });
  const j = await r.json().catch(() => ({}));
  if (!r.ok || !j.access_token) {
    const code = String(j?.error_code || j?.error || r.status);
    // 리프레시 토큰이 죽었으면(만료·연결 끊김) 행을 지운다 — 다음에 다시 동의받는다
    if (/KOE319|KOE320|KOE322|invalid_grant/i.test(code)) await sb.from("kakao_tokens").delete().eq("uid", t.uid);
    else await sb.from("kakao_tokens").update({ fail_count: (t.fail_count || 0) + 1, last_error: `refresh ${code}` }).eq("uid", t.uid);
    return null;
  }
  const now = Date.now();
  const patch: Record<string, unknown> = { access_token: j.access_token, access_expires_at: new Date(now + (j.expires_in || 21599) * 1000).toISOString(), last_error: null };
  if (j.refresh_token) { patch.refresh_token = j.refresh_token; patch.refresh_expires_at = new Date(now + (j.refresh_token_expires_in || 5183999) * 1000).toISOString(); }
  await sb.from("kakao_tokens").update(patch).eq("uid", t.uid);
  return j.access_token as string;
}

/* 처음 연결: Supabase OAuth 세션이 준 카카오 토큰을 검사해 저장 */
export async function linkKakao(sb: SupabaseClient, uid: string, accessToken: string, refreshToken?: string | null): Promise<{ ok: boolean; linked: boolean; scopes: string[]; reason?: string }> {
  const sc = await kakaoScopes(accessToken);
  if (!sc.ok) return { ok: false, linked: false, scopes: [], reason: "카카오 토큰 확인 실패: " + (sc.error || "") };
  if (!sc.agreed.includes("talk_message")) return { ok: false, linked: false, scopes: sc.agreed, reason: "카카오톡 메시지 전송에 동의하지 않았습니다" };
  const now = Date.now();
  const row = { uid, access_token: accessToken, access_expires_at: new Date(now + 5 * 3600e3).toISOString(), scopes: sc.agreed, linked_at: new Date().toISOString(), fail_count: 0, last_error: null } as Record<string, unknown>;
  if (refreshToken) { row.refresh_token = refreshToken; row.refresh_expires_at = new Date(now + 59 * 864e5).toISOString(); }
  const { error } = await sb.from("kakao_tokens").upsert(row, { onConflict: "uid" });
  if (error) return { ok: false, linked: false, scopes: sc.agreed, reason: error.message };
  return { ok: true, linked: true, scopes: sc.agreed };
}

/* 알림 한 건을 그 회원의 카톡으로. 토큰이 없으면 {ok:false, skip:true} */
export async function sendKakaoMemo(sb: SupabaseClient, uid: string, m: { title: string; body?: string; url?: string }): Promise<SendResult> {
  const { data } = await sb.from("kakao_tokens").select("*").eq("uid", uid).maybeSingle();
  const t = data as KakaoToken | null;
  if (!t) return { ok: false, skip: true, reason: "연결 안 됨" };
  let token = t.access_token;
  if (!token || !t.access_expires_at || Date.parse(t.access_expires_at) - Date.now() < 60e3) token = await refresh(sb, t);
  if (!token) return { ok: false, reason: KAKAO_REST_KEY ? "토큰 갱신 실패" : "KAKAO_REST_KEY 없음" };
  const url = absUrl(m.url);
  const text = [m.title, m.body].filter(Boolean).join("\n").slice(0, 200);     // 텍스트 템플릿은 200자 제한
  const template_object = { object_type: "text", text, link: { web_url: url, mobile_web_url: url }, button_title: "밸류노트에서 보기" };
  const send = (tk: string) => fetch("https://kapi.kakao.com/v2/api/talk/memo/default/send", { method: "POST", headers: { Authorization: `Bearer ${tk}`, "Content-Type": "application/x-www-form-urlencoded;charset=utf-8" }, body: form({ template_object: JSON.stringify(template_object) }) });
  let r = await send(token);
  if (r.status === 401) { const nt = await refresh(sb, t); if (!nt) return { ok: false, reason: "토큰 만료" }; r = await send(nt); }
  const j = await r.json().catch(() => ({}));
  if (!r.ok || j.result_code !== 0) {
    const code = j?.code ?? r.status, msg = `${code} ${j?.msg || ""}`.trim();
    if (code === -402) await sb.from("kakao_tokens").delete().eq("uid", uid);   // 동의 철회(scope 없음) → 다시 동의받아야 함
    else await sb.from("kakao_tokens").update({ fail_count: (t.fail_count || 0) + 1, last_error: msg }).eq("uid", uid);
    return { ok: false, reason: msg };
  }
  await sb.from("kakao_tokens").update({ last_sent_at: new Date().toISOString(), fail_count: 0, last_error: null }).eq("uid", uid);
  return { ok: true };
}
