/* 네이버 블로그 복사 페이지 (2026-11-21 대표: "블로그 글만 하면 되지" — 블로그 글은 사이트 배포를 기다리지 않게)
   /naver, /naver/<글 id> 페이지를 GitHub 저장소(main)의 naver/ 에서 바로 읽어 text/html 로 내준다.
   사진·zip·post.json(/naver/<id>/<파일>)은 vercel.json rewrite 가 raw.githubusercontent.com 으로 바로 넘긴다.
   그래서 블로그 글은 push 뒤 최대 5분(raw 캐시) 안에 보이고, naver/ 만 바뀐 커밋은 배포하지 않는다(vercel.json ignoreCommand).
   naver/ 는 .vercelignore 로 배포에서 뺐다. 되돌리려면 .vercelignore 의 naver 줄과 vercel.json 의 /naver rewrite 3개를 지우면 된다. */
const RAW = 'https://raw.githubusercontent.com/immin03/haeja/main/naver/';
module.exports = async (req, res) => {
  const q = (req.query && req.query.p) || '';
  let p = (Array.isArray(q) ? q.join('/') : String(q)).replace(/^\/+|\/+$/g, '');
  if (p && !/^[A-Za-z0-9_-]+(\.html)?$/.test(p)) { res.status(404).send('Not found'); return; }
  let file = p || 'index.html';
  if (!/\.html$/.test(file)) file += '.html';
  try {
    const r = await fetch(RAW + file);
    if (!r.ok) { res.status(r.status === 404 ? 404 : 502).send('Not found'); return; }
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    res.setHeader('Cache-Control', 'no-store');
    res.setHeader('X-Robots-Tag', 'noindex');
    res.status(200).send(Buffer.from(await r.arrayBuffer()));
  } catch (e) {
    res.status(502).send('잠시 뒤 다시 열어 주세요');
  }
};
