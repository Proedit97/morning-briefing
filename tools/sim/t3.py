from playwright.sync_api import sync_playwright
import json, sys
NEW = sys.argv[1] == "new"
def route(r):
    u=r.request.url
    if "www/index.html" in u: r.fulfill(path="/tmp/sim/app13.html" if NEW else "/tmp/sim/app.html", content_type="text/plain", headers={"Access-Control-Allow-Origin":"*","Access-Control-Allow-Headers":"*"})
    elif "index.json" in u: r.fulfill(body=json.dumps({"dates":["2026-11-23-12"]}))
    elif "releases" in u: r.fulfill(body=json.dumps({"tag_name":"v1.0.7" if NEW else "v1.0.6","assets":[{"name":"a.apk","browser_download_url":"https://x/a.apk"}]}))
    else: r.fulfill(path="/tmp/shot/e12.json")
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":390,"height":844})
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.add_init_script(path="/tmp/sim/fakephone.js"); pg.add_init_script(path="/tmp/sim/native-bridge.js")
    for pat in ["https://raw.githubusercontent.com/**","https://api.github.com/**"]: pg.route(pat, route)
    pg.route("https://fonts.googleapis.com/**", lambda r: r.abort())
    pg.goto("file:///tmp/sim/app.html", wait_until="commit")
    pg.wait_for_function("document.querySelectorAll('.story .s-title').length>0", timeout=8000)
    pg.wait_for_timeout(3500)
    pg.click("#setBtn"); pg.wait_for_timeout(1500)
    for i in ["sScreen","sApk","sChecked","sEdition","sNext"]: print(i, "|", pg.inner_text("#"+i).replace("\n"," / "))
    pg.screenshot(path=f"/tmp/sim/set_{sys.argv[1]}.png")
    if NEW:
        pg.click("#sScreen button"); pg.wait_for_timeout(1500)
        print("after apply ver:", pg.evaluate("document.querySelector('meta[name=app-version]').content"))
    print("errors:", errs); b.close()
