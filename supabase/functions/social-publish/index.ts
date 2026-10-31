// 인스타·쓰레드 카드뉴스·릴스 자동 게시
// - {} (5분마다 cron)      : 토큰 갱신 → 처리 중인 영상 마무리 → 시간이 된 글을 채널별로 1편씩 게시
//                            릴스(영상)는 컨테이너를 만들고 'processing'으로 둔 뒤, 다음 실행 때 처리가 끝났으면 게시
//                            같은 채널은 최소 90분 간격(연결이 늦어 밀린 글이 한꺼번에 올라가지 않게)
// - {action:"now", id, t}  : (관리자) 해당 글을 지금 바로 게시
// - {action:"check", t}    : (관리자) 두 계정 연결 상태와 게시 한도 확인
// - 날짜 경과 차단: 캡션·제목에 연도 없이 적힌 'N월 N일'(올해 날짜) 중 가장 최근 날짜가 지금(KST)보다 2일 넘게 지났으면
//                   정기 게시하지 않고 paused=true + '보류: 날짜 경과'로 돌린다 (미리 만든 콘텐츠를 며칠 뒤 올려 숫자가 달라지는 일 방지, 2026-10-28)
// - 스토리: 인스타에 올라간 릴스·카드뉴스를 다음 실행 때 스토리로도 게시 (릴스=같은 영상, 안 되면 표지 / 카드=첫 장). instagram_story_paused=true면 멈춤 (2026-10-31)
// - app_config: social_paused(전체) / instagram_paused / threads_paused(채널별) 가 true면 정기 게시를 건너뜀 (수동 '지금 올리기'는 그대로 동작)
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const cors = { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type", "Access-Control-Allow-Methods": "POST, OPTIONS" };
const json = (o: unknown, status = 200) => new Response(JSON.stringify(o), { status, headers: { ...cors, "Content-Type": "application/json" } });
const IG = "https://graph.instagram.com/v23.0", TH = "https://graph.threads.net/v1.0";
const GAP_MIN = 90;
const DISC = "*본 콘텐츠는 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아닙니다.";
// 모든 게시물 본문 끝에 붙는 고정 안내 (해시태그·고지문 앞)
const CTA = "▶ 현명한 투자를 위한 가치투자 가이드, 밸류노트\n600여 개 기업의 점수와 적정 주가를 프로필 링크에서 확인하세요.";
const igCaption = (p: any) => { const tags = (p.hashtags || []).map((h: string) => "#" + h).join(" "); return p.caption + "\n\n" + CTA + (tags ? "\n\n" + tags : "") + "\n\n" + DISC; };
// 쓰레드에는 댓글 → DM 자동 발송이 없으므로 인스타용 댓글 안내 줄은 뺀다
const thText = (p: any) => { const tail = "\n\n" + CTA + "\n\n" + DISC; const body = String(p.caption).split("\n\n").filter((x: string) => !x.startsWith("💬 댓글에")).join("\n\n"); return body.slice(0, 500 - tail.length) + tail; };
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
  const caption = igCaption(p);
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
  const params: Record<string, string> = { media_type: "CAROUSEL", children: kids.join(","), text: thText(p), access_token: a.access_token };
  if (p.threads_tag) params.topic_tag = p.threads_tag;
  const c = await call(`${TH}/${a.account_id}/threads`, params);
  await waitReady(`${TH}/${c.id}`, "status", a.access_token);
  const pub = await call(`${TH}/${a.account_id}/threads_publish`, { creation_id: c.id, access_token: a.access_token });
  const link = await call(`${TH}/${pub.id}`, { fields: "permalink", access_token: a.access_token }, "GET").catch(() => ({}));
  return { id: pub.id, permalink: link.permalink || null };
}

// 릴스: 영상 컨테이너만 만든다 (처리에 1~3분 걸려 다음 실행에서 게시)
async function startReel(ch: "ig" | "th", a: Acc, p: any, site: string) {
  if (ch === "ig") {
    const params: Record<string, string> = { media_type: "REELS", video_url: site + p.video, share_to_feed: "true",
      caption: igCaption(p), access_token: a.access_token };
    if (p.cover) params.cover_url = site + p.cover;
    return (await call(`${IG}/${a.account_id}/media`, params)).id as string;
  }
  const params: Record<string, string> = { media_type: "VIDEO", video_url: site + p.video,
    text: thText(p), access_token: a.access_token };
  if (p.threads_tag) params.topic_tag = p.threads_tag;
  return (await call(`${TH}/${a.account_id}/threads`, params)).id as string;
}

