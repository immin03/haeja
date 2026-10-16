/* ============ 내 계정 (웹 버전) ============
   이름·이메일·비밀번호 변경, 처음 안내 다시 보기, 로그아웃. Supabase Auth의 updateUser를 쓴다. */

async function loadUser(){ try{ const { data } = await store.client.auth.getUser(); S.user = data?.user || null; }catch(_){ S.user = null; } paintAcctMenu(); }
const userName = () => (S.user?.user_metadata?.name || '').trim();
function paintAcctMenu(){
  const n = document.querySelector('.acct-name'), m = document.querySelector('.acct-mail');
  if(n) n.textContent = userName() ? userName() + ' 님' : '내 계정';
  if(m) m.textContent = S.user?.email || '';
}
function viewAccount(){
  const u = S.user, q = (typeof AZ !== 'undefined' && AZ.quota) ? AZ.quota : null;
  const since = u?.created_at ? String(u.created_at).slice(0,10) : '';
  return `
  <h2 class="guide-title">내 계정</h2>
  <div class="card ac-head">
    <span class="ac-avatar" aria-hidden="true">${esc((userName() || u?.email || '?').slice(0,1).toUpperCase())}</span>
    <div style="min-width:0"><b>${esc(userName() || '이름 없음')}</b><div class="small muted ac-mail">${esc(u?.email || '')}</div>${since ? `<div class="small muted">가입 ${esc(since)}</div>` : ''}</div>
  </div>

  <h3 class="eyebrow guide-h">기본 정보</h3>
  <div class="card ac-list">
    <form class="ac-row" data-ac="name"><label class="f">이름<input name="v" value="${esc(userName())}" placeholder="예: 홍길동" autocomplete="name" maxlength="30"></label><button class="btn" type="submit">저장</button></form>
    <form class="ac-row" data-ac="email"><label class="f">이메일<input name="v" type="email" value="${esc(u?.email || '')}" autocomplete="email"></label><button class="btn" type="submit">변경</button></form>
    <div class="status-line small" id="ac-msg-1"></div>
  </div>

  <h3 class="eyebrow guide-h">비밀번호</h3>
  <form class="card ac-list" data-ac="password">
    <label class="f">새 비밀번호<input name="p1" type="password" autocomplete="new-password" minlength="8" placeholder="8자 이상"></label>
    <label class="f" style="margin-top:10px">새 비밀번호 확인<input name="p2" type="password" autocomplete="new-password" minlength="8"></label>
    <div class="row" style="justify-content:space-between;margin-top:12px"><span class="status-line small" id="ac-msg-2"></span><button class="btn primary" type="submit">비밀번호 바꾸기</button></div>
  </form>

  <h3 class="eyebrow guide-h">나의 투자 점검 ${inv().at ? `<span class="muted" style="font-weight:400">· ${esc(inv().at)}</span>` : ''}</h3>
  <div class="card">${invQHtml(INV_Q.map(x => x.k))}${invAdvice().length ? `<div class="in-adv" style="margin:16px 0 0"><b>맞춤 제안</b>${invAdvice().map(a => `<span>${esc(a)}</span>`).join('')}</div>` : ''}</div>

  <h3 class="eyebrow guide-h">이용</h3>
  <div class="card ac-list">
    <button type="button" class="ac-link" data-al="open"><span>알림 설정</span><span class="muted">›</span></button>
    <button type="button" class="ac-link" data-act="go-tab" data-v="grade"><span>내 투자자 등급</span><span class="muted">›</span></button>
    <button type="button" class="ac-link" data-act="intro-open"><span>처음 안내 다시 보기</span><span class="muted">›</span></button>
    <div class="ac-link static"><span>목록에 없는 종목 분석</span><span class="muted num">${q ? `${q.left}/${q.limit}회 남음` : '–'}</span></div>
  </div>

  <div style="margin-top:20px"><button type="button" class="btn ac-out" data-acct="logout">로그아웃</button></div>
  <p class="small muted" style="margin-top:12px">내 데이터는 이 계정에만 저장되고, 다른 사람은 볼 수 없습니다.</p>`;
}
document.addEventListener('submit', async e => {
  const f = e.target.closest && e.target.closest('form[data-ac]'); if(!f) return;
  e.preventDefault();
  const k = f.dataset.ac, btn = f.querySelector('button[type="submit"]');
  const say = (id, t, ok) => { const el = document.getElementById(id); if(el){ el.textContent = t; el.style.color = ok ? 'var(--accent)' : 'var(--bad)'; } };
  btn.disabled = true;
  try{
    if(k === 'name'){
      const v = f.v.value.trim();
      const { data, error } = await store.client.auth.updateUser({ data: { name: v } }); if(error) throw error;
      S.user = data.user; paintAcctMenu(); say('ac-msg-1', '이름을 저장했습니다.', true);
    }
    if(k === 'email'){
      const v = f.v.value.trim(); if(!v || v === S.user?.email){ say('ac-msg-1', '바꿀 이메일을 입력하세요.'); return; }
      const { error } = await store.client.auth.updateUser({ email: v }, { emailRedirectTo: location.origin }); if(error) throw error;
      say('ac-msg-1', `${v}로 확인 메일을 보냈습니다. 메일의 링크를 누르면 바뀝니다.`, true);
    }
    if(k === 'password'){
      const p1 = f.p1.value, p2 = f.p2.value;
      if(p1.length < 8){ say('ac-msg-2', '8자 이상으로 정하세요.'); return; }
      if(p1 !== p2){ say('ac-msg-2', '두 비밀번호가 다릅니다.'); return; }
      const { error } = await store.client.auth.updateUser({ password: p1 }); if(error) throw error;
      f.reset(); say('ac-msg-2', '비밀번호를 바꿨습니다.', true);
    }
  }catch(err){
    const m = String(err?.message || err);
    const t = /same|different from the old/i.test(m) ? '지금 비밀번호와 다른 비밀번호를 쓰세요.' : /reauth|recent/i.test(m) ? '보안을 위해 다시 로그인한 뒤 바꿔 주세요.' : /rate|seconds/i.test(m) ? '잠시 후 다시 시도하세요.' : '바꾸지 못했습니다: ' + m;
    say(k === 'password' ? 'ac-msg-2' : 'ac-msg-1', t);
  }finally{ btn.disabled = false; }
});
document.addEventListener('click', e => { if(e.target.closest('[data-acct="logout"]')) store.logout(); });

