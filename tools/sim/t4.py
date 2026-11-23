from playwright.sync_api import sync_playwright
import json
def route(r):
    u=r.request.url
    if "www/index.html" in u: r.fulfill(path="/tmp/sim/app12.html", content_type="text/plain; charset=utf-8", headers={"Access-Control-Allow-Origin":"*"})
    elif "index.json" in u: r.fulfill(body=json.dumps({"dates":["2026-11-23-12"]}))
    elif "releases" in u: r.fulfill(body=json.dumps({"tag_name":"v1.0.6","assets":[]}))
    else: r.fulfill(path="/tmp/shot/e12.json")
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":390,"height":844}, device_scale_factor=2)
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.add_init_script(path="/tmp/sim/fakephone.js"); pg.add_init_script(path="/tmp/sim/native-bridge.js")
    for pat in ["https://raw.githubusercontent.com/**","https://api.github.com/**"]: pg.route(pat, route)
    pg.goto("file:///tmp/sim/app11.html", wait_until="commit")
    pg.wait_for_function("document.querySelectorAll('.story .s-title').length>0", timeout=8000)
    pg.wait_for_timeout(3000)
    pg.screenshot(path="/tmp/sim/v11.png", full_page=True)
    pg.click("#refreshBtn"); pg.wait_for_timeout(4000)
    pg.wait_for_function("document.querySelectorAll('.story .s-title').length>0", timeout=8000)
    print("ver", pg.evaluate("document.querySelector('meta[name=app-version]').content"), pg.evaluate("document.characterSet"))
    pg.screenshot(path="/tmp/sim/v12.png", full_page=True)
    print(errs); b.close()
