from playwright.sync_api import sync_playwright
import json, os
D="/home/claude/morning-briefing/data/"
def route(r):
    u=r.request.url.split("?")[0]
    if "www/index.html" in u: r.fulfill(path="/home/claude/morning-briefing/docs/app/index.html", content_type="text/plain"); return
    if "api.github.com" in u: r.fulfill(body=json.dumps({"tag_name":"v1.0.7","assets":[]})); return
    name=u.split("/data/")[-1]
    r.fulfill(path=D+name) if os.path.exists(D+name) else r.fulfill(status=404, body="no")
with sync_playwright() as p:
    for eng in ("webkit","chromium"):
        try: b=getattr(p,eng).launch()
        except Exception as e: print(eng, "not available:", str(e)[:80]); continue
        ctx=b.new_context(viewport={"width":390,"height":844}, user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1")
        pg=ctx.new_page(); errs=[]; pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.add_init_script("""window.__spoken=[]; if (!window.speechSynthesis || 1) { const ss={speaking:false,pending:false,paused:false,getVoices:()=>[{name:'Yuna',lang:'ko-KR',localService:true,default:true,voiceURI:'Yuna'}],speak(u){window.__spoken.push(u.text); setTimeout(()=>{u.onstart&&u.onstart(); setTimeout(()=>u.onend&&u.onend(),5)},5)},cancel(){},pause(){},resume(){},addEventListener(){},onvoiceschanged:null}; Object.defineProperty(window,'speechSynthesis',{value:ss,configurable:true}); window.SpeechSynthesisUtterance=function(t){this.text=t}; }""")
        for pat in ["https://raw.githubusercontent.com/**","https://api.github.com/**"]: pg.route(pat, route)
        pg.route("https://fonts.googleapis.com/**", lambda r: r.abort())
        pg.goto("file:///home/claude/morning-briefing/docs/app/index.html")
        try:
            pg.wait_for_function("document.querySelectorAll('.story .s-title').length>0", timeout=10000)
        except Exception as e: print(eng, "NO NEWS", errs); b.close(); continue
        pg.wait_for_timeout(800)
        print(eng, "| label:", pg.inner_text("#dateLabel"), "| tabs:", len(pg.query_selector_all(".tab")), "| mic hidden:", pg.evaluate("document.getElementById('micBtn').hidden"))
        pg.click("#playBtn"); pg.wait_for_timeout(2500)
        print(eng, "| spoken chunks:", len(pg.evaluate("window.__spoken")), "| status:", pg.inner_text("#status")[:60])
        pg.screenshot(path=f"/tmp/sim/web_{eng}.png")
        print(eng, "errors:", errs); b.close()
