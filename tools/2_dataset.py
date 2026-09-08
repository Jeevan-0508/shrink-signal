"""Folds the raw Eurostat series into data/crime.json, the single file the page
reads, and computes the Loss Pressure Index.

    python tools/1_fetch.py && python tools/2_dataset.py

The index is a stated judgement, not a measurement, and the page says so. Its
three components are published separately so anyone can disagree with the
weighting and re-rank on a component instead:

  pressure    where a country's rate sits against the other reporting countries
              in the reference year, averaged over the categories it reports
  trend       change in that rate over the trend window, in percent
  confidence  how completely the country actually reported, A to C

Nothing here invents a value. A country-year that Eurostat does not publish
stays missing, is counted as missing, and drags the confidence grade down.
"""
import json
import os
import statistics

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, "data", "raw")
OUT = os.path.join(HERE, "data", "crime.json")

CATEGORIES = [
    ("ICCS0502", "Theft", "Retail and household theft together — Eurostat does not separate shoplifting"),
    ("ICCS0501", "Burglary", "Includes commercial premises; the closest proxy for break-ins at a site"),
    ("ICCS05012", "Residential burglary", "Households only — published so the commercial share can be reasoned about"),
    ("ICCS05021", "Vehicle theft", "Motorised vehicle or parts; bears directly on yards and fleets"),
    ("ICCS0401", "Robbery", "Theft with force or threat — the violent tail of loss"),
    ("ICCS0701", "Fraud", "Recorded fraud offences, all types"),
    ("ICCS0903", "Cyber offences", "Acts against computer systems"),
    ("ICCS09051", "Organised crime", "Participation in an organised criminal group"),
]

# Ranking uses the most recent year with broad reporting rather than the newest
# year present, because the newest year is always thin and would rank countries
# on who files early.
MIN_CATEGORIES_FOR_REFERENCE = 5
MIN_COUNTRIES_FOR_REFERENCE = 20
TREND_YEARS = 5

# The weighting is a judgement. It is published here, in the dataset and on the
# page, so that it can be argued with.
W_PRESSURE = 0.7
W_TREND = 0.3


def load(code):
    with open(os.path.join(RAW, code + ".json"), encoding="utf-8") as f:
        return json.load(f)


