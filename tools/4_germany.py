"""Folds the two BKA tables into data/germany.json, the file the Germany panel
reads.

    python tools/3_bka_fetch.py && python tools/4_germany.py

This dataset is deliberately kept apart from data/crime.json and is never merged
into it. BKA counts to German recording rules, Eurostat to a harmonised
international definition, so joining a BKA year onto a Eurostat line would put a
definition change in the middle of a trend and hide it. The panel carries its
own source label and its own caveat for the same reason.

What BKA gives that Eurostat does not:

  * the current reporting year, roughly a year before Eurostat has it
  * a shoplifting category, which the harmonised ICCS list has no code for
  * a clearance rate (Aufklaerungsquote) per offence
  * a Bundesland breakdown

No index is computed here. Ranking sixteen Bundeslaender against each other on a
weighted score would repeat the Eurostat panel's judgement without adding
anything; the numbers are published as they are recorded.
"""
import hashlib
import io
import json
import os

import openpyxl

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, "data", "raw", "bka")
OUT = os.path.join(HERE, "data", "germany.json")

NATIONAL = "ZR-Bund-Faelle.xlsx"
LAENDER = "LA-F-02-HZ.xlsx"

# BKA Straftatenschluessel. An asterisk is BKA's own wildcard for a summary key
# that adds a simple and an aggravated variant together, so '****00' is theft in
# all its forms and '*26*00' is shoplifting simple and aggravated.
CATEGORIES = [
    ("------", "All recorded offences",
     "Every offence in the catalogue, the denominator everything else sits in"),
    ("****00", "Theft, all forms",
     "Simple and aggravated theft together, the broadest loss figure BKA publishes"),
    ("*26*00", "Shoplifting",
     "Retail theft as its own offence - the harmonised ICCS list Eurostat uses has no code for this"),
    ("*10*00", "Theft from commercial and warehouse premises",
     "Offices, workshops, factories and storage rooms - the closest thing in the statistic to loss at a site"),
    ("435*00", "Residential burglary",
     "Wohnungseinbruchdiebstahl, published so the commercial share of burglary can be reasoned about"),
    ("***100", "Car theft",
     "Cars including unauthorised use; bears on yards and fleets"),
    ("210000", "Robbery",
     "Robbery, extortionate robbery and attacks on drivers - the violent tail of loss"),
    ("510000", "Fraud",
     "Recorded fraud offences under sections 263 to 265e StGB"),
]

# Column positions, read off the numbered header row BKA prints in every table.
NAT_YEAR, NAT_CASES, NAT_HZ, NAT_AQ = 2, 3, 4, 9
LAND_NAME, LAND_CASES, LAND_HZ, LAND_AQ = 2, 3, 4, 8

# BKA requires the file version to be cited alongside the source and the
# reporting year, and prints it in a cell near the top of each sheet.
VERSION_SCAN_ROWS = 12


def sheet(name):
    wb = openpyxl.load_workbook(os.path.join(RAW, name), read_only=True, data_only=True)
    return wb, wb[wb.sheetnames[0]]


def digest(name):
    with open(os.path.join(RAW, name), "rb") as f:
        body = f.read()
    return {"file": name, "bytes": len(body), "sha256": hashlib.sha256(body).hexdigest()}


def version_line(rows):
    for row in rows[:VERSION_SCAN_ROWS]:
        for cell in row:
            if isinstance(cell, str) and cell.startswith("V") and "erstellt am" in cell:
                return " ".join(cell.split())
    raise SystemExit("no version line found - BKA requires it to be cited")


def read_national(keys):
    wb, ws = sheet(NATIONAL)
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    series = dict((k, []) for k in keys)
    for row in rows:
        key, year = row[0], row[NAT_YEAR]
        if key in series and isinstance(year, (int, float)):
            series[key].append({
                "year": int(year),
                "cases": int(row[NAT_CASES]),
                "per100k": round(float(row[NAT_HZ]), 1),
                "clearance": round(float(row[NAT_AQ]), 1),
            })
    for k in keys:
        series[k].sort(key=lambda p: p["year"])
        if not series[k]:
            raise SystemExit("national series empty for %s" % k)
    return series, version_line(rows)


