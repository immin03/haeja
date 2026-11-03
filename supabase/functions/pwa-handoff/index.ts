// 홈 화면 앱 로그인 이어받기
// 아이폰은 Safari와 홈 화면 앱의 로그인이 따로 저장된다. 카카오 가입자는 비밀번호가 없어서 홈 화면 앱에서 다시 로그인하기 어렵다.
// - {action:"create"}          : (Safari, 로그인 상태) 20분짜리 일회용 연결 코드 h(주소용)와 pin(6자리, 직접 입력용)을 만든다.
// - {action:"claim", h | pin}  : (홈 화면 앱, 비로그인) 코드가 맞으면 그 계정의 새 로그인 토큰(token_hash)을 돌려준다.
//                                화면에서 sb.auth.verifyOtp({ token_hash, type: "magiclink" }) 로 로그인한다. Safari 쪽 로그인은 그대로 유지된다.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (o: unknown, status = 200) => new Response(JSON.stringify(o), { status, headers: { ...cors, "Content-Type": "application/json" } });
const TTL_MIN = 20;
const rand = (n: number, abc: string) => { const b = crypto.getRandomValues(new Uint8Array(n)); return [...b].map(x => abc[x % abc.length]).join(""); };

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  const body = await req.json().catch(() => ({}));
  try {
    if (body.action === "create") {
      const jwt = (req.headers.get("Authorization") || "").replace(/^Bearer\s+/i, "");
      const { data: u } = await sb.auth.getUser(jwt);
      const user = u?.user;
      if (!user?.email) return json({ ok: false, msg: "로그인이 필요합니다" }, 401);
      /* 같은 계정의 아직 안 쓴 코드가 20분 안에 있으면 그대로 돌려준다 (안내창을 여러 번 열어도 코드가 바뀌지 않게) */
      const since = new Date(Date.now() - (TTL_MIN - 2) * 60e3).toISOString();
      const { data: old } = await sb.from("pwa_handoff").select("h, pin").eq("user_id", user.id).is("used_at", null).gte("created_at", since).order("created_at", { ascending: false }).limit(1).maybeSingle();
      if (old) return json({ ok: true, h: old.h, pin: old.pin, ttl: TTL_MIN });
      for (let i = 0; i < 5; i++) {
        const h = rand(24, "abcdefghijkmnpqrstuvwxyz23456789"), pin = rand(6, "0123456789");
        const live = new Date(Date.now() - TTL_MIN * 60e3).toISOString();
        const { data: clash } = await sb.from("pwa_handoff").select("h").eq("pin", pin).is("used_at", null).gte("created_at", live).limit(1);
        if (clash && clash.length) continue;
        const { error } = await sb.from("pwa_handoff").insert({ h, pin, user_id: user.id, email: user.email });
        if (!error) return json({ ok: true, h, pin, ttl: TTL_MIN });
      }
      return json({ ok: false, msg: "코드를 만들지 못했습니다" }, 500);
    }

    if (body.action === "claim") {
      const h = typeof body.h === "string" && /^[a-z0-9]{24}$/.test(body.h) ? body.h : "";
      const pin = typeof body.pin === "string" && /^\d{6}$/.test(body.pin) ? body.pin : "";
      if (!h && !pin) return json({ ok: false, msg: "코드 형식이 맞지 않습니다" }, 400);
      /* 숫자 코드 무작위 대입 막기: 최근 10분 실패가 많으면 잠시 막는다 */
      if (pin) {
        const { count } = await sb.from("pwa_handoff_fail").select("id", { count: "exact", head: true }).gte("at", new Date(Date.now() - 10 * 60e3).toISOString());
        if ((count || 0) >= 40) return json({ ok: false, msg: "잠시 뒤 다시 시도해 주세요" }, 429);
      }
      const live = new Date(Date.now() - TTL_MIN * 60e3).toISOString();
      let q = sb.from("pwa_handoff").select("h, email, user_id").is("used_at", null).gte("created_at", live);
      q = h ? q.eq("h", h) : q.eq("pin", pin);
      const { data: row } = await q.order("created_at", { ascending: false }).limit(1).maybeSingle();
      if (!row) {
        if (pin) await sb.from("pwa_handoff_fail").insert({});
        return json({ ok: false, msg: "코드가 맞지 않거나 시간이 지났습니다. Safari에서 새 코드를 확인해 주세요." }, 404);
      }
      const { data: mark } = await sb.from("pwa_handoff").update({ used_at: new Date().toISOString() }).eq("h", row.h).is("used_at", null).select("h");
      if (!mark || !mark.length) return json({ ok: false, msg: "이미 사용된 코드입니다" }, 409);
      const { data: link, error } = await sb.auth.admin.generateLink({ type: "magiclink", email: row.email });
      const token_hash = link?.properties?.hashed_token;
      if (error || !token_hash) return json({ ok: false, msg: "로그인 토큰을 만들지 못했습니다" }, 500);
      /* 오래된 기록 정리 */
      sb.from("pwa_handoff").delete().lt("created_at", new Date(Date.now() - 86400e3).toISOString()).then(() => {});
      sb.from("pwa_handoff_fail").delete().lt("at", new Date(Date.now() - 86400e3).toISOString()).then(() => {});
      return json({ ok: true, token_hash });
    }
    return json({ ok: false, msg: "action 필요" }, 400);
  } catch (e) {
    return json({ ok: false, error: String((e as Error)?.message || e) }, 500);
  }
});
