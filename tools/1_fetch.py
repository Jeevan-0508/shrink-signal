"""Pulls the raw Eurostat series this project is built on.

One request per offence category, both units in one go (Eurostat publishes the
per-100,000-inhabitants rate itself, so no population join is needed and there
is no chance of dividing by the wrong denominator).

    python tools/1_fetch.py

Writes data/raw/<ICCS code>.json, which 2_dataset.py folds into data/crime.json.
The raw files are kept out of git; the built dataset is the artefact.
"""
import json
import os
import time
import urllib.request

API = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/crim_off_cat"
RAW = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw")
UA = "shrink-signal/1.0 (jeevansiddhabhaktula@gmail.com)"

# The eight categories that bear on commercial loss and the fraud that rides
# alongside it. Eurostat has no shoplifting category, which is the single most
# important limitation of this dataset and is stated on the page itself.
CODES = [
    "ICCS0502",   # Theft
    "ICCS0501",   # Burglary
    "ICCS05012",  # Burglary of private residential premises
    "ICCS05021",  # Theft of a motorised vehicle or parts thereof
    "ICCS0401",   # Robbery
    "ICCS0701",   # Fraud
    "ICCS0903",   # Acts against computer systems
    "ICCS09051",  # Participation in an organised criminal group
]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def main():
    os.makedirs(RAW, exist_ok=True)
    for code in CODES:
        url = "%s?format=JSON&lang=EN&iccs=%s&unit=NR&unit=P_HTHAB" % (API, code)
        d = get(url)
        with open(os.path.join(RAW, code + ".json"), "w", encoding="utf-8") as f:
            json.dump(d, f)
        years = d["dimension"]["time"]["category"]["index"]
        print("%-10s %d countries  %s-%s  %d observations"
              % (code, len(d["dimension"]["geo"]["category"]["index"]),
                 min(years), max(years), len(d["value"])))
        time.sleep(1)


if __name__ == "__main__":
    main()
