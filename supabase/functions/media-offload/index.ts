// media-offload (2026-11-06, mirror 추가 2026-11-20)
// 저장소(GitHub)에 커밋된 영상 파일을 Supabase Storage 'media' 버킷의 같은 경로로 복사한다.
// 게시가 끝나고 3일이 지난 영상만 '정리 가능(safe)'으로 돌려준다. 정리(저장소에서 삭제)는 GitHub 워크플로 media-offload 가 한다.
// 사이트 주소(/social/reels/..., /docs/emperor/ep/..., /social/side/gen/...)는 vercel.json 의 rewrite 로 Storage 파일을 그대로 내준다.
// 황제 클립 라이브러리(ed·edv·ev·libv)는 새벽 제작 세션이 저장소에서 직접 읽으므로 옮기지 않는다(저장소에서 지우지 않는다).
//
// mirror (2026-11-20 Vercel 비용 사고 대응): 저장소의 docs/emperor/ep/*.mp4 · social/side/gen/*.mp4 를
// 커밋 직후 Storage 에 '사본'으로 올린다(저장소 원본은 그대로). 이 두 경로의 mp4 는 .vercelignore 로 Vercel 배포에서 빠지고,
// 사이트 주소로 들어온 요청은 vercel.json rewrite 가 Storage 사본을 내준다. 크론 media-mirror 가 10분마다 {mode:'mirror'} 로 부른다.
// {mirror_paths:[path,...]} 는 그 경로만 바로 복사한다(ed-publish 가 게시 직전 파일이 없을 때 부른다).
import { createClient } from 'npm:@supabase/supabase-js@2.45.4';

const URL_ = Deno.env.get('SUPABASE_URL')!;
const KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
const sb = createClient(URL_, KEY);
const REPO = 'immin03/haeja';
const RAW = `https://raw.githubusercontent.com/${REPO}/main/`;
const OK_PATH = /^(social\/reels\/[A-Za-z0-9_-]+\/reel\.mp4|docs\/emperor\/ep\/[A-Za-z0-9_.-]+\.mp4|social\/side\/gen\/[A-Za-z0-9_.-]+\.mp4)$/;
const MIRROR_PATH = /^(docs\/emperor\/ep\/[A-Za-z0-9_.-]+\.mp4|social\/side\/gen\/[A-Za-z0-9_.-]+\.mp4)$/;
const EMPEROR_CLIP = /^social\/side\/gen\/(ed|edv|ev\d*|libv)[_0-9]/;
const json = (o: unknown, status = 200) => new Response(JSON.stringify(o), { status, headers: { 'content-type': 'application/json' } });

async function storedSize(path: string): Promise<number | null> {
  const r = await fetch(`${URL_}/storage/v1/object/public/media/${path}`, { method: 'HEAD' });
  if (!r.ok) return null;
  const n = Number(r.headers.get('content-length'));
  return Number.isFinite(n) ? n : null;
}

async function copy(path: string): Promise<void> {
  const src = await fetch(RAW + path);
  if (!src.ok || !src.body) throw new Error(`원본 ${src.status}`);
  const up = await fetch(`${URL_}/storage/v1/object/media/${path}`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${KEY}`, 'content-type': 'video/mp4', 'x-upsert': 'true', 'cache-control': 'max-age=31536000' },
    body: src.body,
    // @ts-ignore Deno streaming upload
    duplex: 'half',
  });
  if (!up.ok) throw new Error(`업로드 ${up.status} ${(await up.text()).slice(0, 120)}`);
}

// 아직 쓰일 수 있는 영상인지 (게시 전·검수 중·3일 안·기록 없는 황제 영상·황제 클립 라이브러리)
async function busy(path: string): Promise<string | null> {
  if (EMPEROR_CLIP.test(path)) return '황제 클립 라이브러리 — 보관';
  if (path.startsWith('social/side/gen/')) return null;   // 생성 클립: 게시 기록과 무관 (최근 7일·기록 파일 조건은 워크플로가 본다)
  const p = '/' + path;
  const since = new Date(Date.now() - 3 * 864e5).toISOString();
  const [a, b, c] = await Promise.all([
    sb.from('social_posts').select('id,ig_status,scheduled_at').eq('video', p),
    sb.from('youtube_posts').select('id,status,scheduled_at').eq('video_url', p),
    sb.from('ed_posts').select('id,ig_status,scheduled_at').eq('video_path', p),
  ]);
  if (a.error || b.error || c.error) return 'DB 조회 실패';
  for (const r of a.data ?? []) {
    if (r.ig_status === 'pending' || r.ig_status === 'processing') return `릴스 ${r.id} 게시 전`;
    if (r.scheduled_at > since) return `릴스 ${r.id} 3일 안`;
  }
  for (const r of b.data ?? []) {
    if (!['uploaded', 'hold', 'stale', 'deleted'].includes(r.status)) return `유튜브 ${r.id} ${r.status}`;
    if (r.scheduled_at > since) return `유튜브 ${r.id} 3일 안`;
  }
  for (const r of c.data ?? []) {
    if (r.ig_status === 'pending' || r.ig_status === 'processing') return `황제 ${r.id} 게시 전`;
    if (r.scheduled_at > since) return `황제 ${r.id} 3일 안`;
  }
  if (path.startsWith('docs/emperor/') && !(c.data ?? []).length) return '황제 게시 기록 없음 — 보관';
  return null;
}

// Storage 에 있는 파일 크기 (폴더 단위, 1000개씩)
async function storedMap(dir: string): Promise<Map<string, number>> {
  const m = new Map<string, number>();
  for (let off = 0; off < 20000; off += 1000) {
    const { data, error } = await sb.storage.from('media').list(dir, { limit: 1000, offset: off });
    if (error) throw new Error('Storage 목록 실패: ' + error.message);
    for (const f of data ?? []) if (f.id) m.set(`${dir}/${f.name}`, Number((f.metadata as any)?.size ?? -1));
    if (!data || data.length < 1000) break;
  }
  return m;
}

// 저장소 main 의 파일 목록 (경로·크기)
async function repoTree(): Promise<{ path: string; size: number }[]> {
  const h: Record<string, string> = { Accept: 'application/vnd.github+json', 'User-Agent': 'valuenote-media-mirror' };
  const tok = Deno.env.get('GITHUB_TOKEN') || Deno.env.get('GH_TOKEN');
  if (tok) h.Authorization = `Bearer ${tok}`;
  // 2026-11-20: 저장소 전체 목록(recursive)은 너무 커서 GitHub이 500을 낸다 → 필요한 폴더 두 개만 따로 읽는다
  const out: { path: string; size: number }[] = [];
  for (const dir of ['docs/emperor/ep', 'social/side/gen']) {
    const r = await fetch(`https://api.github.com/repos/${REPO}/git/trees/main:${dir}`, { headers: h });
    if (!r.ok) throw new Error(`저장소 목록 ${dir} ${r.status}`);
    const j = await r.json();
    for (const e of j.tree ?? []) {
      const path = `${dir}/${e.path}`;
      if (e.type === 'blob' && MIRROR_PATH.test(path)) out.push({ path, size: e.size });
    }
  }
  return out;
}

