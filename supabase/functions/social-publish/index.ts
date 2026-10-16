// 인스타·쓰레드 카드뉴스 자동 게시
// - {} (5분마다 cron)      : 토큰 갱신 → 시간이 된 글을 채널별로 1편씩 게시
//                            같은 채널은 최소 90분 간격(연결이 늦어 밀린 글이 한꺼번에 올라가지 않게)
// - {action:"now", id, t}  : (관리자) 해당 글을 지금 바로 게시
// - {action:"check", t}    : (관리자) 두 계정 연결 상태와 게시 한도 확인
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const cors = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type", "Access-Control-Allow-Methods": "POST, OPTIONS" };
const json = (o: unknown, status = 200) => new Response(JSON.stringify(o), { status, headers: { ...cors, "Content-Type": "application/json" } });
const IG = "https://graph.instagram.com/v23.0", TH = "https://graph.threads.net/v1.0";
const GAP_MIN = 90;
const sleep = (ms: number) => new Promise(r => setTimeout(r, ms));

type Acc = { platform: string; account_id: string; username: string; access_token: string; expires_at: string };

async function isAdmin(token: string) {
  const { data } = await sb.auth.getUser(token || "");
  const email = data?.user?.email; if (!email) return false;
  const { data: cfg } = await sb.from("app_config").select("value").eq("key", "admins").maybeSingle();
  return Array.isArray(cfg?.value) && cfg!.value.includes(email);
}
async function cfg(key: string) { const { data } = await sb.from("app_config").select("value").eq("key", key).maybeSingle(); return data?.value; }
async function accounts(): Promise<Record<string, Acc>> {
  const { data } = await sb.from("social_accounts").select("*");
  return Object.fromEntries((data || []).map((a: Acc) => [a.platform, a]));
}
async function call(url: string, params: Record<string, string>, method = "POST") {
  const q = new URLSearchParams(params);
  const r = method === "GET" ? await fetch(url + "?" + q) : await fetch(url, { method, body: q });
  const j = await r.json().catch(() => ({}));
  if (!r.ok || j.error) throw new Error((j.error && (j.error.error_user_msg || j.error.message)) || `HTTP ${r.status}`);
  return j;
}

// 만료 10일 전이면 갱신 (둘 다 60일 장기 토큰)
async function refresh(acc: Record<string, Acc>) {
  for (const a of Object.values(acc)) {
    if (!a.expires_at || new Date(a.expires_at).getTime() - Date.now() > 10 * 864e5) continue;
    try {
      const j = a.platform === "instagram"
        ? await call("https://graph.instagram.com/refresh_access_token", { grant_type: "ig_refresh_token", access_token: a.access_token }, "GET")
        : await call("https://graph.threads.net/refresh_access_token", { grant_type: "th_refresh_token", access_token: a.access_token }, "GET");
      a.access_token = j.access_token;
      a.expires_at = new Date(Date.now() + (Number(j.expires_in) || 5184000) * 1000).toISOString();
      await sb.from("social_accounts").update({ access_token: a.access_token, expires_at: a.expires_at, updated_at: new Date().toISOString() }).eq("platform", a.platform);
    } catch (e) { console.error("refresh", a.platform, e); }
  }
}

async function waitReady(url: string, field: string, token: string) {
  for (let i = 0; i < 20; i++) {
    const j = await call(url, { fields: field, access_token: token }, "GET");
    const s = j[field];
    if (s === "FINISHED" || s === "PUBLISHED") return;
    if (s === "ERROR" || s === "EXPIRED") throw new Error("미디어 처리 실패: " + JSON.stringify(j));
    await sleep(3000);
  }
  throw new Error("미디어 처리 시간이 초과됐습니다");
}

async function postInstagram(a: Acc, p: any, site: string) {
  const urls = p.images.map((x: string) => site + x);
  const kids: string[] = [];
  for (const image_url of urls) kids.push((await call(`${IG}/${a.account_id}/media`, { image_url, is_carousel_item: "true", access_token: a.access_token })).id);
  for (const k of kids) await waitReady(`${IG}/${k}`, "status_code", a.access_token);
  const caption = p.caption + "\n\n" + (p.hashtags || []).map((h: string) => "#" + h).join(" ");
  const c = await call(`${IG}/${a.account_id}/media`, { media_type: "CAROUSEL", children: kids.join(","), caption, access_token: a.access_token });
  await waitReady(`${IG}/${c.id}`, "status_code", a.access_token);
  const pub = await call(`${IG}/${a.account_id}/media_publish`, { creation_id: c.id, access_token: a.access_token });
  const link = await call(`${IG}/${pub.id}`, { fields: "permalink", access_token: a.access_token }, "GET").catch(() => ({}));
  return { id: pub.id, permalink: link.permalink || null };
}