def unpack(d):
    """JSON-stat to {geo: {year: {'nr': n, 'rate': r}}}."""
    dim = d["dimension"]
    units = dim["unit"]["category"]["index"]
    geos = dim["geo"]["category"]["index"]
    years = dim["time"]["category"]["index"]
    n_unit, n_geo, n_year = len(units), len(geos), len(years)
    key = {"NR": "nr", "P_HTHAB": "rate"}
    out = {}
    for flat, value in d["value"].items():
        i = int(flat)
        year_i = i % n_year
        geo_i = (i // n_year) % n_geo
        unit_i = (i // (n_year * n_geo)) % n_unit
        geo = next(g for g, gi in geos.items() if gi == geo_i)
        year = next(y for y, yi in years.items() if yi == year_i)
        unit = next(u for u, ui in units.items() if ui == unit_i)
        out.setdefault(geo, {}).setdefault(year, {})[key[unit]] = value
    return out, {g: d["dimension"]["geo"]["category"]["label"][g] for g in geos}, sorted(years)


def percentile_rank(value, population):
    """Share of the reporting countries this country sits above, 0-100."""
    below = sum(1 for v in population if v < value)
    return round(100.0 * below / (len(population) - 1), 1) if len(population) > 1 else 50.0


def main():
    series = {}
    countries = {}
    years = None
    updated = None
    for code, _, _ in CATEGORIES:
        d = load(code)
        updated = updated or d["updated"]
        s, names, yrs = unpack(d)
        series[code] = s
        countries.update(names)
        years = yrs if years is None else years

    # --- reference year: the latest year that is broadly reported ------------
    reference = None
    for year in reversed(years):
        wide = [
            geo for geo in countries
            if sum(1 for code, _, _ in CATEGORIES
                   if series[code].get(geo, {}).get(year, {}).get("rate") is not None)
            >= MIN_CATEGORIES_FOR_REFERENCE
        ]
        if len(wide) >= MIN_COUNTRIES_FOR_REFERENCE:
            reference = year
            break
    if reference is None:
        raise SystemExit("no year is reported widely enough to rank on")

    trend_from = str(int(reference) - TREND_YEARS)

    # --- the index ----------------------------------------------------------
    pool = {}
    for code, _, _ in CATEGORIES:
        pool[code] = [series[code][g][reference]["rate"]
                      for g in series[code]
                      if series[code].get(g, {}).get(reference, {}).get("rate") is not None]

    window = [str(y) for y in range(int(trend_from), int(reference) + 1)]
    index = []
    for geo, name in sorted(countries.items(), key=lambda kv: kv[1]):
        parts, trends, reported, possible = [], [], 0, 0
        for code, _, _ in CATEGORIES:
            row = series[code].get(geo, {})
            for y in window:
                possible += 1
                if row.get(y, {}).get("rate") is not None:
                    reported += 1
            now = row.get(reference, {}).get("rate")
            if now is None:
                continue
            parts.append(percentile_rank(now, pool[code]))
            then = row.get(trend_from, {}).get("rate")
            if then:
                trends.append(100.0 * (now - then) / then)
        if not parts:
            continue
        coverage = round(100.0 * reported / possible, 1) if possible else 0.0
        grade = "A" if coverage >= 85 else ("B" if coverage >= 60 else "C")
        pressure = round(statistics.mean(parts), 1)
        trend = round(statistics.median(trends), 1) if trends else None
        # A trend is mapped onto 0-100 by clamping at plus or minus 50 percent,
        # so one runaway series cannot dominate the ranking.
        trend_component = 50.0 if trend is None else max(0.0, min(100.0, 50.0 + trend))
        index.append({
            "geo": geo, "name": name,
            "pressure": pressure,
            "trend": trend,
            "categories_reported": len(parts),
            "coverage": coverage,
            "confidence": grade,
            "score": round(W_PRESSURE * pressure + W_TREND * trend_component, 1),
        })
    index.sort(key=lambda r: -r["score"])
    for i, row in enumerate(index, 1):
        row["rank"] = i

    payload = {
        "generated_by": "tools/2_dataset.py",
        "source": {
            "name": "Eurostat, police-recorded offences by offence category (crim_off_cat)",
            "doi": "10.2908/CRIM_OFF_CAT",
            "updated": updated,
            "licence": "Eurostat re-use policy, Commission Decision 2011/833/EU",
            "page": "https://ec.europa.eu/eurostat/databrowser/view/crim_off_cat/default/table",
            "metadata": "https://ec.europa.eu/eurostat/cache/metadata/en/crim_sims.htm",
        },
        "limits": [
            "These are offences recorded by police, not losses. Unreported and "
            "unrecorded crime is missing, so every figure is a floor.",
            "Eurostat publishes no shoplifting category. Theft covers retail and "
            "household together, so this is crime pressure on a market, not retail shrink.",
            "Recording practice differs between countries. Eurostat warns that "
            "levels are not strictly comparable across borders; trends within one "
            "country are the sounder reading.",
            "The index weighting is a stated judgement, not a measurement. Its "
            "three components are published separately so it can be re-ranked.",
            "Rates in very small countries swing on small absolute changes. Read "
            "Luxembourg, Liechtenstein, Malta, Cyprus and Iceland with that in mind.",
            "Some national series contain breaks where a counting rule changed. A "
            "step in a single year is more likely to be a definition change than a "
            "real jump, so read the shape of a line rather than one year against "
            "the next.",
        ],
        "index_definition": {
            "reference_year": reference,
            "trend_window": trend_from + "-" + reference,
            "weights": {"pressure": W_PRESSURE, "trend": W_TREND},
            "trend_clamp_percent": 50,
            "confidence": {"A": "coverage 85% or better", "B": "60-85%", "C": "below 60%"},
        },
        "categories": [{"code": c, "label": l, "note": n} for c, l, n in CATEGORIES],
        "countries": countries,
        "years": years,
        "series": series,
        "index": index,
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, indent=1, sort_keys=False)
    print("reference year %s, trend %s, %d countries ranked, %d categories"
          % (reference, payload["index_definition"]["trend_window"], len(index), len(CATEGORIES)))
    print("top five:", ", ".join("%s %s" % (r["name"], r["score"]) for r in index[:5]))
    print("wrote", OUT, os.path.getsize(OUT), "bytes")


if __name__ == "__main__":
    main()
