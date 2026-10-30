#!/usr/bin/env python3
"""네이버 블로그(메르 등) 최근 글을 RSS + 모바일 본문으로 받아 scripts/blog/bench/<blogId>/ 에 저장.
   GitHub Actions(bench-blog.yml)에서 실행. 작업 공간에서는 네이버에 접속할 수 없다.
   사용: python3 scripts/blog/bench/fetch_naver.py ranto28 30
"""
import html as H, json, os, re, sys, time, urllib.request

blog = sys.argv[1] if len(sys.argv) > 1 else "ranto28"
maxn = int(sys.argv[2]) if len(sys.argv) > 2 else 30
UA = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
      "Accept-Language": "ko-KR,ko;q=0.9"}
out = os.path.join(os.path.dirname(__file__), blog)
os.makedirs(out, exist_ok=True)

def get(url):
    r = urllib.request.Request(url, headers=UA)
    return urllib.request.urlopen(r, timeout=30).read().decode("utf-8", "ignore")

def strip(s):
    s = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", "", s, flags=re.I)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"</(p|div|li|h\d|tr)>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = H.unescape(s)
    s = re.sub(r"[ \t​]+\n", "\n", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()

rss = get(f"https://rss.blog.naver.com/{blog}.xml")
items = []
for m in re.finditer(r"<item>([\s\S]*?)</item>", rss):
    x = m.group(1)
    t = re.search(r"<title>([\s\S]*?)</title>", x)
    l = re.search(r"<link>([\s\S]*?)</link>", x)
    d = re.search(r"<pubDate>([\s\S]*?)</pubDate>", x)
    title = strip(t.group(1)) if t else ""
    link = l.group(1).strip() if l else ""
    logno = (re.search(r"(\d{10,})", link) or [None, ""])[1]
    items.append({"title": title, "link": link, "pub": d.group(1) if d else "", "logNo": logno})
print("rss items", len(items))

index = []
for it in items[:maxn]:
    if not it["logNo"]:
        continue
    try:
        page = get(f"https://m.blog.naver.com/PostView.naver?blogId={blog}&logNo={it['logNo']}")
    except Exception as e:
        print("fail", it["logNo"], e); continue
    m = re.search(r'class="se-main-container"', page)
    body_html = page[m.start():] if m else page
    # 본문 끝: 댓글·추천 영역 앞까지
    end = re.search(r'class="(post_btn|section_t1|btn_area|_postCommentArea|comment_area)', body_html)
    if end:
        body_html = body_html[:end.start()]
    body = strip(body_html)
    imgs = len(re.findall(r"se-image-resource|se-module-image", body_html))
    date = (re.search(r"(\d{4}\. ?\d{1,2}\. ?\d{1,2}\.)", page) or [None, ""])[1]
    fn = os.path.join(out, f"{it['logNo']}.md")
    with open(fn, "w", encoding="utf-8") as f:
        f.write(f"# {it['title']}\n\n- 날짜: {date} ({it['pub']})\n- 주소: {it['link']}\n- 이미지 수(본문 태그 기준): {imgs}\n- 글자 수: {len(body)}\n\n---\n\n{body}\n")
    index.append({"logNo": it["logNo"], "title": it["title"], "date": date, "chars": len(body), "imgs": imgs})
    print("ok", it["logNo"], it["title"][:40], len(body), imgs)
    time.sleep(1.5)

with open(os.path.join(out, "index.json"), "w", encoding="utf-8") as f:
    json.dump(index, f, ensure_ascii=False, indent=1)