// 처리 중인 영상 컨테이너를 확인해, 끝났으면 게시
async function finishReels(acc: Record<string, Acc>) {
  const out: unknown[] = [];
  for (const ch of ["ig", "th"] as const) {
    const a = acc[ch === "ig" ? "instagram" : "threads"]; if (!a) continue;
    const { data: rows } = await sb.from("social_posts").select("*").eq(`${ch}_status`, "processing");
    for (const p of rows || []) {
      const cid = p[`${ch}_container`]; const base = ch === "ig" ? IG : TH; const field = ch === "ig" ? "status_code" : "status";
      try {
        const st = (await call(`${base}/${cid}`, { fields: field, access_token: a.access_token }, "GET"))[field];
        if (st === "ERROR" || st === "EXPIRED") throw new Error("영상 처리 실패 (" + st + ")");
        if (st !== "FINISHED") {
          if (Date.now() - new Date(p[`${ch}_at`]).getTime() > 40 * 60e3) throw new Error("영상 처리 시간이 40분을 넘었습니다");
          continue;
        }
        const pub = await call(ch === "ig" ? `${IG}/${a.account_id}/media_publish` : `${TH}/${a.account_id}/threads_publish`, { creation_id: cid, access_token: a.access_token });
        const link = await call(`${base}/${pub.id}`, { fields: "permalink", access_token: a.access_token }, "GET").catch(() => ({}));
        await sb.from("social_posts").update({ [`${ch}_status`]: "posted", [`${ch}_media_id`]: pub.id, [`${ch}_permalink`]: link.permalink || null, [`${ch}_at`]: new Date().toISOString() }).eq("id", p.id);
        out.push({ ch, id: p.id, posted: pub.id });
      } catch (e) {
        const msg = String((e as Error).message || e).slice(0, 500);
        await sb.from("social_posts").update({ [`${ch}_status`]: "failed", [`${ch}_error`]: msg, [`${ch}_at`]: new Date().toISOString() }).eq("id", p.id);
        out.push({ ch, id: p.id, error: msg });
      }
    }
  }
  return out;
}

// ── 스토리 자동 게시 (2026-10-31) ─────────────────────────────────────────
// 인스타에 피드 게시물(릴스·카드뉴스)이 올라가면, 다음 실행(5분 안)에 같은 소재로 스토리를 한 번 더 올린다.
// - 릴스: 같은 영상을 스토리로. 영상이 길어 거부·처리 실패하면 표지 이미지로 자동 대체
// - 카드뉴스: 첫 장 이미지
// - 피드 게시 뒤 12시간이 지난 건은 올리지 않고 skipped (밀린 옛 글이 한꺼번에 스토리로 나가지 않게)
// - app_config.instagram_story_paused = true 면 멈춤
// - 스토리는 API로 링크 스티커·게시물 공유 스티커를 붙일 수 없음(메타 제한) → 프로필 방문 유도용
const STORY_MAX_AGE_H = 12;
const storyImage = (p: any) => p.kind === "reel" ? (p.cover || null) : ((p.images || [])[0] || null);

async function startStory(a: Acc, p: any, site: string, mode: "video" | "image") {
  const params: Record<string, string> = { media_type: "STORIES", access_token: a.access_token };
  if (mode === "video") params.video_url = site + p.video;
  else params.image_url = site + storyImage(p);
  const id = (await call(`${IG}/${a.account_id}/media`, params)).id as string;
  await sb.from("social_posts").update({ story_status: "processing", story_container: id, story_mode: mode, story_error: null, story_at: new Date().toISOString() }).eq("id", p.id);
  return id;
}

async function storyFail(p: any, msg: string) {
  await sb.from("social_posts").update({ story_status: "failed", story_error: msg.slice(0, 500), story_at: new Date().toISOString() }).eq("id", p.id);
}

// 영상이 안 되면 이미지로 다시 시도. 이미지도 없으면 실패 처리
async function storyFallback(a: Acc, p: any, site: string, why: string) {
  if (p.story_mode !== "image" && storyImage(p)) {
    try { await startStory(a, { ...p, story_mode: "image" }, site, "image"); return { id: p.id, fallback: "image", why }; }
    catch (e) { why += " / 이미지 대체도 실패: " + String((e as Error).message || e); }
  }
  await storyFail(p, why);
  return { id: p.id, error: why };
}

