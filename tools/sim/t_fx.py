from playwright.sync_api import sync_playwright
import json, os, sys
D="/home/claude/morning-briefing/data/"
MODE=sys.argv[1]
HANA=[{"code":"FRX.KRWUSD","currencyCode":"USD","date":"2026-11-24","time":"15:54:02","basePrice":1342.5,"changePrice":3.4,"signedChangePrice":-3.4,"signedChangeRate":-0.0025,"change":"FALL","provider":"하나은행"},
      {"code":"FRX.KRWJPY","currencyCode":"JPY","date":"2026-11-24","time":"15:54:02","basePrice":912.35,"signedChangePrice":2.1,"signedChangeRate":0.0023,"change":"RISE","currencyUnit":100,"provider":"하나은행"},
      {"code":"FRX.KRWNZD","currencyCode":"NZD","date":"2026-11-24","time":"15:54:02","basePrice":781.2,"signedChangePrice":0,"signedChangeRate":0,"change":"EVEN","provider":"하나은행"}]
ER={"result":"success","time_last_update_unix":1795392001,"rates":{"KRW":1345.9,"JPY":147.2,"NZD":1.72,"USD":1}}
def route(r):
    u=r.request.url
    if "dunamu" in u:
        return r.fulfill(body=json.dumps(HANA), headers={"Access-Control-Allow-Origin":"*"}) if MODE=="hana" else r.abort()
    if "open.er-api" in u: return r.fulfill(body=json.dumps(ER), headers={"Access-Control-Allow-Origin":"*"})
    if "yahoo" in u: return r.abort()
    u=u.split("?")[0]
    if "www/index.html" in u: return r.fulfill(path="/tmp/sim/app.html", content_type="text/plain")
    if "api.github.com" in u: return r.fulfill(body=json.dumps({"tag_name":"v1.0.7","assets":[]}))
    name=u.split("/data/")[-1]
    r.fulfill(path=D+name) if os.path.exists(D+name) else r.fulfill(status=404, body="no")
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":390,"height":844})
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    import re as _re; pg.route(_re.compile(r"^https://.*"), route)
    pg.goto("file:///tmp/sim/app.html")
    pg.wait_for_function("document.querySelectorAll('.story .s-title').length>0", timeout=8000); pg.wait_for_timeout(1500)
    print(MODE, "| fx:", pg.inner_text("#fx").replace("\n"," / "))
    pg.evaluate("document.getElementById('fx').scrollIntoView()"); pg.wait_for_timeout(200); pg.screenshot(path=f"/tmp/sim/fx_{MODE}.png", clip={"x":0,"y":0,"width":390,"height":420})
    pg.fill("#askInput","환율 알려줘"); pg.press("#askInput","Enter"); pg.wait_for_timeout(800)
    print(MODE, "| answer:", pg.evaluate("(document.querySelector('.answer, #answer')||{}).innerText||''")[:200])
    print("tab:", pg.eval_on_selector_all(".tab[aria-pressed=true]","e=>e.map(x=>x.textContent)"), "errors:", errs); b.close()
