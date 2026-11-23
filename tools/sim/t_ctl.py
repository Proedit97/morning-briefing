from playwright.sync_api import sync_playwright
import json
def route(r):
    u=r.request.url
    if "www/index.html" in u: r.fulfill(path="/tmp/sim/app.html", content_type="text/plain")
    elif "index.json" in u: r.fulfill(body=json.dumps({"dates":["2026-11-23-12"]}))
    elif "releases" in u: r.fulfill(body=json.dumps({"tag_name":"v1.0.6","assets":[]}))
    else: r.fulfill(path="/tmp/shot/e12.json")
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":390,"height":844})
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.add_init_script("window.__slow=1"); pg.add_init_script(path="/tmp/sim/fakephone2.js"); pg.add_init_script(path="/tmp/sim/native-bridge.js")
    for pat in ["https://raw.githubusercontent.com/**","https://api.github.com/**"]: pg.route(pat, route)
    pg.goto("file:///tmp/sim/app.html", wait_until="commit")
    pg.wait_for_function("document.querySelectorAll('.story .s-title').length>0", timeout=8000); pg.wait_for_timeout(2000)
    pg.evaluate("window.__hold=true")
    pg.click("#playBtn"); pg.wait_for_timeout(30)
    pg.click("#stopBtn"); pg.wait_for_timeout(300)
    print("after stop playing:", pg.evaluate("document.getElementById('status').textContent"))
    pg.click("#nextBtn"); pg.wait_for_timeout(30)
    print("next queued first:", pg.evaluate("(window.__queued||[])[0]"))
    pg.wait_for_timeout(1500)
    pg.fill("#askInput", "주식 알려줘"); pg.press("#askInput", "Enter"); pg.wait_for_timeout(300)
    print("stock queued:", pg.evaluate("window.__queued"))
    pg.evaluate("window.Capacitor.fromNative({callbackId: window.__listeners.remoteStop, pluginId:'NativeVoice', methodName:'addListener', success:true, data:{}, save:true})"); pg.wait_for_timeout(200)
    print("remote stop:", pg.inner_text("#status"))
    print("errors:", errs); b.close()
