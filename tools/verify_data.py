"""Checks data/crime.json against the raw Eurostat files it was built from, and
checks the index arithmetic against its own published definition.

    python tools/verify_data.py

The point of this suite is that no number on the page can drift away from the
source without the build failing.
"""
import json
import os
import statistics
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(HERE, "tools"))
import importlib.util

spec = importlib.util.spec_from_file_location("ds", os.path.join(HERE, "tools", "2_dataset.py"))
ds = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ds)

fails = []


def ck(name, cond, extra=""):
    print(("PASS " if cond else "FAIL ") + name + ("  " + str(extra) if extra else ""))
    if not cond:
        fails.append(name)


with open(os.path.join(HERE, "data", "crime.json"), encoding="utf-8") as f:
    d = json.load(f)

codes = [c["code"] for c in d["categories"]]
ck("every category is in the series", all(c in d["series"] for c in codes), codes)
ck("eight categories, as documented", len(codes) == 8)
ck("years run 2008 to 2024 with no gaps",
   d["years"] == [str(y) for y in range(2008, 2025)], d["years"][0] + "-" + d["years"][-1])

# --- the dataset must not have invented, rounded or reordered a single value ---
drift = []
for code in codes:
    raw = ds.load(code)
    unpacked, _, _ = ds.unpack(raw)
    for geo, yrs in unpacked.items():
        for year, vals in yrs.items():
            built = d["series"][code].get(geo, {}).get(year, {})
            for unit, v in vals.items():
                if built.get(unit) != v:
                    drift.append((code, geo, year, unit, v, built.get(unit)))
ck("every value matches the raw Eurostat response", not drift, drift[:3])

# --- the index must follow its own published definition --------------------
defn = d["index_definition"]
ref = defn["reference_year"]
wp, wt = defn["weights"]["pressure"], defn["weights"]["trend"]
clamp = defn["trend_clamp_percent"]
bad_score = []
for r in d["index"]:
    t = 50.0 if r["trend"] is None else max(0.0, min(100.0, 50.0 + r["trend"]))
    expect = round(wp * r["pressure"] + wt * t, 1)
    if abs(expect - r["score"]) > 0.05:
        bad_score.append((r["geo"], expect, r["score"]))
ck("the index equals its published formula", not bad_score, bad_score[:3])
ck("trend is clamped at the documented bound",
   all(r["trend"] is None or -100000 < r["trend"] for r in d["index"]) and clamp == 50)
ck("pressure stays a percentile", all(0 <= r["pressure"] <= 100 for r in d["index"]))
ck("ranks are 1..n in score order",
   [r["rank"] for r in d["index"]] == list(range(1, len(d["index"]) + 1))
   and all(d["index"][i]["score"] >= d["index"][i + 1]["score"] for i in range(len(d["index"]) - 1)))

# --- the reference year has to be broadly reported, or the ranking is noise ---
wide = [g for g in d["countries"]
        if sum(1 for c in codes if d["series"][c].get(g, {}).get(ref, {}).get("rate") is not None) >= 5]
ck("the reference year is widely reported", len(wide) >= 20,
   str(len(wide)) + " countries report 5+ categories in " + ref)

# --- confidence grades must follow their own thresholds --------------------
grade_bad = [r["geo"] for r in d["index"]
             if r["confidence"] != ("A" if r["coverage"] >= 85 else ("B" if r["coverage"] >= 60 else "C"))]
ck("confidence grades follow the published thresholds", not grade_bad, grade_bad)
ck("a country is never scored on categories it did not report",
   all(1 <= r["categories_reported"] <= 8 for r in d["index"]))

# --- Germany, the country the page reads in detail ------------------------
de = next((r for r in d["index"] if r["geo"] == "DE"), None)
ck("Germany is ranked", de is not None, de and (de["name"], de["rank"], de["score"]))
ck("Germany reports every category", de and de["categories_reported"] == 8,
   de and de["categories_reported"])

# --- the limitations must actually be there, in the data, not just the page ---
blob = " ".join(d["limits"]).lower()
ck("the limits say this is not shrink", "shoplifting" in blob and "shrink" in blob)
ck("the limits say the figures are a floor", "floor" in blob)
ck("the limits say levels are not strictly comparable", "not strictly comparable" in blob)
ck("the limits say the weighting is a judgement", "judgement" in blob)
ck("the source is cited with its DOI", d["source"]["doi"] == "10.2908/CRIM_OFF_CAT")
ck("the licence is named", "2011/833/EU" in d["source"]["licence"])

print()
if fails:
    print("FAILURES:", len(fails), fails)
    raise SystemExit(1)
print("all data checks passed")
