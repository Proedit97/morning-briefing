from playwright.sync_api import sync_playwright
import json, time
def route(r):
    u=r.request.url
    if "www/index.html" in u: r.fulfill(path="/tmp/sim/app.html", content_type="text/plain")
    elif "index.json" in u: r.fulfill(body=json.dumps({"dates":["2026-11-23-12"]}))
    elif "api.github.com" in u: r.fulfill(body=json.dumps({"tag_name":"v1.0.6","assets":[]}))
    else: r.fulfill(path="/tmp/shot/e12.json")
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":390,"height":844})
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.add_init_script(path="/tmp/sim/fakephone2.js"); pg.add_init_script(path="/tmp/sim/native-bridge.js")
    pg.route("https://raw.githubusercontent.com/**", route); pg.route("https://api.github.com/**", route); pg.route("https://fonts.googleapis.com/**", lambda r: r.abort())
    t=time.time(); pg.goto("http://localhost/" if False else "file:///tmp/sim/app.html", wait_until="commit")
    pg.wait_for_function("document.getElementById('intro').classList.contains('hide') && document.querySelectorAll('.story .s-title').length>0", timeout=8000)
    print("뉴스 화면까지 %.2fs" % (time.time()-t), "| platform:", pg.evaluate("window.capacitorExports.Capacitor.getPlatform()"), "| mic shown:", pg.is_visible("#micBtn"))
    pg.click("#playBtn"); pg.wait_for_timeout(1500)
    print("queued:", pg.evaluate("(window.__queued||[]).length"), "last:", pg.evaluate("(window.__queued||[]).slice(-1)[0]")); print("calls:", sorted(set(pg.evaluate("window.__calls"))))
    print("speak calls:", pg.evaluate("window.__calls.filter(c=>c.endsWith('speak')).length"), "| status:", pg.inner_text("#status"))
    pg.click("text=말로 할 수 있는 것"); print("ver:", pg.inner_text("#verLine"))
    print("errors:", errs, "| dateLabel:", pg.inner_text("#dateLabel"))
    b.close()
