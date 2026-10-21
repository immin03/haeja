// 관리자 검수 탭에서 롱폼 영상을 바로 재생하기 위한 중계 (GitHub 릴리스 파일은 브라우저가 영상으로 재생하지 않는다)
// GET ?u=<https://github.com/immin03/haeja/releases/download/...mp4>  (Range 요청 그대로 전달, video/mp4 로 응답)
// verify_jwt = false (video 태그는 인증 헤더를 보내지 못한다). 이 저장소의 릴리스 mp4 주소만 허용한다.
import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const ALLOW = /^https:\/\/github\.com\/immin03\/haeja\/releases\/download\/yt-[A-Za-z0-9._-]+\/[A-Za-z0-9._-]+\.mp4$/;

Deno.serve(async (req: Request) => {
  const u = new URL(req.url).searchParams.get("u") || "";
  if (!ALLOW.test(u)) return new Response("not allowed", { status: 400 });
  const h: Record<string, string> = {};
  const range = req.headers.get("range"); if (range) h["Range"] = range;
  const r = await fetch(u, { headers: h, redirect: "follow" });
  const out = new Headers({ "Content-Type": "video/mp4", "Accept-Ranges": "bytes", "Cache-Control": "private, max-age=600", "Access-Control-Allow-Origin": "*" });
  for (const k of ["content-length", "content-range"]) { const v = r.headers.get(k); if (v) out.set(k, v); }
  return new Response(r.body, { status: r.status, headers: out });
});