/* ============ 비밀번호 재설정 ============
   로그인 화면의 "비밀번호를 잊으셨나요?" → 재설정 메일 → 메일 링크로 돌아오면 새 비밀번호 입력 창을 띄운다. */
const VN_RECOVERY = /type=recovery/.test(location.hash) || /[?&]reset=1/.test(location.search);
document.addEventListener('click', async e => {
  const b = e.target.closest('[data-lg="forgot"]'); if(!b) return;
  const em = (document.getElementById('lg-email')?.value || '').trim(), msg = document.getElementById('lg-msg');
  if(!/^\S+@\S+\.\S+$/.test(em)){ msg.textContent = '위 이메일 칸에 가입한 이메일을 먼저 입력하세요.'; document.getElementById('lg-email')?.focus(); return; }
  b.disabled = true; msg.textContent = '보내는 중';
  try{
    const { error } = await store.client.auth.resetPasswordForEmail(em, { redirectTo: location.origin + '/?reset=1' });
    msg.textContent = error ? (/rate|seconds/i.test(error.message) ? '잠시 후 다시 시도하세요.' : '보내지 못했습니다: ' + error.message)
      : `${em}로 비밀번호 재설정 메일을 보냈습니다. 메일의 링크를 누르면 새 비밀번호를 정할 수 있어요.`;
  }finally{ b.disabled = false; }
});
function vnRecoveryPrompt(){
  if(document.getElementById('vn-rec')) return;
  const d = document.createElement('div'); d.id = 'vn-rec';
  d.style.cssText = 'position:fixed;inset:0;z-index:9999;background:rgba(10,19,34,.6);display:flex;align-items:center;justify-content:center;padding:16px';
  d.innerHTML = `<form class="card stack" style="max-width:380px;width:100%;margin:0" onsubmit="return false">
    <h3 style="margin:0">새 비밀번호 정하기</h3>
    <p class="small muted" style="margin:0">8자 이상으로 정해 주세요. 정하면 바로 로그인된 상태로 이어집니다.</p>
    <label class="f">새 비밀번호<input id="rec-p1" type="password" autocomplete="new-password"></label>
    <label class="f">한 번 더<input id="rec-p2" type="password" autocomplete="new-password"></label>
    <button class="btn primary" id="rec-go" type="submit">저장</button><div class="status-line" id="rec-msg"></div></form>`;
  document.body.appendChild(d);
  setTimeout(() => document.getElementById('rec-p1')?.focus(), 50);
  document.getElementById('rec-go').onclick = async () => {
    const p1 = document.getElementById('rec-p1').value, p2 = document.getElementById('rec-p2').value, m = document.getElementById('rec-msg');
    if(p1.length < 8){ m.textContent = '8자 이상으로 정해 주세요.'; return; }
    if(p1 !== p2){ m.textContent = '두 칸이 서로 다릅니다.'; return; }
    m.textContent = '저장하는 중';
    const { data, error } = await store.client.auth.updateUser({ password: p1 });
    if(error){ m.textContent = /same|different/i.test(error.message) ? '예전과 다른 비밀번호를 쓰세요.' : /session|missing|expired/i.test(error.message) ? '링크가 만료됐습니다. 로그인 화면에서 메일을 다시 받아 주세요.' : '저장하지 못했습니다: ' + error.message; return; }
    try{ if(window.PasswordCredential && navigator.credentials && data?.user?.email) await navigator.credentials.store(new PasswordCredential({ id: data.user.email, password: p1, name: data.user.email })); }catch(_){}
    history.replaceState(null, '', location.pathname); d.remove(); location.reload();
  };
}
if(VN_RECOVERY){
  let tries = 0;
  const wait = setInterval(async () => {
    tries++;
    try{ const s = store.client && (await store.client.auth.getSession()).data.session; if(s){ clearInterval(wait); vnRecoveryPrompt(); return; } }catch(_){}
    if(tries > 40){ clearInterval(wait); }
  }, 250);
}

