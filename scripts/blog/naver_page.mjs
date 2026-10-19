// 네이버 블로그 붙여넣기용 페이지 만들기
// 사용: node scripts/blog/naver_page.mjs naver/<글 id>
//   naver/<글 id>/post.json 을 읽어 naver/<글 id>.html 과 naver/<글 id>/photos.zip 을 만든다.
// post.json = { "title": "...", "tags": ["..."], "category": "거장의 투자" (선택: 블로그 카테고리. 없으면 요일로 정함), "order": 1 (선택: 첫 글 묶음의 올리는 순서), "posted": "2026-10-18" (선택: 블로그에 올린 날), "blocks": [
//     {"h": "소제목"}, {"p": "문단. **굵게** 가능"}, {"img": "01.png", "cap": "사진 설명"},
//     {"img": "banner.png", "href": "https://..."} (링크 걸린 배너, 설명 없음),
//     {"quote": "인용문", "src": "출처"}, {"link": "https://...", "text": "링크 문구"}, {"note": "작은 글씨 고지"},
//     {"summary": ["핵심 1", "핵심 2", "핵심 3"]}  (글 첫머리 요약 상자),
//     {"table": {"head": ["항목", "값"], "rows": [["코스피", "−16.2%"], ...]}},
//     {"sources": [["자료 이름", "https://..."], ...]} ] }
// 이 페이지는 검색에서 빠지도록 noindex 를 단다(사이트 칼럼과 겹치는 글이 검색되지 않게).
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';

const SITE = 'https://www.valuenote.co.kr';
const dir = process.argv[2];
if (!dir) { console.error('사용법: node scripts/blog/naver_page.mjs naver/<글 id>'); process.exit(1); }
const id = path.basename(dir);
const post = JSON.parse(fs.readFileSync(path.join(dir, 'post.json'), 'utf8'));
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const inline = (s) => esc(s).replace(/\*\*(.+?)\*\*/g, '<b>$1</b>');
const imgUrl = (f) => `${SITE}/naver/${id}/${f}`;
// 블로그 카테고리: post.json 의 category, 없으면 id 끝 글자로 정한다 (m 주간 시장 정리 · w 기업 분석 · f 거장의 투자)
const CAT_BY_DAY = { m: '주간 시장 정리', w: '기업 분석', f: '거장의 투자', x: '주간 시장 정리' };
const catOf = (d, pj) => pj.category || CAT_BY_DAY[(String(d).match(/^b\d{6}([mwfx])/) || [])[1]] || '';
const category = catOf(id, post);

