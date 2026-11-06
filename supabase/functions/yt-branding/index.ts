// 유튜브 채널 꾸미기 (2026-11-06 브랜드 개편)
// GET ?k=<실행 키> : 저장소의 배너 이미지를 채널 배너로 올리고, 채널 설명을 새 문구로 바꾼다.
// 실행 키는 sha256 값만 코드에 둔다 (한 번 쓰고 끝나는 작업용). 프로필 사진은 유튜브 API로 바꿀 수 없어 스튜디오에서 직접.
// verify_jwt = false (브라우저 주소창에서 바로 실행하기 위해서) — 키가 맞지 않으면 아무것도 하지 않는다.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const KEY_HASH = "bca8dc4d95be579003c6d0f098fb38b98b39be21334cb4418afc277800f0aea1";
const BANNER = "https://raw.githubusercontent.com/immin03/haeja/main/brand/youtube-banner-2048x1152.png";
const DESCRIPTION = [
  "현명한 투자를 위한 경제·투자 채널, 밸류노트입니다.",
  "",
  "기업의 숫자부터 그 숫자를 만든 이야기까지 한 장의 노트로 정리합니다. 실적과 재무로 보는 기업 분석, 지금 가격이 싼지 비싼지 따져 보는 주가 전망, 그리고 브랜드가 성공한 이유와 창업부터 지금까지의 기업 역사를 다룹니다.",
  "",
  "투자 권유가 아니라, 판단에 필요한 숫자와 맥락을 드립니다.",
  "",
  "앱 · https://www.valuenote.co.kr",
  "문의 · value.note.korea@gmail.com",
].join("\n");

const json = (o: unknown, status = 200) => new Response(JSON.stringify(o, null, 2), { status, headers: { "Content-Type": "application/json; charset=utf-8" } });
async function sha256(s: string) {
  const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
  return [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, "0")).join("");
}

async function accessToken() {
  const { data } = await sb.from("youtube_account").select("refresh_token").eq("id", 1).maybeSingle();
  if (!data?.refresh_token) throw new Error("youtube_account 에 갱신 토큰이 없습니다");
  const form = new URLSearchParams({ client_id: Deno.env.get("YOUTUBE_CLIENT_ID")!, client_secret: Deno.env.get("YOUTUBE_CLIENT_SECRET")!, grant_type: "refresh_token", refresh_token: data.refresh_token });
  const t = await (await fetch("https://oauth2.googleapis.com/token", { method: "POST", body: form })).json();
  if (!t.access_token) throw new Error("토큰 갱신 실패: " + JSON.stringify(t));
  return t.access_token as string;
}

Deno.serve(async (req: Request) => {
  const k = new URL(req.url).searchParams.get("k") || "";
  if ((await sha256(k)) !== KEY_HASH) return json({ ok: false, error: "key" }, 403);
  const steps: Record<string, unknown> = {};
  try {
    const at = await accessToken();
    const H = { Authorization: "Bearer " + at };

    // 1) 배너 업로드
    const img = await fetch(BANNER);
    if (!img.ok) throw new Error("배너 이미지를 받지 못했습니다: HTTP " + img.status);
    const up = await fetch("https://www.googleapis.com/upload/youtube/v3/channelBanners/insert?uploadType=media", { method: "POST", headers: { ...H, "Content-Type": "image/png" }, body: await img.arrayBuffer() });
    const upj = await up.json();
    if (!up.ok || !upj.url) throw new Error("배너 업로드 실패: " + JSON.stringify(upj));
    steps.banner_uploaded = true;

    // 2) 채널 정보 읽고, 기존 값은 그대로 두고 설명·배너만 바꿔서 저장
    const cj = await (await fetch("https://www.googleapis.com/youtube/v3/channels?part=brandingSettings&mine=true", { headers: H })).json();
    const ch = cj.items?.[0];
    if (!ch) throw new Error("채널을 찾지 못했습니다: " + JSON.stringify(cj));
    const bs = ch.brandingSettings || {};
    steps.old_description = bs.channel?.description || "";
    const body = { id: ch.id, brandingSettings: { ...bs, channel: { ...(bs.channel || {}), description: DESCRIPTION }, image: { ...(bs.image || {}), bannerExternalUrl: upj.url } } };
    const put = await fetch("https://www.googleapis.com/youtube/v3/channels?part=brandingSettings", { method: "PUT", headers: { ...H, "Content-Type": "application/json" }, body: JSON.stringify(body) });
    const pj = await put.json();
    if (!put.ok) throw new Error("채널 저장 실패: " + JSON.stringify(pj));
    steps.channel_updated = true;
    steps.new_description = pj.brandingSettings?.channel?.description;
    return json({ ok: true, steps });
  } catch (e) {
    return json({ ok: false, steps, error: String((e as Error).message || e) }, 500);
  }
});
