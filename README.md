# Shrink Signal

A loss-prevention reading of European police-recorded crime. Eight Eurostat
offence categories, 41 countries, 2008 to 2024, folded into a priority order you
can defend in a room — with the reasons it might be wrong printed above the
charts rather than in a footnote.

Then a second panel for Germany from the **Bundeskriminalamt's own statistic**,
which reaches 2025, has a shoplifting category Eurostat has no code for, and
breaks down to the sixteen Bundesländer. The two sources sit side by side and are
never joined, because they count to different rules.

**Live:** https://jeevan-0508.github.io/shrink-signal/

![Shrink Signal](docs/screenshot.png)

## What it measures, and what it does not

It measures **recorded crime pressure on a market**. It does **not** measure
retail shrink, and it does not measure loss.

That is not a caveat added at the end. It is the first thing on the page,
because the gap is real:

- These are offences **recorded by police**. Unreported and unrecorded crime is
  missing, so every figure here is a **floor**, never a total.
- Eurostat publishes **no shoplifting category**. Theft covers retail and
  household together, so nothing in the European panel isolates a store or a
  site. Germany's own statistic does have one, which is part of why the Germany
  panel exists — but recorded shoplifting is still offences reported to police,
  not inventory written off.
- **Recording practice differs between countries.** Eurostat warns that levels
  are not strictly comparable across borders. A trend inside one country is the
  sounder reading, because the practice is broadly constant there.
- Rates in **very small countries** swing on small absolute changes. Luxembourg,
  Liechtenstein, Malta, Cyprus and Iceland need reading with that in mind.
- Some national series contain **breaks** where a counting rule changed. A step in
  a single year is more likely to be a definition change than a real jump.

Anyone who wants true shrink figures needs a retail panel such as EHI or the
Global Retail Theft Barometer. Those are not open data, so they are not in here.
What is in here is public, citable and reproducible from the scripts in `tools/`.

## The Loss Pressure Index

Three components, published separately so the ranking can be argued with rather
than taken on trust.

| Component | What it is |
| --- | --- |
| **Pressure** | Where a country sits as a percentile against every other reporting country in the reference year, averaged over the categories it actually reports |
| **Trend** | Median percentage change across those categories over the trend window, clamped at plus or minus 50 percent so one runaway series cannot dominate |
| **Confidence** | How completely the country reported — A is 85 percent or better, B is 60 to 85, C is below 60. It grades completeness, never accuracy |

Index = `0.7 x pressure + 0.3 x trend`, with the trend mapped onto the same 0-100
range. **Those weights are a judgement, not a finding**, which is why both
components sit in the table next to the score.

The reference year is the most recent year that enough countries report widely
enough to rank on — currently **2024**, with 32 countries reporting at least five
of the eight categories. Ranking on the newest year present would rank countries
on who files first.

A country is only ever scored on the categories it reported, and the count is
shown in the table. Nothing is imputed and no missing value is treated as zero.

## The eight categories

| ICCS code | Category | Why it is here |
| --- | --- | --- |
| `ICCS0502` | Theft | Retail and household together — the closest available signal, and the reason the shrink caveat exists |
| `ICCS0501` | Burglary | Includes commercial premises: break-ins at a site |
| `ICCS05012` | Residential burglary | Households only, published so the commercial share can be reasoned about |
| `ICCS05021` | Vehicle theft | Motorised vehicle or parts — yards and fleets |
| `ICCS0401` | Robbery | The violent tail of loss |
| `ICCS0701` | Fraud | Recorded fraud offences, all types |
| `ICCS0903` | Cyber offences | Acts against computer systems |
| `ICCS09051` | Organised crime | Participation in an organised criminal group |

## Germany, in the European panel

Germany is the country the page reads in detail, and it is one of the few that
reports **all eight categories**, with 97.9 percent coverage over the trend
window — grade **A**. It ranks **13th of 35** on the index: pressure 64.9, trend
+4.0 percent over 2019 to 2024.

Underneath that flat headline the categories move in opposite directions —
recorded theft rose from 1,235 to 1,377 per 100,000 between 2019 and 2024, while
recorded fraud fell from 1,003 to 894. A single national number would have hidden
both, which is why the per-category view exists.

## Germany, from the national statistic

A second panel, from a second authority, on the same page — and deliberately
never joined to the first. The **Bundeskriminalamt's Polizeiliche
Kriminalstatistik** counts to German recording rules rather than the harmonised
international definition, so splicing a BKA year onto a Eurostat line would put a
definition change in the middle of a trend and hide it. The panel carries its own
source label, its own caveats and its own colour, and `verify_site.py` asserts
that the BKA reporting year appears on **no** Eurostat chart.

What BKA gives that Eurostat cannot:

| | Eurostat | BKA PKS |
| --- | --- | --- |
| Latest year | 2024 | **2025** |
| Shoplifting as its own offence | no code exists | yes |
| Clearance rate | no such field | yes, per offence |
| Sub-national detail | Germany is one number | **16 Bundesländer** |
| Years | 2008- | **1987-** |

Eight BKA Straftatenschlüssel, chosen to read as a loss lens. An asterisk is
BKA's own wildcard for a summary key that adds the simple and the aggravated
variant together.

