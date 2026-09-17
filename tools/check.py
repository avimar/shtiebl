"""Pre-push check for shtiebl. Serves the repo locally and drives it with Playwright (Edge).

usage: python tools/check.py [--quick]      (--quick skips the per-post scroll test and Sefaria lookups)
Exit code 0 = safe to push. Every failure is printed.
"""
import json, re, subprocess, sys, time, urllib.parse, urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
PORT = 8765
BASE = f"http://localhost:{PORT}/"
STYLES = ["snapshot_gpt", "snapshot", "cartoon", "cinematic"]
ROUTE_KINDS = ["p"]                         # add "r", "u" as those views ship
SEF_CACHE = ROOT / "tools" / ".sefaria_ok.json"   # refs already verified (gitignored)
QUICK = "--quick" in sys.argv

fails = []
def fail(msg):
    fails.append(msg)
    print("  FAIL", msg)


def check_files(pg):
    """Every by: is a known user; POST_ORDER and content/posts/*.js match."""
    order = pg.evaluate("POST_ORDER")
    files = sorted(p.stem for p in (ROOT / "content" / "posts").glob("*.js"))
    for i in set(order) - set(files): fail(f"POST_ORDER has {i} but no content/posts/{i}.js")
    for i in set(files) - set(order): fail(f"content/posts/{i}.js is not in POST_ORDER")
    missing = pg.evaluate("""() => { const out = new Set();
      const walk = c => { if (!USERS[c.by]) out.add(c.by); (c.replies||[]).forEach(walk); };
      POSTS.forEach(p => { if (!USERS[p.by]) out.add(p.by); p.thread.forEach(walk); });
      return [...out]; }""")
    for u in missing: fail(f"user not in content/users.js: {u}")
    if pg.inner_text("#loadErr"): fail(pg.inner_text("#loadErr"))


def routes(pg):
    out = ["#/"]
    if "p" in ROUTE_KINDS: out += [f"#/p/{i}" for i in pg.evaluate("POST_ORDER")]
    if "r" in ROUTE_KINDS: out += [f"#/r/{s}" for s in pg.evaluate("Object.keys(SUBS)")]
    if "u" in ROUTE_KINDS: out += [f"#/u/{u}" for u in pg.evaluate("Object.keys(USERS)")]
    return out


def open_route(pg, r):
    pg.goto(BASE + "?fresh=" + str(time.time()) + r)
    pg.wait_for_selector("#col .post, #col .c, #col h1, #col .empty", timeout=10000)


def check_views(pg, errors, hrefs):
    """No page errors; every image loads in every style; every .src box has a link."""
    for style in STYLES:
        pg.evaluate(f"localStorage.setItem('shtiebl-pic','{style}')")
        for r in routes(pg):
            errors.clear()
            open_route(pg, r)
            pg.evaluate("document.querySelectorAll('img').forEach(i => i.loading = 'eager')")
            pg.wait_for_function("[...document.images].every(i => i.complete)", timeout=20000)
            for e in errors: fail(f"{r}: pageerror {e}")
            bad = pg.evaluate("[...document.querySelectorAll('#col img')].filter(i => !i.naturalWidth).map(i => i.src)")
            for b in bad: fail(f"[{style}] {r}: image did not load {b}")
            if style == STYLES[0]:
                empty = pg.evaluate("[...document.querySelectorAll('.src')].filter(s => !s.querySelector('a')).map(s => s.textContent)")
                for t in empty: fail(f"{r}: source box without a link: {t}")
                hrefs.update(pg.evaluate("[...document.querySelectorAll('.src a')].map(a => a.href)"))
    pg.evaluate("localStorage.removeItem('shtiebl-pic')")


def check_permalinks(pg):
    for i in pg.evaluate("POST_ORDER"):
        pg.goto(BASE + f"?x={time.time()}#/p/{i}")
        pg.wait_for_selector(".thread")
        y = pg.evaluate("scrollY")
        if y != 0: fail(f"#/p/{i} fresh load: scrollY={y}, expected 0")


