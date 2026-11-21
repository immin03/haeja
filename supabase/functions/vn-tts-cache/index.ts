// vn-tts-cache (2026-11-21 대표: "같은 걸 다시 렌더할 때 타입캐스트를 다시 사지 않게 최대 효율")
// 모든 렌더(롱폼·쇼츠·릴스·영어 더빙·사이드)가 함께 쓰는 '영구 음성 보관함'.
// GitHub actions/cache 는 7일 미사용·10GB 초과 때 지워지고, 동시에 돈 작업끼리 서로의 새 녹음을 덮어써 잃는다
// (11/16 엔비디아 30일 편 3시간 뒤 재렌더에서 5,110자를 다시 삼). 그래서 산 녹음은 여기 Storage 'tts' 버킷(비공개)에 영구 보관한다.
//   POST ?op=has   {paths:[...]}  → {have:[...]}       (여러 개를 한 번에 확인)
//   GET  ?op=get&p=<경로>          → 음성 파일 그대로 (없으면 404)
//   PUT  ?op=put&p=<경로>  (본문=파일) → 저장 (이미 있으면 그대로 둠)
//   POST ?op=prune                → 마지막으로 쓴 지 60일 지난 녹음 정리 (주 1회 크론 tts-prune, 인증 불필요 — 규칙대로만 지움)
// 경로: ko|en|side / <키 8~64자>.mp3|.wav
// 정리 기준(2026-11-21 대표 "업로드 끝난 건 지워도 되지 않나?"): 업로드 직후 지우면 게시 후 수정·쇼츠·영어 더빙·재렌더 때 다시 사야 한다.
// 그래서 '마지막으로 쓴 날' 기준 60일이 지나면 지운다. 다시 쓰이면(get) 날짜가 갱신돼 자주 쓰는 공용 문장은 남는다.
// 인증: 헤더 X-API-KEY = 타입캐스트 키(렌더 작업이 이미 가진 비밀값). 처음 한 번 타입캐스트에 키가 진짜인지 확인한 뒤
// 그 sha256 을 app_config.tts_cache_key_sha 에 고정한다. 이후엔 그 키만 통과. 키를 바꾸면 app_config 의 그 행을 지우면 된다.
import { createClient } from 'npm:@supabase/supabase-js@2.45.4';

const URL_ = Deno.env.get('SUPABASE_URL')!;
const SKEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const sb = createClient(URL_, SKEY);
const BUCKET = 'tts';
const OK = /^(ko|en|side)\/[a-z0-9_]{8,64}\.(mp3|wav)$/;
const json = (o: unknown, status = 200) => new Response(JSON.stringify(o), { status, headers: { 'content-type': 'application/json' } });
let PIN: string | null = null;

async function sha(s: string) {
  const b = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(s));
  return [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, '0')).join('');
}

async function authed(req: Request): Promise<boolean> {
  const k = req.headers.get('x-api-key') || '';
  if (k.length < 10) return false;
  const h = await sha(k);
  if (!PIN) {
    const { data } = await sb.from('app_config').select('value').eq('key', 'tts_cache_key_sha').maybeSingle();
    PIN = (data?.value as string) || null;
  }
  if (PIN) return h === PIN;
  // 처음 한 번: 타입캐스트에 진짜 키인지 물어본 뒤 고정
  let ok = false;
  for (const u of ['https://api.typecast.ai/v2/voices?model=ssfm-v30', 'https://api.typecast.ai/v1/voices?model=ssfm-v30', 'https://api.typecast.ai/v3/voices?model=ssfm-v30']) {
    const r = await fetch(u, { headers: { 'X-API-KEY': k } });
    await r.body?.cancel();
    if (r.ok) { ok = true; break; }
    if (r.status === 401 || r.status === 403) return false;
  }
  if (!ok) return false;
  await sb.from('app_config').upsert({ key: 'tts_cache_key_sha', value: h });
  PIN = h;
  return true;
}

async function exists(p: string): Promise<boolean> {
  const r = await fetch(`${URL_}/storage/v1/object/authenticated/${BUCKET}/${p}`, { method: 'HEAD', headers: { Authorization: `Bearer ${SKEY}`, apikey: SKEY } });
  await r.body?.cancel();
  return r.ok;
}

const KEEP_DAYS = 60;

async function prune() {
  let removed = 0;
  for (let i = 0; i < 10; i++) {
    const { data, error } = await sb.rpc('tts_expired', { days: KEEP_DAYS, lim: 1000 });
    if (error) return { error: error.message, removed };
    const names = (data || []) as string[];
    if (!names.length) break;
    const { error: e2 } = await sb.storage.from(BUCKET).remove(names);
    if (e2) return { error: e2.message, removed };
    removed += names.length;
    if (names.length < 1000) break;
  }
  return { removed, keep_days: KEEP_DAYS };
}

Deno.serve(async (req) => {
  try {
    const u = new URL(req.url);
    const op = u.searchParams.get('op');
    if (op === 'prune') return json(await prune());
    if (!(await authed(req))) return json({ error: 'unauthorized' }, 401);
    if (op === 'has') {
      const { paths } = await req.json();
      const ps = (Array.isArray(paths) ? paths : []).filter((p: string) => OK.test(p)).slice(0, 40);
      const have: string[] = [];
      await Promise.all(ps.map(async (p: string) => { if (await exists(p)) have.push(p); }));
      return json({ have });
    }
    const p = u.searchParams.get('p') || '';
    if (!OK.test(p)) return json({ error: 'bad path' }, 400);
    if (op === 'get') {
      const { data, error } = await sb.storage.from(BUCKET).download(p);
      if (error || !data) return json({ error: 'not found' }, 404);
      await sb.rpc('tts_touch', { p: [p] });   // 마지막으로 쓴 날 갱신 (60일 정리 기준)
      return new Response(data, { headers: { 'content-type': 'application/octet-stream' } });
    }
    if (op === 'put') {
      const buf = new Uint8Array(await req.arrayBuffer());
      if (buf.length < 500 || buf.length > 10 * 1024 * 1024) return json({ error: 'bad size' }, 400);
      const ct = p.endsWith('.wav') ? 'audio/wav' : 'audio/mpeg';
      const { error } = await sb.storage.from(BUCKET).upload(p, buf, { contentType: ct, upsert: false });
      if (error && !/exists|Duplicate/i.test(error.message)) return json({ error: error.message }, 500);
      return json({ ok: true });
    }
    return json({ error: 'bad op' }, 400);
  } catch (e) {
    return json({ error: String(e) }, 500);
  }
});
