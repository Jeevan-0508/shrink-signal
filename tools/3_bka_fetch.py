"""Pulls the two BKA tables the Germany panel is built on.

    python tools/3_bka_fetch.py

The Bundeskriminalamt publishes the Polizeiliche Kriminalstatistik a year
earlier than Eurostat publishes its harmonised series, and it publishes two
things Eurostat has no field for at all: a shoplifting category and a clearance
rate. Both arrive as xlsx, one national time series and one Bundesland table.

BKA's own reuse condition is that the source, the reporting year AND the file
version are cited, so the version line inside each workbook is carried into
data/germany.json rather than being read once and forgotten.

Writes data/raw/bka/*.xlsx, which 4_germany.py folds into data/germany.json.
The raw files are kept out of git; the built dataset is the artefact.
"""
import datetime
import hashlib
import os
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, "data", "raw", "bka")
# BKA files the tables under the reporting year and publishes a new edition each
# March. The edition this project was built against is pinned as a floor, and the
# newer ones are discovered, so a monthly refresh moves on by itself instead of
# quietly serving a year-old panel. The version suffix BKA puts on its own links
# is left off, because the download serves the current version without it.
PINNED_YEAR = 2025

BASE = ("https://www.bka.de/SharedDocs/Downloads/DE/Publikationen/"
        "PolizeilicheKriminalstatistik/%d")

# A desktop user agent is required; the default urllib one is refused.
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

FILES = [
    ("ZR-Bund-Faelle.xlsx",
     "Interpretation/Faelle/T01-ZR-Bund-F%C3%A4lle_xls.xlsx?__blob=publicationFile"),
    ("LA-F-02-HZ.xlsx",
     "Land/Faelle/LA-F-02-T01-Laender-Faelle-HZ_xls.xlsx?__blob=publicationFile"),
]


def serves(year):
    """Whether BKA is already serving the national time series for this edition."""
    req = urllib.request.Request((BASE % year) + "/" + FILES[0][1],
                                 headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status == 200 and r.read(2)[:2] == b"PK"
    except (urllib.error.HTTPError, urllib.error.URLError, OSError):
        return False


def latest_year():
    """The newest edition BKA actually serves, never older than the pinned one.

    Probing upwards rather than trusting the calendar means the March gap, when
    the new edition is announced before the tables appear, does not break the
    refresh; and a temporary 404 upstream cannot silently downgrade the panel.
    """
    year = PINNED_YEAR
    while year < datetime.date.today().year and serves(year + 1):
        year += 1
    return year


def main():
    os.makedirs(RAW, exist_ok=True)
    year = latest_year()
    print("PKS edition %d%s" % (year, "" if year == PINNED_YEAR else " (newer than the pinned %d)" % PINNED_YEAR))
    for name, path in FILES:
        req = urllib.request.Request((BASE % year) + "/" + path, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=180) as r:
            body = r.read()
        with open(os.path.join(RAW, name), "wb") as f:
            f.write(body)
        print("%-22s %9d bytes  sha256 %s" % (name, len(body),
                                              hashlib.sha256(body).hexdigest()[:16]))


if __name__ == "__main__":
    main()
