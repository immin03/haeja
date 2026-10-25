// 한국어 AI 문체 점검 (2026-10-26 도입) — 블로그·릴스·쇼츠·롱폼 공통
// 근거: epoko77-ai/im-not-ai (MIT) quick-rules v2 에서 밸류노트 글에 맞는 패턴만 골라 정규식으로 옮김.
// 규칙 설명과 고치는 법은 scripts/CONTENT.md 6절.
//
// 사용:
//   node scripts/humanize_ko.mjs scan <파일|naver/<id>> [...]   AI 문체 패턴 찾기 (✗ 있으면 종료 코드 1)
//   node scripts/humanize_ko.mjs diff <고치기 전> <고친 뒤>       숫자·고유명사 보존, 변경률(30% 경고 / 50% 중단) 확인
//   파일: post.json · 릴스 specs/*.json · 롱폼 원고 .md/.txt/.json 모두 됨
// 다른 스크립트에서: import { scanKo, textFromFile } from '../humanize_ko.mjs'
import fs from 'node:fs';
import path from 'node:path';

const strip = (s) => String(s || '').replace(/\*\*/g, '');
const count = (t, re) => (t.match(new RegExp(re.source, re.flags.includes('g') ? re.flags : re.flags + 'g')) || []).length;
const hits = (t, re) => [...new Set((t.match(new RegExp(re.source, re.flags.includes('g') ? re.flags : re.flags + 'g')) || []).map((x) => x.trim()))];

