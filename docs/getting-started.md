# Getting started

Shrink Signal is a static data story about recorded crime pressure and loss prevention. It places eight Eurostat offence categories across 41 countries from 2008–2024 beside a separate German BKA panel reaching 2025.

## Explore the live panels

Open the [live panels](https://jeevan-0508.github.io/shrink-signal/). Read the definition and limitations above the charts, then compare pressure, trend and reporting confidence. The European and German sources remain separate because they count under different rules.

## Reproduce the analysis

The browser reads generated JSON and renders it with Chart.js. Follow the repository's reproduction section to rebuild the data; then inspect the generated files and run the verification checks before publishing.

```bash
python3 -m pytest
```

## Interpret carefully

The Loss Pressure Index is a declared judgement combining pressure and trend. It is not a probability of fraud, a forecast of incidents or a measure of reporting accuracy. Confidence grades completeness of reporting, not truthfulness of the underlying records.
