/* ============ 알림함 (웹 버전) ============
   alerts 문서: {at, level: urgent|warn|good|info, title, body, link:{tab, co}, read, push, source}
   새 알림 문서가 생기면 DB 트리거 → notify 함수가 휴대폰으로 푸시를 보낸다. */
const AL_LV = {urgent:{c:'var(--bad)', l:'긴급'}, warn:{c:'var(--warn)', l:'확인'}, good:{c:'var(--accent)', l:'기회'}, info:{c:'var(--muted)', l:'소식'}};
const alUnread = () => (S.alerts||[]).filter(a => !a.read).length;
function bellHtml(){
  const n = alUnread();
  return `<button type="button" class="bell" data-al="open" aria-label="알림 ${n}개 안 읽음">
    <svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M12 3a6 6 0 0 0-6 6v3.6L4.3 15.4A1 1 0 0 0 5.2 17h13.6a1 1 0 0 0 .9-1.6L18 12.6V9a6 6 0 0 0-6-6zm0 19a2.5 2.5 0 0 0 2.4-2h-4.8A2.5 2.5 0 0 0 12 22z" fill="currentColor"/></svg>
    ${n ? `<span class="bell-n num">${n > 9 ? '9+' : n}</span>` : ''}</button>`;
}
function updateBell(){ const b = document.getElementById('bellSlot'); if(b) b.innerHTML = bellHtml(); }
function agoText(iso){
  const t = Date.parse(iso); if(!t) return '';
  const m = Math.round((Date.now() - t)/60000);
  if(m < 1) return '방금'; if(m < 60) return m + '분 전'; if(m < 1440) return Math.round(m/60) + '시간 전';
  const d = Math.round(m/1440); return d === 1 ? '어제' : d + '일 전';
}
function dayGroup(iso){
  const k = new Date(Date.parse(iso) + 9*3600e3).toISOString().slice(0,10), t = today();
  const y = new Date(Date.now() + 9*3600e3 - 864e5).toISOString().slice(0,10);
  return k === t ? '오늘' : k === y ? '어제' : '이전';
}
/* 푸시 상태: on | off | denied | unsupported | ios-install */
let pushState = 'off';
const isIOS = () => /iPhone|iPad|iPod/.test(navigator.userAgent);
const isStandalone = () => window.matchMedia('(display-mode: standalone)').matches || navigator.standalone === true;
async function checkPush(){
  if(!('serviceWorker' in navigator) || !('PushManager' in window) || !('Notification' in window)){ pushState = isIOS() && !isStandalone() ? 'ios-install' : 'unsupported'; return; }
  if(Notification.permission === 'denied'){ pushState = 'denied'; return; }
  try{
    const reg = await navigator.serviceWorker.register('/sw.js');
    const sub = await reg.pushManager.getSubscription();
    pushState = sub ? 'on' : 'off';
  }catch(_){ pushState = 'unsupported'; }
}
function b64ToU8(b64){ const p = '='.repeat((4 - b64.length % 4) % 4); const s = atob((b64 + p).replace(/-/g,'+').replace(/_/g,'/')); return Uint8Array.from(s, c => c.charCodeAt(0)); }
async function subId(endpoint){ const h = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(endpoint)); return 'sub-' + [...new Uint8Array(h)].slice(0,10).map(x => x.toString(16).padStart(2,'0')).join(''); }
async function enablePush(){
  const msg = document.getElementById('al-msg');
  const say = t => { if(msg) msg.textContent = t; };
  try{
    if(pushState === 'ios-install'){ say('아이폰은 공유 버튼 → "홈 화면에 추가" 후, 홈 화면의 ValueNote 아이콘으로 열어야 알림을 받을 수 있습니다.'); return; }
    if(pushState === 'unsupported'){ say('이 브라우저는 푸시 알림을 지원하지 않습니다.'); return; }
    say('권한 요청 중');
    const perm = await Notification.requestPermission();
    if(perm !== 'granted'){ pushState = perm === 'denied' ? 'denied' : 'off'; say('알림이 허용되지 않았습니다. 브라우저 설정에서 이 사이트 알림을 허용하세요.'); return; }
    const reg = await navigator.serviceWorker.register('/sw.js'); await navigator.serviceWorker.ready;
    const { data, error } = await store.client.functions.invoke('notify', { body: { action: 'pubkey' } });
    if(error || !data?.publicKey) throw error || new Error('키를 받지 못함');
    const sub = await reg.pushManager.subscribe({ userVisibleOnly: true, applicationServerKey: b64ToU8(data.publicKey) });
    const id = await subId(sub.endpoint);
    await store.set('push_subs', id, { sub: sub.toJSON(), device: (isIOS() ? '아이폰' : /Android/.test(navigator.userAgent) ? '안드로이드' : 'PC') , at: new Date().toISOString() });
    pushState = 'on';
    await store.set('alerts', 'test-' + Date.now(), { at: new Date().toISOString(), level: 'good', title: '알림이 연결됐습니다', body: '이 기기로 ValueNote 알림이 옵니다.', read: false, source: '설정' });
    say('');
    render();
  }catch(e){ say('연결하지 못했습니다: ' + (e.message || e)); }
}
async function disablePush(){
  try{
    const reg = await navigator.serviceWorker.getRegistration('/sw.js'); const sub = reg && await reg.pushManager.getSubscription();
    if(sub){ await store.del('push_subs', await subId(sub.endpoint)); await sub.unsubscribe(); }
  }catch(_){}
  pushState = 'off'; render();
}
function pushCard(){
  const on = pushState === 'on';
  const txt = {on:'이 기기로 알림이 옵니다.', off:'중요한 일이 생기면 휴대폰으로 바로 알려 줍니다.', denied:'이 기기에서 알림이 차단돼 있습니다. 브라우저 설정 → 사이트 알림에서 허용하세요.', unsupported:'이 브라우저는 푸시 알림을 지원하지 않습니다.', 'ios-install':'아이폰은 Safari 공유 버튼 → "홈 화면에 추가" 후, 홈 화면 아이콘으로 열면 알림을 켤 수 있습니다.'}[pushState];
  return `<div class="card row al-push" style="justify-content:space-between">
    <div style="min-width:0"><b>휴대폰 알림</b> <span class="pill ${on?'p-good':'p-none'}">${on?'켜짐':'꺼짐'}</span><div class="small muted">${txt}</div><div class="status-line" id="al-msg"></div></div>
    ${on ? `<button class="btn" data-al="push-off">끄기</button>` : (pushState==='off'||pushState==='ios-install') ? `<button class="btn primary" data-al="push-on">알림 켜기</button>` : ''}
  </div>`;
}
function viewAlerts(){
  const list = [...(S.alerts||[])].sort((a,b) => (b.at||'').localeCompare(a.at||'')).slice(0, 60);
  const groups = {}; list.forEach(a => (groups[dayGroup(a.at)] ||= []).push(a));
  const item = a => { const lv = AL_LV[a.level] || AL_LV.info;
    return `<button type="button" class="al-item ${a.read?'read':''}" data-al="go" data-id="${esc(a.id)}">
      <span class="al-dot" style="background:${lv.c}"></span>
      <span class="al-main"><span class="al-top"><b>${esc(a.title)}</b><span class="small muted">${agoText(a.at)}</span></span>${a.body?`<span class="small al-body">${esc(a.body)}</span>`:''}</span>
    </button>`; };
  return `
  <div class="row" style="justify-content:space-between;margin-top:20px"><h2 style="margin:0">알림</h2>${alUnread() ? `<button class="btn" data-al="read-all">모두 읽음</button>` : ''}</div>
  <div style="margin-top:12px">${pushCard()}</div>
  <div class="legend" style="margin-top:12px">${Object.values(AL_LV).map(v => `<span style="--c:${v.c}">${v.l}</span>`).join('')}</div>
  ${list.length ? ['오늘','어제','이전'].filter(g => groups[g]).map(g => `<h3 class="eyebrow" style="margin:18px 0 6px">${g}</h3><div class="card al-list">${groups[g].map(item).join('')}</div>`).join('') : `<div class="card empty" style="margin-top:12px">아직 알림이 없습니다. 아침 브리핑, 급등락, 매수 가격 도달 같은 일이 생기면 여기에 쌓입니다.</div>`}`;
}
async function markRead(ids){
  for(const id of ids){ const a = (S.alerts||[]).find(x => x.id === id); if(a && !a.read){ a.read = true; await store.set('alerts', id, { ...a, read: true }); } }
  updateBell();
}
document.addEventListener('click', async e => {
  const el = e.target.closest('[data-al]'); if(!el) return;
  const k = el.dataset.al;
  if(k === 'open'){ S.tab = 'alerts'; await checkPush(); render(); window.scrollTo(0,0); }
  if(k === 'push-on') enablePush();
  if(k === 'push-off') disablePush();
  if(k === 'read-all'){ await markRead((S.alerts||[]).filter(a => !a.read).map(a => a.id)); render(); }
  if(k === 'go'){
    const a = (S.alerts||[]).find(x => x.id === el.dataset.id); if(!a) return;
    await markRead([a.id]);
    const l = a.link || {};
    if(l.co){ S.curId = l.co; S.tab = 'analyze'; render(); updateEval(); }
    else { S.tab = l.tab || 'portfolio'; render(); }
    window.scrollTo(0,0);
  }
});
/* 화면에서 판단하는 알림: 매수 가격 도달, 내재가치 초과 (한 달에 한 번) */
async function scanAlerts(){
  if(!S.loaded.c || !S.loaded.h || !S.alertsLoaded) return;
  const month = today().slice(0,7), have = new Set((S.alerts||[]).map(a => a.id)), now = new Date().toISOString();
  const held = new Set(S.holdings.map(h => companyFor(h)?.id).filter(Boolean));
  for(const c of S.companies){
    if(c.kind !== 'stock' || held.has(c.id) || !(c.watch || c.pinned || (c.thesis?.memo||'').trim())) continue;
    const ev = evaluate(c); const id = `buy-${c.id}-${month}`;
    if(ev.verdict === '매수 후보' && isNum(ev.buyBelow) && isNum(c.price) && c.price <= ev.buyBelow && !have.has(id))
      await store.set('alerts', id, { at: now, level: 'good', title: `${c.name} 매수 가격 도달`, body: `현재가 ${fmtPx(c.price, curOf(c.market))} · 매수가 ${fmtPx(ev.buyBelow, curOf(c.market))} 이하`, link: { co: c.id }, read: false, source: '장부 판정' });
  }
  for(const h of S.holdings){
    const c = companyFor(h); if(!c || h.kind !== 'stock') continue;
    const ev = evaluate(c); const id = `sell-${h.id}-${month}`;
    if(isNum(ev.mos) && ev.mos < -10 && !have.has(id))
      await store.set('alerts', id, { at: now, level: 'warn', title: `${h.name} 내재가치 초과`, body: `주가가 내재가치보다 ${fmt(-ev.mos,0)}% 높습니다. 매도 조건을 점검할 때입니다.`, link: { co: c.id }, read: false, source: '장부 판정' });
  }
}
