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
import hashlib
import os
import urllib.request

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(HERE, "data", "raw", "bka")
# BKA files the tables under the reporting year. A new PKS edition appears each
# March and is the one line in this project that has to be changed by hand; the
# version suffix BKA puts on its own links is left off, because the download
# serves the current version without it.
YEAR = 2025

BASE = ("https://www.bka.de/SharedDocs/Downloads/DE/Publikationen/"
        "PolizeilicheKriminalstatistik/%d" % YEAR)

# A desktop user agent is required; the default urllib one is refused.
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

FILES = [
    ("ZR-Bund-Faelle.xlsx",
     "Interpretation/Faelle/T01-ZR-Bund-F%C3%A4lle_xls.xlsx?__blob=publicationFile"),
    ("LA-F-02-HZ.xlsx",
     "Land/Faelle/LA-F-02-T01-Laender-Faelle-HZ_xls.xlsx?__blob=publicationFile"),
]


def main():
    os.makedirs(RAW, exist_ok=True)
    for name, path in FILES:
        req = urllib.request.Request(BASE + "/" + path, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=180) as r:
            body = r.read()
        with open(os.path.join(RAW, name), "wb") as f:
            f.write(body)
        print("%-22s %9d bytes  sha256 %s" % (name, len(body),
                                              hashlib.sha256(body).hexdigest()[:16]))


if __name__ == "__main__":
    main()