// lv: 'err' = 사람 글에 거의 없는 표현(바로 고친다) · 'warn' = 몰려 있을 때만 문제(읽고 판단)
// n: 이 횟수 이상일 때만 걸린다
export const RULES = [
  // D. AI 관용구
  { id: 'D-1', lv: 'err', n: 1, re: /결론적으로|종합적으로|요약하자면|요약하면|정리하자면|정리하면/, fix: '결산 접속어는 지우고 바로 말한다' },
  { id: 'D-1b', lv: 'warn', n: 3, re: /따라서|그러므로|이를 통해|이를 바탕으로/, fix: '결산 접속어는 1~2개만 남긴다' },
  { id: 'D-2', lv: 'err', n: 1, re: /시사하는 바가 크|시사점이 크|주목할 만(하|합|한)|주목할 필요|눈여겨볼 필요|매우 중요(하|합|한)|필수적(이|입)|의미가 크(다|습)/, fix: '의의 과장은 지우거나 구체 결론 한 문장으로' },
  { id: 'D-3', lv: 'err', n: 1, re: /(두|세|네|다섯) 가지로 나눌 수|다음과 같(습니다|다|은 )|아래와 같(습니다|다|은 )/, fix: '열거 도입구는 지우고 바로 본론' },
  { id: 'D-6', lv: 'warn', n: 1, re: /(할|볼|살필|챙길|돌아볼) (때|시점|순간)(입니다|이다|다\.)/, fix: '"~할 때입니다" 결말은 구체 동사로' },
  { id: 'D-8', lv: 'warn', n: 2, re: /(중요한|필요한) (것|건)은|(핵심|관건|포인트)은 /, fix: '"핵심은 ~다" 분열문은 주어-서술 직결로' },
  { id: 'D-9', lv: 'warn', n: 2, re: /(로|으로) 이어(집니다|진다|질 수)|직결(됩니다|된다)/, fix: '"~로 이어진다"는 인과를 구체로 쓴다' },
  { id: 'D-9b', lv: 'warn', n: 3, re: /결국/, fix: '"결국"은 한 번만' },
  { id: 'D-10', lv: 'warn', n: 2, re: /(는|은) 이유(입니다|다)\./, fix: '"~하는 이유다" 도치는 "그래서 ~다"로' },
  { id: 'D-12', lv: 'warn', n: 1, re: /과제도 남아|한계도 분명|아쉬운 점도 있/, fix: '문패 문장은 지우고 실제 과제를 바로' },
  { id: 'D-14', lv: 'warn', n: 1, re: /(?<!자본)잠식|청사진|적신호|경고등|신호탄|움켜쥐|뿌리내리|짓누르/, fix: '사전 은유는 명제로("잠식한다" → "점유율을 뺏는다")' },
  { id: 'A-21', lv: 'err', n: 1, re: /단순한? [^.?!]{1,20}(을|를) 넘어/, fix: '"단순한 X를 넘어 Y"는 "X만이 아니라 Y다"로' },
  { id: 'D-7', lv: 'warn', n: 2, re: /에서 [^\s.]{1,10}(으로|로)의 (전환|변화|이동)/, fix: '"X에서 Y로의 전환"은 직접 단언으로' },
  // A. 번역투
  { id: 'A-3', lv: 'warn', n: 2, re: /에 있어(서)? /, fix: '"~에 있어"는 "~에서"로' },
  { id: 'A-5', lv: 'warn', n: 3, re: /와 관련(하여|해서|된)|과 관련(하여|해서|된)/, fix: '"~와 관련하여"는 "~에"·"~의"로' },
  { id: 'A-6', lv: 'warn', n: 3, re: /에 기반(하여|해|한)|(을|를) 바탕으로/, fix: '"~에 기반하여"는 "~로"·"~을 보고"로' },
  { id: 'A-7', lv: 'warn', n: 2, re: /(을|를) 가지고 있(다|습|는)/, fix: '"경쟁력을 가지고 있다" → "경쟁력이 강하다"' },
  { id: 'A-8', lv: 'err', n: 1, re: /되어지|되어진|되어집/, fix: '이중 피동은 단일 피동·능동으로' },
  { id: 'A-8c', lv: 'warn', n: 2, re: /지게 (되었|됐|된|되는|됩니)/, fix: '"~지게 된다"는 단일 동사로' },
  { id: 'A-8b', lv: 'warn', n: 2, re: /보여지|보여집|보여진/, fix: '"보여진다" → "보인다"' },
  { id: 'A-9', lv: 'warn', n: 2, re: /에 의해(서)? /, fix: '"~에 의해"는 행위자를 주어로' },
  { id: 'A-19', lv: 'warn', n: 2, re: /에서의 |에로의 |으로의 |에의 |으로부터의 /, fix: '이중 조사는 절로 풀어 쓴다' },
  { id: 'A-20', lv: 'warn', n: 3, re: /(되고|지고) 있(다|습|는)/, fix: '"~되고 있다"는 일부를 "~졌다"로' },
  { id: 'A-22', lv: 'warn', n: 1, re: /(것|점)(은|이) (분명|명확)(하|합|한)/, fix: '"~은 분명하다"는 명제를 바로 단언' },
  { id: 'A-24', lv: 'warn', n: 2, re: /더 이상 /, fix: '"더 이상"은 "이제"로' },
  { id: 'A-15', lv: 'warn', n: 3, re: /(을|를) (보여 ?줍니다|보여 ?준다|제공합니다|제공한다|가져옵니다|가져온다)/, fix: '추상 주어 + 만능 동사는 구체 주어로' },
  // C·I·H·J. 구조·형식명사·장식
  { id: 'C-11', lv: 'warn', n: 6, errAt: 8, re: /(?<!그리|그러)(고|며|지만|면서|아서|어서|해서),/, fix: '연결어미 뒤 쉼표는 뺀다' },
  { id: 'C-8', lv: 'warn', n: 3, re: /(것이|게) 아니라|가 아니라 |이 아니라 /, fix: '"A가 아니라 B" 대구는 한 번만 살린다' },
  { id: 'I-2', lv: 'warn', n: 1, re: /주목할 점은|눈여겨볼 점은|흥미로운 점은/, fix: '"주목할 점은 ~"은 직설로' },
  { id: 'I-3', lv: 'warn', n: 3, re: /다는 (것|뜻|말)(입니다|이다|이죠|이에요)/, fix: '"~다는 것이다"는 "~다"로' },
  { id: 'I-7', lv: 'warn', n: 2, re: /다는 (분석|평가|전망)(입니다|이다)/, fix: '출처 없는 "~다는 분석이다"는 직접 서술로' },
  { id: 'H-4', lv: 'warn', n: 3, re: /(^|[\s"'(])즉[ ,]/, fix: '"즉"은 두 번까지' },
  { id: 'F-5', lv: 'warn', n: 3, re: /[가-힣]+적 (함의|기반|의미|관점|측면|요소|가치|역할|맥락|차원)/, fix: '"~적 N" 추상 체인은 풀어 쓴다' },
  { id: 'G-1', lv: 'warn', n: 4, re: /(로|으로) (보입니다|보인다|판단됩니다|판단된다|여겨집니다|여겨진다)/, fix: '같은 추측 종결 반복 — 유보는 두고 형태만 바꾼다(단정 전환 금지)' },
  { id: 'J-3', lv: 'warn', n: 4, re: /[가-힣a-z0-9)] — [가-힣]/, fix: '문장마다 대시 부가설명 금지' },
];

// 문장 리듬: 길이가 고르고 긴 문장이 없으면 AI 리듬(E-1), 같은 종결어미 5연속(E-2)
function rhythm(text) {
  const out = [];
  const paras = text.split(/\n+/).map((x) => x.trim()).filter((x) => x.length > 80);
  const ss = text.split(/(?<=[.?!])\s+/).map((x) => x.trim()).filter((x) => x.length >= 8 && /[가-힣]/.test(x));
  if (ss.length >= 12) {
    const L = ss.map((x) => x.length), m = L.reduce((a, b) => a + b, 0) / L.length;
    const cv = Math.sqrt(L.reduce((a, b) => a + (b - m) ** 2, 0) / L.length) / m;
    if (cv < 0.33) out.push({ id: 'E-1', lv: 'warn', n: 1, c: 1, ex: [`문장 길이 편차 ${cv.toFixed(2)}`], fix: '문단마다 짧은 문장 1~2개, 이어 붙인 긴 문장 1개를 섞는다' });
    let run = 1, worst = 1, end = '';
    for (let i = 1; i < ss.length; i++) {
      const e = (s) => s.replace(/[.?!"'”’)\s]+$/, '').slice(-3);
      if (e(ss[i]) === e(ss[i - 1])) { run++; if (run > worst) { worst = run; end = e(ss[i]); } } else run = 1;
    }
    if (worst >= 6) out.push({ id: 'E-2', lv: 'warn', n: 1, c: worst, ex: [`"~${end}" ${worst}문장 연속`], fix: '종결어미를 바꾼다(~죠·~거든요·명사 종결·질문)' });
  }
  void paras;
  return out;
}

// 영어 괄호 병기 반복(B-1)
function parenEnglish(text) {
  const m = [...text.matchAll(/[가-힣]+\(([A-Za-z][A-Za-z .&-]{1,30})\)/g)].map((x) => x[1].trim());
  const dup = [...new Set(m.filter((x, i) => m.indexOf(x) !== i))];
  return dup.length ? [{ id: 'B-1', lv: 'warn', n: 1, c: dup.length, ex: dup, fix: '영어 병기는 첫 등장 한 번만' }] : [];
}

export function scanKo(text) {
  const t = strip(text);
  const out = [];
  for (const r of RULES) {
    const c = count(t, r.re);
    if (c >= r.n) out.push({ ...r, lv: r.errAt && c >= r.errAt ? 'err' : r.lv, c, ex: hits(t, r.re).slice(0, 5) });
  }
  return [...out, ...rhythm(t), ...parenEnglish(t)];
}

// 글자만 모은다: 사실 표·태그·주소·이미지 이름 등은 빼고 사람이 읽는 문장만
const SKIP = new Set(['facts', 'tags', 'src', 'img', 'href', 'link', 'url', 'kind', 'alt', 'id', 'slug', 'plan_review', 'voice', 'bgm', 'font', 'color', 'file', 'path', 'audio']);
function collect(v, key, out) {
  if (SKIP.has(key)) return;
  if (typeof v === 'string') { if (/[가-힣]/.test(v) && v.length >= 10 && !/^— Editor/.test(v)) out.push(v); return; }
  if (Array.isArray(v)) { for (const x of v) collect(x, key, out); return; }
  if (v && typeof v === 'object') for (const [k, x] of Object.entries(v)) collect(x, k, out);
}
export function textFromFile(f) {
  let file = f;
  if (fs.existsSync(f) && fs.statSync(f).isDirectory()) file = path.join(f, 'post.json');
  const raw = fs.readFileSync(file, 'utf8');
  if (!file.endsWith('.json')) return raw;
  const j = JSON.parse(raw), out = [];
  if (Array.isArray(j.blocks)) { // 블로그 post.json: 본문 블록만 (고지 note 는 고정 문구라 뺀다)
    if (j.title) out.push(j.title);
    for (const b of j.blocks) for (const k of ['h', 'p', 'quote']) if (b[k] && b[k] !== '— Editor: Luciano') out.push(b[k]);
    for (const b of j.blocks) if (b.summary) out.push(...b.summary);
  } else collect(j, '', out);
  return out.join('\n');
}

// ── 변경 확인: 숫자·고유명사는 그대로인가, 얼마나 바꿨나 ─────────────
const toks = (s) => strip(s).split(/\s+/).filter(Boolean);
function lcs(a, b) {
  let prev = new Array(b.length + 1).fill(0);
  for (let i = 1; i <= a.length; i++) {
    const cur = [0];
    for (let j = 1; j <= b.length; j++) cur[j] = a[i - 1] === b[j - 1] ? prev[j - 1] + 1 : Math.max(prev[j], cur[j - 1]);
    prev = cur;
  }
  return prev[b.length];
}
const numsOf = (s) => (strip(s).match(/\d[\d,.]*(%|%p|배|원|달러|억|조|만|년|월|일|점)?/g) || []).map((x) => x.replace(/[.,]$/, ''));
const bag = (arr) => arr.reduce((m, x) => (m[x] = (m[x] || 0) + 1, m), {});
export function diffKo(before, after) {
  const a = toks(before), b = toks(after);
  const rate = 1 - lcs(a, b) / Math.max(a.length, 1);
  const na = bag(numsOf(before)), nb = bag(numsOf(after));
  const lost = Object.keys(na).filter((k) => (nb[k] || 0) < na[k]);
  const added = Object.keys(nb).filter((k) => (na[k] || 0) < nb[k]);
  // 고유명사 후보: 영문 대문자 단어·괄호 앞 한글 이름·따옴표 안 말
  const names = (s) => new Set([...(strip(s).match(/[A-Z][A-Za-z0-9&.]{1,}/g) || []), ...[...strip(s).matchAll(/"([^"]{2,30})"/g)].map((x) => x[1])]);
  const nA = names(before), nB = strip(after);
  const lostNames = [...nA].filter((x) => !nB.includes(x));
  return { rate, lost, added, lostNames };
}

// ── CLI ─────────────────────────────────────────────
const isMain = process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname);
if (isMain) {
  const [cmd, ...args] = process.argv.slice(2);
  if (cmd === 'scan' && args.length) {
    let bad = 0;
    for (const f of args) {
      const r = scanKo(textFromFile(f));
      console.log(`\n[${f}] AI 문체 ${r.length ? r.length + '건' : '없음'}`);
      for (const x of r) console.log(`  ${x.lv === 'err' ? '✗' : '!'} ${x.id} ${x.c}회 ${x.ex.join(' / ')} → ${x.fix}`);
      bad += r.filter((x) => x.lv === 'err').length;
    }
    process.exit(bad ? 1 : 0);
  } else if (cmd === 'diff' && args.length === 2) {
    const d = diffKo(textFromFile(args[0]), textFromFile(args[1]));
    const pct = Math.round(d.rate * 100);
    console.log(`변경률 ${pct}% ${pct > 50 ? '✗ 50% 초과 — 고친 판을 버리고 다시' : pct > 30 ? '! 30% 초과 — 문체만 고쳤는지 다시 확인' : '✓'}`);
    console.log(d.lost.length ? `✗ 사라진 숫자: ${d.lost.join(', ')}` : '✓ 숫자 그대로');
    if (d.added.length) console.log(`! 새로 생긴 숫자: ${d.added.join(', ')} (문체 손질에서 숫자를 더하지 않는다)`);
    console.log(d.lostNames.length ? `! 사라진 이름·인용: ${d.lostNames.join(', ')}` : '✓ 이름·인용 그대로');
    process.exit(pct > 50 || d.lost.length ? 1 : 0);
  } else {
    console.error('사용법: node scripts/humanize_ko.mjs scan <파일|naver/id> ... | diff <전> <후>');
    process.exit(1);
  }
}