async function stories(acc: Record<string, Acc>, site: string) {
  const a = acc.instagram; if (!a || !site) return [];
  if ((await cfg("instagram_story_paused")) === true) return [{ idle: "paused" }];
  const out: unknown[] = [];

  // 1) 처리 중인 스토리 마무리
  const { data: proc } = await sb.from("social_posts").select("*").eq("story_status", "processing");
  for (const p of proc || []) {
    try {
      const st = (await call(`${IG}/${p.story_container}`, { fields: "status_code", access_token: a.access_token }, "GET")).status_code;
      if (st === "ERROR" || st === "EXPIRED") { out.push(await storyFallback(a, p, site, "스토리 처리 실패 (" + st + ")")); continue; }
      if (st !== "FINISHED") {
        if (Date.now() - new Date(p.story_at).getTime() > 30 * 60e3) out.push(await storyFallback(a, p, site, "스토리 처리 시간이 30분을 넘었습니다"));
        continue;
      }
      const pub = await call(`${IG}/${a.account_id}/media_publish`, { creation_id: p.story_container, access_token: a.access_token });
      await sb.from("social_posts").update({ story_status: "posted", story_media_id: pub.id, story_error: null, story_at: new Date().toISOString() }).eq("id", p.id);
      out.push({ id: p.id, story: pub.id, mode: p.story_mode });
    } catch (e) {
      const msg = String((e as Error).message || e);
      await storyFail(p, msg); out.push({ id: p.id, error: msg });
    }
  }

  // 2) 피드에 올라간 글 → 스토리 시작 (한 번에 최대 2편)
  const { data: due } = await sb.from("social_posts").select("*")
    .eq("to_ig", true).eq("ig_status", "posted").eq("story_status", "pending")
    .order("ig_at").limit(10);
  let started = 0;
  for (const p of due || []) {
    if (started >= 2) break;
    if (!p.ig_at || Date.now() - new Date(p.ig_at).getTime() > STORY_MAX_AGE_H * 3600e3) {
      await sb.from("social_posts").update({ story_status: "skipped", story_error: `피드 게시 뒤 ${STORY_MAX_AGE_H}시간이 지나 스토리를 건너뜀` }).eq("id", p.id);
      continue;
    }
    const { data: lock } = await sb.from("social_posts").update({ story_status: "publishing" }).eq("id", p.id).eq("story_status", "pending").select("id");
    if (!lock?.length) continue;
    const mode: "video" | "image" | null = p.kind === "reel" && p.video ? "video" : storyImage(p) ? "image" : null;
    if (!mode) { await storyFail(p, "스토리로 올릴 영상·이미지가 없습니다"); continue; }
    try { await startStory(a, p, site, mode); out.push({ id: p.id, started: mode }); }
    catch (e) { out.push(await storyFallback(a, { ...p, story_mode: mode }, site, String((e as Error).message || e))); }
    started++;
  }
  return out;
}

// 인스타 게시 직후 관리자 휴대폰으로 알림: 음악 추가 안내
async function remind(p: any, link: string | null) {
  const owner = await cfg("publisher"); if (!owner) return;
  const id = "sns-" + p.id + "-" + Date.now();
  await sb.from("docs").insert({ owner, collection: "alerts", id, data: {
    at: new Date().toISOString(), level: "info", source: "SNS 게시", read: false,
    title: `인스타 #${p.id} 게시 완료 · 음악을 붙여 주세요`,
    body: `${p.title}${p.music ? " · 추천: " + p.music : ""}. 게시물 ··· → 수정 → 음악 추가.`,
    link: link ? { url: link } : {} } });
}

