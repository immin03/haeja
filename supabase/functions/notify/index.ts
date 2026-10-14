// 휴대폰 푸시 알림
// - {action:"pubkey"}  : (화면에서 호출) 푸시 공개키를 돌려준다. 키가 없으면 처음 한 번 만들어 push_config 표에 저장한다.
// - {id, owner}        : (DB 트리거가 호출) 새 알림 문서를 그 사용자의 모든 기기로 보낸다. 만료된 구독은 지운다.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";
import webpush from "npm:web-push@3.6.7";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const cors = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};
const json = (o: unknown, status = 200) => new Response(JSON.stringify(o), { status, headers: { ...cors, "Content-Type": "application/json" } });

async function keys() {
  const { data } = await sb.from("push_config").select("public_key, private_key").eq("id", 1).maybeSingle();
  if (data) return { pub: data.public_key, priv: data.private_key };
  const k = webpush.generateVAPIDKeys();
  const { error } = await sb.from("push_config").insert({ id: 1, public_key: k.publicKey, private_key: k.privateKey });
  if (error) { const again = await sb.from("push_config").select("public_key, private_key").eq("id", 1).single(); return { pub: again.data!.public_key, priv: again.data!.private_key }; }
  return { pub: k.publicKey, priv: k.privateKey };
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  const body = await req.json().catch(() => ({}));
  try {
    const k = await keys();
    if (body.action === "pubkey") return json({ publicKey: k.pub });

    if (!body.id || !body.owner) return json({ ok: false, msg: "id, owner 필요" }, 400);
    const { data: alert } = await sb.from("docs").select("data").eq("collection", "alerts").eq("id", body.id).eq("owner", body.owner).maybeSingle();
    if (!alert) return json({ ok: false, msg: "알림 없음" }, 404);
    const a = alert.data || {};
    const { data: subs } = await sb.from("docs").select("id, data").eq("collection", "push_subs").eq("owner", body.owner);
    webpush.setVapidDetails("mailto:noreply@haeja.app", k.pub, k.priv);
    const payload = JSON.stringify({ title: a.title || "스노우볼 노트", body: a.body || "", tag: a.tag || body.id, url: "/#alerts" });
    let sent = 0, gone = 0;
    for (const s of subs || []) {
      try { await webpush.sendNotification(s.data.sub, payload, { TTL: 86400, urgency: a.level === "urgent" ? "high" : "normal" }); sent++; }
      catch (e) {
        const code = (e as { statusCode?: number }).statusCode;
        if (code === 404 || code === 410) { await sb.from("docs").delete().eq("collection", "push_subs").eq("id", s.id); gone++; }
      }
    }
    return json({ ok: true, sent, gone });
  } catch (e) {
    return json({ ok: false, error: String((e as Error)?.message || e) }, 500);
  }
});