async function postThreads(a: Acc, p: any, site: string) {
  const urls = p.images.map((x: string) => site + x);
  const kids: string[] = [];
  for (const image_url of urls) kids.push((await call(`${TH}/${a.account_id}/threads`, { media_type: "IMAGE", image_url, is_carousel_item: "true", access_token: a.access_token })).id);
  for (const k of kids) await waitReady(`${TH}/${k}`, "status", a.access_token);
  const params: Record<string, string> = { media_type: "CAROUSEL", children: kids.join(","), text: p.caption, access_token: a.access_token };
  if (p.threads_tag) params.topic_tag = p.threads_tag;
  const c = await call(`${TH}/${a.account_id}/threads`, params);
  await waitReady(`${TH}/${c.id}`, "status", a.access_token);
  const pub = await call(`${TH}/${a.account_id}/threads_publish`, { creation_id: c.id, access_token: a.access_token });
  const link = await call(`${TH}/${pub.id}`, { fields: "permalink", access_token: a.access_token }, "GET").catch(() => ({}));
  return { id: pub.id, permalink: link.permalink || null };
}

// 한 채널에 한 편 게시. 상태를 먼저 'publishing'으로 잡아 중복 게시를 막는다.
async function publish(ch: "ig" | "th", p: any, acc: Record<string, Acc>, site: string) {
  const a = acc[ch === "ig" ? "instagram" : "threads"]; if (!a) return { skipped: "not connected" };
  const { data: lock } = await sb.from("social_posts").update({ [`${ch}_status`]: "publishing", [`${ch}_error`]: null })
    .eq("id", p.id).in(`${ch}_status`, ["pending", "failed"]).select("id");
  if (!lock?.length) return { skipped: "locked" };
  try {
    const r = ch === "ig" ? await postInstagram(a, p, site) : await postThreads(a, p, site);
    await sb.from("social_posts").update({ [`${ch}_status`]: "posted", [`${ch}_media_id`]: r.id, [`${ch}_permalink`]: r.permalink, [`${ch}_at`]: new Date().toISOString() }).eq("id", p.id);
    return { posted: r };
  } catch (e) {
    const msg = String((e as Error).message || e).slice(0, 500);
    await sb.from("social_posts").update({ [`${ch}_status`]: "failed", [`${ch}_error`]: msg, [`${ch}_at`]: new Date().toISOString() }).eq("id", p.id);
    return { error: msg };
  }
}

async function lastAt(ch: "ig" | "th") {
  const { data } = await sb.from("social_posts").select(`${ch}_at`).eq(`${ch}_status`, "posted").order(`${ch}_at`, { ascending: false }).limit(1);
  return data?.[0]?.[`${ch}_at`] ? new Date(data[0][`${ch}_at`]).getTime() : 0;
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: cors });
  const body = await req.json().catch(() => ({}));
  try {
    const site = String((await cfg("site_url")) || "").replace(/\/$/, "");
    const acc = await accounts();

    if (body.action === "check") {
      if (!(await isAdmin(body.t))) return json({ error: "not admin" }, 403);
      const out: Record<string, unknown> = { site };
      if (acc.instagram) out.instagram = await call(`${IG}/${acc.instagram.account_id}/content_publishing_limit`, { fields: "quota_usage,config", access_token: acc.instagram.access_token }, "GET").catch(e => ({ error: String(e.message) }));
      if (acc.threads) out.threads = await call(`${TH}/${acc.threads.account_id}/threads_publishing_limit`, { fields: "quota_usage,config", access_token: acc.threads.access_token }, "GET").catch(e => ({ error: String(e.message) }));
      return json(out);
    }

    if (body.action === "now") {
      if (!(await isAdmin(body.t))) return json({ error: "not admin" }, 403);
      if (!site) return json({ error: "사이트 주소가 아직 없습니다. 관리자 SNS 탭을 한 번 열어 주세요." });
      const { data: p } = await sb.from("social_posts").select("*").eq("id", body.id).single();
      const res: Record<string, unknown> = {};
      if (p.to_ig && p.ig_status !== "posted") res.ig = await publish("ig", p, acc, site);
      if (p.to_threads && p.th_status !== "posted") res.th = await publish("th", p, acc, site);
      return json(res);
    }

    // 정기 실행
    await refresh(acc);
    if (!site || (await cfg("social_paused")) === true) return json({ idle: !site ? "no site" : "paused" });
    const now = new Date().toISOString();
    const res: Record<string, unknown> = {};
    for (const ch of ["ig", "th"] as const) {
      if (!acc[ch === "ig" ? "instagram" : "threads"]) continue;
      if (Date.now() - (await lastAt(ch)) < GAP_MIN * 60e3) continue;
      const { data: due } = await sb.from("social_posts").select("*")
        .eq(ch === "ig" ? "to_ig" : "to_threads", true).eq(`${ch}_status`, "pending")
        .eq("approved", true).eq("paused", false).lte("scheduled_at", now)
        .order("scheduled_at").limit(1);
      if (due?.length) res[ch] = { id: due[0].id, ...(await publish(ch, due[0], acc, site)) };
    }
    return json(res);
  } catch (e) {
    return json({ error: String((e as Error).message || e) }, 500);
  }
});
