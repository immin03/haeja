/* 가치노트 푸시 알림 서비스 워커 */
self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', e => e.waitUntil(self.clients.claim()));
self.addEventListener('push', e => {
  let d = {};
  try { d = e.data ? e.data.json() : {}; } catch (_) { d = { body: e.data ? e.data.text() : '' }; }
  e.waitUntil(self.registration.showNotification(d.title || 'ValueNote', {
    body: d.body || '', tag: d.tag || 'haeja', icon: '/icon-192.png?v=6', badge: '/badge-72.png?v=5', data: { url: d.url || '/#alerts' }
  }));
});
self.addEventListener('notificationclick', e => {
  e.notification.close();
  const url = new URL(e.notification.data?.url || '/#alerts', self.location.origin).href;
  // 바깥 주소(인스타 릴스 등 — 2026-11-07 '스토리에 추가' 알림)는 새 창으로 열어 휴대폰이 해당 앱으로 넘기게 한다
  if (!url.startsWith(self.location.origin)) { e.waitUntil(self.clients.openWindow(url)); return; }
  e.waitUntil(self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(ws => {
    for (const w of ws) { if (w.url.startsWith(self.location.origin)) { w.navigate(url); return w.focus(); } }
    return self.clients.openWindow(url);
  }));
});
