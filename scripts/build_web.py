"""가치노트 아티팩트 HTML → 웹 버전(index.html) 변환.
사용: python3 scripts/build_web.py <artifact.html> index.html
- 저장소를 Supabase로 교체 (로그인한 본인 데이터만)
- 로그인 화면, 로그아웃 버튼
- 열려 있는 동안 10분마다 보유 종목 시세·환율 갱신 (/api/quote)
"""
import sys

APP_NAME = "ValueNote"
APP_SLOGAN = "On the Shoulders of Giants"

src, dst = sys.argv[1], sys.argv[2]
s = open(src, encoding="utf-8").read()


def rep(a, b):
    global s
    assert s.count(a) == 1, ("not unique/absent", a[:80])
    s = s.replace(a, b)


# 1) 저장소 교체
i = s.index("const store = (() => {")
j = s.index("let sampleFn = null;")
STORE = r"""const store = (() => {
  /* Supabase 저장소. 표 하나(docs: collection, id, data)에 아티팩트 시절 구조 그대로 저장한다.
     행 수준 보안(RLS)으로 로그인한 본인 행만 읽고 쓴다. */
  let sb = null, mode = 'init', user = null;
  const timers = {};
  const DEMO_EMAIL = 'demo@valuenote.app';
  /* 방문 기록: 기기마다 무작위 방문자 번호 하나, 페이지를 열 때마다 한 줄 */
  const sid = () => { try{ let v = localStorage.getItem('vn-sid'); if(!v){ v = (crypto.randomUUID ? crypto.randomUUID() : String(Math.random()).slice(2) + Date.now()).replace(/-/g,'').slice(0,32); localStorage.setItem('vn-sid', v); } return v; }catch(_){ return 'nosid'; } };
  const device = () => { const u = navigator.userAgent; const os = /iPhone|iPad|iPod/.test(u) ? 'iOS' : /Android/.test(u) ? 'Android' : /Mac/.test(u) ? 'Mac' : /Windows/.test(u) ? 'Windows' : '기타'; return (/Mobi|iPhone|Android/.test(u) ? '모바일' : 'PC') + ' · ' + os; };
  const refHost = () => { try{ if(!document.referrer) return ''; const h = new URL(document.referrer).hostname; return h === location.hostname ? '' : h; }catch(_){ return ''; } };
  return {
    get mode(){ return mode },
    get user(){ return user },
    get client(){ return sb },
    get isDemo(){ return !!user && user.email === DEMO_EMAIL },
    async track(kind){
      try{ if(!sb) return; const q = new URLSearchParams(location.search);
        let ref = q.get('utm_source') || q.get('ref') || refHost();
        try{ if(ref && !localStorage.getItem('vn-ref')) localStorage.setItem('vn-ref', ref); if(kind !== 'visit') ref = localStorage.getItem('vn-ref') || ref; }catch(_){}
        await sb.from('events').insert({ kind, sid: sid(), path: location.pathname.slice(0, 200), ref: ref.slice(0, 300), device: device() }); }catch(_){}
    },
    async init(){
      const C = window.HAEJA_CONFIG || {};
      if(!window.supabase || !C.SUPABASE_URL || !C.SUPABASE_ANON_KEY){ mode = 'noconfig'; return; }
      sb = window.supabase.createClient(C.SUPABASE_URL, C.SUPABASE_ANON_KEY);
      const { data: { session } } = await sb.auth.getSession();
      if(session){ try{ if(localStorage.getItem('vn-noauto') === '1' && !sessionStorage.getItem('vn-live')){ await sb.auth.signOut(); mode = 'login'; this.track('visit'); return; } sessionStorage.setItem('vn-live', '1'); }catch(_){} }
      if(!session){ mode = 'login'; this.track('visit'); return; }
      user = session.user; mode = 'db'; this.track('visit');
    },
    async login(email, password){
      const r = await sb.auth.signInWithPassword({ email, password });
      if(!r.error) await this.track('login');
      return r;
    },
    async signup(email, password){
      const at = new Date().toISOString();
      const r = await sb.auth.signUp({ email, password, options: { emailRedirectTo: location.origin, data: { agreed: at, terms: '2026-10-15', privacy: '2026-10-15', age14: true } } });
      if(!r.error) await this.track('signup');
      return r;
    },
    async logout(){ await sb.auth.signOut(); location.reload(); },
    sub(col, cb){
      const load = async () => {
        const rows = []; let from = 0;
        for(;;){
          const { data, error } = await sb.from('docs').select('id,data').eq('collection', col).range(from, from + 999);
          if(error){ setSave('연결 오류: ' + error.message); return; }
          rows.push(...data); if(data.length < 1000) break; from += 1000;
        }
        cb(rows.map(r => ({ id: r.id, ...r.data })));
      };
      load();
      sb.channel('docs-' + col)
        .on('postgres_changes', { event: '*', schema: 'public', table: 'docs', filter: 'collection=eq.' + col }, () => { clearTimeout(timers[col]); timers[col] = setTimeout(load, 300); })
        .subscribe();
    },
    async set(col, id, data){
      if(this.isDemo) return; /* 체험 계정: 저장하지 않음 (화면 위 안내 띠로 알림) */
      const body = { ...data }; delete body.id;
      const { error } = await sb.from('docs').upsert({ owner: user.id, collection: col, id, data: body, updated_at: new Date().toISOString() }, { onConflict: 'owner,collection,id' });
      if(error){ setSave('저장 실패: ' + error.message); throw error; }
    },
    async del(col, id){
      if(this.isDemo) return;
      const { error } = await sb.from('docs').delete().eq('collection', col).eq('id', id);
      if(error){ setSave('삭제 실패: ' + error.message); throw error; }
    }
  };
})();
function loginView(){
  if(store.mode === 'noconfig') return `<div class="card" style="margin-top:24px"><h3>설정이 필요합니다</h3><p class="small muted">config.js에 Supabase 주소와 공개 키(anon key)를 넣어 주세요. README의 3단계입니다.</p></div>`;
  return `<div class="login">
    <div class="login-brand"><div class="wordmark lg"><span class="wm-a">Value</span><span class="wm-b">Note</span></div><div class="login-sub"><b class="ko-name">밸류노트</b> · On the Shoulders of Giants</div>
      <p>그레이엄·버핏·멍거의 어깨 위에서, 멀리 보고 오래 투자하는 노트</p></div>
    <div class="card stack login-card">
    ${kakaoBtnHtml()}<div class="lg-tabs" role="tablist"><button type="button" role="tab" data-lg="login" aria-selected="${lgMode==='login'}">로그인</button><button type="button" role="tab" data-lg="signup" aria-selected="${lgMode==='signup'}">회원가입</button></div>
    <form id="lg-form" class="stack" method="post" action="#" autocomplete="on" style="margin:0">
    <label class="f">이메일<input id="lg-email" name="email" type="email" autocomplete="username" inputmode="email" placeholder="you@example.com" value="${esc(lgSavedEmail())}"></label>
    <label class="f">비밀번호<input id="lg-pw" name="password" type="password" autocomplete="${lgMode==='signup'?'new-password':'current-password'}" placeholder="${lgMode==='signup'?'8자 이상':''}"></label>
    ${lgMode==='signup' ? `<label class="f">비밀번호 확인<input id="lg-pw2" name="password2" type="password" autocomplete="new-password" placeholder="한 번 더 입력"></label>` : `<div class="lg-keep"><label><input type="checkbox" id="lg-remember" ${lgPref('vn-remember', true) ? 'checked' : ''}> 아이디 저장</label><label><input type="checkbox" id="lg-auto" ${lgPref('vn-noauto', false) ? '' : 'checked'}> 자동 로그인</label></div>`}
    ${lgMode==='signup' ? `<div class="lg-agree">
      <label class="ag-all"><input type="checkbox" id="ag-all"> <b>모두 동의합니다</b></label>
      <label><input type="checkbox" class="ag" data-k="terms"> <span>[필수] 이용약관 동의</span> <a href="/terms" target="_blank" rel="noopener">보기</a></label>
      <label><input type="checkbox" class="ag" data-k="privacy"> <span>[필수] 개인정보 수집·이용 동의</span> <a href="/privacy" target="_blank" rel="noopener">보기</a></label>
      <div class="ag-sum">수집 항목: 이메일, 비밀번호(암호화) · 목적: 회원 식별과 서비스 제공 · 보유 기간: 회원 탈퇴 시까지</div>
      <label><input type="checkbox" class="ag" data-k="invest"> <span>[필수] 투자 자문이 아닌 정보 도구임을 이해합니다</span> <button type="button" class="linkbtn" data-lg="terms">보기</button></label>
      <label><input type="checkbox" class="ag" data-k="age"> <span>[필수] 만 14세 이상입니다</span></label>
    </div>` : ''}
    <button class="btn primary" id="lg-go" type="submit">${lgMode==='signup' ? '시작하기' : '로그인'}</button>
    <div class="status-line" id="lg-msg"></div>
    ${lgMode==='login' ? `<button type="button" class="linkbtn" data-lg="forgot" style="align-self:flex-start;font-size:13px">비밀번호를 잊으셨나요?</button>` : ''}
    </form>
    </div><p class="small muted" style="text-align:center;margin-top:12px">${lgMode==='signup' ? '이미 계정이 있으면 위의 "로그인"을 누르세요.' : '자동 로그인을 끄면 브라우저를 닫을 때 로그아웃됩니다.'}</p>
    <div class="lg-demo"><span>먼저 둘러보고 싶다면</span><button type="button" class="btn" data-lg="demo">체험 계정으로 보기</button></div>
    <div id="lg-terms" class="disc-box small" style="display:none;margin-top:12px"></div>
  </div>`;
}
let lgMode = (location.hash === '#signup' || location.search.includes('signup')) ? 'signup' : 'login';
const lgPref = (k, def) => { try{ const v = localStorage.getItem(k); return v === null ? def : v === '1'; }catch(_){ return def; } };
const lgSavedEmail = () => { try{ return lgPref('vn-remember', true) ? (localStorage.getItem('vn-email') || '') : ''; }catch(_){ return ''; } };
/* 로그인 성공 직후: 아이디 저장·자동 로그인 설정을 기록하고, 브라우저 비밀번호 관리자에 저장을 요청한다 */
async function lgAfterLogin(email, pw){
  if(email === 'demo@valuenote.app'){ try{ sessionStorage.setItem('vn-live', '1'); }catch(_){} return; } /* 체험 계정은 저장하지 않는다 */
  try{
    const rem = document.getElementById('lg-remember'), auto = document.getElementById('lg-auto');
    const remember = rem ? rem.checked : true, autoOn = auto ? auto.checked : true;
    localStorage.setItem('vn-remember', remember ? '1' : '0');
    if(remember) localStorage.setItem('vn-email', email); else localStorage.removeItem('vn-email');
    localStorage.setItem('vn-noauto', autoOn ? '0' : '1');
    sessionStorage.setItem('vn-live', '1');
  }catch(_){}
  try{ if(window.PasswordCredential && navigator.credentials) await navigator.credentials.store(new PasswordCredential({ id: email, password: pw, name: email })); }catch(_){}
}
document.addEventListener('click', e => {
  const b = e.target.closest('[data-lg]'); if(!b) return;
  const k = b.dataset.lg;
  if(k === 'login' || k === 'signup'){ lgMode = k; const app = document.getElementById('app'); if(app){ app.innerHTML = loginView(); bindLogin(); } }
  if(k === 'terms'){ const t = document.getElementById('lg-terms'); if(t){ t.textContent = typeof DISC_FULL === 'string' ? DISC_FULL : ''; t.style.display = t.style.display === 'none' ? 'block' : 'none'; } }
  if(k === 'demo'){ const em = document.getElementById('lg-email'), pw = document.getElementById('lg-pw'); lgMode = 'login'; const app = document.getElementById('app'); if(app){ app.innerHTML = loginView(); bindLogin(); }
    document.getElementById('lg-email').value = 'demo@valuenote.app'; document.getElementById('lg-pw').value = 'valuenote'; document.getElementById('lg-go').click(); }
});
function bindLogin(){
  const go = document.getElementById('lg-go'); if(!go) return;
  const form = document.getElementById('lg-form'); if(form) form.addEventListener('submit', e => { e.preventDefault(); });
  if(lgMode === 'login' && document.getElementById('lg-email')?.value) setTimeout(() => document.getElementById('lg-pw')?.focus(), 50);
  /* Enter는 폼 제출로 로그인 버튼이 눌린다 */
  go.onclick = async () => {
    const email = document.getElementById('lg-email').value.trim(), pw = document.getElementById('lg-pw').value; const msg = document.getElementById('lg-msg');
    if(!email || !pw){ msg.textContent = '이메일과 비밀번호를 입력하세요.'; return; }
    if(lgMode === 'signup'){
      if(!/^\S+@\S+\.\S+$/.test(email)){ msg.textContent = '이메일 형식을 확인해 주세요.'; return; }
      if(pw.length < 8){ msg.textContent = '비밀번호는 8자 이상으로 정해 주세요.'; return; }
      if(pw !== (document.getElementById('lg-pw2')?.value || '')){ msg.textContent = '비밀번호 확인이 일치하지 않습니다.'; return; }
      if([...document.querySelectorAll('.lg-agree .ag')].some(x => !x.checked)){ msg.textContent = '필수 항목에 모두 동의해 주세요.'; return; }
      go.disabled = true; msg.textContent = '가입하는 중';
      const { data, error } = await store.signup(email, pw);
      if(error){ go.disabled = false; msg.textContent = /registered|exists/i.test(error.message) ? '이미 가입된 이메일입니다. "로그인"을 눌러 주세요.' : /signups? not allowed|disabled/i.test(error.message) ? '지금은 가입을 받지 않습니다.' : '가입하지 못했습니다: ' + error.message; return; }
      if(data?.session){ await lgAfterLogin(email, pw); location.reload(); return; }
      const r2 = await store.login(email, pw); if(!r2.error){ await lgAfterLogin(email, pw); location.reload(); return; }
      go.disabled = false; msg.textContent = '가입은 됐지만 바로 로그인하지 못했습니다. "로그인" 탭에서 다시 시도해 주세요.'; return;
    }
    go.disabled = true; msg.textContent = '확인 중';
    const { error } = await store.login(email, pw);
    if(!error) await lgAfterLogin(email, pw);
    if(error){ go.disabled = false; msg.textContent = '로그인하지 못했습니다: ' + (error.message === 'Invalid login credentials' ? '이메일 또는 비밀번호가 틀립니다' : /confirm/i.test(error.message) ? '메일함의 확인 링크를 먼저 눌러 주세요' : error.message); return; }
    location.reload();
  };
}
/* ============ 처음 한 번: 기존 장부 데이터 가져오기 ============ */
function importView(){
  return `<div class="card stack" style="margin-top:24px;max-width:520px">
    <h3 style="margin:0">기존 장부 가져오기</h3>
    <p class="small muted" style="margin:0">아직 데이터가 없습니다. Claude가 보내 준 <b>haeja-data.json</b> 파일을 고르면 보유 종목, 기업 분석, 스크리너, 뉴스, 가격 기록이 한 번에 들어옵니다. 처음 한 번만 하면 됩니다.</p>
    <label class="f">파일<input id="im-file" type="file" accept=".json,application/json"></label>
    <button class="btn primary" id="im-go">가져오기</button>
    <div class="status-line" id="im-msg"></div>
  </div>`;
}
function bindImport(){
  const go = document.getElementById('im-go'); if(!go) return;
  go.onclick = async () => {
    const f = document.getElementById('im-file').files[0], msg = document.getElementById('im-msg');
    if(!f){ msg.textContent = '파일을 고르세요.'; return; }
    go.disabled = true;
    try{
      const docs = JSON.parse(await f.text());
      if(!Array.isArray(docs) || !docs.every(d => d && d.collection && d.id && typeof d.data === 'object')) throw new Error('형식이 맞지 않는 파일');
      const rows = docs.map(d => ({ collection: d.collection, id: d.id, data: d.data, updated_at: new Date().toISOString() }));
      for(let i = 0; i < rows.length; i += 100){
        const { error } = await store.client.from('docs').upsert(rows.slice(i, i + 100));
        if(error) throw error;
        msg.textContent = `${Math.min(i + 100, rows.length)} / ${rows.length}`;
      }
      msg.textContent = '완료. 다시 불러옵니다.'; setTimeout(() => location.reload(), 600);
    }catch(e){ msg.textContent = '가져오지 못했습니다: ' + (e.message || e); go.disabled = false; }
  };
}
/* ============ 시세 자동 갱신 (웹 버전) ============ */
const QUOTE_EVERY = 10*60e3;
function yfSymbol(h){
  const c = companyFor(h); if(c && c.yf) return c.yf;
  const t = (h.ticker||'').trim().toUpperCase(), m = h.market || 'KR';
  if(m === 'US') return t; if(m === 'JP') return t + '.T'; if(m === 'HK') return t.padStart(4,'0') + '.HK';
  if(m === 'CN') return t + (t.startsWith('6') ? '.SS' : '.SZ'); if(m === 'KOSDAQ') return t + '.KQ';
  return t + '.KS';
}
let quoteBusy = false;
async function refreshQuotes(force){
  if(store.mode !== 'db' || quoteBusy || !S.loaded.h) return;
  let last = 0; try{ last = +(localStorage.getItem('q-at') || 0); }catch(_){}
  if(!force && Date.now() - last < QUOTE_EVERY) return;
  quoteBusy = true;
  try{
    const hs = S.holdings.filter(h => (h.ticker||'').trim());
    const syms = [...new Set(hs.map(yfSymbol))];
    const fxSyms = ['KRW=X','JPYKRW=X','CNYKRW=X','HKDKRW=X'];
    const { data: q, error: qe } = await store.client.functions.invoke('quote', { body: { symbols: [...syms, ...fxSyms] } });
    if(qe || !q) throw qe || new Error('no data');
    for(const h of hs){
      const x = q[yfSymbol(h)];
      if(x && isNum(x.price) && x.price !== h.price) await store.set('holdings', h.id, { ...h, price: x.price, prevClose: x.prev ?? null, priceAt: x.time, updatedAt: today() });
    }
    const upd = {};
    if(isNum(q['KRW=X']?.price)) upd.fx = q['KRW=X'].price;
    if(isNum(q['JPYKRW=X']?.price)) upd.fxJPY = q['JPYKRW=X'].price;
    if(isNum(q['CNYKRW=X']?.price)) upd.fxCNY = q['CNYKRW=X'].price;
    if(isNum(q['HKDKRW=X']?.price)) upd.fxHKD = q['HKDKRW=X'].price;
    if(Object.keys(upd).length) await store.set('settings', 'main', { ...(S.settings || {}), ...upd });
    try{ localStorage.setItem('q-at', String(Date.now())); }catch(_){}
    if(S.tab === 'portfolio' && !S.editHold) refresh('q');
  }catch(e){ setSave('시세 갱신 실패'); }
  finally{ quoteBusy = false; }
}
"""
SPLASH_JS = """
function hideSplash(){ const el = document.getElementById('splash'); if(!el || el.dataset.out) return; el.dataset.out = '1'; const wait = Math.max(0, 2500 - (Date.now() - (window.__t0 || 0))); setTimeout(() => { el.classList.add('out'); setTimeout(() => el.remove(), 450); }, wait); }
setTimeout(() => { if(typeof hideSplash === 'function') hideSplash(); }, 5000);
"""
s = s[:i] + STORE + SPLASH_JS + open(__file__.replace('build_web.py','web_alerts.js'), encoding='utf-8').read() + open(__file__.replace('build_web.py','web_account.js'), encoding='utf-8').read() + s[j:]

