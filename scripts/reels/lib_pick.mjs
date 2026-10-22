// 미리 써 둔 릴스(날짜 없는 대본)를 정해진 칸에 하나씩 꺼내 쓴다 (company-cards 워크플로가 전날 저녁 실행)
// 사용: node scripts/reels/lib_pick.mjs <macro|compare> YYYY-MM-DD HH:MM
//   macro   = 위기 교과서 (화·목 18:00)    compare = 비교·상식 (수 18:00)  — 2026-10-22 하루 최대 3편 편성
// 그 시각에 이미 릴스가 있으면 건너뛴다. 꺼낸 대본은 <dir>/used/ 로 옮긴다. 남은 편수가 2편 이하면 관리자 알림을 남긴다.
import fs from 'node:fs';
import path from 'node:path';
const [kind, ymd, hm] = process.argv.slice(2);
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..', '..');
const DIR = path.join(ROOT, 'scripts', 'reels', kind), SPECS = path.join(ROOT, 'scripts', 'reels', 'specs');
const when = `${ymd}T${hm}:00+09:00`;
const taken = fs.readdirSync(SPECS).filter((f) => f.endsWith('.json')).some((f) => { try { return JSON.parse(fs.readFileSync(path.join(SPECS, f), 'utf8')).scheduled_at === when; } catch (_) { return false; } });
if (taken) { console.log('이미 릴스 있음', when); process.exit(0); }
const files = fs.existsSync(DIR) ? fs.readdirSync(DIR).filter((f) => f.endsWith('.json')).sort() : [];
if (!files.length) { console.log('남은 대본 없음:', kind); process.exit(0); }
const f = files[0], spec = JSON.parse(fs.readFileSync(path.join(DIR, f), 'utf8'));
spec.id = (kind === 'macro' ? 'M' : 'X') + ymd.replace(/-/g, '').slice(2); spec.scheduled_at = when;
fs.writeFileSync(path.join(SPECS, spec.id + '.json'), JSON.stringify(spec, null, 1));
fs.mkdirSync(path.join(DIR, 'used'), { recursive: true }); fs.renameSync(path.join(DIR, f), path.join(DIR, 'used', f));
console.log(JSON.stringify({ id: spec.id, title: spec.title, left: files.length - 1 }));
if (files.length - 1 <= 2) fs.writeFileSync(path.join(ROOT, 'social', 'reels', `low_${kind}.txt`), `${kind} 대본이 ${files.length - 1}편 남았습니다 (${ymd})\n`);
