from playwright.sync_api import sync_playwright
import json
old=json.load(open('/tmp/shot/e12.json')); old.pop('markets',None)
def route(r):
    u=r.request.url
    if "www/index.html" in u: r.fulfill(path="/tmp/sim/app.html", content_type="text/plain")
    elif "index.json" in u: r.fulfill(body=json.dumps({"dates":["2026-11-23-12"]}))
    elif "releases" in u: r.fulfill(body=json.dumps({"tag_name":"v1.0.6","assets":[]}))
    else: r.fulfill(path="/tmp/shot/e12.json")
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":390,"height":844})
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.add_init_script(path="/tmp/sim/fakephone.js"); pg.add_init_script(path="/tmp/sim/native-bridge.js")
    pg.add_init_script("localStorage.setItem('brief.cache', JSON.stringify([%s]))" % json.dumps(old, ensure_ascii=False))
    for pat in ["https://raw.githubusercontent.com/**","https://api.github.com/**"]: pg.route(pat, route)
    pg.goto("file:///tmp/sim/app.html", wait_until="commit")
    pg.wait_for_timeout(1500)
    print("tabs:", pg.eval_on_selector_all(".tab", "e=>e.slice(0,3).map(x=>x.textContent)"))
    print("errors:", errs); b.close()
