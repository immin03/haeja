"""댓글 → DM → 정리본 페이지 (2026-10-21 운영자 요청)

릴스 대본에 "dm" 블록이 있으면
- /g/<릴스 id>.html : 정리본 페이지 (전체 공개, 끝에서 '새 정리본 받기' 이메일 등록 → 카카오 1초 가입으로 이어짐)
- /g/index.html     : 정리본 모음 (자동 DM 도구가 릴스마다 링크를 못 바꿀 때 보내는 공용 링크, 최신순)
- /g/index.json     : 자동 DM 함수(ig-dm)와 관리자 화면이 읽는 목록
을 만든다. 이메일은 Supabase leads 테이블에 쌓인다(익명은 추가만 가능, 읽기 불가).

대본의 "dm" 블록:
  "dm": {
    "keyword": "이자",                       # 댓글 키워드 (짧은 한 단어, 영상 마지막 장면·캡션·자동 DM이 모두 이 말을 쓴다)
    "title": "게티이미지는 왜 무너졌을까",     # 정리본 제목 (없으면 릴스 제목)
    "points": ["…", "…", "…"],              # 핵심 정리 3줄 (완결된 문장)
    "check": ["…", "…", "…"],               # 내 종목에 적용하는 법 (밸류노트에서 실제로 할 수 있는 순서)
    "guide": "N261020c"                      # (선택) 다른 릴스의 정리본을 그대로 쓸 때 그 릴스 id. 이때 points·check는 쓰지 않는다
  }
정리본 본문은 대본의 caption 전체를 쓴다. 인스타 캡션은 build.py가 앞 두 문단 + 댓글 안내로 줄인다.
"""
import os, json, html, datetime as dt

SITE = "https://www.valuenote.co.kr"
EV_KEY = ("eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1zamJyd3l6a2l1ZXFuemplaWNtIiwicm9sZSI6ImFub24i"
          "LCJpYXQiOjE3OTE4NTk0NTcsImV4cCI6MjEwNzQzNTQ1N30.RIq2MRW8bwHQUO_dPeIarujjWcYD_dXn06icr1Mpmuw")
SB = "https://msjbrwyzkiueqnzjeicm.supabase.co"
DISC = "*본 콘텐츠는 투자 교육용 정보이며 특정 종목의 매수·매도 권유가 아닙니다. 적정 주가는 워렌 버핏·그레이엄·찰리 멍거의 방식으로 계산한 결과이며, 이 방식이 늘 맞지는 않습니다."

_BAT = {"0": 1, "1": 1, "2": 0, "3": 1, "4": 0, "5": 0, "6": 1, "7": 1, "8": 1, "9": 0}
def josa(w, a, b):
    c = str(w).strip()[-1:]
    if "가" <= c <= "힣": return a if (ord(c) - 0xAC00) % 28 else b
    if c in _BAT: return a if _BAT[c] else b
    return b

def clean_title(sp):
    t = (sp.get("dm") or {}).get("title") or sp["title"]
    return t.split(" · ", 1)[1] if " · " in t and t.split(" · ")[0] in ("이슈 픽", "리포트 해설", "칼럼") else t

def paragraphs(caption):
    return [p.strip() for p in str(caption or "").split("\n\n") if p.strip()]

def short_caption(sp):
    """인스타 캡션: 앞 두 문단 + 댓글 안내 (전체 내용은 정리본으로)"""
    kw = (sp.get("dm") or {}).get("keyword")
    ps = paragraphs(sp.get("caption"))
    if not kw: return sp.get("caption", "")
    head = ps[:2]
    if len(head) == 2 and len(head[0]) + len(head[1]) > 420: head = head[:1]
    return "\n\n".join(head + [f"💬 댓글에 '{kw}'{josa(kw, '을', '를')} 남기시면 전체 숫자와 내 종목 점검법을 담은 정리본을 DM으로 보내 드립니다."])

