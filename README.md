# 가치노트 — 웹 버전

지금 claude.ai 아티팩트로 쓰는 가치노트를 내 도메인의 웹사이트로 옮긴 버전이다. 화면과 점수 엔진은 그대로이고, 저장소만 Supabase로 바뀌었다. 기존 데이터(보유 종목 4개, 기업 20개, 스크리너 221개, 뉴스·브리핑·가격 기록)는 `seed/docs.json`에 모두 들어 있다.

## 구조

| 부분 | 쓰는 것 | 하는 일 | 비용 |
|---|---|---|---|
| 화면 | `index.html` (Vercel 배포) | 지금 장부와 같은 화면, 로그인 | 무료 |
| 데이터 | Supabase (`docs` 표 1개) | 내 포트폴리오·기업·일지 저장, 본인만 접근 | 무료 |
| 시세 (화면 열려 있을 때) | `api/quote.js` | 보유 종목·환율을 10분마다 갱신 | 무료 |
| 종가 (매일 2회) | GitHub Actions `daily-prices.yml` | 보유·관심 종목 종가, 차트 기록, 스크리너 221개 가격, 환율 | 무료 |
| 뉴스·분석 (매일 아침) | Claude 예약 작업 | 뉴스, 정성 분석, 버크셔 점검, 급락 점검 | 지금 쓰는 그대로 |

실시간 체결가 수준은 아니다. 화면을 여는 순간과 그 뒤 10분마다 최신가(무료 시세는 약 15분 지연)를 가져오고, 장 마감 뒤에는 종가가 저장된다. 장기 투자 판단에는 이 정도면 충분하다.

## 처음 한 번만 하는 설정 (약 30분)

### 1. Supabase 프로젝트 만들기
1. supabase.com 가입 → New project. 지역은 Northeast Asia (Seoul).
2. 왼쪽 SQL Editor → `supabase/schema.sql` 내용을 통째로 붙여넣고 Run.
3. Authentication → Users → Add user → Create new user: 본인 이메일 입력, "Auto Confirm User" 체크.
4. Authentication → Sign In / Providers → "Allow new users to sign up" 끄기. 이제 나 말고는 아무도 가입할 수 없다.
5. 방금 만든 사용자를 눌러 User UID를 복사해 둔다.
6. Project Settings → API에서 세 값을 복사한다: Project URL, anon public key, service_role key.

### 2. 기존 데이터 옮기기
Cursor에서 이 폴더를 열고 터미널에서:
```bash
npm install
SUPABASE_URL="Project URL" SUPABASE_SERVICE_KEY="service_role key" OWNER_ID="User UID" npm run seed
```
`298 / 298`, `완료`가 나오면 끝이다.

### 3. config.js 채우기
`config.js`에 Project URL과 anon public key를 넣는다. service_role 키는 절대 넣지 않는다.

### 4. GitHub에 올리고 Vercel로 배포
1. GitHub에 비공개 저장소를 만들고 이 폴더를 올린다 (Cursor의 Source Control → Publish to GitHub).
2. vercel.com → Add New → Project → 그 저장소 선택 → Deploy. 설정은 건드리지 않는다.
3. 배포 주소(예: `haeja.vercel.app`)를 복사한다. 내 도메인을 쓰려면 Vercel → Settings → Domains에서 연결한다.
4. Supabase → Authentication → URL Configuration → Site URL에 배포 주소를 넣고, Redirect URLs에도 같은 주소를 추가한다.

### 5. 매일 종가 자동 갱신 켜기
GitHub 저장소 → Settings → Secrets and variables → Actions → New repository secret으로 두 개를 넣는다.
- `SUPABASE_URL`: Project URL
- `SUPABASE_SERVICE_KEY`: service_role key

Actions 탭 → "매일 종가 갱신" → Run workflow로 한 번 돌려 보고 초록색이 뜨면 끝이다. 이후 평일 16:10과 06:40(KST)에 자동으로 돈다.

### 6. 아침 뉴스·분석을 웹 DB로 연결
claude.ai → 설정 → 커넥터에서 Supabase를 연결한 뒤, Claude에게 "아침 작업을 Supabase로 바꿔줘"라고 말하면 된다. 그 전까지는 아침 분석이 기존 아티팩트에 계속 쌓인다.

## 쓰는 법
- 배포 주소로 들어가 이메일을 넣으면 로그인 링크가 온다. 한 번 로그인하면 그 기기에서는 계속 열린다.
- 포트폴리오 → 보유 종목 → "종목 추가" / "수정" / "삭제"로 언제든 넣고 뺀다. 핵심·탐험 분류와 할 일은 자동으로 다시 계산된다.
- 휴대폰에서는 브라우저 메뉴의 "홈 화면에 추가"로 앱처럼 쓸 수 있다.

## Cursor로 고칠 때
- 화면과 점수 로직은 모두 `index.html` 한 파일에 있다.
- 점수 엔진은 `index.html`의 `scoreRow`·`evaluate`, 집중 구조 판단은 `autoBucket`·`concPlan`이다.
- 데이터는 `docs` 표의 `collection`·`id`·`data(JSON)` 구조다. 새 기능도 이 구조에 문서를 추가하는 방식으로 만든다.
- 비밀 키(service_role)는 `config.js`나 `index.html`에 절대 넣지 않는다. GitHub Secrets에만 둔다.
