from playwright.sync_api import sync_playwright
import json, os
D="/home/claude/morning-briefing/data/"
def route(r):
    u=r.request.url.split("?")[0]
    if "www/index.html" in u: r.fulfill(path="/tmp/sim/app.html", content_type="text/plain"); return
    if "releases" in u: r.fulfill(body=json.dumps({"tag_name":"v1.0.7","assets":[]})); return
    name=u.split("/data/")[-1]
    if os.path.exists(D+name): r.fulfill(path=D+name)
    else: r.fulfill(status=404, body="no")
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":390,"height":844})
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.add_init_script(path="/tmp/sim/fakephone2.js"); pg.add_init_script(path="/tmp/sim/native-bridge.js")
    for pat in ["https://raw.githubusercontent.com/**","https://api.github.com/**"]: pg.route(pat, route)
    pg.goto("file:///tmp/sim/app.html", wait_until="commit")
    pg.wait_for_function("document.querySelectorAll('.story .s-title').length>0", timeout=8000); pg.wait_for_timeout(1500)
    print("day options:", pg.eval_on_selector_all("#daySel option","e=>e.map(x=>x.textContent)"))
    pg.click("#arcBtn"); pg.wait_for_timeout(800)
    print("count:", pg.inner_text("#arcCount"), "| days:", pg.eval_on_selector_all(".arc-day","e=>e.map(x=>x.textContent)"))
    pg.screenshot(path="/tmp/sim/arc.png")
    pg.fill("#arcQ","이강인"); pg.wait_for_timeout(200)
    print("search 이강인:", pg.inner_text("#arcCount"), pg.eval_on_selector_all("#arcList .s-title","e=>e.map(x=>x.textContent)"))
    pg.fill("#arcQ",""); pg.click("#arcChips button:has-text('증시')"); pg.wait_for_timeout(200)
    print("chip 증시:", pg.inner_text("#arcCount"))
    pg.click("#arcPlay"); pg.wait_for_timeout(500)
    print("queued:", len(pg.evaluate("window.__queued||[]")), "status:", pg.inner_text("#status"))
    pg.click("#arcClose"); pg.select_option("#daySel", "2026-11-23-12"); pg.wait_for_timeout(800)
    print("old edition:", pg.inner_text("#dateLabel"))
    print("errors:", errs); b.close()