def para_html(p):
    p = p.replace("워런 버핏", "워렌 버핏").replace("워런", "워렌")
    lines = p.split("\n")
    if all(l.startswith("· ") for l in lines[1:]) and len(lines) > 1 and lines[1:]:
        head = f"<p>{html.escape(lines[0])}</p>" if not lines[0].startswith("· ") else ""
        items = [l for l in lines if l.startswith("· ")]
        return head + "<ul>" + "".join(f"<li>{html.escape(l[2:])}</li>" for l in items) + "</ul>"
    if all(l.startswith("· ") for l in lines):
        return "<ul>" + "".join(f"<li>{html.escape(l[2:])}</li>" for l in lines) + "</ul>"
    return "<p>" + "<br>".join(html.escape(l) for l in lines) + "</p>"

CSS = """:root{--navy:#0A1730;--navy2:#0E2342;--navy3:#13305A;--gold:#E4C78D;--gold2:#C99A50;--ivory:#F7F2E8;--paper:#FBF8F2;--ink:#14213A;--muted:#5D6779;--line:#E6DFD1;--card:#fff}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"SUIT Variable","SUIT",-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;word-break:keep-all;overflow-wrap:break-word;line-height:1.75;-webkit-font-smoothing:antialiased}
a{color:inherit}button{font:inherit;cursor:pointer}
.wrap{max-width:640px;margin:0 auto;padding:0 16px}
.wm{font-family:"Fraunces",Georgia,serif;font-weight:600;letter-spacing:-.02em;font-size:22px;color:#fff;text-decoration:none;line-height:1.1}
.wm i{font-style:italic;color:var(--gold)}.wm small{display:block;font-family:"SUIT Variable",sans-serif;font-size:10.5px;font-weight:600;color:rgba(247,242,232,.62)}
.hero{background:radial-gradient(120% 80% at 90% 0%,rgba(228,199,141,.2) 0,rgba(228,199,141,0) 55%),linear-gradient(170deg,var(--navy2),var(--navy) 75%);color:var(--ivory);padding:18px 0 30px}
.eyebrow{display:inline-block;margin-top:26px;font-size:12.5px;font-weight:800;letter-spacing:.06em;color:var(--gold);border:1px solid rgba(228,199,141,.4);border-radius:999px;padding:4px 12px}
h1{margin:12px 0 10px;font-size:28px;line-height:1.3;font-weight:850;letter-spacing:-.02em;color:#fff}
.hero p.sub{margin:0;color:rgba(247,242,232,.82);font-size:15.5px}
.inside{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}
.inside span{font-size:13px;font-weight:700;color:var(--gold);background:rgba(228,199,141,.1);border-radius:10px;padding:6px 10px}
main{padding:22px 0 40px}
.lead p,.body p{margin:0 0 14px;font-size:16.5px}
.body ul{margin:0 0 14px;padding-left:20px}.body li{margin:4px 0;font-size:16px}
h2{font-size:19px;margin:30px 0 12px;font-weight:850;letter-spacing:-.01em}
.points{list-style:none;margin:0;padding:0;display:grid;gap:10px}
.points li{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px 14px 48px;position:relative;font-size:15.5px;font-weight:600}
.points li b{position:absolute;left:14px;top:13px;width:24px;height:24px;border-radius:50%;background:var(--navy);color:#FFFFFF;font-size:13px;display:flex;align-items:center;justify-content:center}
.check{counter-reset:c;list-style:none;margin:0;padding:0}
.check li{position:relative;padding:0 0 14px 34px;font-size:15.5px}
.check li:before{counter-increment:c;content:counter(c);position:absolute;left:0;top:2px;width:22px;height:22px;border-radius:7px;background:var(--gold);color:var(--navy);font-weight:850;font-size:12.5px;display:flex;align-items:center;justify-content:center}
.sum{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px 16px 6px;margin:4px 0 8px}
.sum .points li{border:0;background:transparent;padding:4px 0 10px 38px;font-weight:650}
.sum .points li b{left:0;top:5px}
.sum .lbl{font-size:12.5px;font-weight:800;color:var(--gold2);letter-spacing:.04em;margin-bottom:8px}
.toc{margin:18px 0 0;padding:14px 16px;border-left:3px solid var(--gold);background:rgba(228,199,141,.12);border-radius:0 12px 12px 0}
.toc b{display:block;font-size:13px;margin-bottom:4px}.toc a{display:block;font-size:14.5px;text-decoration:none;padding:3px 0;color:var(--ink)}
.tw{overflow-x:auto;-webkit-overflow-scrolling:touch;margin:4px 0 8px;border:1px solid var(--line);border-radius:12px;background:var(--card)}
table{border-collapse:collapse;width:100%;font-size:14px;min-width:100%}
th,td{padding:9px 10px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top;white-space:nowrap}
td:first-child,th:first-child{white-space:normal;min-width:96px}
td:last-child{white-space:normal;min-width:110px}
th{background:var(--navy);color:#fff;font-weight:700;font-size:13px;white-space:nowrap}
tr:last-child td{border-bottom:0}
.src{font-size:12px;color:var(--muted);margin:2px 0 14px}
.warn{background:#FFF6E6;border:1px solid #F0D9A8;border-radius:14px;padding:14px 16px;margin-top:22px}
.warn b{display:block;margin-bottom:4px;font-size:15px}.warn p{margin:0;font-size:15px}
details{border-bottom:1px solid var(--line);padding:12px 0}
summary{font-weight:800;font-size:15.5px;cursor:pointer;list-style:none;position:relative;padding-right:26px}
summary::-webkit-details-marker{display:none}
summary:after{content:"+";position:absolute;right:2px;top:-2px;font-size:20px;color:var(--gold2)}
details[open] summary:after{content:"−"}
details p{margin:8px 0 0;font-size:15.5px;color:#2A3550}
.gbox{margin-top:30px}
.gbox ul{margin:0 0 14px;padding-left:18px;font-size:14px;color:rgba(247,242,232,.86)}
.gbox li{margin:3px 0}
.ok{display:none;font-size:15px;font-weight:700;color:var(--gold)}
.done .ef,.done .agree{display:none}.done .ok{display:block}
.srcs{margin-top:26px;font-size:12.5px;color:var(--muted)}.srcs b{display:block;color:var(--ink);font-size:13px;margin-bottom:4px}
.srcs a{display:block;color:var(--muted);text-decoration:none;padding:2px 0}
.gbox{background:var(--navy);color:var(--ivory);border-radius:18px;padding:20px 18px}
.gbox h3{margin:0 0 6px;font-size:18px;color:#fff}
.gbox p{margin:0 0 14px;font-size:14px;color:rgba(247,242,232,.78)}
.ef{display:flex;gap:8px}
.ef input{flex:1;min-width:0;height:50px;border-radius:13px;border:1px solid rgba(228,199,141,.4);background:rgba(255,255,255,.08);color:#fff;font:inherit;font-size:16px;padding:0 14px;outline:none}
.ef input::placeholder{color:rgba(247,242,232,.5)}.ef input:focus{border-color:var(--gold)}
.btn{display:inline-flex;align-items:center;justify-content:center;gap:6px;height:50px;padding:0 18px;border-radius:13px;border:0;font-weight:800;font-size:15.5px;text-decoration:none;white-space:nowrap}
.btn.gold{background:linear-gradient(90deg,var(--gold2),var(--gold));color:var(--navy)}
.btn.kakao{background:#FEE500;color:#191600;width:100%;height:54px;font-size:16px}
.btn.line{background:transparent;border:1px solid var(--line);color:var(--ink);width:100%}
.agree{display:block;margin-top:10px;font-size:12px;color:rgba(247,242,232,.6);line-height:1.55}
.agree a{color:rgba(247,242,232,.85)}
.err{color:#FFB4AA;font-size:13px;margin-top:8px;min-height:1px}
.cta{margin-top:30px;background:var(--card);border:1px solid var(--line);border-radius:18px;padding:20px 18px}
.cta h3{margin:0 0 6px;font-size:18px}.cta p{margin:0 0 14px;color:var(--muted);font-size:14.5px}
.cta .row{display:grid;gap:8px}
.more{margin-top:26px}.more a{display:block;text-decoration:none;border-bottom:1px solid var(--line);padding:12px 0;font-weight:700;font-size:15px}
.more a small{display:block;font-weight:600;color:var(--muted);font-size:12.5px}
.disc{margin-top:30px;font-size:11.5px;color:var(--muted)}
.list a.card{display:block;text-decoration:none;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;margin-bottom:10px}
.list .kw{display:inline-block;font-size:12px;font-weight:800;color:var(--navy);background:var(--gold);border-radius:8px;padding:2px 8px;margin-bottom:6px}
.list .t{display:block;font-size:16.5px;font-weight:800;line-height:1.45}
.list .d{display:block;font-size:12.5px;color:var(--muted);margin-top:4px}"""

