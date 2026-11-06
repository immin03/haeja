/* 홈 화면 앱 매니페스트 (아이폰 로그인 이어받기용)
   아이폰 Safari에서 "홈 화면에 추가"를 누르기 직전에 화면이 이 주소로 매니페스트를 바꿔 둔다.
   그러면 홈 화면 아이콘이 /?h=연결코드 로 처음 열리고, 앱이 그 코드로 같은 계정에 자동 로그인한다.
   코드는 20분 일회용이라, 그 뒤로 아이콘을 눌러도 이미 로그인된 상태로 그냥 열린다. */
module.exports = (req, res) => {
  const h = String((req.query && req.query.h) || '');
  const ok = /^[a-z0-9]{24}$/.test(h);
  const m = {
    id: '/',
    name: '밸류노트',
    short_name: '밸류노트',
    start_url: ok ? '/?h=' + h : '/',
    scope: '/',
    display: 'standalone',
    background_color: '#0E1A2B',
    theme_color: '#0E1A2B',
    lang: 'ko',
    icons: [
      { src: '/icon-192.png?v=6', sizes: '192x192', type: 'image/png', purpose: 'any maskable' },
      { src: '/icon-512.png?v=6', sizes: '512x512', type: 'image/png', purpose: 'any maskable' }
    ]
  };
  res.setHeader('Content-Type', 'application/manifest+json; charset=utf-8');
  res.setHeader('Cache-Control', 'no-store');
  res.status(200).send(JSON.stringify(m));
};
