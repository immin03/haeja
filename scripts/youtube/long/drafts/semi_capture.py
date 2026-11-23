import asyncio, mimetypes, os, sys
from playwright.async_api import async_playwright
ROOT = '/tmp/hj'
async def main(out_png, width=430, height=932, full=True):
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': width, 'height': height}, device_scale_factor=2)
        async def route(r):
            path = r.request.url.split('https://vn.local', 1)[1].split('?')[0]
            f = ROOT + (path if path != '/' else '/semi.html')
            if os.path.isfile(f):
                await r.fulfill(path=f, content_type=mimetypes.guess_type(f)[0] or 'application/octet-stream')
            else:
                await r.fulfill(status=404, body='')
        await pg.route('https://vn.local/**', route)
        await pg.goto('https://vn.local/semi.html', wait_until='networkidle')
        await pg.wait_for_timeout(2500)
        await pg.add_style_tag(content='.sticky{display:none!important} body{padding-bottom:0!important}')
        await pg.screenshot(path=out_png, full_page=full)
        h = await pg.evaluate('document.body.scrollHeight')
        print('height', h)
        await b.close()
asyncio.run(main(sys.argv[1]))
