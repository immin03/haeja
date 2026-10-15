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
