// ed-yt-long (2026-11-04): 황제의 일기 롱폼을 유튜브(youtube_account id=2)에 올린다.
// 영상 파일은 32MB 조각으로 나눠 Storage 'ed-tmp' 버킷(비공개)에 올려 두고(action sign 으로 받은 서명 주소),
// 조각을 차례로 받아 유튜브 이어 올리기(resumable)로 보낸다. 끝나면 action clean 으로 조각을 지운다.
// 업로드 세션 주소는 app_config 'ed_yt_long_state' 에만 저장하고 응답으로 돌려주지 않는다.
// key 는 app_config 'ed_yt_long_key' 와 같아야 한다.
// state_key (2026-11-04): 쇼츠 등 다른 업로드는 b.state_key(예: ed_yt_up_<id>)로 상태를 따로 둔다. publish_at 을 주면 비공개로 올려 그 시각에 공개 예약.
// action meta (2026-11-04 대표: "제목도 바꿔줘"): {video_id?, title?, desc_prefix?} — 기존 snippet(설명·태그·카테고리)을 그대로 두고 제목만 바꾸거나 설명 맨 앞에 줄을 더한다.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";
import { createClient } from "npm:@supabase/supabase-js@2.45.4";

const sb = createClient(Deno.env.get("SUPABASE_URL")!, Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!, { auth: { persistSession: false } });
const ED_CH = "UCR5ao2RmISHYMmDinRPIaDw";
const CHUNK = 32 * 1024 * 1024;
const BUCKET = "ed-tmp";
const json = (o: unknown, s = 200) => new Response(JSON.stringify(o), { status: s, headers: { "Content-Type": "application/json" } });
async function cfg(key: string) { const { data } = await sb.from("app_config").select("value").eq("key", key).maybeSingle(); return data?.value; }
async function setCfg(key: string, value: unknown) { await sb.from("app_config").upsert({ key, value }); }

async function ytTok(): Promise<string> {
  const { data: a } = await sb.from("youtube_account").select("*").eq("id", 2).maybeSingle();
  if (!a?.refresh_token || a.channel_id !== ED_CH) throw new Error("황제의 일기 유튜브 연결 없음");
  if (a.access_token && a.expires_at && Date.parse(a.expires_at) - Date.now() > 300e3) return a.access_token;
  const form = new URLSearchParams({ client_id: Deno.env.get("YOUTUBE_CLIENT_ID")!, client_secret: Deno.env.get("YOUTUBE_CLIENT_SECRET")!, grant_type: "refresh_token", refresh_token: a.refresh_token });
  const t = await (await fetch("https://oauth2.googleapis.com/token", { method: "POST", body: form })).json();
  if (!t.access_token) throw new Error("토큰 갱신 실패: " + JSON.stringify(t).slice(0, 200));
  await sb.from("youtube_account").update({ access_token: t.access_token, expires_at: new Date(Date.now() + (t.expires_in || 3600) * 1000).toISOString(), updated_at: new Date().toISOString() }).eq("id", 2);
  return t.access_token;
}

async function offsetOf(session: string, total: number, tok: string): Promise<{ done?: unknown; off: number }> {
  const r = await fetch(session, { method: "PUT", headers: { Authorization: "Bearer " + tok, "Content-Range": `bytes */${total}`, "Content-Length": "0" } });
  if (r.status === 200 || r.status === 201) return { done: await r.json(), off: total };
  const rg = r.headers.get("range"); await r.body?.cancel();
  if (r.status !== 308) throw new Error("세션 상태 확인 실패: HTTP " + r.status);
  return { off: rg ? Number(rg.split("-")[1]) + 1 : 0 };
}