HEAD = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title}</title><meta name="description" content="{desc}">
<meta property="og:type" content="article"><meta property="og:site_name" content="밸류노트 ValueNote">
<meta property="og:title" content="{title}"><meta property="og:description" content="{desc}">
<meta property="og:image" content="{og}"><meta property="og:url" content="{url}"><link rel="canonical" href="{url}">
<link rel="icon" type="image/png" href="/favicon-64.png?v=4"><meta name="theme-color" content="#0A1730">
<style>@font-face{{font-family:"Fraunces";font-style:normal;font-weight:600;font-display:swap;src:url(/fonts/fraunces-latin-600-normal.woff2) format("woff2")}}@font-face{{font-family:"Fraunces";font-style:italic;font-weight:600;font-display:swap;src:url(/fonts/fraunces-latin-600-italic.woff2) format("woff2")}}</style>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/sun-typeface/SUIT@2.0.5/fonts/variable/woff2/SUIT-Variable.css">
<style>{css}</style></head><body>"""

JS = """<script>
(function(){
var SB='%(sb)s',K='%(key)s',G='%(gid)s';
function sid(){try{var v=localStorage.getItem('vn-sid');if(!v){v=(crypto.randomUUID?crypto.randomUUID():String(Math.random()).slice(2)+Date.now()).replace(/-/g,'').slice(0,32);localStorage.setItem('vn-sid',v);}return v;}catch(_){return 'nosid';}}
var q=new URLSearchParams(location.search),src=q.get('utm_source')||(/Instagram/.test(navigator.userAgent)?'ig-dm':'')||'direct';
try{if(src&&!localStorage.getItem('vn-ref'))localStorage.setItem('vn-ref',src);}catch(_){}
var bot=/bot|crawl|spider|headless|preview|facebookexternalhit/i.test(navigator.userAgent)||navigator.webdriver;try{if(q.get('staff')==='1')localStorage.setItem('vn-staff','1');if(localStorage.getItem('vn-staff')==='1')bot=true;}catch(_){}
function ev(path){if(bot)return;try{fetch(SB+'/rest/v1/events',{method:'POST',keepalive:true,headers:{apikey:K,Authorization:'Bearer '+K,'Content-Type':'application/json',Prefer:'return=minimal'},body:JSON.stringify({kind:'engage',sid:sid(),path:path.slice(0,200),ref:src.slice(0,300),device:/Mobi|iPhone|Android/.test(navigator.userAgent)?'모바일':'PC'})}).catch(function(){});}catch(_){}}
var box=document.getElementById('gbox');
var done=false;try{done=localStorage.getItem('vn-lead')==='1';}catch(_){}
if(done&&box)box.classList.add('done');
ev('/g/'+G+':view');
var deep=false;window.addEventListener('scroll',function(){if(deep)return;var h=document.documentElement;if(h.scrollTop+innerHeight>h.scrollHeight*.8){deep=true;ev('/g/'+G+':read80');}},{passive:true});
document.querySelectorAll('a[data-out]').forEach(function(a){a.href=a.href.replace('utm_source=dm','utm_source=dm-'+G);a.addEventListener('click',function(){ev('/g/'+G+':'+a.dataset.out);});});
var f=document.getElementById('ef');if(!f)return;
f.addEventListener('submit',function(e){e.preventDefault();
  var m=document.getElementById('em').value.trim(),er=document.getElementById('er'),b=f.querySelector('button');
  if(!/^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$/.test(m)){er.textContent='이메일 주소를 다시 확인해 주세요.';return;}
  er.textContent='';b.disabled=true;b.textContent='등록 중…';
  fetch(SB+'/rest/v1/leads',{method:'POST',headers:{apikey:K,Authorization:'Bearer '+K,'Content-Type':'application/json',Prefer:'return=minimal'},
    body:JSON.stringify({email:m.toLowerCase().slice(0,200),guide:G,src:src.slice(0,79),sid:sid()})})
  .then(function(r){if(r.ok||r.status===409){try{localStorage.setItem('vn-lead','1');}catch(_){}ev('/g/'+G+':subscribe');if(box)box.classList.add('done');}
    else{throw 0;}})
  .catch(function(){b.disabled=false;b.textContent='새 정리본 받기';er.textContent='잠시 연결이 불안정합니다. 한 번 더 눌러 주세요.';});
});
})();
</script>"""

def top():
    return ('<header class="hero"><div class="wrap"><a class="wm" href="/start?utm_source=dm" data-out="logo">Value<i>Note</i><small>밸류노트</small></a>')

def table_html(t):
    if not t or not t.get("rows"): return ""
    head = "".join(f"<th>{html.escape(str(h))}</th>" for h in t.get("head", []))
    rows = "".join("<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in r) + "</tr>" for r in t["rows"])
    return f'<div class="tw"><table>{"<thead><tr>" + head + "</tr></thead>" if head else ""}<tbody>{rows}</tbody></table></div>'

SUBSCRIBE = (
    '<section class="gbox" id="gbox"><h3>이런 정리본, 앞으로도 계속 받아 보세요</h3>'
    '<p>릴스 한 편으로는 다 담지 못하는 숫자와 원인, 그리고 내 종목에 바로 적용하는 법을 정리본으로 만들고 있습니다. 새 정리본이 나오면 메일로 보내 드립니다.</p>'
    '<ul><li>화제의 기업 분석: 주가 뒤에 숨은 원인까지 숫자로</li><li>시장 신호 해설: 금리·환율·공포지수가 지금 어느 단계인지</li>'
    '<li>워렌 버핏·찰리 멍거의 원칙을 내 종목에 적용하는 법</li></ul>'
    '<form class="ef" id="ef" novalidate><input id="em" type="email" inputmode="email" autocomplete="email" placeholder="이메일 주소" aria-label="이메일 주소">'
    '<button class="btn gold" type="submit">새 정리본 받기</button></form><div class="err" id="er"></div>'
    '<span class="agree">일주일에 한두 통, 정리본과 주간 칼럼만 보내 드립니다. 메일 아래 링크로 언제든 그만 받을 수 있습니다. '
    '<a href="/privacy" target="_blank">개인정보 처리방침</a></span>'
    '<p class="ok">등록했습니다. 다음 정리본부터 메일로 보내 드리겠습니다.</p></section>')

def page(sp, others):
    dm = sp["dm"]; gid = sp["id"]; kw = dm["keyword"]
    title = clean_title(sp); ps = paragraphs(sp.get("caption"))
    pts = [p for p in dm.get("points", []) if p]; chk = [c for c in dm.get("check", []) if c]
    secs = [x for x in dm.get("sections", []) if x.get("h")]; faq = [x for x in dm.get("faq", []) if x.get("q")]
    url = f"{SITE}/g/{gid}"
    desc = (ps[0] if ps else title)[:140]
    tags = [f"핵심 {len(pts)}줄" if pts else "", f"깊이 보기 {len(secs)}편" if secs else "전체 숫자",
            f"내 종목 점검 {len(chk)}단계" if chk else "", f"자주 묻는 질문 {len(faq)}개" if faq else ""]
    out = [HEAD.format(title=html.escape(title + " · 밸류노트 정리본"), desc=html.escape(desc), og=f"{SITE}/social/reels/{gid}/cover.jpg",
                       url=url, css=CSS)]
    out.append(top() + f'<span class="eyebrow">밸류노트 정리본 · 댓글 키워드 \'{html.escape(kw)}\'</span>'
               f'<h1>{html.escape(title)}</h1><p class="sub">릴스에서 다 못 한 숫자와 원인, 내 종목에 바로 적용하는 방법까지 정리했습니다.</p>'
               '<div class="inside">' + "".join(f"<span>{t}</span>" for t in tags if t) + '</div></div></header>')
    out.append('<main class="wrap">')
    if pts:
        out.append('<div class="sum"><div class="lbl">한눈에 보기</div><ol class="points">' + "".join(f"<li><b>{i + 1}</b>{html.escape(p)}</li>" for i, p in enumerate(pts)) + '</ol><div style="height:10px"></div></div>')
    # 깊이 보기(sections)가 있으면 캡션은 앞 두 문단만 도입부로 쓴다(같은 내용을 두 번 읽지 않게, 숫자가 엇갈리지 않게)
    toc = ([] if secs else [("s-reel", "릴스 내용 전체")]) + [(f"s{i}", x["h"]) for i, x in enumerate(secs)]
    if dm.get("wrong"): toc.append(("s-wrong", "이 분석이 틀릴 수 있는 경우"))
    if chk: toc.append(("s-check", "내 종목에 적용하는 법"))
    if faq: toc.append(("s-faq", "자주 묻는 질문"))
    if len(toc) > 3:
        out.append('<nav class="toc"><b>목차</b>' + "".join(f'<a href="#{a}">{html.escape(t)}</a>' for a, t in toc) + '</nav>')
    if secs:
        out.append('<div class="body lead" style="margin-top:20px">' + "".join(para_html(p) for p in ps[:2]) + '</div>')
    else:
        out.append('<h2 id="s-reel">릴스 내용 전체</h2><div class="body">' + "".join(para_html(p) for p in ps) + '</div>')
    for i, x in enumerate(secs):
        out.append(f'<h2 id="s{i}">{html.escape(x["h"])}</h2><div class="body">' + "".join(para_html(p) for p in x.get("p", [])) + '</div>')
        out.append(table_html(x.get("table")))
        if x.get("note"): out.append(f'<p class="src">{html.escape(x["note"])}</p>')
    if dm.get("wrong"):
        out.append(f'<div class="warn" id="s-wrong"><b>이 분석이 틀릴 수 있는 경우</b><p>{html.escape(dm["wrong"])}</p></div>')
    if chk:
        out.append('<h2 id="s-check">내 종목에 적용하는 법</h2><ol class="check">' + "".join(f"<li>{html.escape(c)}</li>" for c in chk) + '</ol>')
    if faq:
        out.append('<h2 id="s-faq">자주 묻는 질문</h2>' + "".join(f'<details><summary>{html.escape(f["q"])}</summary><p>{html.escape(f["a"])}</p></details>' for f in faq))
    out.append('<section class="cta"><h3>내 종목도 같은 기준으로 확인해 보세요</h3>'
               '<p>밸류노트는 600여 개 기업의 점수와 적정 주가를 워렌 버핏·그레이엄·찰리 멍거의 방식으로 매일 계산합니다. 내 종목을 넣으면 같은 기준으로 바로 채점합니다.</p>'
               '<div class="row"><a class="btn kakao" href="/?kakao=1&amp;from=guide&amp;utm_source=dm" data-out="kakao">카카오로 1초 만에 시작하기</a>'
               '<a class="btn line" href="/start?utm_source=dm" data-out="start">밸류노트 먼저 둘러보기</a></div></section>')
    out.append(SUBSCRIBE)
    if others:
        out.append('<div class="more"><h2>다른 정리본</h2>' + "".join(
            f'<a href="/g/{o["id"]}">{html.escape(o["title"])}<small>댓글 키워드 \'{html.escape(o["keyword"])}\'</small></a>' for o in others[:4]) + '</div>')
    if dm.get("sources"):
        out.append('<div class="srcs"><b>참고한 자료</b>' + "".join(
            f'<a href="{html.escape(x["url"])}" target="_blank" rel="noopener">{html.escape(x["t"])}</a>' for x in dm["sources"] if x.get("url")) + '</div>')
    out.append(f'<p class="disc">{DISC}</p></main>')
    out.append(JS % {"sb": SB, "key": EV_KEY, "gid": gid} + "</body></html>")
    return "".join(out)

def index_page(items):
    out = [HEAD.format(title="밸류노트 정리본 모음", desc="릴스에서 다 못 한 숫자와 내 종목 점검법을 정리한 밸류노트 정리본입니다.",
                       og=f"{SITE}/og.png", url=f"{SITE}/g", css=CSS)]
    out.append(top() + '<span class="eyebrow">밸류노트 정리본</span><h1>릴스에서 보신 내용,<br>여기 정리해 두었습니다</h1>'
               '<p class="sub">댓글에 남기신 키워드를 찾아 눌러 주세요. 가장 최근 릴스가 맨 위에 있습니다.</p></div></header><main class="wrap list">')
    for o in items:
        out.append(f'<a class="card" href="/g/{o["id"]}?utm_source=dm"><span class="kw">댓글 키워드 \'{html.escape(o["keyword"])}\'</span>'
                   f'<span class="t">{html.escape(o["title"])}</span><span class="d">{o["date"]}</span></a>')
    out.append('<section class="cta"><h3>내 종목도 같은 기준으로</h3><p>밸류노트는 600여 개 기업의 점수와 적정 주가를 매일 계산합니다.</p>'
               '<div class="row"><a class="btn kakao" href="/?kakao=1&amp;from=guide&amp;utm_source=dm-hub" data-out="kakao">카카오로 1초 만에 시작하기</a></div></section>' + SUBSCRIBE)
    out.append(f'<p class="disc">{DISC}</p></main>')
    out.append(JS % {"sb": SB, "key": EV_KEY, "gid": "hub"} + "</body></html>")
    return "".join(out)

def build(specs, root, now=None):
    """specs: [(path, spec)]. 이미 게시됐거나 오늘 게시될 정리본만 모음·다른 정리본 목록에 보인다(예정 릴스 내용이 미리 노출되지 않게)."""
    now = now or dt.datetime.now(dt.timezone.utc)
    d = os.path.join(root, "g"); os.makedirs(d, exist_ok=True)
    items = []; ref = {}
    specs = list(specs)
    for _, sp in specs:   # 후속 릴스가 다른 릴스 정리본을 쓰면, 모음에서 그 정리본을 후속 릴스 날짜로 위로 올린다
        g_ = (sp.get("dm") or {}).get("guide")
        if g_ and sp.get("approved") is not False:
            w_ = dt.datetime.fromisoformat(sp["scheduled_at"])
            if w_ <= now + dt.timedelta(hours=3): ref[g_] = max(ref.get(g_, w_), w_)
    for _, sp in specs:
        dm = sp.get("dm") or {}
        if not dm.get("keyword") or sp.get("approved") is False: continue
        if dm.get("guide"): continue   # 다른 릴스의 정리본을 그대로 쓰는 릴스(예: 같은 회사 후속 릴스)는 페이지를 따로 만들지 않는다
        when = dt.datetime.fromisoformat(sp["scheduled_at"])
        items.append({"id": sp["id"], "keyword": dm["keyword"], "title": clean_title(sp), "at": sp["scheduled_at"],
                      "date": when.astimezone(dt.timezone(dt.timedelta(hours=9))).strftime("%Y년 %-m월 %-d일"), "_sp": sp, "_when": when,
                      "_rank": max(when, ref.get(sp["id"], when))})
    items.sort(key=lambda x: x["_rank"], reverse=True)
    live = [o for o in items if o["_when"] <= now + dt.timedelta(hours=3)]
    for o in items:
        others = [x for x in live if x["id"] != o["id"]]
        open(os.path.join(d, o["id"] + ".html"), "w", encoding="utf-8").write(page(o["_sp"], others))
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(index_page(live))
    json.dump([{k: v for k, v in o.items() if not k.startswith("_")} for o in items],
              open(os.path.join(d, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return len(items)