def check_scroll(pg):
    """Feed -> thread shows ~22-30% of the image; Back puts the card back where it was."""
    pg.goto(BASE); pg.wait_for_selector(".post")
    for i in pg.evaluate("POST_ORDER"):
        # place the card 150px below the header ourselves (Playwright's auto-scroll fakes offsets)
        pg.evaluate(f"""() => {{ const el = document.getElementById('p-{i}');
            scrollTo(0, el.getBoundingClientRect().top + scrollY - headerH() - 150); }}""")
        before = pg.evaluate(f"document.getElementById('p-{i}').getBoundingClientRect().top")
        box = pg.locator(f"#p-{i} .title").bounding_box()
        pg.mouse.click(box["x"] + 10, box["y"] + box["height"] / 2)
        pg.wait_for_selector(".thread")
        frac = pg.evaluate("""() => { const r = document.querySelector('#col .pimg').getBoundingClientRect();
            return (r.bottom - headerH()) / r.height; }""")
        if not 0.22 <= frac <= 0.30: fail(f"{i}: thread opened with {frac:.0%} of the image visible (want 22-30%)")
        pg.go_back()
        pg.wait_for_selector(f"#p-{i}")
        after = pg.evaluate(f"document.getElementById('p-{i}').getBoundingClientRect().top")
        if abs(after - before) > 2: fail(f"{i}: Back put the card at {after:.0f}px, was {before:.0f}px")


def check_mobile(browser):
    ctx = browser.new_context(viewport={"width": 412, "height": 915}, is_mobile=True, has_touch=True)
    pg = ctx.new_page()
    pg.goto(BASE); pg.wait_for_selector(".post")
    h = pg.evaluate("document.querySelector('header').offsetHeight")
    if h > 50: fail(f"phone header is {h}px tall (max 50)")
    wide = pg.evaluate("document.documentElement.scrollWidth > innerWidth")
    if wide: fail("phone: page scrolls sideways")
    ctx.close()


def sef_ok(url):
    """True if a sefaria.org text link resolves through the v3 API. Search links are skipped."""
    p = urllib.parse.urlparse(url)
    if p.path.startswith("/search"): return True
    ref = urllib.parse.unquote(p.path.lstrip("/"))
    try:
        with urllib.request.urlopen("https://www.sefaria.org/api/v3/texts/" + urllib.parse.quote(ref), timeout=30) as r:
            d = json.load(r)
        # an out-of-range ref silently falls back to the whole book (sections == []), so require real sections + text
        return bool(d.get("sections")) and any(v.get("text") for v in d.get("versions", []))
    except Exception:
        return False


def check_sefaria(hrefs):
    known = set(json.loads(SEF_CACHE.read_text())) if SEF_CACHE.exists() else set()
    todo = sorted(h for h in hrefs if "sefaria.org" in h and h.split("?")[0] not in known)
    print(f"  {len(todo)} new Sefaria refs to verify")
    with ThreadPoolExecutor(6) as ex:
        for h, ok in zip(todo, ex.map(sef_ok, todo)):
            if ok: known.add(h.split("?")[0])
            else: fail(f"Sefaria ref does not resolve: {h}")
    SEF_CACHE.write_text(json.dumps(sorted(known), indent=0))


def main():
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--directory", str(ROOT)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge")
            pg = browser.new_page(viewport={"width": 1280, "height": 900})
            errors = []
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.goto(BASE); pg.wait_for_selector(".post")
            hrefs = set()
            print("files + users"); check_files(pg)
            print("views, images, sources"); check_views(pg, errors, hrefs)
            print("permalinks open at top"); check_permalinks(pg)
            if not QUICK: print("feed -> thread -> back, every post"); check_scroll(pg)
            print("phone header"); check_mobile(browser)
            browser.close()
        if not QUICK: print("Sefaria refs"); check_sefaria(hrefs)
    finally:
        srv.terminate()
    print(f"\n{'FAILED: ' + str(len(fails)) + ' problem(s)' if fails else 'OK: all checks passed'}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
