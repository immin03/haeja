"""스노우볼 노트 아티팩트 HTML → 웹 버전(index.html) 변환.
사용: python3 scripts/build_web.py <artifact.html> index.html
- 저장소를 Supabase로 교체 (로그인한 본인 데이터만)
- 로그인 화면, 로그아웃 버튼
- 열려 있는 동안 10분마다 보유 종목 시세·환율 갱신 (/api/quote)
"""
import sys

APP_NAME = "스노우볼 노트"
APP_SLOGAN = "Inspired by Graham & Buffett"

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
  return {
    get mode(){ return mode },
    get user(){ return user },
    get client(){ return sb },
    async init(){
      const C = window.HAEJA_CONFIG || {};
      if(!window.supabase || !C.SUPABASE_URL || !C.SUPABASE_ANON_KEY){ mode = 'noconfig'; return; }
      sb = window.supabase.createClient(C.SUPABASE_URL, C.SUPABASE_ANON_KEY);
      const { data: { session } } = await sb.auth.getSession();
      if(!session){ mode = 'login'; return; }
      user = session.user; mode = 'db';
    },
    async login(email, password){
      return sb.auth.signInWithPassword({ email, password });
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
      const body = { ...data }; delete body.id;
      const { error } = await sb.from('docs').upsert({ collection: col, id, data: body, updated_at: new Date().toISOString() });
      if(error){ setSave('저장 실패: ' + error.message); throw error; }
    },
    async del(col, id){
      const { error } = await sb.from('docs').delete().eq('collection', col).eq('id', id);
      if(error){ setSave('삭제 실패: ' + error.message); throw error; }
    }
  };
})();
function loginView(){
  if(store.mode === 'noconfig') return `<div class="card" style="margin-top:24px"><h3>설정이 필요합니다</h3><p class="small muted">config.js에 Supabase 주소와 공개 키(anon key)를 넣어 주세요. README의 3단계입니다.</p></div>`;
  return `<div class="card stack" style="margin-top:24px;max-width:420px">
    <h3 style="margin:0">로그인</h3>
    <p class="small muted" style="margin:0">Supabase에 등록한 이메일과 비밀번호로 로그인합니다. 한 번 로그인하면 이 기기에서는 계속 열립니다.</p>
    <label class="f">이메일<input id="lg-email" type="email" autocomplete="email" inputmode="email"></label>
    <label class="f">비밀번호<input id="lg-pw" type="password" autocomplete="current-password"></label>
    <button class="btn primary" id="lg-go">로그인</button>
    <div class="status-line" id="lg-msg"></div>
  </div>`;
}
function bindLogin(){
  const go = document.getElementById('lg-go'); if(!go) return;
  document.getElementById('lg-pw')?.addEventListener('keydown', e => { if(e.key === 'Enter') go.click(); });
  go.onclick = async () => {
    const email = document.getElementById('lg-email').value.trim(), pw = document.getElementById('lg-pw').value; const msg = document.getElementById('lg-msg');
    if(!email || !pw){ msg.textContent = '이메일과 비밀번호를 입력하세요.'; return; }
    go.disabled = true; msg.textContent = '확인 중';
    const { error } = await store.login(email, pw);
    if(error){ go.disabled = false; msg.textContent = '로그인하지 못했습니다: ' + (error.message === 'Invalid login credentials' ? '이메일 또는 비밀번호가 틀립니다' : error.message); return; }
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
    setSave('시세 ' + new Date().toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' }) + ' 기준');
  }catch(e){ setSave('시세 갱신 실패'); }
  finally{ quoteBusy = false; }
}
"""
s = s[:i] + STORE + open(__file__.replace('build_web.py','web_alerts.js'), encoding='utf-8').read() + s[j:]

# 2) 시작 루틴: 로그인 분기, 시세 타이머, 로그아웃 버튼
rep("""  await store.init();
  setSave(store.mode==='db' ? '동기화됨' : '이 기기에 저장');
  render();""", """  await store.init();
  if(store.mode !== 'db'){ setSave(''); document.querySelectorAll('nav.tabs, nav.subtabs').forEach(n => n.style.display = 'none'); document.getElementById('app').innerHTML = loginView(); bindLogin(); return; }
  { const { count } = await store.client.from('docs').select('id', { count: 'exact', head: true });
    if(count === 0){ setSave(''); document.querySelectorAll('nav.tabs, nav.subtabs').forEach(n => n.style.display = 'none'); document.getElementById('app').innerHTML = importView(); bindImport(); return; } }
  setSave('동기화됨');
  const brand = document.querySelector('.brand');
  if(brand){ const wrap = document.createElement('div'); wrap.className = 'brand-r';
    const slot = document.createElement('span'); slot.id = 'bellSlot'; slot.innerHTML = bellHtml();
    const b = document.createElement('button'); b.className = 'btn'; b.style.cssText = 'font-size:12px;padding:4px 10px'; b.textContent = '로그아웃'; b.onclick = () => store.logout();
    wrap.appendChild(slot); wrap.appendChild(b); brand.appendChild(wrap); }
  if(location.hash === '#alerts'){ S.tab = 'alerts'; checkPush().then(() => { if(S.tab === 'alerts') render(); }); history.replaceState(null, '', location.pathname); }
  window.addEventListener('hashchange', () => { if(location.hash === '#alerts'){ S.tab = 'alerts'; render(); history.replaceState(null, '', location.pathname); } });
  render();""")
rep("""  store.sub('holdings', docs => { S.holdings = docs; S.loaded.h = 1; refresh('h'); });""",
    """  store.sub('holdings', docs => { const firstLoad = !S.loaded.h; S.holdings = docs; S.loaded.h = 1; refresh('h'); if(firstLoad) setTimeout(() => refreshQuotes(false), 1500); });
  setInterval(() => refreshQuotes(false), QUOTE_EVERY);
  store.sub('alerts', docs => { S.alerts = docs; const first = !S.alertsLoaded; S.alertsLoaded = true; updateBell(); if(S.tab === 'alerts') refresh('a'); if(first) setTimeout(scanAlerts, 2500); });
  document.addEventListener('visibilitychange', () => { if(document.visibilityState === 'visible') refreshQuotes(false); });""")

rep("  if(S.tab === 'dividend') app.innerHTML = viewDividend();", "  if(S.tab === 'dividend') app.innerHTML = viewDividend();\n  if(S.tab === 'alerts') app.innerHTML = viewAlerts();")
rep("  if(sub) sub.innerHTML = g.subs.map(", "  if(sub && S.tab === 'alerts'){ sub.innerHTML = ''; document.querySelectorAll('nav.tabs button').forEach(b => b.setAttribute('aria-selected','false')); return; }\n  if(sub) sub.innerHTML = g.subs.map(")
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

rep('<div class="brand"><h1>스노우볼 노트</h1><small id="saveState">불러오는 중</small></div>', '<div class="brand"><div class="brand-l"><h1>' + APP_NAME + '</h1><span class="brand-sub">' + APP_SLOGAN + ' · <span id="saveState">불러오는 중</span></span></div></div>')
s = s.replace('<title>스노우볼 노트</title>', '<title>' + APP_NAME + '</title>')
HEAD = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="robots" content="noindex,nofollow">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%231E6A4C'/%3E%3Ccircle cx='19' cy='15.5' r='7.5' fill='%23FFFFFF'/%3E%3Ccircle cx='9.2' cy='21.5' r='1.9' fill='%23FFFFFF'/%3E%3Ccircle cx='5.6' cy='24.2' r='1.35' fill='%23FFFFFF'/%3E%3Crect x='3' y='27.6' width='26' height='1.4' rx='.7' fill='%23FFFFFF'/%3E%3C/svg%3E">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="apple-touch-icon" href="/icon-192.png">
<meta name="theme-color" content="#1E6A4C">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="스노우볼 노트">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js"></script>
<script src="config.js"></script>
</head>
<body>
"""
s = HEAD.replace("스노우볼 노트", APP_NAME) + s.lstrip() + "\n</body>\n</html>\n"
open(dst, "w", encoding="utf-8").write(s)
print("wrote", dst, len(s))