| Key | Category |
| --- | --- |
| `------` | All recorded offences |
| `****00` | Theft, all forms |
| `*26*00` | **Shoplifting** — no equivalent in the ICCS list Eurostat publishes |
| `*10*00` | Theft from commercial and warehouse premises |
| `435*00` | Residential burglary (Wohnungseinbruchdiebstahl) |
| `***100` | Car theft, including unauthorised use |
| `210000` | Robbery and extortionate robbery |
| `510000` | Fraud (§§ 263-265e StGB) |

Recorded shoplifting in 2025 was **458.4 per 100,000**, down 5.5 percent on
2024. The number the European panel structurally cannot show is the spread
underneath it: **Bremen 1,418.7 against Bayern 289.8**, a 4.9x gap inside one
country. The sixteen Bundesländer are checked to add up to the national figure,
and the two BKA workbooks are checked against each other.

Clearance rates are published alongside, with the reason they are easy to
misread: shoplifting clears at roughly 89 percent because the offence is usually
recorded at the moment someone is caught. That is a recording artefact, not
police performance — and a clearance rate is never a recovery rate.

BKA's reuse condition is that the source, the reporting year **and** the file
version are cited, so the version line printed inside each workbook is carried
into `data/germany.json`, onto the page and into the footer, and the verifier
fails if it is missing.

## Why the European panel stops at 2024, and how it stays current

Eurostat publishes this dataset about once a year and runs roughly a year and a
half behind: the release of **2026-04-29** is the one that added **2024**. Asked
directly for 2025, the API returns a valid response with **zero observations** —
the year does not exist yet rather than being missing from this build. On that
cadence 2025 should appear in spring 2027.

For Germany alone the 2025 figures already exist, which is what the second panel
is for.

A monthly GitHub Action (`.github/workflows/refresh.yml`) re-pulls both sources,
rebuilds both datasets, runs both verifiers, and **commits only if the numbers
actually moved**. So a quiet month leaves no commit, and the day Eurostat adds
2025 the page picks it up on its own — including a new reference year, since that
is derived from the data rather than hard-coded. The one thing that is not
automatic is the PKS edition: BKA files each year under its own path, so a new
edition means changing `YEAR` in `tools/3_bka_fetch.py`, one line, once a year.

## Reproducing it

```bash
python tools/1_fetch.py         # Eurostat API to data/raw/, one file per category
python tools/2_dataset.py       # builds data/crime.json and the index
python tools/verify_data.py     # 19 checks

python tools/3_bka_fetch.py     # two BKA xlsx tables to data/raw/bka/
python tools/4_germany.py       # builds data/germany.json
python tools/verify_germany.py  # 23 checks
```

`data/raw/` is gitignored. The built dataset is the artefact, and the verifier
re-derives it from the raw files, so a value cannot drift away from the source
without the suite failing.

## Verification

`python tools/verify_data.py` — 19 checks, including:

- **every value matches the raw Eurostat response** — no rounding, no reordering,
  no quiet imputation
- **the index equals its own published formula**, recomputed from the components
- ranks are a strict ordering of the score; pressure stays inside 0-100
- confidence grades follow the thresholds the dataset itself declares
- the reference year is reported by at least 20 countries
- the limitations are asserted to be **in the data**, not only in the page copy

`python tools/verify_germany.py` — 23 checks, including:

- **every national and every Bundesland value re-read out of the BKA workbook**
- the **sixteen Bundesländer add up to the national figure**, and the two
  workbooks agree with each other
- the national series runs unbroken from 1987 to the reporting year
- no Eurostat ICCS code appears anywhere in the Germany dataset
- both file versions are recorded, because BKA's reuse terms require them
- the panel's own limitations are asserted to be in the data

`python tools/verify_site.py` — 19 checks in a real browser: every ranked country
reaches the table, every limitation on both panels renders, the DOI and licence
are on the page, Germany's row matches the dataset, all four charts draw, the bar
chart contains no stand-in zeros for countries that did not report, re-sorting
genuinely re-ranks, the Bundesland table is the dataset in the dataset's order,
and **the BKA reporting year appears on the BKA chart and on no other** — the
mechanical test that the two sources never cross.

## Source and licence

Data: **Eurostat, police-recorded offences by offence category** (`crim_off_cat`),
DOI [10.2908/CRIM_OFF_CAT](https://doi.org/10.2908/CRIM_OFF_CAT), last updated
2026-04-29. Re-used under the Eurostat re-use policy (Commission Decision
2011/833/EU). Eurostat is not responsible for this presentation of the data.
Definitions and comparability notes:
[crim_sims](https://ec.europa.eu/eurostat/cache/metadata/en/crim_sims.htm).

Germany panel: **PKS Bundeskriminalamt**, reporting year 2025, national time
series V1.1 and Bundesländer table V1.0. Use of the data, whole or in part, is
permitted only with the source, the reporting year and the file version cited
([Nutzungshinweis](https://www.bka.de/DE/AktuelleInformationen/StatistikenLagebilder/PolizeilicheKriminalstatistik/PKS2025/pksTabellen_Interpretationshilfen/pksTabellen_Interpretationshilfen_node.html)).
The two datasets are published side by side and are not comparable with each
other.

Code in this repository: MIT.