/* ============ 카카오 로그인 + 소셜 가입자 동의 ============
   config.js의 KAKAO가 true일 때만 버튼이 보인다. 카카오로 처음 들어온 사람은 약관·개인정보·14세·투자 고지를 한 화면에서 받는다. */
const kakaoOn = () => !!(window.HAEJA_CONFIG || {}).KAKAO;
const KAKAO_SVG = '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path fill="#000" d="M12 3C6.48 3 2 6.58 2 11c0 2.83 1.84 5.31 4.6 6.73l-.98 3.62c-.09.33.29.59.57.39l4.3-2.86c.5.06 1 .1 1.51.1 5.52 0 10-3.58 10-8S17.52 3 12 3z"/></svg>';
function kakaoBtnHtml(){
  if(!kakaoOn()) return '';
  return `<button type="button" class="btn kakao-btn" data-lg="kakao">${KAKAO_SVG}<span>카카오로 3초 만에 시작하기</span></button><div class="lg-or"><span>또는 이메일로</span></div>`;
}
document.addEventListener('click', async e => {
  const b = e.target.closest('[data-lg="kakao"]'); if(!b) return;
  b.disabled = true;
  try{ localStorage.setItem('vn-remember', '1'); localStorage.setItem('vn-noauto', '0'); sessionStorage.setItem('vn-live', '1'); }catch(_){}
  const { error } = await store.client.auth.signInWithOAuth({ provider: 'kakao', options: { redirectTo: location.origin + '/' } });
  if(error){ b.disabled = false; const m = document.getElementById('lg-msg'); if(m) m.textContent = '카카오 로그인을 시작하지 못했습니다: ' + error.message; }
});
const needSignupAgree = () => !!store.user && !store.isDemo && ((store.user.app_metadata || {}).provider || 'email') !== 'email' && !(store.user.user_metadata || {}).agreed;
function oauthAgreeHtml(){
  return `<div class="ca-list"><div class="ca-t">처음 오셨네요. 아래 항목에 동의해 주세요.</div>
    <label><input type="checkbox" class="ca-req"> <span>[필수] 이용약관 동의</span> <a href="/terms" target="_blank" rel="noopener">보기</a></label>
    <label><input type="checkbox" class="ca-req"> <span>[필수] 개인정보 수집·이용 동의</span> <a href="/privacy" target="_blank" rel="noopener">보기</a></label>
    <label><input type="checkbox" class="ca-req"> <span>[필수] 만 14세 이상입니다</span></label></div>`;
}
async function oauthAgreeSave(){
  const at = new Date().toISOString();
  await store.client.auth.updateUser({ data: { agreed: at, terms: '2026-10-15', privacy: '2026-10-15', age14: true } });
  await store.track('signup');
}
