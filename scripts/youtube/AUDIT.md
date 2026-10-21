# 유튜브 API 심사 신청서 (YouTube API Services – Audit and Quota Extension Form)

목적: API로 올린 영상이 '비공개 고정'되는 제한을 풀기 위한 심사. 할당량(하루 100개 업로드)은 지금으로 충분하므로 **추가 할당량은 요청하지 않는다.**

신청서 주소: https://support.google.com/youtube/contact/yt_api_form
결과: 보통 몇 주 안에 이메일로 연락이 온다. 추가 질문이 오면 그 메일을 그대로 Claude에게 붙여 주면 된다.

---

## 1. 신청 전에 준비할 것 (10분)

1. **화면 녹화 1개 (1~2분, 소리 없어도 됨).** 유튜브 비공개(일부 공개 'unlisted')로 올리고 링크를 신청서에 붙인다.
   녹화할 순서:
   1. valuenote.co.kr 접속 → 맨 아래 '개인정보처리방침' → **12. YouTube API 서비스 이용** 부분을 보여 준다.
   2. 관리자 페이지 → SNS 탭 → 유튜브 카드의 '연결' 버튼 → 구글 로그인·권한 동의 화면(권한 3개가 보이게) → 연결됨 표시.
   3. 관리자 페이지 → **유튜브 검수** 탭 → 영상 하나를 재생 → 제목·설명 확인 → '승인' 버튼.
   4. 마지막에 유튜브 스튜디오에서 그 채널(밸류노트 ValueNote)의 영상 목록을 잠깐 보여 준다.
2. **구글 클라우드 프로젝트 ID.** console.cloud.google.com 상단 프로젝트 선택 창에 보이는 ID (프로젝트 번호는 983810071354).
3. 연락받을 이메일 (구글 클라우드 프로젝트 소유자 계정 권장).

---

## 2. 항목별 답 (영어 칸에는 아래 영어 문장을 그대로 붙여 넣기)

| 항목 | 답 |
|---|---|
| Organization name | ValueNote (밸류노트) |
| Organization website | https://valuenote.co.kr |
| Contact email | (본인 이메일) |
| Country | South Korea |
| Google Cloud project number | 983810071354 |
| Google Cloud project ID | (콘솔에서 복사) |
| API client name | ValueNote YouTube Publisher |
| Is the API client used internally only? | Yes — it is used only by ValueNote staff to publish videos to ValueNote's own channel. |
| YouTube channel(s) | https://www.youtube.com/@valuenote_korea (Channel ID UCXh2Zs40HIrLZK5GTrHyYSQ) |
| APIs used | YouTube Data API v3, YouTube Analytics API |
| Requesting additional quota? | No. The default quota is sufficient. We are requesting an audit so that videos uploaded through the API are not locked as private. |

### Describe your API client / use case
> ValueNote (valuenote.co.kr) is a Korean investment-education service that scores listed companies using criteria derived from Warren Buffett, Charlie Munger and Benjamin Graham. We produce our own educational videos (long-form explainers and Shorts) about companies and markets.
>
> Our internal tool renders each video, then places it in a review queue inside our admin page. A staff member watches every video and approves it manually. Only approved videos are uploaded, via videos.insert, to our own channel (@valuenote_korea), with the title, description, tags, thumbnail and scheduled publish time the reviewer approved. After publishing, the tool posts one pinned comment from our own channel (commentThreads.insert) that lists data sources and a disclaimer.
>
> We also read basic YouTube Analytics reports for our own channel (views, watch time, subscribers per video) to decide which topics to make next. This data is shown only to our staff in the admin page.
>
> The tool is not offered to the public and acts only on the single channel we own.

### Which API methods / scopes and why
> - youtube.upload — videos.insert and thumbnails.set to publish approved videos to our own channel.
> - youtube.force-ssl — commentThreads.insert to post a pinned sources/disclaimer comment on our own videos, and videos.update to fix typos in titles or descriptions.
> - yt-analytics.readonly — reports.query for our own channel's performance (views, watch time, subscribers gained) per video.
> - channels.list (mine=true) — to confirm which channel was connected.

### How is YouTube data stored, refreshed and deleted?
> We store only: the OAuth refresh token for our own channel (encrypted at rest in our Supabase database, access restricted to server functions), our channel ID/title/handle, the IDs of videos we uploaded, and daily aggregated analytics numbers for our own videos.
> Analytics data is refreshed daily and kept for at most 30 days, after which it is deleted or replaced. If the channel is disconnected or access is revoked (https://myaccount.google.com/permissions), the stored token and channel data are deleted within 7 days.
> We do not store or process any other users' YouTube data, and we do not share YouTube data with third parties.

### Do end users see YouTube data? Is there a login?
> No public end users. Only ValueNote staff can access the admin page, which requires our own staff login. The screencast linked below shows the full flow.

### Privacy policy / terms
> Privacy policy (section 12, "YouTube API Services"): https://valuenote.co.kr/privacy.html — includes links to the YouTube Terms of Service, the Google Privacy Policy and the Google security settings page for revoking access.
> Terms of service (Article 8): https://valuenote.co.kr/terms.html

### Supporting documents / screencast
> Screencast of the full flow (OAuth consent → review queue → approval → video on our channel): (붙여 넣을 비공개 링크)

---

## 3. 심사 통과 뒤 (Claude가 할 일)
- 승인된 영상을 예약 시간에 자동으로 올리고 고정 댓글을 다는 기능을 켠다 (현재는 '유튜브에 올렸어요' 버튼으로 손으로 표시).
- 승인 전까지는 지금처럼 검수 탭에서 내려받아 유튜브 스튜디오에 직접 올린다.