# 2) 시작 루틴: 로그인 분기, 시세 타이머, 로그아웃 버튼
rep("""  await store.init();
  setSave(store.mode==='db' ? '동기화됨' : '이 기기에 저장');
  render();""", """  await store.init();
  if(store.mode !== 'db'){ setSave(''); document.querySelectorAll('nav.tabs, nav.subtabs').forEach(n => n.style.display = 'none'); document.getElementById('app').innerHTML = loginView(); bindLogin(); hideSplash(); return; }
  { const { count } = await store.client.from('docs').select('id', { count: 'exact', head: true });
    /* 새 사용자는 빈 상태로 바로 시작한다 (튜토리얼은 예시 데이터로 보여 준다). 옛 JSON 가져오기는 ?import 로만 연다 */
    if(count === 0 && location.search.includes('import')){ setSave(''); document.querySelectorAll('nav.tabs, nav.subtabs').forEach(n => n.style.display = 'none'); document.getElementById('app').innerHTML = importView(); bindImport(); hideSplash(); return; } }
  setSave('동기화됨');
  const brand = document.querySelector('.brand');
  if(brand){ const wrap = document.createElement('div'); wrap.className = 'brand-r';
    const slot = document.createElement('span'); slot.id = 'bellSlot'; slot.innerHTML = bellHtml();
    const b = document.createElement('div'); b.className = 'acct';
    b.innerHTML = '<button type="button" class="bell" aria-label="계정" aria-haspopup="true" aria-expanded="false"><svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><circle cx="12" cy="8.6" r="3.6" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M4.8 19.4c1.4-3.2 4.1-4.8 7.2-4.8s5.8 1.6 7.2 4.8" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg></button><div class="acct-menu" role="menu" hidden><div class="acct-who"><b class="acct-name">내 계정</b><div class="acct-mail small muted"></div></div><button type="button" role="menuitem" class="acct-item" data-acct-go="account">계정 설정</button><button type="button" role="menuitem" class="acct-item" data-acct-go="grade">내 투자자 등급</button><button type="button" role="menuitem" class="acct-item" data-acct-go="intro">처음 안내 다시 보기</button><div class="acct-sep"></div><button type="button" role="menuitem" class="acct-item" data-acct="logout">로그아웃</button></div>';
    const ab = b.querySelector('button'), am = b.querySelector('.acct-menu');
    setTimeout(loadUser, 0);
    ab.onclick = e => { e.stopPropagation(); const open = am.hidden; am.hidden = !open; ab.setAttribute('aria-expanded', String(open)); };
    document.addEventListener('click', e => { if(!b.contains(e.target)){ am.hidden = true; ab.setAttribute('aria-expanded','false'); } });
    b.querySelectorAll('[data-acct-go]').forEach(x => x.onclick = () => { am.hidden = true; ab.setAttribute('aria-expanded','false'); const g = x.dataset.acctGo;
      if(g === 'intro'){ S.introForce = true; S.introStep = 0; } else S.tab = g; render(); window.scrollTo(0,0); });
    const q = document.createElement('button'); q.type = 'button'; q.className = 'bell help'; q.setAttribute('aria-label', 'Q&A: 사용법과 설계'); q.innerHTML = '<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><circle cx="12" cy="12" r="9.2" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M9.6 9.3a2.5 2.5 0 1 1 3.6 2.2c-.8.4-1.2.9-1.2 1.8v.4" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/><circle cx="12" cy="16.9" r="1.1" fill="currentColor"/></svg>';
    q.onclick = () => { S.tab = 'guide'; render(); window.scrollTo(0,0); };
    const home = document.querySelector('.brand-t'); if(home){ home.setAttribute('role','link'); home.tabIndex = 0; home.setAttribute('aria-label','홈으로'); const goHome = () => { S.tab = 'portfolio'; S.introForce = false; render(); window.scrollTo({top:0, behavior:'smooth'}); }; home.onclick = goHome; home.onkeydown = e => { if(e.key === 'Enter') goHome(); }; }
    wrap.appendChild(q); wrap.appendChild(slot); wrap.appendChild(b); brand.appendChild(wrap); }
  if(location.hash === '#alerts'){ S.tab = 'alerts'; checkPush().then(() => { if(S.tab === 'alerts') render(); }); history.replaceState(null, '', location.pathname); }
  window.addEventListener('hashchange', () => { if(location.hash === '#alerts'){ S.tab = 'alerts'; render(); history.replaceState(null, '', location.pathname); } });
  render(); hideSplash();""")
