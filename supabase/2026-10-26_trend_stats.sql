-- 트렌드 대시보드 통계 (2026-10-26 운영자): "어떤 흐름이, 어떤 키워드가 더 많이 됐고 이런 것들을 표나 통계로 쉽게 볼 수 있었으면."
-- 영상별 하루 증가량(전날 스냅샷이 있으면 실제 차이, 처음 본 영상은 조회수 ÷ 올린 지 며칠로 추정)을
-- 카테고리·검색어·제목 단어·날짜로 묶어 돌려준다. 쇼츠(90초 미만)는 뺀다.
create or replace function public.trend_stats(p_days int default 14)
returns jsonb language plpgsql stable security definer set search_path to 'public' as $f$
declare today date := (now() at time zone 'Asia/Seoul')::date;
declare d0 date := today - greatest(least(p_days, 60), 2) + 1;
declare last_day date; prev_day date;
begin
  if not (public.is_admin() or session_user = 'postgres') then raise exception 'not admin'; end if;
  select max(day) into last_day from trend_snaps;
  select max(day) into prev_day from trend_snaps where day < last_day;
  return (
  with s as (
    select ts.video_id, ts.day, ts.views, ts.taken_at,
           lag(ts.views) over w as pv, lag(ts.taken_at) over w as pt
    from trend_snaps ts where ts.day >= d0 - 1
    window w as (partition by ts.video_id order by ts.day)
  ), g as (
    select s.video_id, s.day, v.title, lower(coalesce(v.channel, '')) as channel, v.cats, v.queries, v.lang,
           (s.pv is null) as est,
           case when s.pv is not null then greatest(s.views - s.pv, 0) / greatest(extract(epoch from s.taken_at - s.pt) / 86400.0, 0.25)
                else s.views / greatest(extract(epoch from s.taken_at - coalesce(v.published_est, v.first_seen)) / 86400.0, 1) end as growth
    from s join trend_videos v using (video_id)
    where s.day >= d0
      and not (v.length_text ~ '^\d{1,2}:\d\d$' and split_part(v.length_text, ':', 1)::int * 60 + split_part(v.length_text, ':', 2)::int < 90)
  ), cat_day as (
    select g.day, c as cat, sum(g.growth) as growth, count(*) as videos, bool_and(g.est) as est
    from g, unnest(g.cats) c group by g.day, c
  ), q_day as (
    select g.day, q, sum(g.growth) as growth, count(*) as videos
    from g, unnest(g.queries) q group by g.day, q
  ), words as (
    -- 제목 단어: 기호로 자르고 흔한 조사를 떼고, 2글자 이상·불용어 제외. 하루 증가량으로 가중.
    select g.day, w, sum(g.growth) as growth, count(distinct g.video_id) as videos,
           count(distinct g.video_id) filter (where position(w in g.channel) > 0) as in_ch
    from g, lateral (
      -- 조사를 뗀 뒤 1글자만 남으면(물가→물, 주가→주) 원래 단어를 쓴다
      select distinct case when char_length(st) >= 2 then st else lower(t) end as w
      from regexp_split_to_table(g.title, '[^0-9A-Za-z가-힣]+') t,
           lateral (select regexp_replace(lower(t), '(은|는|이|가|을|를|의|에|에서|로|으로|과|와|도|만|까지|부터|이다|입니다|했다|한다|하는|하면|해야|됩니다|된다)$', '') as st) z
    ) x
    where g.day in (last_day, prev_day) and char_length(w) >= 2 and w !~ '^[0-9]+(년|월|일|원|만|억|위|부|편|가지|개)?$'
      and w not in ('진짜','지금','됩니다','얼마나','인포맥스라이브','이것','무엇','어떻게','하나','모든','이유','이렇게','정말','그냥','결국','이제','오늘','내일','방송','1부','2부','3부','풀버전','대표','교수','소장','이사','위원','박사',
                    'to','of','in','on','is','my','it','be','we','do','at','by','or','an','if','so','up','me','he','us',
                    'the','and','for','you','your','are','this','that','with','what','why','how','its','not','will','just','into','from','has','have','was','about','right','now','going')
    group by g.day, w
  )
  select jsonb_build_object(
    'days', (select jsonb_agg(d order by d) from (select distinct day d from g) x),
    'last_day', last_day, 'prev_day', prev_day,
    'cat_series', coalesce((select jsonb_agg(jsonb_build_object('day', day, 'cat', cat, 'growth', round(growth), 'videos', videos, 'est', est) order by day, cat) from cat_day), '[]'),
    'queries', coalesce((select jsonb_agg(x order by (x->>'growth')::numeric desc) from (
        select jsonb_build_object('q', tq.q, 'cat', tq.cat, 'lang', tq.lang,
          'growth', round(coalesce((select growth from q_day where q = tq.q and day = last_day), 0)),
          'prev', round((select growth from q_day where q = tq.q and day = prev_day)),
          'videos', coalesce((select videos from q_day where q = tq.q and day = last_day), 0),
          'hot', (select count(*) from trend_hot h where h.flag is not null and tq.q = any(h.queries)),
          'spark', (select jsonb_agg(coalesce(round(qd.growth), 0) order by dd) from generate_series(greatest(d0, last_day - 6), last_day, interval '1 day') dd
                    left join q_day qd on qd.q = tq.q and qd.day = dd::date)) x
        from trend_queries tq where tq.active) y), '[]'),
    'words', coalesce((select jsonb_agg(jsonb_build_object('w', w, 'growth', round(growth), 'videos', videos,
          'prev', round((select w2.growth from words w2 where w2.w = w1.w and w2.day = prev_day))) order by growth desc)
        -- 3개 이상 영상에 나오고, 채널 이름에서 온 단어(KBS·크랩 등)는 뺀다
        from (select * from words where day = last_day and videos >= 3 and in_ch * 2 < videos order by growth desc limit 25) w1), '[]'),
    'stocks', coalesce((select jsonb_agg(jsonb_build_object('src', a.src, 'rank', a.rank, 'name', a.name, 'code', a.code, 'change', a.change,
          'prev_rank', b.rank, 'days_in', (select count(distinct c.day) from trend_stocks c where c.src = a.src and c.code = a.code and c.day > last_day - 14))
          order by a.src, a.rank)
        from trend_stocks a left join trend_stocks b on b.src = a.src and b.code = a.code and b.day = (select max(day) from trend_stocks where day < a.day)
        where a.day = (select max(day) from trend_stocks)), '[]')
  ));
end $f$;
revoke all on function public.trend_stats(int) from public, anon;
grant execute on function public.trend_stats(int) to authenticated;