async function mirror(only: string[] | null, budgetMs: number) {
  const t0 = Date.now();
  const copied: string[] = [], failed: { path: string; err: string }[] = [];
  let todo: { path: string; size: number | null }[];
  if (only) {
    todo = only.filter(p => MIRROR_PATH.test(p)).map(p => ({ path: p, size: null }));
  } else {
    const [tree, ep, gen] = await Promise.all([repoTree(), storedMap('docs/emperor/ep'), storedMap('social/side/gen')]);
    const have = new Map([...ep, ...gen]);
    todo = tree.filter(f => have.get(f.path) !== f.size);
    // 게시가 다가오는 황제 영상부터
    const { data: soon } = await sb.from('ed_posts').select('video_path').eq('ig_status', 'pending').not('video_path', 'is', null);
    const first = new Set((soon ?? []).map((r: any) => String(r.video_path).replace(/^\//, '')));
    todo.sort((a, b) => Number(first.has(b.path)) - Number(first.has(a.path)) || Number(b.path.startsWith('docs/')) - Number(a.path.startsWith('docs/')));
  }
  // 프로젝트 업로드 한도(대시보드 Storage 설정)를 넘는 파일은 받지도 않고 건너뛴다. 한도를 올리면 app_config media_mirror_max_mb 도 같이 올린다.
  const { data: lim } = await sb.from('app_config').select('value').eq('key', 'media_mirror_max_mb').maybeSingle();
  const maxBytes = (Number(lim?.value) || 50) * 1024 * 1024;
  const tooBig = todo.filter(f => f.size !== null && f.size > maxBytes).map(f => f.path);
  todo = todo.filter(f => !(f.size !== null && f.size > maxBytes));
  const total = todo.length;
  for (const f of todo) {
    if (Date.now() - t0 > budgetMs) break;
    try {
      await copy(f.path);
      const s = await storedSize(f.path);
      if (f.size !== null && s !== f.size) throw new Error(`크기 불일치 ${s}/${f.size}`);
      copied.push(f.path);
    } catch (e) {
      failed.push({ path: f.path, err: String((e as Error).message || e).slice(0, 120) });
    }
  }
  return { mode: 'mirror', missing: total, copied: copied.length, failed, remaining: total - copied.length - failed.length, over_limit: tooBig, ms: Date.now() - t0 };
}

Deno.serve(async (req) => {
  if (req.method !== 'POST') return new Response('POST only', { status: 405 });
  const body = await req.json().catch(() => ({}));
  try {
    if (body.mode === 'mirror') return json(await mirror(null, 110_000));
    if (Array.isArray(body.mirror_paths)) return json(await mirror(body.mirror_paths.map(String).slice(0, 5), 110_000));
  } catch (e) {
    return json({ mode: 'mirror', error: String((e as Error).message || e).slice(0, 300) }, 500);
  }
  const { files = [], copy: doCopy = true } = body;
  const out: any[] = [];
  const t0 = Date.now();
  for (const f of files.slice(0, 15)) {
    const path = String(f.path || '');
    const size = Number(f.size || 0);
    if (!OK_PATH.test(path)) { out.push({ path, safe: false, reason: '대상 경로 아님' }); continue; }
    if (Date.now() - t0 > 120_000) { out.push({ path, safe: false, reason: '시간 초과 — 다음 회차' }); continue; }
    try {
      const why = await busy(path);
      if (why) { out.push({ path, safe: false, reason: why }); continue; }
      let s = await storedSize(path);
      if (s !== size && doCopy) { await copy(path); s = await storedSize(path); }
      const stored = s === size && size > 0;
      out.push({ path, safe: stored, stored, size: s, reason: stored ? 'Storage 저장 확인' : `크기 불일치 ${s}/${size}` });
    } catch (e) {
      out.push({ path, safe: false, reason: String((e as Error).message || e).slice(0, 160) });
    }
  }
  return json({ results: out });
});