rep("""  store.sub('holdings', docs => { S.holdings = docs; S.loaded.h = 1; refresh('h'); });""",
    """  store.sub('holdings', docs => { const firstLoad = !S.loaded.h; S.holdings = docs; S.loaded.h = 1; refresh('h'); if(firstLoad) setTimeout(() => refreshQuotes(false), 1500); });
  setInterval(() => refreshQuotes(false), QUOTE_EVERY);
  store.sub('alerts', docs => { S.alerts = docs; const first = !S.alertsLoaded; S.alertsLoaded = true; updateBell(); if(S.tab === 'alerts') refresh('a'); if(first) setTimeout(scanAlerts, 2500); });
  document.addEventListener('visibilitychange', () => { if(document.visibilityState === 'visible') refreshQuotes(false); });""")

rep("  if(S.tab === 'dividend') app.innerHTML = viewDividend();", "  if(S.tab === 'dividend') app.innerHTML = viewDividend();\n  if(S.tab === 'alerts') app.innerHTML = viewAlerts();\n  if(S.tab === 'account') app.innerHTML = viewAccount();")
rep("  if(sub) sub.innerHTML = g.subs.map(", "  if(sub && (S.tab === 'alerts' || S.tab === 'account' || S.tab === 'guide')){ sub.innerHTML = ''; document.querySelectorAll('nav.tabs button').forEach(b => b.setAttribute('aria-selected','false')); return; }\n  if(sub) sub.innerHTML = g.subs.map(")
rep(".dropbox{", """.brand-r{display:flex;align-items:center;gap:8px;margin-left:auto}
.bell{all:unset;position:relative;cursor:pointer;color:var(--ink);display:flex;padding:6px;border-radius:8px}
.bell:focus-visible{outline:2px solid var(--accent)}
.bell-n{position:absolute;top:0;right:-2px;min-width:17px;height:17px;padding:0 4px;box-sizing:border-box;border-radius:9px;background:var(--bad);color:#FFFFFF;font-size:11px;font-weight:700;display:flex;align-items:center;justify-content:center}
.al-list{padding:4px 12px}
.al-item{all:unset;box-sizing:border-box;width:100%;display:grid;grid-template-columns:10px 1fr;gap:10px;align-items:start;padding:12px 2px;border-bottom:1px solid var(--line);cursor:pointer}
.al-item:last-child{border-bottom:0}
.al-item:focus-visible{outline:2px solid var(--accent)}
.al-item.read{opacity:.55}
.al-dot{width:10px;height:10px;border-radius:50%;margin-top:6px}
.al-main{display:flex;flex-direction:column;gap:2px;min-width:0}
.al-top{display:flex;justify-content:space-between;gap:10px;align-items:baseline}
.al-top .small{white-space:nowrap;flex:0 0 auto}
.al-top b{font-size:15px}
.al-body{color:var(--ink)}
.dropbox{""")
# 3) 로컬 저장 안내 문구 제거 (웹에서는 항상 DB)
s = s.replace("${store.mode==='local'?`<div class=\"notice\" style=\"margin-top:16px\">로그인 상태가 아니어서 이 기기 브라우저에만 저장됩니다.</div>`:''}", "")