# The Bundesland table carries a national row alongside the sixteen. It is held
# out of the ranking and used as a cross-check that the two workbooks agree.
NATIONAL_ROW = "Bundesrepublik Deutschland"


def read_laender(keys):
    wb, ws = sheet(LAENDER)
    rows = list(ws.iter_rows(values_only=True))
    wb.close()
    out = {}
    order = []
    for row in rows:
        key, name = row[0], row[LAND_NAME]
        if key not in keys or not isinstance(name, str) or row[LAND_HZ] is None:
            continue
        name = " ".join(name.split())
        if name not in out:
            out[name] = {}
            order.append(name)
        out[name][key] = {
            "cases": int(row[LAND_CASES]),
            "per100k": round(float(row[LAND_HZ]), 1),
            "clearance": round(float(row[LAND_AQ]), 1),
        }
    return out, order, version_line(rows)


LIMITS = [
    "BKA counts to German recording rules. These figures are not comparable with the Eurostat series on this page and are never joined to it.",
    "Police-recorded offences are a floor, not a total. Retail loss that is written off rather than reported never enters this statistic.",
    "A clearance rate is the share of cases the police closed with a suspect, not the share of loss recovered.",
    "Shoplifting clearance is high because the offence is usually recorded at the moment someone is caught. A high rate here is a recording artefact, not police performance.",
    "Haeufigkeitszahl is per 100,000 inhabitants. City states carry commuter and visitor crime against a resident denominator, so Berlin, Hamburg and Bremen read high by construction.",
    "The population basis changed to the 2022 census from the 2024 reporting year, which shifts every rate slightly against earlier years.",
]


def main():
    keys = [c[0] for c in CATEGORIES]
    national, nat_version = read_national(keys)
    laender, order, land_version = read_laender(keys)
    national_row = laender.pop(NATIONAL_ROW)
    order.remove(NATIONAL_ROW)

    total = national["------"]
    years = [p["year"] for p in total]
    latest = years[-1]

    doc = {
        "meta": {
            "title": "Germany, from the national statistic",
            "source": "PKS Bundeskriminalamt",
            "reporting_year": latest,
            "publisher": "Bundeskriminalamt (BKA)",
            "landing_page": ("https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/"
                             "PolizeilicheKriminalstatistik/PKS%d/pks%d_node.html" % (latest, latest)),
            "reuse_terms": ("Use of the data, whole or in part, is permitted only with the source, "
                            "the reporting year and the file version cited "
                            "(Nutzungshinweis, bka.de)."),
            "versions": {"national_time_series": nat_version, "laender_table": land_version},
            "files": [digest(NATIONAL), digest(LAENDER)],
            "rate_unit": "Haeufigkeitszahl, recorded cases per 100,000 inhabitants",
            "population_basis": "2022 census from the 2024 reporting year; earlier years use the previous basis",
            "years": [years[0], latest],
            "not_comparable_with": ("data/crime.json - Eurostat harmonised ICCS series. "
                                    "The two are shown as separate panels and never spliced."),
        },
        "categories": [{"key": k, "label": lab, "note": note} for k, lab, note in CATEGORIES],
        "national": national,
        "laender": {"order": order, "values": laender, "national_row": national_row},
        "limits": LIMITS,
    }

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1, sort_keys=False)

    for key in keys:
        got, want = national_row[key]["cases"], national[key][-1]["cases"]
        if got != want:
            raise SystemExit("workbooks disagree on %s in %d: %d vs %d" % (key, latest, got, want))

    print("years %d-%d   categories %d   Bundeslaender %d" % (years[0], latest, len(CATEGORIES), len(order)))
    print("version national: %s" % nat_version)
    print("version laender : %s" % land_version)
    for name in order:
        row = laender[name].get("*26*00")
        if row:
            print("  %-26s shoplifting %8.1f /100k   clearance %5.1f%%"
                  % (name, row["per100k"], row["clearance"]))
    print("wrote %s (%d bytes)" % (OUT, os.path.getsize(OUT)))


if __name__ == "__main__":
    main()
