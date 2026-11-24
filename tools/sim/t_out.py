from playwright.sync_api import sync_playwright
exec(open('/tmp/sim/t_arc.py').read().split("with sync_playwright")[0])
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":390,"height":844})
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.add_init_script(path="/tmp/sim/fakephone2.js"); pg.add_init_script(path="/tmp/sim/native-bridge.js")
    for pat in ["https://raw.githubusercontent.com/**","https://api.github.com/**"]: pg.route(pat, route)
    pg.goto("file:///tmp/sim/app.html", wait_until="commit")
    pg.wait_for_function("document.querySelectorAll('.story .s-title').length>0", timeout=8000); pg.wait_for_timeout(1800)
    print("tabs:", pg.eval_on_selector_all(".tab","e=>e.map(x=>x.textContent)"))
    print("전체 stories:", pg.evaluate("document.querySelectorAll('#list .story').length"))
    for t in ["MBC","SBS","JTBC"]:
        pg.click(f".tab:has-text('{t}')"); pg.wait_for_timeout(300)
        print(t, "| heads:", pg.eval_on_selector_all("#list .arc-day","e=>e.map(x=>x.textContent)"), "| stories:", pg.evaluate("document.querySelectorAll('#list .story').length"))
    pg.click(".tab:has-text('SBS')"); pg.evaluate("document.querySelector('.tabs-wrap').scrollIntoView()"); pg.wait_for_timeout(200); pg.screenshot(path="/tmp/sim/out.png")
    pg.click("#list .arc-list .s-play, #list .group:last-of-type .s-play"); pg.wait_for_timeout(300)
    print("old play queued:", len(pg.evaluate("window.__queued||[]")))
    print("errors:", errs); b.close()