LOGO = '<svg class="logo-mark" viewBox="0 0 64 64" width="30" height="30" aria-hidden="true"><rect width="64" height="64" rx="15" fill="#16243A"/><rect x="17" y="13" width="30" height="38" rx="4" fill="#FFFFFF"/><rect x="22" y="36" width="4.5" height="9" rx="1.2" fill="#C9A45C"/><rect x="29.7" y="30" width="4.5" height="15" rx="1.2" fill="#C9A45C"/><rect x="37.4" y="23" width="4.5" height="22" rx="1.2" fill="#C9A45C"/></svg>'
rep('<div class="brand"><h1>가치노트</h1><small id="saveState">불러오는 중</small></div>', '<div class="brand"><div class="brand-l"><div class="brand-t"><h1 class="wordmark" aria-label="ValueNote 가치노트"><span class="wm-a">Value</span><span class="wm-b">Note</span></h1><span class="brand-sub">' + APP_SLOGAN + '</span></div></div></div><div id="saveState" class="save-toast" role="status" aria-live="polite"></div>')
rep("function setSave(t){ const el = $('#saveState'); if(el) el.textContent = t; }", "function setSave(t){ const el = $('#saveState'); if(!el) return; clearTimeout(setSave._t); if(!t || t === '동기화됨'){ el.classList.remove('show'); return; } el.textContent = t; el.classList.add('show'); if(!/중$/.test(t)) setSave._t = setTimeout(() => el.classList.remove('show'), t.includes('실패') ? 5000 : 1400); }")
# tab icons (bottom bar on mobile)
ICONS = {'portfolio':'<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M4 19V10m5.3 9V5m5.4 14v-7M20 19V8" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/></svg>',
 'briefing':'<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><rect x="4.5" y="3.8" width="15" height="16.4" rx="2.6" fill="none" stroke="currentColor" stroke-width="1.8"/><path d="M8.3 8.6h7.4M8.3 12h7.4M8.3 15.4h4.4" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/></svg>',
 'companies':'<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><circle cx="10.6" cy="10.6" r="5.8" fill="none" stroke="currentColor" stroke-width="1.9"/><path d="m15 15 4.6 4.6" stroke="currentColor" stroke-width="1.9" stroke-linecap="round"/></svg>'}