// 한 채널에 한 편 게시. 상태를 먼저 'publishing'으로 잡아 중복 게시를 막는다.
async function publish(ch: "ig" | "th", p: any, acc: Record<string, Acc>, site: string) {
  const a = acc[ch === "ig" ? "instagram" : "threads"]; if (!a) return { skipped: "not connected" };
  const { data: lock } = await sb.from("social_posts").update({ [`${ch}_status`]: "publishing", [`${ch}_error`]: null })
    .eq("id", p.id).in(`${ch}_status`, ["pending", "failed"]).select("id");
  if (!lock?.length) return { skipped: "locked" };
  try {
    if (p.kind === "reel") {
      const cid = await startReel(ch, a, p, site);
      await sb.from("social_posts").update({ [`${ch}_status`]: "processing", [`${ch}_container`]: cid, [`${ch}_at`]: new Date().toISOString() }).eq("id", p.id);
      return { processing: cid };
    }
    const r = ch === "ig" ? await postInstagram(a, p, site) : await postThreads(a, p, site);
    await sb.from("social_posts").update({ [`${ch}_status`]: "posted", [`${ch}_media_id`]: r.id, [`${ch}_permalink`]: r.permalink, [`${ch}_at`]: new Date().toISOString() }).eq("id", p.id);
    if (ch === "ig" && p.music) await remind(p, r.permalink).catch(e => console.error("remind", e));
    return { posted: r };
  } catch (e) {
    const msg = String((e as Error).message || e).slice(0, 500);
    await sb.from("social_posts").update({ [`${ch}_status`]: "failed", [`${ch}_error`]: msg, [`${ch}_at`]: new Date().toISOString() }).eq("id", p.id);
    return { error: msg };
  }
}

// 캡션·제목 속 '올해' 날짜(앞에 'YYYY년'이 없는 'N월 N일') 중 가장 최근 날짜. 연도가 붙은 과거 사례(예: 2001년 11월 30일)는 제외.
const STALE_DAYS = 2;
function latestDate(p: any): Date | null {
  const text = `${p.title || ""}\n${p.caption || ""}`;
  const kst = new Date(Date.now() + 9 * 3600e3);
  let best: Date | null = null;
  for (const m of text.matchAll(/(\d{4}년\s*)?(\d{1,2})월\s*(\d{1,2})일/g)) {
    if (m[1]) continue;
    const mo = +m[2], d = +m[3]; if (mo < 1 || mo > 12 || d < 1 || d > 31) continue;
    let dt = new Date(Date.UTC(kst.getUTCFullYear(), mo - 1, d));
    if (dt.getTime() - kst.getTime() > 60 * 864e5) dt = new Date(Date.UTC(kst.getUTCFullYear() - 1, mo - 1, d)); // 연말→연초
    if (!best || dt > best) best = dt;
  }
  return best;
}
function staleReason(p: any): string | null {
  const d = latestDate(p); if (!d) return null;
  const kst = new Date(Date.now() + 9 * 3600e3);
  const today = Date.UTC(kst.getUTCFullYear(), kst.getUTCMonth(), kst.getUTCDate());
  const days = Math.floor((today - d.getTime()) / 864e5);
  return days > STALE_DAYS ? `보류: 날짜 경과 (내용 기준일 ${d.getUTCMonth() + 1}/${d.getUTCDate()}, ${days}일 지남)` : null;
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
    const res: Record<string, unknown> = { finished: await finishReels(acc) };
    if (!site || (await cfg("social_paused")) === true) return json({ ...res, idle: !site ? "no site" : "paused" });
    res.stories = await stories(acc, site).catch(e => [{ error: String((e as Error).message || e) }]);
    const now = new Date().toISOString();
    for (const ch of ["ig", "th"] as const) {
      if (!acc[ch === "ig" ? "instagram" : "threads"]) continue;
      if ((await cfg(ch === "ig" ? "instagram_paused" : "threads_paused")) === true) { res[ch] = { idle: "paused" }; continue; }
      const { count: busy } = await sb.from("social_posts").select("id", { count: "exact", head: true }).eq(`${ch}_status`, "processing");
      if (busy) continue;
      if (Date.now() - (await lastAt(ch)) < GAP_MIN * 60e3) continue;
      const { data: due } = await sb.from("social_posts").select("*")
        .eq(ch === "ig" ? "to_ig" : "to_threads", true).eq(`${ch}_status`, "pending")
        .eq("approved", true).eq("paused", false).lte("scheduled_at", now)
        .order("scheduled_at").limit(10);
      for (const p of due || []) {
        const why = staleReason(p);
        if (why) {
          await sb.from("social_posts").update({ paused: true, [`${ch}_error`]: why }).eq("id", p.id);
          ((res.held ||= []) as unknown[]).push({ ch, id: p.id, why });
          continue;
        }
        res[ch] = { id: p.id, ...(await publish(ch, p, acc, site)) };
        break;
      }
    }
    return json(res);
  } catch (e) {
    return json({ error: String((e as Error).message || e) }, 500);
  }
});
