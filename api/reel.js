// 릴스 영상(/social/reels/<id>/reel.mp4)을 배포 없이 내준다 (2026-11-22 Vercel 비용 분리).
// 최근 영상은 GitHub 저장소(main)에, 오래된 영상은 Supabase Storage 에 있어서 순서대로 찾는다.
// vercel.json rewrite: /social/reels/:id/reel.mp4 -> /api/reel?id=:id
export const config = { runtime: 'edge' };

const SOURCES = [
  'https://raw.githubusercontent.com/immin03/haeja/main/social/reels/',
  'https://msjbrwyzkiueqnzjeicm.supabase.co/storage/v1/object/public/media/social/reels/',
];
const PASS = ['content-length', 'content-range', 'accept-ranges', 'etag', 'last-modified'];

export default async function handler(req) {
  const id = new URL(req.url).searchParams.get('id') || '';
  if (!/^[A-Za-z0-9_-]{1,60}$/.test(id)) return new Response('bad id', { status: 400 });
  const headers = {};
  const range = req.headers.get('range');
  if (range) headers.Range = range;
  const method = req.method === 'HEAD' ? 'HEAD' : 'GET';
  for (const base of SOURCES) {
    let r;
    try {
      r = await fetch(base + id + '/reel.mp4', { method, headers });
    } catch (e) {
      continue;
    }
    if (r.ok) {
      const out = new Headers();
      for (const k of PASS) {
        const v = r.headers.get(k);
        if (v) out.set(k, v);
      }
      if (!out.has('accept-ranges')) out.set('accept-ranges', 'bytes');
      out.set('content-type', 'video/mp4');
      out.set('cache-control', 'public, max-age=300');
      return new Response(method === 'HEAD' ? null : r.body, { status: r.status, headers: out });
    }
  }
  return new Response('not found', { status: 404 });
}
