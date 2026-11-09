// 카카오 "나에게 보내기" 연결 (2026-11-10) — 로그인한 회원 본인만, Authorization: Bearer <Supabase JWT>
// - {action:"link", provider_token, provider_refresh_token} : 카카오 로그인 직후 세션의 카카오 토큰을 검사(talk_message 동의)해 저장 → {ok, linked, scopes, reason?}
// - {action:"status"} : {ok, linked, linked_at, last_sent_at, enabled}   (enabled = app_config.kakao_msg 스위치)
// - {action:"unlink"} : 저장한 토큰 삭제 → {ok}
// - {action:"test"}   : 본인 카톡으로 테스트 메시지 1건 → {ok, reason?}
// verify_jwt = false (함수 안에서 사용자를 확인한다)
// 배포: deploy_edge_function files 에 _shared/kakao.ts(리포 supabase/functions/_shared/kakao.ts)를 "_shared/kakao.ts" 이름으로 함께 올린다. 번들러가 함수 폴더(source/) 기준으로 경로를 풀어 import 는 ./_shared/ 로 쓴다.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";
import { linkKakao, sendKakaoMemo, KAKAO_REST_KEY } from "./_shared/kakao.ts";

const URL_ = Deno.env.get("SUPABASE_URL")!, SRK = Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, ANON = Deno.env.get("SUPABASE_ANON_KEY")!;
const sb = createClient(URL_, SRK, { auth: { persistSession: false } });
const cors = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type", "Access-Control-Allow-Methods": "POST, OPTIONS" };
const json = (o: unknown, status = 200) => new Response(JSON.stringify(o), { status, headers: { ...cors, "Content-Type": "application/json" } });

async function userOf(req: Request) {
  const auth = req.headers.get("Authorization") || "";
  if (!auth.startsWith("Bearer ")) return null;
  const c = createClient(URL_, ANON, { global: { headers: { Authorization: auth } }, auth: { persistSession: false } });
  const { data: { user } } = await c.auth.getUser();
  return user;
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  try {
    const body = await req.json().catch(() => ({}));
    const user = await userOf(req);
    if (!user) return json({ ok: false, error: "로그인이 필요합니다" }, 401);
    const uid = user.id;

    if (body.action === "link") {
      if (!KAKAO_REST_KEY) return json({ ok: false, linked: false, scopes: [], reason: "KAKAO_REST_KEY 없음 — 함수 비밀값에 카카오 REST API 키를 넣어야 합니다" });
      if (!body.provider_token) return json({ ok: false, linked: false, scopes: [], reason: "provider_token 필요" }, 400);
      return json(await linkKakao(sb, uid, String(body.provider_token), body.provider_refresh_token ? String(body.provider_refresh_token) : null));
    }
    if (body.action === "status") {
      const [{ data: t }, { data: on }] = await Promise.all([
        sb.from("kakao_tokens").select("linked_at,last_sent_at,fail_count,last_error").eq("uid", uid).maybeSingle(),
        sb.from("app_config").select("value").eq("key", "kakao_msg").maybeSingle(),
      ]);
      return json({ ok: true, linked: !!t, linked_at: t?.linked_at || null, last_sent_at: t?.last_sent_at || null, enabled: on?.value === true, key: !!KAKAO_REST_KEY });
    }
    if (body.action === "unlink") { await sb.from("kakao_tokens").delete().eq("uid", uid); return json({ ok: true }); }
    if (body.action === "test") {
      const r = await sendKakaoMemo(sb, uid, { title: "밸류노트 카카오톡 알림이 연결됐습니다", body: "관심 회사가 싸지거나 점수가 바뀌면 이렇게 알려 드립니다.", url: "/?tab=alerts&from=kakao" });
      return json(r.ok ? { ok: true } : { ok: false, reason: r.reason });
    }
    return json({ ok: false, error: "action 필요" }, 400);
  } catch (e) {
    return json({ ok: false, error: String((e as Error)?.message || e) }, 500);
  }
});
