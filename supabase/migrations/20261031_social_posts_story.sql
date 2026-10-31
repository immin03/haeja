-- 인스타 게시 뒤 같은 콘텐츠를 스토리로 자동 게시 (2026-10-31)
alter table social_posts
  add column if not exists story_status text,      -- null: 대상 아님(옛 글) / pending / processing / posted / failed / skipped
  add column if not exists story_container text,
  add column if not exists story_media_id text,
  add column if not exists story_error text,
  add column if not exists story_at timestamptz,
  add column if not exists story_mode text;         -- video / image
alter table social_posts alter column story_status set default 'pending';
insert into app_config(key, value) values ('instagram_story_paused', 'false'::jsonb)
  on conflict (key) do nothing;
