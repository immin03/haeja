/* 밸류노트 유튜브 연결 (2026-10-23)
   어느 페이지든 아래 자리표시만 넣고 <script src="/yt.js" defer></script> 를 붙이면 된다.
     <div data-yt="co:000660"></div>  그 회사 롱폼 영상(가장 최근)을 바로 재생할 수 있는 카드. 영상이 없으면 아무것도 안 보인다
     <div data-yt="latest"></div>     가장 최근 롱폼 영상 카드
     <div data-yt="channel"></div>    채널 구독 띠 (영상 목록을 못 불러와도 보인다)
   선택: data-yt-src="hynix" (통계에 남길 위치 이름)
   영상 목록은 Supabase yt_public() 에서 읽는다: 관리자 승인 → 업로드 → 공개 시각이 지나면 사이트에 저절로 붙는다.
   앱(index.html)처럼 화면이 바뀌는 페이지도 새로 생긴 자리표시를 알아서 채운다. */
(function(){
  if (window.VNYT) return;
  var SB = 'https://msjbrwyzkiueqnzjeicm.supabase.co';
  var K = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1zamJyd3l6a2l1ZXFuemplaWNtIiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTE4NTk0NTcsImV4cCI6MjEwNzQzNTQ1N30.RIq2MRW8bwHQUO_dPeIarujjWcYD_dXn06icr1Mpmuw';
  var HANDLE = '@valuenote_korea';
  var CH_URL = 'https://www.youtube.com/' + HANDLE;
  var SUB_URL = CH_URL + '?sub_confirmation=1';

  var css = ''
  + '@font-face{font-family:"VN Arrow";src:url(/fonts/vn-arrow-400.woff2) format("woff2");font-weight:100 599;unicode-range:U+2190-21FF,U+27F6;font-display:swap}@font-face{font-family:"VN Arrow";src:url(/fonts/vn-arrow-700.woff2) format("woff2");font-weight:600 1000;unicode-range:U+2190-21FF,U+27F6;font-display:swap}.vnyt{--yn:#0A1730;--yn2:#13305A;--yg:#EADBB9;--yg2:#C9AF7A;--yi:#F7F2E8;font-family:"VN Arrow","SUIT Variable","SUIT","Pretendard",-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;word-break:keep-all;overflow-wrap:break-word;margin:22px 0;text-align:left}'
  + '.vnyt *{box-sizing:border-box}'
  + '.vnyt-card{background:linear-gradient(165deg,var(--yn2),var(--yn) 70%);border-radius:18px;overflow:hidden;color:var(--yi);box-shadow:0 10px 26px rgba(10,23,48,.16)}'
  + '.vnyt-top{display:flex;align-items:center;gap:8px;padding:14px 16px 10px;font-size:12.5px;font-weight:800;color:var(--yg);letter-spacing:.02em}'
  + '.vnyt-top .vnyt-dot{width:7px;height:7px;border-radius:50%;background:#FF4D6A;flex:none}'
  + '.vnyt-frame{position:relative;width:100%;aspect-ratio:16/9;background:#000;cursor:pointer;display:block;border:0;padding:0}'
  + '.vnyt-frame img,.vnyt-frame iframe{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;border:0;display:block}'
  + '.vnyt-play{position:absolute;left:50%;top:50%;width:68px;height:48px;margin:-24px 0 0 -34px;border-radius:14px;background:#FF0000;display:flex;align-items:center;justify-content:center;box-shadow:0 6px 18px rgba(0,0,0,.35);transition:transform .15s}'
  + '.vnyt-frame:hover .vnyt-play{transform:scale(1.06)}'
  + '.vnyt-play:after{content:"";border-style:solid;border-width:10px 0 10px 17px;border-color:transparent transparent transparent #FFFFFF;margin-left:4px}'
  + '.vnyt-dur{position:absolute;right:10px;bottom:10px;background:rgba(0,0,0,.78);color:#FFFFFF;font-size:12px;font-weight:700;border-radius:6px;padding:2px 7px}'
  + '.vnyt-body{padding:12px 16px 16px}'
  + '.vnyt-t{display:block;font-size:16.5px;font-weight:850;line-height:1.45;color:#fff;margin:0}'
  + '.vnyt-s{display:block;font-size:13px;line-height:1.55;color:rgba(247,242,232,.72);margin-top:6px}'
  + '.vnyt-row{display:flex;gap:8px;margin-top:12px}'
  + '.vnyt-btn{flex:1;display:inline-flex;align-items:center;justify-content:center;gap:6px;height:44px;border-radius:12px;font-size:14.5px;font-weight:800;text-decoration:none;white-space:nowrap}'
  + '.vnyt-btn.sub{background:#FF0000;color:#FFFFFF}'
  + '.vnyt-btn.ghost{background:rgba(255,255,255,.08);border:1px solid rgba(234,219,185,.35);color:var(--yi)}'
  + '.vnyt-more{display:inline-block;margin-top:8px;font-size:13px;font-weight:800;color:var(--yg);text-decoration:none}'
  + '.vnyt[data-yt-compact]{margin:14px 0 0}.vnyt[data-yt-compact] .vnyt-card{box-shadow:none}'
  + '.vnyt-ov{position:fixed;inset:0;z-index:2147483000;background:rgba(5,12,26,.86);display:flex;align-items:center;justify-content:center;padding:16px;font-family:"VN Arrow","SUIT Variable","SUIT",-apple-system,sans-serif}'
  + '.vnyt-ov-in{width:100%;max-width:880px;text-align:center}.vnyt-ov .vnyt-frame{border-radius:12px;overflow:hidden;cursor:default}'
  + '.vnyt-x{display:block;margin:0 0 8px auto;width:40px;height:40px;border-radius:50%;border:0;background:rgba(255,255,255,.14);color:#FFFFFF;font-size:24px;line-height:1;cursor:pointer}'
  + '.vnyt-ov .vnyt-more{margin-top:14px;color:#EADBB9}'
  + '.vnyt-ch{display:flex;align-items:center;gap:12px;text-decoration:none;border-radius:16px;padding:14px 16px;background:var(--yn);color:var(--yi)}'
  + '.vnyt-ic{flex:none;width:42px;height:42px;border-radius:12px;background:#FF0000;display:flex;align-items:center;justify-content:center}'
  + '.vnyt-ic:after{content:"";border-style:solid;border-width:8px 0 8px 13px;border-color:transparent transparent transparent #FFFFFF;margin-left:3px}'
  + '.vnyt-ch b{display:block;font-size:15.5px;color:#fff;line-height:1.35}'
  + '.vnyt-ch small{display:block;font-size:12.5px;line-height:1.5;color:rgba(247,242,232,.72);margin-top:2px}'
  + '.vnyt-ch .vnyt-go{flex:none;margin-left:auto;font-size:13px;font-weight:850;color:var(--yn);background:var(--yg);border-radius:10px;padding:8px 11px;white-space:nowrap}';

  function addCss(){ if (document.getElementById('vnyt-css')) return; var s = document.createElement('style'); s.id = 'vnyt-css'; s.textContent = css; document.head.appendChild(s); }
  function esc(s){ return String(s == null ? '' : s).replace(/[&<>"']/g, function(c){ return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function dur(n){ n = Math.round(+n || 0); if (!n) return ''; var m = Math.floor(n / 60), s = n % 60; return m + ':' + (s < 10 ? '0' : '') + s; }
  function durKo(n){ n = Math.round(+n || 0); var m = Math.round(n / 60); return m >= 1 ? m + '분' : n + '초'; }

  /* 통계: 기존 events 테이블에 engage 로 남긴다 (/yt/<위치>:<행동>) */
  function sid(){ try{ var v = localStorage.getItem('vn-sid'); if (!v){ v = (crypto.randomUUID ? crypto.randomUUID() : String(Math.random()).slice(2) + Date.now()).replace(/-/g, '').slice(0, 32); localStorage.setItem('vn-sid', v); } return v; }catch(_){ return 'nosid'; } }
  function isBot(){ var b = /bot|crawl|spider|headless|preview|facebookexternalhit/i.test(navigator.userAgent) || navigator.webdriver; try{ if (localStorage.getItem('vn-staff') === '1') b = true; }catch(_){} return b; }
  function ev(path){
    if (isBot()) return;
    var ref = ''; try{ ref = localStorage.getItem('vn-ref') || ''; }catch(_){}
    try{ fetch(SB + '/rest/v1/events', { method: 'POST', keepalive: true, headers: { apikey: K, Authorization: 'Bearer ' + K, 'Content-Type': 'application/json', Prefer: 'return=minimal' },
      body: JSON.stringify({ kind: 'engage', sid: sid(), path: ('/yt' + path).slice(0, 200), ref: (ref || location.pathname).slice(0, 300), device: /Mobi|iPhone|Android/.test(navigator.userAgent) ? '모바일' : 'PC' }) }).catch(function(){}); }catch(_){}
  }

  /* 영상 목록: 한 번만 불러오고 10분 동안 재사용 */
  var P = null;
  function load(){
    if (P) return P;
    try{ var c = JSON.parse(sessionStorage.getItem('vn-yt') || 'null'); if (c && Date.now() - c.t < 6e5) return (P = Promise.resolve(c.d)); }catch(_){}
    P = fetch(SB + '/rest/v1/rpc/yt_public', { method: 'POST', headers: { apikey: K, Authorization: 'Bearer ' + K, 'Content-Type': 'application/json' }, body: '{}' })
      .then(function(r){ return r.ok ? r.json() : { videos: [] }; })
      .then(function(d){ d = d || { videos: [] }; try{ sessionStorage.setItem('vn-yt', JSON.stringify({ t: Date.now(), d: d })); }catch(_){} return d; })
      .catch(function(){ P = null; return { videos: [] }; });
    return P;
  }
  function pick(d, key){
    var L = (d.videos || []).filter(function(v){ return v.kind === 'long'; });
    if (key === 'latest') return L[0];
    if (key.indexOf('co:') === 0){ var co = key.slice(3).toLowerCase().split('-')[0].split('.')[0]; return L.filter(function(v){ return String(v.company || '').toLowerCase() === co; })[0]; }
    return null;
  }

  function chHtml(){
    return '<a class="vnyt-ch" href="' + SUB_URL + '" target="_blank" rel="noopener" data-a="channel"><span class="vnyt-ic" aria-hidden="true"></span>'
      + '<span><b>밸류노트 유튜브</b><small>화제의 기업을 워렌 버핏·찰리 멍거의 기준으로 10분 안팎에 풀어 드립니다. 월·수·금 새 영상이 올라옵니다.</small></span>'
      + '<span class="vnyt-go">구독</span></a>';
  }
  function cardHtml(v, label, compact){
    var id = encodeURIComponent(v.yid);
    return '<div class="vnyt-card"><div class="vnyt-top"><span class="vnyt-dot"></span>' + esc(label) + (v.dur ? ' · ' + durKo(v.dur) : '') + '</div>'
      + '<button type="button" class="vnyt-frame" data-a="play" aria-label="' + esc(v.title) + ' 영상 재생">'
      + '<img src="https://i.ytimg.com/vi/' + id + '/maxresdefault.jpg" alt="" loading="lazy" onerror="this.onerror=null;this.src=\'https://i.ytimg.com/vi/' + id + '/hqdefault.jpg\'">'
      + '<span class="vnyt-play"></span>' + (v.dur ? '<span class="vnyt-dur">' + dur(v.dur) + '</span>' : '') + '</button>'
      + '<div class="vnyt-body"><b class="vnyt-t">' + esc(v.title) + '</b>'
      + (compact ? '<a class="vnyt-more" href="' + SUB_URL + '" target="_blank" rel="noopener" data-a="subscribe">밸류노트 유튜브 채널 구독하기 ›</a></div></div>' :
        '<span class="vnyt-s">숫자와 원인을 글보다 쉽게, 영상 한 편으로 정리했습니다.</span>'
      + '<div class="vnyt-row"><a class="vnyt-btn sub" href="' + SUB_URL + '" target="_blank" rel="noopener" data-a="subscribe">채널 구독하기</a>'
      + '<a class="vnyt-btn ghost" href="https://youtu.be/' + id + '" target="_blank" rel="noopener" data-a="open">유튜브에서 보기</a></div></div></div>');
  }

  function iframe(v){
    return '<iframe src="https://www.youtube-nocookie.com/embed/' + encodeURIComponent(v.yid) + '?autoplay=1&rel=0&playsinline=1&modestbranding=1" title="' + esc(v.title)
      + '" referrerpolicy="strict-origin-when-cross-origin" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>';
  }
  function overlay(v){
    var o = document.createElement('div'); o.className = 'vnyt-ov';
    o.innerHTML = '<div class="vnyt-ov-in"><button type="button" class="vnyt-x" aria-label="닫기">×</button><div class="vnyt-frame">' + iframe(v) + '</div>'
      + '<a class="vnyt-more" href="' + SUB_URL + '" target="_blank" rel="noopener">밸류노트 유튜브 채널 구독하기 ›</a></div>';
    function close(){ o.remove(); document.removeEventListener('keydown', key); }
    function key(e){ if (e.key === 'Escape') close(); }
    o.addEventListener('click', function(e){ if (e.target === o || e.target.closest('.vnyt-x')) close(); });
    document.addEventListener('keydown', key);
    document.body.appendChild(o);
  }
  function wire(el, src, v){
    el.addEventListener('click', function(e){
      var t = e.target.closest('[data-a]'); if (!t) return;
      var a = t.getAttribute('data-a');
      if (a === 'play' && v){
        e.preventDefault();
        if (t.querySelector('iframe')) return;
        // 앱(#main)은 화면을 자주 다시 그리므로, 재생 중 끊기지 않게 화면 위 창으로 띄운다
        if (el.closest('#main')) overlay(v); else { t.innerHTML = iframe(v); t.style.cursor = 'default'; }
      }
      ev('/' + src + ':' + a + (v ? ':' + v.yid : ''));
    });
  }

  function mountOne(el){
    if (el.getAttribute('data-yt-done')) return;
    el.setAttribute('data-yt-done', '1');
    var key = el.getAttribute('data-yt') || '', src = (el.getAttribute('data-yt-src') || location.pathname.replace(/^\/|\.html$/g, '') || 'home').replace(/[^\w가-힣/-]/g, '').slice(0, 40);
    el.classList.add('vnyt');
    if (key === 'channel'){ el.innerHTML = chHtml(); wire(el, src, null); return; }
    el.style.display = 'none';
    load().then(function(d){
      var v = pick(d, key); if (!v) return;
      el.innerHTML = cardHtml(v, el.getAttribute('data-yt-label') || (key === 'latest' ? '밸류노트 유튜브 최신 영상' : '영상으로 보기'), el.hasAttribute('data-yt-compact'));
      el.style.display = '';
      wire(el, src, v);
      ev('/' + src + ':view:' + v.yid);
    });
  }
  function mount(root){ addCss(); (root || document).querySelectorAll('[data-yt]:not([data-yt-done])').forEach(mountOne); }

  window.VNYT = { mount: mount, load: load, channel: CH_URL, subscribe: SUB_URL };
  function start(){
    mount();
    if (window.MutationObserver){ var pend = 0; new MutationObserver(function(){ if (pend) return; pend = requestAnimationFrame(function(){ pend = 0; if (document.querySelector('[data-yt]:not([data-yt-done])')) mount(); }); }).observe(document.body, { childList: true, subtree: true }); }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();
