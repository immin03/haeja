#!/usr/bin/env python3
"""네이버 블로그 글(naver/<id>/post.json)을 사이트 칼럼(docs trends col-*) 데이터로 바꾼다.

사용: python3 scripts/blog/to_column.py naver/<id> <YYYY-MM-DD> [b|c] > /tmp/col.json
  - 블로그 본문을 그대로 옮긴다(문장 수정 없음). 제목·요약·소제목·문단·표·이미지 순서 유지.
  - 표지(cover)는 data.cover로, 끝 배너(href 있는 이미지)·태그·고지 문구 중복은 뺀다.
  - 칼럼 id = col-<날짜>b (그날 두 번째 블로그 글은 c). 주간 칼럼 col-<날짜>와 겹치지 않게.
운영자 결정(2026-10-27): 매일 블로그 2편(점심·저녁)을 모두 칼럼에 그대로 올린다.
운영자 결정(2026-10-26): "블로그 내용을 그대로 칼럼에 올려 주면 돼. 하루에 하나, 이틀에 하나."
"""
import json, sys, os, datetime

BASE = 'https://www.valuenote.co.kr'
SERIES = {'기업 분석': 'company', '거장의 투자': 'giants', '투자 상식': 'basics',
          '밸류노트 사용법': 'guide', '주간 시장 정리': 'weekly'}


def convert(d, date, suf='b'):
    pid = os.path.basename(os.path.normpath(d))
    p = json.load(open(os.path.join(d, 'post.json')))
    out, cover = [], None
    for b in p['blocks']:
        if 'img' in b:
            url = f"{BASE}/naver/{pid}/{b['img']}"
            if b.get('href'):            # 끝 배너는 칼럼에서 뺀다
                continue
            if b.get('kind') == 'cover' and not cover:
                cover = url
                continue
            out.append(f"![{b.get('cap', '')}]({url})")
        elif 'summary' in b:
            out.append('\n'.join('> ' + s for s in b['summary']))
        elif 'h' in b:
            out.append('■ ' + b['h'])
        elif 'p' in b:
            out.append(b['p'])
        elif 'table' in b:
            t = b['table']
            rows = [t['head']] + t['rows']
            lines = ['| ' + ' | '.join(str(x).replace('|', '/') for x in r) + ' |' for r in rows]
            out.append('\n'.join(lines))
        elif 'link' in b:
            out.append(f"{b.get('text', '')}")
        elif 'note' in b:
            continue                     # 사이트 칼럼은 하단에 고지 문구가 따로 붙는다
    body = '\n\n'.join(x for x in out if x.strip())
    srcs = []
    for f in p.get('facts', []):
        s = f.get('src', '')
        if s.startswith('http') and s not in srcs:
            srcs.append(s)
    return {
        'id': f'col-{date}{suf}',
        'data': {
            'title': p['title'], 'body': body, 'cover': cover,
            'at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'author': 'Editor: Luciano', 'series': SERIES.get(p.get('category'), 'weekly'),
            'from': f'naver/{pid}', 'sources': srcs[:8], 'auto': True,
        },
    }


if __name__ == '__main__':
    print(json.dumps(convert(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else 'b'), ensure_ascii=False))