Deno.serve(async (req: Request) => {
  const b = await req.json().catch(() => ({}));
  const key = await cfg("ed_yt_long_key");
  if (!key || b.key !== key) return json({ error: "forbidden" }, 403);
  const SK = /^ed_yt_(long_state|up_[a-z0-9_]{1,40})$/.test(String(b.state_key || "")) ? String(b.state_key) : "ed_yt_long_state";
  try {
    if (b.action === "sign") {
      const urls: string[] = [];
      for (let i = 0; i < Number(b.n); i++) {
        const path = `${b.prefix}/${String(i).padStart(3, "0")}`;
        const { data, error } = await sb.storage.from(BUCKET).createSignedUploadUrl(path, { upsert: true });
        if (error) throw new Error("서명 실패: " + error.message); urls.push(data.signedUrl);
      }
      if (b.thumb) { const { data } = await sb.storage.from(BUCKET).createSignedUploadUrl(`${b.prefix}/thumb.jpg`, { upsert: true }); urls.push(data!.signedUrl); }
      return json({ urls });
    }
    const tok = await ytTok();
    if (b.action === "start") {
      const total = Number(b.total);
      const meta = {
        snippet: { title: b.title, description: b.description, tags: b.tags || [], categoryId: String(b.category || "27"), defaultLanguage: "ko", defaultAudioLanguage: "ko" },
        status: { privacyStatus: b.publish_at ? "private" : (b.privacy || "public"), ...(b.publish_at ? { publishAt: b.publish_at } : {}), selfDeclaredMadeForKids: false, containsSyntheticMedia: true, embeddable: true },
      };
      const r = await fetch("https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status", {
        method: "POST", headers: { Authorization: "Bearer " + tok, "Content-Type": "application/json; charset=UTF-8", "X-Upload-Content-Type": "video/mp4", "X-Upload-Content-Length": String(total) },
        body: JSON.stringify(meta) });
      const session = r.headers.get("location");
      if (!session) return json({ error: "세션 생성 실패", status: r.status, body: (await r.text()).slice(0, 500) }, 500);
      await setCfg(SK, { session, total, prefix: b.prefix, started: new Date().toISOString() });
      return json({ ok: true, total });
    }
    const st = await cfg(SK) as { session: string; total: number; prefix: string; video_id?: string } | null;
    if (b.action === "meta") {
      const vid = b.video_id || st?.video_id;
      if (!vid) return json({ error: "video_id 없음" }, 400);
      const g = await (await fetch(`https://www.googleapis.com/youtube/v3/videos?part=snippet&id=${vid}`, { headers: { Authorization: "Bearer " + tok } })).json();
      const sn = g.items?.[0]?.snippet;
      if (!sn) return json({ error: "영상을 찾지 못함", body: JSON.stringify(g).slice(0, 300) }, 404);
      if (sn.channelId !== ED_CH) return json({ error: "황제의 일기 채널 영상이 아님" }, 400);
      const before = { title: sn.title, desc_head: String(sn.description || "").slice(0, 120) };
      const snippet: Record<string, unknown> = { title: b.title || sn.title, description: sn.description || "", tags: sn.tags || [], categoryId: sn.categoryId };
      if (sn.defaultLanguage) snippet.defaultLanguage = sn.defaultLanguage;
      if (sn.defaultAudioLanguage) snippet.defaultAudioLanguage = sn.defaultAudioLanguage;
      if (b.desc_prefix && !String(sn.description || "").startsWith(b.desc_prefix)) snippet.description = b.desc_prefix + "\n\n" + (sn.description || "");
      if (typeof b.description === "string" && b.description) snippet.description = b.description;   // 2026-11-04: 설명 전체 교체
      const r = await fetch("https://www.googleapis.com/youtube/v3/videos?part=snippet", { method: "PUT", headers: { Authorization: "Bearer " + tok, "Content-Type": "application/json; charset=UTF-8" }, body: JSON.stringify({ id: vid, snippet }) });
      const out = await r.json();
      return json({ status: r.status, before, after: { title: out.snippet?.title, desc_head: String(out.snippet?.description || "").slice(0, 120) }, error: out.error?.message });
    }
    if (b.action === "privacy") {   // 2026-11-04: 예약 공개 취소/변경 {video_id, privacy, publish_at?}
      const r = await fetch("https://www.googleapis.com/youtube/v3/videos?part=status", { method: "PUT", headers: { Authorization: "Bearer " + tok, "Content-Type": "application/json; charset=UTF-8" },
        body: JSON.stringify({ id: b.video_id, status: { privacyStatus: b.privacy || "private", ...(b.publish_at ? { publishAt: b.publish_at } : {}), selfDeclaredMadeForKids: false, embeddable: true } }) });
      const out = await r.json();
      return json({ status: r.status, privacy: out.status?.privacyStatus, publishAt: out.status?.publishAt || null, error: out.error?.message });
    }
    if (!st) return json({ error: "start 먼저" }, 400);
    if (b.action === "push") {
      if (st.video_id) return json({ done: true, video_id: st.video_id });
      const t0 = Date.now(); let { done, off } = await offsetOf(st.session, st.total, tok);
      while (!done && Date.now() - t0 < 95e3) {
        const end = Math.min(off + CHUNK, st.total) - 1;
        if (off % CHUNK) throw new Error("조각 경계가 아닌 위치: " + off);
        const { data: blob, error } = await sb.storage.from(BUCKET).download(`${st.prefix}/${String(off / CHUNK).padStart(3, "0")}`);
        if (error || !blob) throw new Error("조각 받기 실패: " + (error?.message || ""));
        const buf = new Uint8Array(await blob.arrayBuffer());
        if (buf.length !== end - off + 1) throw new Error(`조각 크기 불일치 ${buf.length} vs ${end - off + 1}`);
        const r = await fetch(st.session, { method: "PUT", headers: { Authorization: "Bearer " + tok, "Content-Range": `bytes ${off}-${end}/${st.total}`, "Content-Length": String(buf.length) }, body: buf });
        if (r.status === 200 || r.status === 201) { done = await r.json(); off = st.total; break; }
        if (r.status !== 308) throw new Error("조각 올리기 실패: HTTP " + r.status + " " + (await r.text()).slice(0, 300));
        const rg = r.headers.get("range"); await r.body?.cancel(); off = rg ? Number(rg.split("-")[1]) + 1 : 0;
      }
      if (done) {
        const vid = (done as { id?: string }).id;
        await setCfg(SK, { ...st, video_id: vid, finished: new Date().toISOString(), result: done });
        return json({ done: true, video_id: vid });
      }
      return json({ done: false, off, total: st.total, pct: Math.round(off / st.total * 1000) / 10 });
    }
    if (b.action === "thumb") {
      if (!st.video_id) return json({ error: "영상 먼저" }, 400);
      const { data: tb } = await sb.storage.from(BUCKET).download(`${st.prefix}/thumb.jpg`);
      if (!tb) return json({ error: "썸네일 없음" }, 400);
      const img = new Uint8Array(await tb.arrayBuffer());
      const r = await fetch(`https://www.googleapis.com/upload/youtube/v3/thumbnails/set?videoId=${st.video_id}`, { method: "POST", headers: { Authorization: "Bearer " + tok, "Content-Type": "image/jpeg" }, body: img });
      return json({ status: r.status, body: (await r.text()).slice(0, 500) });
    }
    if (b.action === "clean") {
      const { data: ls } = await sb.storage.from(BUCKET).list(st.prefix, { limit: 1000 });
      const paths = (ls || []).map(f => `${st.prefix}/${f.name}`);
      if (paths.length) await sb.storage.from(BUCKET).remove(paths);
      return json({ removed: paths.length });
    }
    if (b.action === "status") return json({ video_id: st.video_id || null, total: st.total });
    return json({ error: "unknown action" }, 400);
  } catch (e) {
    return json({ error: String((e as Error).message || e).slice(0, 500) }, 500);
  }
});