// 네이버 편집기가 잘 받아들이는 단순한 태그만 쓴다 (p, b, img, blockquote, a)
// 간격 규칙: 네이버는 문단 여백이 없고 빈 줄(<p><br></p>)로만 간격이 생긴다.
//   소제목 위 = 빈 줄 2개(새 단락이 시작된다는 느낌), 소제목 아래 = 빈 줄 없음(소제목이 아래 글에 붙는다),
//   그 밖의 블록 사이 = 빈 줄 1개.
const BLANK = '<p><br></p>';
const blockHtml = (b) => {
  if (b.h) return `<p><span style="font-size:19px"><b><span style="color:#C99A50">■</span> ${inline(b.h)}</b></span></p>`;
  if (b.p && /^— Editor:/.test(b.p)) return `<p style="text-align:right"><b>${inline(b.p)}</b></p>`;
  if (b.p) return `<p>${inline(b.p)}</p>`;
  if (b.img && b.href) return `<p><a href="${esc(b.href)}"><img src="${imgUrl(b.img)}" alt="${esc(b.cap || '')}" width="720"></a></p>`;
  if (b.img) return `<p><img src="${imgUrl(b.img)}" alt="${esc(b.cap || '')}" width="720"></p>${b.cap ? `<p><span style="color:#888888;font-size:13px">${esc(b.cap)}</span></p>` : ''}`;
  if (b.quote) return `<blockquote><p>"${esc(b.quote)}"</p>${b.src ? `<p>— ${esc(b.src)}</p>` : ''}</blockquote>`;
  if (b.link) return `<p><a href="${esc(b.link)}">${esc(b.text || b.link)}</a></p>`;
  if (b.note) return `<p><span style="color:#888888;font-size:13px">${esc(b.note)}</span></p>`;
  if (b.summary) return `<blockquote><p><b>3줄 요약</b></p>${b.summary.map((x) => `<p>· ${inline(x)}</p>`).join('')}</blockquote>`;
  if (b.table) return `<table border="1" cellpadding="8" style="border-collapse:collapse;width:100%"><thead><tr>${b.table.head.map((x) => `<th style="background:#F3EEE3">${esc(x)}</th>`).join('')}</tr></thead><tbody>${b.table.rows.map((r) => `<tr>${r.map((x) => `<td>${inline(x)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  if (b.sources) return `<p><b>참고한 자료</b></p>${b.sources.map(([n, u]) => `<p><span style="font-size:13px">· ${esc(n)} <a href="${esc(u)}">${esc(u.replace(/^https?:\/\//, '').slice(0, 60))}</a></span></p>`).join('')}`;
  return '';
};
const body = post.blocks.map((b, i) => {
  const html = blockHtml(b);
  if (i === 0) return html;
  const prev = post.blocks[i - 1];
  const gap = b.h ? BLANK + BLANK : prev.h ? '' : BLANK;
  return gap + '\n' + html;
}).join('\n');
const plain = post.blocks.map((b) => b.h ? `■ ${b.h}` : b.p ? b.p.replace(/\*\*/g, '') : b.img ? `[사진: ${b.cap || b.img}]` : b.quote ? `"${b.quote}"${b.src ? ` — ${b.src}` : ''}` : b.link ? `${b.text || ''} ${b.link}` : b.summary ? '3줄 요약\n' + b.summary.map((x) => '· ' + x.replace(/\*\*/g, '')).join('\n') : b.table ? [b.table.head, ...b.table.rows].map((r) => r.join(' | ')).join('\n') : b.sources ? '참고한 자료\n' + b.sources.map(([n, u]) => `· ${n} ${u}`).join('\n') : b.note || '').join('\n\n');
const tags = (post.tags || []).map((t) => '#' + t.replace(/\s+/g, '')).join(' ');
const imgs = post.blocks.filter((b) => b.img).map((b) => b.img);

// 사진 한꺼번에 받기 (zip)
const zip = path.join(dir, 'photos.zip');
fs.rmSync(zip, { force: true });
execFileSync('zip', ['-j', '-q', zip, ...imgs.map((f) => path.join(dir, f))]);

const html = `<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>블로그 붙여넣기 · ${esc(post.title)}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/sun-typeface/SUIT@2.0.5/fonts/variable/woff2/SUIT-Variable.css">
<style>
:root{--navy:#0E1A2B;--gold:#C99A50;--line:#E7E2D8;--bg:#F6F3EC;--muted:#6B7584}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:#1B2433;font:16px/1.7 "SUIT Variable",SUIT,Pretendard,-apple-system,"Malgun Gothic",sans-serif;word-break:keep-all}
.top{background:var(--navy);color:#F3EEE3;padding:14px 16px;font-weight:800;display:flex;align-items:center;gap:12px}.top span{color:#E4C78D}.bk{color:#F3EEE3;text-decoration:none;font-size:14px;font-weight:700;border:1px solid rgba(255,255,255,.25);border-radius:10px;padding:5px 10px}.bk:hover{border-color:#E4C78D}
.cat{display:inline-block;background:#FBF5EA;border:1px solid #E4C78D;color:#7A5A22;font-weight:800;border-radius:10px;padding:6px 12px}
main{max-width:760px;margin:0 auto;padding:16px 16px 60px}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px;margin:14px 0}
h2{font-size:15px;color:var(--muted);margin:0 0 8px;font-weight:700}
.row{display:flex;gap:10px;align-items:flex-start;justify-content:space-between}
.btn{font:inherit;font-weight:800;font-size:15px;border:0;border-radius:12px;padding:11px 16px;background:var(--navy);color:#fff;cursor:pointer;white-space:nowrap}
.btn.gold{background:linear-gradient(90deg,#C99A50,#E4C78D);color:#0A1322}
.btn.ok{background:#2E8B62}
.ttl{font-size:20px;font-weight:800}
.steps{margin:0;padding-left:20px;color:#3A4352}.steps li{margin:4px 0}
#art{border:1px dashed var(--line);border-radius:12px;padding:20px 22px;font-size:16px;line-height:1.8;color:#222}#art img{max-width:100%;height:auto;border-radius:8px;display:block}
#art p{margin:0}
#art blockquote{margin:0;padding:12px 16px;border-left:3px solid var(--gold);background:#FBF5EA}#art blockquote p{margin:2px 0}#art table{font-size:14px}#art th,#art td{border:1px solid var(--line);text-align:left}
.ph{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.ph a{display:block}.ph img{width:100%;border-radius:8px;display:block}
.small{font-size:13px;color:var(--muted)}
</style></head><body><div class="top"><a class="bk" href="/naver/">‹ 글 목록</a><b>Value<span>Note</span> · 네이버 블로그 붙여넣기</b></div><main>
<section class="card"><h2>올리는 순서 (PC 권장)</h2><ol class="steps">
<li>네이버 블로그 <b>글쓰기</b>를 연다.</li>
<li>아래 <b>제목 복사</b> → 제목 칸에 붙여넣기.</li>
<li><b>본문 복사</b> → 본문 칸을 한 번 누르고 붙여넣기 (Ctrl+V). 사진도 함께 들어간다.</li>
<li>사진이 빠졌으면 <b>사진 모두 받기</b>로 받아서 [사진] 위치에 넣는다.</li>
<li>발행 화면에서 <b>카테고리</b>를 아래 이름으로 고른다.</li>
<li><b>태그 복사</b> → 발행 화면의 태그 칸에 붙여넣기 → 발행.</li></ol></section>
${category ? `<section class="card"><h2>카테고리</h2><div class="row"><span class="cat" id="catv">${esc(category)}</span><button class="btn" data-copy="catv">카테고리 복사</button></div></section>` : ''}
<section class="card"><h2>제목</h2><div class="row"><div class="ttl" id="ttl">${esc(post.title)}</div><button class="btn" data-copy="ttl">제목 복사</button></div></section>
<section class="card"><div class="row" style="margin-bottom:12px"><h2 style="margin:0">본문 (사진 ${imgs.length}장 포함)</h2><button class="btn gold" id="cpBody">본문 복사</button></div>
<div id="art">${body}</div></section>
<section class="card"><h2>태그</h2><div class="row"><div id="tags">${esc(tags)}</div><button class="btn" data-copy="tags">태그 복사</button></div></section>
<section class="card"><div class="row" style="margin-bottom:10px"><h2 style="margin:0">사진</h2><a class="btn" href="/naver/${id}/photos.zip" download>사진 모두 받기</a></div>
<div class="ph">${imgs.map((f, i) => `<a href="${imgUrl(f)}" download="valuenote-${id}-${i + 1}.png"><img src="${imgUrl(f)}" alt="사진 ${i + 1}" loading="lazy"></a>`).join('')}</div>
<p class="small" style="margin:10px 0 0">휴대폰에서는 사진을 길게 눌러 저장할 수 있습니다.</p></section>
</main>
<script>
const PLAIN = ${JSON.stringify(plain).replace(/</g, '\\u003c')};
function done(b, t){ const o = b.textContent; b.textContent = t; b.classList.add('ok'); setTimeout(() => { b.textContent = o; b.classList.remove('ok'); }, 1800); }
function selectCopy(el){ const r = document.createRange(); r.selectNodeContents(el); const s = getSelection(); s.removeAllRanges(); s.addRange(r); const ok = document.execCommand('copy'); s.removeAllRanges(); return ok; }
document.querySelectorAll('[data-copy]').forEach(b => b.onclick = async () => { const t = document.getElementById(b.dataset.copy).textContent; try { await navigator.clipboard.writeText(t); } catch(e) { selectCopy(document.getElementById(b.dataset.copy)); } done(b, '복사했어요'); });
document.getElementById('cpBody').onclick = async (ev) => { const b = ev.currentTarget, art = document.getElementById('art');
  try { await navigator.clipboard.write([new ClipboardItem({ 'text/html': new Blob([art.innerHTML], { type: 'text/html' }), 'text/plain': new Blob([PLAIN], { type: 'text/plain' }) })]); }
  catch(e) { selectCopy(art); }
  done(b, '복사했어요 · 붙여넣기 하세요'); };
</script></body></html>`;
fs.writeFileSync(`${dir}.html`, html);
console.log(`✓ ${dir}.html · 사진 ${imgs.length}장 · ${zip}`);

// 블로그 글 목록 페이지(naver/index.html): 관리자 페이지 위 '블로그 글'에서 연다. 최신 글이 위
const root = path.dirname(dir);
const list = fs.readdirSync(root).filter((d) => fs.existsSync(path.join(root, d, 'post.json')))
  .map((d) => { const pj = JSON.parse(fs.readFileSync(path.join(root, d, 'post.json'), 'utf8')); return { d, title: pj.title, cat: catOf(d, pj), order: pj.order, posted: pj.posted, at: fs.statSync(path.join(root, d, 'post.json')).mtimeMs, n: pj.blocks.filter((b) => b.img).length }; })
  .sort((a, b) => (/^b\d/.test(b.d) - /^b\d/.test(a.d)) || ((a.order ?? 99) - (b.order ?? 99)) || b.d.localeCompare(a.d));
const L = (x) => { const m = x.d.match(/^b(\d\d)(\d\d)(\d\d)([mwfx])/); return m ? `20${m[1]}.${m[2]}.${m[3]} · ${{ m: '시장 · 매크로', w: '기업 분석', f: '가치투자 공부 · 사용법', x: '시장 이슈 (수시)' }[m[4]]}` : (x.order ? `첫 글 묶음 · 올리는 순서 ${x.order}번` : '첫 글'); };
// 올린 글 표시: post.json 의 posted(날짜) + 관리자 로그인 시 docs(collection=naver, id=posted)에 저장한 표시를 합친다
const baked = Object.fromEntries(list.filter((x) => x.posted).map((x) => [x.d, x.posted]));
fs.writeFileSync(path.join(root, 'index.html'), `<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow"><title>블로그 글 목록 · 밸류노트</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/sun-typeface/SUIT@2.0.5/fonts/variable/woff2/SUIT-Variable.css">
<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js"></script>
<script src="/config.js"></script>
<style>body{margin:0;background:#F6F3EC;color:#1B2433;font:16px/1.6 "SUIT Variable",SUIT,Pretendard,-apple-system,sans-serif;word-break:keep-all}.top{background:#0E1A2B;color:#F3EEE3;padding:14px 16px;font-weight:800;display:flex;align-items:center;gap:12px}.top span{color:#E4C78D}.bk{color:#F3EEE3;text-decoration:none;font-size:14px;font-weight:700;border:1px solid rgba(255,255,255,.25);border-radius:10px;padding:5px 10px}main{max-width:760px;margin:0 auto;padding:16px}
.cat{font-style:normal;display:inline-block;background:#FBF5EA;border:1px solid #E4C78D;color:#7A5A22;font-weight:800;border-radius:8px;padding:1px 7px;margin-right:4px;font-size:12px}
.it{display:flex;gap:14px;align-items:center;background:#fff;border:1px solid #E7E2D8;border-radius:14px;padding:12px;margin:10px 0}.it a{display:flex;gap:14px;align-items:center;flex:1;min-width:0;text-decoration:none;color:inherit}.it img{width:84px;height:84px;border-radius:10px;flex-shrink:0}.it b{display:block}.it small{color:#6B7584}
.ck{font:inherit;font-size:14px;font-weight:800;border:1px solid #E7E2D8;background:#fff;color:#6B7584;border-radius:10px;padding:8px 10px;cursor:pointer;white-space:nowrap;flex-shrink:0}.ck:hover{border-color:#C99A50;color:#0E1A2B}
.it.done{background:#F1EEE6}.it.done img{opacity:.45}.it.done b{color:#6B7584}.it.done .ck{background:#2E8B62;border-color:#2E8B62;color:#fff}
h3{font-size:15px;color:#6B7584;margin:26px 0 4px}.n{color:#6B7584;font-size:14px}#who{font-size:13px;color:#6B7584}</style></head><body><div class="top"><a class="bk" href="/admin">‹ 관리자</a><b>Value<span>Note</span> · 네이버 블로그 글</b></div><main>
<p class="n">월·수·금 아침에 새 글이 추가됩니다. 글을 눌러 제목·본문·태그를 복사해 블로그에 붙여 넣으세요. (PC 권장)<br>블로그에 올린 글은 오른쪽 <b>올렸어요</b>를 누르면 아래 '올린 글'로 내려갑니다.</p>
<p id="who"></p>
<h3>올릴 글</h3><div id="todo"></div><h3>올린 글</h3><div id="done"></div>
<div id="src" hidden>${list.map((x) => `<div class="it" data-id="${x.d}"><a href="/naver/${x.d}"><img src="/naver/${x.d}/01.png" alt=""><span><small>${x.cat ? `<em class="cat">${esc(x.cat)}</em> ` : ''}${esc(L(x))} · 사진 ${x.n}장</small><b>${esc(x.title)}</b></span></a><button class="ck" type="button">올렸어요</button></div>`).join('')}</div>
</main>
<script>
const BAKED = ${JSON.stringify(baked)};
let POSTED = { ...BAKED }, sb = null, uid = null;
const today = () => new Date(Date.now() + 9 * 3600e3).toISOString().slice(0, 10);
function render() {
  const items = [...document.querySelectorAll('#src .it, #todo .it, #done .it')];
  const todo = document.getElementById('todo'), done = document.getElementById('done');
  items.forEach((el) => { const id = el.dataset.id, at = POSTED[id]; el.classList.toggle('done', !!at); el.querySelector('.ck').textContent = at ? '✓ 올림 · ' + at.slice(5).replace('-', '.') : '올렸어요'; });
  items.filter((el) => !POSTED[el.dataset.id]).forEach((el) => todo.appendChild(el));
  items.filter((el) => POSTED[el.dataset.id]).sort((a, b) => POSTED[b.dataset.id].localeCompare(POSTED[a.dataset.id])).forEach((el) => done.appendChild(el));
  if (!todo.children.length) todo.innerHTML = '<p class="n">올릴 글을 모두 올렸습니다.</p>';
}
async function save() {
  if (!sb || !uid) return;
  await sb.from('docs').upsert({ owner: uid, collection: 'naver', id: 'posted', data: { posted: POSTED, cleared: Object.keys(BAKED).filter((k) => !POSTED[k]), at: new Date().toISOString() }, updated_at: new Date().toISOString() }, { onConflict: 'owner,collection,id' });
}
document.addEventListener('click', async (ev) => {
  const b = ev.target.closest('.ck'); if (!b) return;
  if (!uid) { alert('관리자 계정으로 로그인한 뒤 눌러 주세요. (밸류노트 앱에서 로그인 → 관리자 → 블로그 글)'); return; }
  const id = b.closest('.it').dataset.id;
  if (POSTED[id]) { if (!confirm('올림 표시를 지울까요?')) return; delete POSTED[id]; } else POSTED[id] = today();
  render(); await save();
});
(async () => {
  render();
  try {
    const C = window.HAEJA_CONFIG || {}; sb = window.supabase.createClient(C.SUPABASE_URL, C.SUPABASE_ANON_KEY);
    const { data: { session } } = await sb.auth.getSession(); uid = session?.user?.id || null;
    document.getElementById('who').textContent = uid ? '' : '로그인하지 않은 상태입니다. 올림 표시는 로그인 후 저장됩니다.';
    if (!uid) return;
    const { data } = await sb.from('docs').select('data').eq('collection', 'naver').eq('id', 'posted').maybeSingle();
    POSTED = { ...BAKED, ...(data?.data?.posted || {}) };
    for (const k of (data?.data?.cleared || [])) delete POSTED[k];
    render();
  } catch (e) { console.warn(e); }
})();
</script></body></html>`);