for k, lab in [('portfolio','포트폴리오'),('briefing','브리핑'),('companies','기업')]:
    sel = 'true' if k == 'portfolio' else 'false'
    rep(f'<button role="tab" data-tab="{k}" aria-selected="{sel}">{lab}</button>', f'<button role="tab" data-tab="{k}" aria-selected="{sel}"><span class="tab-ic">{ICONS[k]}</span><span class="tab-l">{lab}</span></button>')
s = s.replace('<title>가치노트</title>', '<title>' + "밸류노트 " + APP_NAME + '</title>')
HEAD = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<link rel="icon" type="image/png" href="/favicon-64.png?v=4">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="apple-touch-icon" href="/apple-touch-icon.png?v=4">
<meta name="theme-color" content="#0E1A2B">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="밸류노트">
<meta name="application-name" content="밸류노트">
<link rel="preload" href="/fonts/fraunces-latin-600-normal.woff2" as="font" type="font/woff2" crossorigin>
<style>@font-face{font-family:"Fraunces";font-style:normal;font-weight:600;font-display:swap;src:url(/fonts/fraunces-latin-600-normal.woff2) format("woff2")}@font-face{font-family:"Fraunces";font-style:italic;font-weight:600;font-display:swap;src:url(/fonts/fraunces-latin-600-italic.woff2) format("woff2")}</style>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/sun-typeface/SUIT@2.0.5/fonts/variable/woff2/SUIT-Variable.css">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js"></script>
<script src="config.js"></script>
<script>window.__t0=Date.now();window.addEventListener('beforeinstallprompt',function(e){e.preventDefault();window.__installEvt=e;});</script>
<style>
#splash{position:fixed;inset:0;z-index:100;background:#0E1A2B;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;transition:opacity .45s ease;font-family:"SUIT Variable","SUIT","Pretendard Variable",system-ui,sans-serif}
#splash.out{opacity:0;pointer-events:none}
#splash .sp-wm{font-family:"Fraunces",Georgia,serif;font-size:46px;font-weight:600;letter-spacing:-.02em;color:#FFFFFF;animation:spIn .7s ease-out both;font-variation-settings:"opsz" 144}
#splash .sp-wm span{color:#C9A45C;font-style:italic}
#splash .sp-sub{color:#C9A45C;font-size:13px;letter-spacing:.14em;text-transform:uppercase;font-weight:600;animation:spIn .7s .15s ease-out both}
#splash .sp-ko{color:rgba(255,255,255,.6);font-size:13px;animation:spIn .7s .3s ease-out both}
#splash .sp-bar{width:120px;height:2px;border-radius:1px;background:rgba(255,255,255,.12);overflow:hidden;margin-top:18px}
#splash .sp-bar i{display:block;height:100%;width:40%;background:#C9A45C;animation:spBar 1.1s ease-in-out infinite}
@keyframes spIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}
@keyframes spBar{0%{transform:translateX(-100%)}100%{transform:translateX(260%)}}
@media (prefers-reduced-motion: reduce){#splash *{animation:none!important}}
</style>
</head>
<body>
<div id="splash" aria-hidden="true"><div class="sp-wm">Value<span>Note</span></div><div class="sp-name">밸류노트</div><div class="sp-sub">On the Shoulders of Giants</div><div class="sp-ko">그레이엄 · 버핏 · 멍거의 어깨 위에서, 멀리 보는 투자</div><div class="sp-bar"><i></i></div></div>
"""
s = HEAD.replace("가치노트", APP_NAME) + s.lstrip() + "\n<style>\n" + open(__file__.replace("build_web.py", "theme.css"), encoding="utf-8").read() + "\n</style>\n</body>\n</html>\n"
open(dst, "w", encoding="utf-8").write(s)
print("wrote", dst, len(s))
