# 제1 원칙 (대표님 지시) — 모든 제작·게시 작업이 가장 먼저 따른다

운영자(최민우) 2026-10-29: "게시하는 방법이 계속 바뀌잖아. 이게 맞는지 나도 계속 검수를 해야 될 거 아니야. 검수할 수 있는 창을 관리자 페이지에 만들어 주고, 아닐 때 내가 바로 피드백해서 업데이트할 수 있는 칸도 만들어 줘. 그게 무조건 우리의 제1 원칙이 되는 거야. 무조건 다 같이 따라야 되는 거고."

## 원칙은 이 파일이 아니라 Supabase에서 읽는다 (2026-11-07 정리)

이 파일에 있던 사본은 11/4 이후 갱신되지 않아 이미 바뀐 원칙(카드뉴스 하루 2~3편, 롱폼 매일 11:30 등)이 그대로 남아 있었다. 그래서 사본을 없애고 원본만 쓴다.

- 원본: Supabase(project msjbrwyzkiueqnzjeicm) docs, collection `agent`, owner = `publisher_id()`. status가 `new`·`applied`인 항목만 따른다.
- 모든 작업: `owner-rules`(공통)를 먼저 읽는다. 그 안의 106번 '읽는 범위'대로 자기 범위 문서를 이어서 읽는다.
  - 롱폼 기획·대본·렌더 → `owner-rules-long`
  - 쇼츠·릴스 제작 → `owner-rules-short`
  - 유튜브 업로드·스튜디오 → `owner-rules-long` + `owner-rules-short`
  - 네이버 블로그·칼럼 → `owner-rules-blog`
  - 카드뉴스 → `owner-rules-card`
  - 브리핑·성과 진단·주간 효율 → `owner-rules-ops` (+ 다루는 채널)
  - 원칙 반영·정리, 전수점검, 애매한 작업 → 전부
- `owner-rules-retired`는 그만 적용한 원칙이라 읽지 않는다.
- 순서: **제1 원칙(DB) > 작업 지시문 > 각 README·FORMAT > 벤치마킹·성과 규칙**. 충돌하면 무조건 제1 원칙을 따른다.
- 이 파일에 원칙 목록을 다시 쓰지 않는다. 새 원칙은 관리자 → 운영 기준(또는 DB `owner-rules`)에만 적는다.

한 번에 읽는 예:

```sql
select id, jsonb_path_query_array(data->'items', '$[*] ? (@.status == "new" || @.status == "applied")') items
from docs where collection = 'agent' and owner = publisher_id() and id in ('owner-rules', 'owner-rules-long');
```
