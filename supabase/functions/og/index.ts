// 기업 점수 카드 이미지 (카톡·인스타 DM·검색 미리보기용 og:image)
// GET /functions/v1/og?c=<기업 주소>&d=<날짜>  →  1200×630 PNG
// 점수는 사이트의 /c/scores.json(매일 페이지 생성 때 함께 만들어짐)에서 읽는다. 로그인 없이 누구나 호출(verify_jwt=false).
import { ImageResponse } from 'https://deno.land/x/og_edge@0.0.6/mod.ts';
import { companyCard, brandCard } from './card.js';

const SITE = 'https://www.valuenote.co.kr';
const FONT_BASE = [
  'https://cdn.jsdelivr.net/npm/pretendard@1.3.9/dist/web/static/woff-subset/',
  'https://unpkg.com/pretendard@1.3.9/dist/web/static/woff-subset/',
];
const WEIGHTS: [string, number][] = [['Bold', 700], ['ExtraBold', 800], ['Black', 900]];

let fontsP: Promise<{ name: string; data: ArrayBuffer; weight: number; style: string }[]> | null = null;
async function fontFile(w: string): Promise<ArrayBuffer> {
  for (const base of FONT_BASE) {
    try { const r = await fetch(`${base}Pretendard-${w}.subset.woff`); if (r.ok) return await r.arrayBuffer(); } catch (_) { /* 다음 주소 */ }
  }
  throw new Error('font ' + w);
}
function fonts() {
  fontsP ||= Promise.all(WEIGHTS.map(async ([w, n]) => ({ name: 'P', data: await fontFile(w), weight: n, style: 'normal' })));
  fontsP.catch(() => { fontsP = null; });
  return fontsP;
}

let scores: { date: string; c: Record<string, unknown[]> } | null = null, scoresAt = 0;
async function loadScores() {
  if (scores && Date.now() - scoresAt < 10 * 60 * 1000) return scores;
  try {
    const r = await fetch(`${SITE}/c/scores.json`, { headers: { 'cache-control': 'no-cache' } });
    if (r.ok) { scores = await r.json(); scoresAt = Date.now(); }
  } catch (_) { /* 이전 값 유지 */ }
  return scores;
}

Deno.serve(async (req) => {
  const u = new URL(req.url);
  const slug = (u.searchParams.get('c') || '').toLowerCase().replace(/[^a-z0-9-]/g, '').slice(0, 40);
  try {
    const [f, s] = await Promise.all([fonts(), slug ? loadScores() : Promise.resolve(null)]);
    const row = s?.c?.[slug];
    const el = row ? companyCard(row, s!.date) : brandCard();
    const img = new ImageResponse(el as any, { width: 1200, height: 630, fonts: f as any });
    const body = await img.arrayBuffer();
    return new Response(body, { headers: {
      'content-type': 'image/png',
      // 주소에 날짜(d)가 들어가므로 하루 동안 캐시해도 다음 날엔 새 그림이 나온다
      'cache-control': row ? 'public, max-age=86400, s-maxage=86400' : 'public, max-age=600',
      'access-control-allow-origin': '*',
    } });
  } catch (e) {
    // 그림을 못 만들면 사이트 기본 이미지로 보낸다
    return Response.redirect(`${SITE}/og.png`, 302);
  }
});
