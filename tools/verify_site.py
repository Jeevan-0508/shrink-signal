"""Loads the page in a real browser and checks that what the dataset says is what
the page shows.

    python -m http.server 8080 &
    SOE_CHROME=... python tools/verify_site.py
"""
import asyncio
import json
import os

from playwright.async_api import async_playwright

CHROME = os.environ.get("SOE_CHROME") or None
ARGS = ["--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--no-sandbox"]
URL = os.environ.get("SHRINK_URL", "http://127.0.0.1:8080/")
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails = []


def ck(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + ("  " + str(extra) if extra else ""))
    if not cond:
        fails.append(name)


async def main():
    with open(os.path.join(HERE, "data", "crime.json"), encoding="utf-8") as f:
        d = json.load(f)

    async with async_playwright() as pw:
        b = await pw.chromium.launch(executable_path=CHROME, args=ARGS)
        pg = await b.new_page(viewport={"width": 1400, "height": 1000})
        errs = []
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        bad = []
        pg.on("response", lambda r: bad.append((r.status, r.url)) if r.status >= 400 else None)
        await pg.goto(URL, wait_until="load")
        await pg.wait_for_function("window.SHRINK && window.SHRINK.data", timeout=60000)
        await pg.wait_for_timeout(1200)

        rows = await pg.eval_on_selector_all("#idxbody tr", "e=>e.length")
        ck("every ranked country is in the table", rows == len(d["index"]),
           str(rows) + " rows for " + str(len(d["index"])) + " countries")

        limits = await pg.eval_on_selector_all("#limits li", "e=>e.length")
        ck("every limitation is on the page", limits == len(d["limits"]), limits)

        prov = await pg.eval_on_selector("#prov", "e=>e.textContent")
        ck("the source and DOI are on the page", d["source"]["doi"] in prov, prov[:90])
        cite = await pg.eval_on_selector("#cite", "e=>e.textContent")
        ck("the licence and the Eurostat disclaimer are in the footer",
           "2011/833/EU" in cite and "not responsible" in cite)

        de = next(r for r in d["index"] if r["geo"] == "DE")
        de_row = await pg.evaluate("""() => {
          const tr = [...document.querySelectorAll('#idxbody tr')].find(
            r => r.children[1].textContent.trim() === 'Germany');
          return tr ? {rank: tr.children[0].textContent.trim(),
                       score: tr.children[2].textContent.trim(),
                       highlighted: tr.className.includes('sky')} : null;
        }""")
        ck("Germany is in the table with the score from the dataset",
           de_row and de_row["score"] == ("%.1f" % de["score"]) and de_row["rank"] == str(de["rank"]),
           de_row)
        ck("Germany is highlighted, since the page is read from here",
           de_row and de_row["highlighted"])

        charts = await pg.evaluate(
            "() => [...document.querySelectorAll('canvas')].map(c => "
            "  ({id: c.id, bars: (Chart.getChart(c) || {}).data ? Chart.getChart(c).data.datasets.length : 0}))")
        ck("all three charts rendered", len(charts) == 3 and all(c["bars"] > 0 for c in charts), charts)

        # The bar chart must show only countries that actually reported, never a
        # zero standing in for a missing country.
        bars = await pg.evaluate("""() => {
          const c = Chart.getChart(document.getElementById('bars'));
          return {n: c.data.labels.length, zeros: c.data.datasets[0].data.filter(v => v === 0).length,
                  nulls: c.data.datasets[0].data.filter(v => v == null).length};
        }""")
        reported = sum(1 for g in d["series"]["ICCS0502"]
                       if d["series"]["ICCS0502"][g].get(d["index_definition"]["reference_year"], {}).get("rate") is not None)
        ck("the bar chart shows the reporting countries and no stand-in zeros",
           bars["n"] == reported and bars["zeros"] == 0 and bars["nulls"] == 0,
           str(bars) + " vs " + str(reported) + " reporting")

        # Re-sorting must reorder the table, not silently do nothing.
        order = "() => [...document.querySelectorAll('#idxbody tr')].map(r => r.children[1].textContent.trim())"
        before = await pg.evaluate(order)
        await pg.eval_on_selector("[data-sort=trend]", "e=>e.click()")
        await pg.wait_for_timeout(300)
        after = await pg.evaluate(order)
        want = [r["name"] for r in sorted(
            d["index"], key=lambda r: (r["trend"] is None, -(r["trend"] or 0)))]
        ck("sorting by trend re-ranks the table on the dataset's trend",
           after != before and after == want,
           before[:3] + [" -> "] + after[:3])

        # Back to the default order first, so the documentation screenshot shows
        # the page as a reader first meets it.
        await pg.eval_on_selector("[data-sort=score]", "e=>e.click()")
        await pg.wait_for_timeout(400)
        await pg.screenshot(path=os.path.join(HERE, "docs", "screenshot.png"), full_page=True)
        ck("no 4xx or 5xx", not bad, bad)
        ck("no console errors", not errs, errs)
        await b.close()

    print()
    if fails:
        print("FAILURES:", len(fails), fails)
        raise SystemExit(1)
    print("all site checks passed")


asyncio.run(main())
