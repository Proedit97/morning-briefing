from playwright.sync_api import sync_playwright
import json, os, re, sys
D="/home/claude/morning-briefing/data/"
MODE=sys.argv[1] if len(sys.argv)>1 else "naver"
def kr(code,name,price,chg,rate,dirn): return {"itemCode":code,"stockName":name,"closePrice":f"{price:,}","compareToPreviousClosePrice":str(chg),"fluctuationsRatio":str(rate),"compareToPreviousPrice":{"code":"2" if dirn=="up" else "5","name":"RISING" if dirn=="up" else "FALLING"},"marketStatus":"CLOSE","localTradedAt":"2026-11-24T15:30:00+09:00"}
def route(r):
    u=r.request.url; H={"Access-Control-Allow-Origin":"*"}
    if "polling.finance.naver.com" in u:
        if MODE!="naver": return r.abort()
        codes=u.split("/stock/")[1].split("?")[0].split(",")
        out=[]
        for c in codes:
            if "." in c or c.isalpha(): out.append({"reutersCode":c,"stockName":c.split(".")[0],"closePrice":"165.05","compareToPreviousClosePrice":"39.5","fluctuationsRatio":"31.48","compareToPreviousPrice":{"name":"RISING"},"currencyType":{"code":"USD"}})
            else: out.append(kr(c,"종목"+c,55700,-300,-0.54,"down"))
        return r.fulfill(body=json.dumps({"datas":out}),headers=H)
    if "m.stock.naver.com/api/stocks" in u:
        if MODE!="naver": return r.abort()
        return r.fulfill(body=json.dumps({"stocks":[kr("00%04d"%i,"순위종목%d"%i,10000+i*100,500,3.1,"up") for i in range(1,31)]}),headers=H)
    if "ac.stock.naver.com" in u:
        return r.fulfill(body=json.dumps({"items":[{"code":"005380","name":"현대차","typeCode":"KOSPI","nationCode":"KOR"}]}),headers=H)
    if "yahoo" in u:
        sym=u.split("/chart/")[1].split("?")[0]
        return r.fulfill(body=json.dumps({"chart":{"result":[{"meta":{"regularMarketPrice":101.5,"chartPreviousClose":100.0,"regularMarketTime":1795410000}}]}}),headers=H)
    if "dunamu" in u or "open.er-api" in u: return r.abort()
    u=u.split("?")[0]
    if "www/index.html" in u: return r.fulfill(path="/tmp/sim/app.html", content_type="text/plain")
    if "api.github.com" in u: return r.fulfill(body=json.dumps({"tag_name":"v1.0.7","assets":[]}))
    name=u.split("/data/")[-1]
    r.fulfill(path=D+name) if os.path.exists(D+name) else r.fulfill(status=404, body="no")
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={"width":390,"height":844})
    errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.route(re.compile(r"^https://.*"), route)
    pg.goto("file:///tmp/sim/app.html")
    pg.wait_for_function("document.querySelectorAll('.story .s-title').length>0", timeout=8000); pg.wait_for_timeout(800)
    pg.click(".tab:has-text('증시')"); pg.wait_for_timeout(1200)
    rows=pg.eval_on_selector_all("#stk .stk-row","e=>e.map(x=>x.innerText.replace(/\\n/g,' '))")
    print(MODE,"| watch rows:",len(rows), rows[:2], rows[-1:])
    print("foot:", pg.inner_text("#stk .fx-foot"))
    pg.click("#stk .stk-chips button:has-text('오른 종목')"); pg.wait_for_timeout(600)
    print("오른 종목 rows:", pg.evaluate("document.querySelectorAll('#stk .stk-row').length"))
    pg.click("#stk .stk-chips button:has-text('미국')"); pg.wait_for_timeout(600)
    print("미국:", pg.eval_on_selector_all("#stk .stk-row","e=>e.slice(0,2).map(x=>x.innerText.replace(/\\n/g,' '))"))
    pg.fill("#stkQ","현대"); pg.wait_for_timeout(900)
    print("search:", pg.eval_on_selector_all("#stk .stk-row","e=>e.slice(0,3).map(x=>x.innerText.replace(/\\n/g,' '))"))
    pg.click("#stk .stk-row .star"); pg.wait_for_timeout(300)
    print("watch has 현대차:", pg.evaluate("JSON.parse(localStorage.getItem('brief.watch')||'[]').some(x=>x.name==='현대차')"))
    pg.fill("#stkQ",""); pg.wait_for_timeout(700)
    pg.evaluate("document.getElementById('stk').scrollIntoView()"); pg.wait_for_timeout(200)
    pg.screenshot(path=f"/tmp/sim/stk_{MODE}.png")
    pg.fill("#askInput","삼성전자 얼마야"); pg.press("#askInput","Enter"); pg.wait_for_timeout(900)
    print("voice:", pg.evaluate("(document.querySelector('.answer')||{}).innerText||''").replace("\n"," / ")[:160])
    pg.fill("#askInput","내 종목 알려줘"); pg.press("#askInput","Enter"); pg.wait_for_timeout(900)
    print("voice2:", pg.evaluate("(document.querySelector('.answer')||{}).innerText||''").replace("\n"," / ")[:160])
    print("errors:", errs); b.close()
