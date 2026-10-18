// 네이버 블로그 붙여넣기용 페이지 만들기
// 사용: node scripts/blog/naver_page.mjs naver/<글 id>
//   naver/<글 id>/post.json 을 읽어 naver/<글 id>.html 과 naver/<글 id>/photos.zip 을 만든다.
// post.json = { "title": "...", "tags": ["..."], "blocks": [
//     {"h": "소제목"}, {"p": "문단. **굵게** 가능"}, {"img": "01.png", "cap": "사진 설명"},
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

// 네이버 편집기가 잘 받아들이는 단순한 태그만 쓴다 (p, b, img, blockquote, a)
const body = post.blocks.map((b) => {
  if (b.h) return `<p><b>■ ${inline(b.h)}</b></p>`;
  if (b.p) return `<p>${inline(b.p)}</p>`;
  if (b.img) return `<p><img src="${imgUrl(b.img)}" alt="${esc(b.cap || '')}" width="720"></p>${b.cap ? `<p><span style="color:#888888;font-size:13px">${esc(b.cap)}</span></p>` : ''}`;
  if (b.quote) return `<blockquote><p>"${esc(b.quote)}"</p>${b.src ? `<p>— ${esc(b.src)}</p>` : ''}</blockquote>`;
  if (b.link) return `<p><a href="${esc(b.link)}">${esc(b.text || b.link)}</a></p>`;
  if (b.note) return `<p><span style="color:#888888;font-size:13px">${esc(b.note)}</span></p>`;
  if (b.summary) return `<blockquote><p><b>3줄 요약</b></p>${b.summary.map((x) => `<p>· ${inline(x)}</p>`).join('')}</blockquote>`;
  if (b.table) return `<table border="1" cellpadding="8" style="border-collapse:collapse;width:100%"><thead><tr>${b.table.head.map((x) => `<th style="background:#F3EEE3">${esc(x)}</th>`).join('')}</tr></thead><tbody>${b.table.rows.map((r) => `<tr>${r.map((x) => `<td>${inline(x)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
  if (b.sources) return `<p><b>참고한 자료</b></p>${b.sources.map(([n, u]) => `<p><span style="font-size:13px">· ${esc(n)} <a href="${esc(u)}">${esc(u.replace(/^https?:\/\//, '').slice(0, 60))}</a></span></p>`).join('')}`;
  return '';
}).join('\n<p><br></p>\n');
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
.top{background:var(--navy);color:#F3EEE3;padding:14px 16px;font-weight:800}.top span{color:#E4C78D}
main{max-width:760px;margin:0 auto;padding:16px 16px 60px}
.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px;margin:14px 0}
h2{font-size:15px;color:var(--muted);margin:0 0 8px;font-weight:700}
.row{display:flex;gap:10px;align-items:flex-start;justify-content:space-between}
.btn{font:inherit;font-weight:800;font-size:15px;border:0;border-radius:12px;padding:11px 16px;background:var(--navy);color:#fff;cursor:pointer;white-space:nowrap}
.btn.gold{background:linear-gradient(90deg,#C99A50,#E4C78D);color:#0A1322}
.btn.ok{background:#2E8B62}
.ttl{font-size:20px;font-weight:800}
.steps{margin:0;padding-left:20px;color:#3A4352}.steps li{margin:4px 0}
#art{border:1px dashed var(--line);border-radius:12px;padding:14px}#art img{max-width:100%;height:auto;border-radius:8px}
#art blockquote{margin:0;padding:10px 14px;border-left:3px solid var(--gold);background:#FBF5EA}#art table{font-size:14px}#art th,#art td{border:1px solid var(--line);text-align:left}
.ph{display:grid;grid-template-columns:repeat(3,1fr);gap:8px}.ph a{display:block}.ph img{width:100%;border-radius:8px;display:block}
.small{font-size:13px;color:var(--muted)}
</style></head><body><div class="top">Value<span>Note</span> · 네이버 블로그 붙여넣기</div><main>
<section class="card"><h2>올리는 순서 (PC 권장)</h2><ol class="steps">
<li>네이버 블로그 <b>글쓰기</b>를 연다.</li>
<li>아래 <b>제목 복사</b> → 제목 칸에 붙여넣기.</li>
<li><b>본문 복사</b> → 본문 칸을 한 번 누르고 붙여넣기 (Ctrl+V). 사진도 함께 들어간다.</li>
<li>사진이 빠졌으면 <b>사진 모두 받기</b>로 받아서 [사진] 위치에 넣는다.</li>
<li><b>태그 복사</b> → 발행 화면의 태그 칸에 붙여넣기 → 발행.</li></ol></section>
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
