// Reads data/crime.json and draws it. No numbers are computed here that are not
// already in the dataset, except the indexing of trend lines to their own first
// year, which is a display choice and is stated on the page.

const PEERS = ['DE', 'FR', 'NL', 'BE', 'AT', 'PL', 'CZ', 'IT', 'ES', 'SE'];
const AXIS = '#94a3b8';
const GRID = 'rgba(148,163,184,0.12)';
const DE_COLOUR = '#38bdf8';
const OTHER = 'rgba(148,163,184,0.45)';
const LINES = ['#38bdf8', '#fbbf24', '#a78bfa', '#fb7185', '#34d399',
               '#f472b6', '#60a5fa', '#facc15', '#4ade80', '#c084fc'];

const el = (id) => document.getElementById(id);
const data = await fetch('data/crime.json').then((r) => r.json());

Chart.defaults.color = AXIS;
Chart.defaults.font.family = 'ui-sans-serif, system-ui, sans-serif';

// ---------------------------------------------------------------- provenance
const src = data.source;
el('prov').textContent = 'Source: ' + src.name + ' · DOI ' + src.doi +
  ' · Eurostat last updated ' + src.updated.slice(0, 10) +
  ' · reference year ' + data.index_definition.reference_year;
el('cite').textContent = 'Data: ' + src.name + '. DOI ' + src.doi +
  '. Re-used under the ' + src.licence + '. Eurostat is not responsible for this presentation of the data.';

el('limits').innerHTML = data.limits.map((t) => '<li>' + t + '</li>').join('');

const def = data.index_definition;
el('howto').innerHTML = [
  '<p><strong class="text-white">Reference year ' + def.reference_year + '.</strong> The latest year that ' +
    'enough countries report widely enough to rank on. Ranking on the newest year present would rank countries on who files first.</p>',
  '<p><strong class="text-white">Pressure.</strong> For each category, where the country sits as a percentile ' +
    'against every other reporting country in ' + def.reference_year + ', averaged over the categories it reports. A country that reports three categories is scored on three, and the count is shown.</p>',
  '<p><strong class="text-white">Trend.</strong> Median percentage change across those categories over ' + def.trend_window +
    ', clamped at plus or minus ' + def.trend_clamp_percent + ' percent so one runaway series cannot dominate.</p>',
  '<p><strong class="text-white">Index.</strong> ' + def.weights.pressure + ' x pressure + ' + def.weights.trend +
    ' x trend. Those weights are a judgement, not a finding. Both components are in the table so you can re-rank on either.</p>',
  '<p><strong class="text-white">Confidence.</strong> ' + Object.entries(def.confidence).map(([g, d]) => g + ' = ' + d).join(', ') +
    '. It grades how completely a country reported, never how accurate the recording is.</p>',
].join('');

// ------------------------------------------------------------------- the table
const GRADE = { A: 'text-emerald-400', B: 'text-amber-400', C: 'text-rose-400' };

function drawTable(key) {
  const rows = data.index.slice().sort((a, b) => {
    const av = a[key], bv = b[key];
    if (av === null) return 1;
    if (bv === null) return -1;
    return bv - av;
  });
  el('idxbody').innerHTML = rows.map((r) => {
    const mine = r.geo === 'DE';
    const trend = r.trend === null ? '&mdash;'
      : (r.trend > 0 ? '+' : '') + r.trend.toFixed(1) + '%';
    const trendClass = r.trend === null ? 'text-slate-500'
      : (r.trend > 0 ? 'text-rose-400' : 'text-emerald-400');
    return '<tr class="' + (mine ? 'bg-sky-500/10' : '') + '">' +
      '<td class="px-4 py-2.5 text-slate-500">' + r.rank + '</td>' +
      '<td class="px-4 py-2.5 ' + (mine ? 'font-semibold text-sky-300' : 'text-slate-200') + '">' + r.name + '</td>' +
      '<td class="px-4 py-2.5 text-right font-medium text-white">' + r.score.toFixed(1) + '</td>' +
      '<td class="px-4 py-2.5 text-right">' + r.pressure.toFixed(1) + '</td>' +
      '<td class="px-4 py-2.5 text-right ' + trendClass + '">' + trend + '</td>' +
      '<td class="px-4 py-2.5 text-center ' + GRADE[r.confidence] + '">' + r.confidence +
        ' <span class="text-slate-500">' + r.coverage.toFixed(0) + '%</span></td>' +
      '<td class="px-4 py-2.5 text-right text-slate-400">' + r.categories_reported + ' of ' + data.categories.length + '</td>' +
      '</tr>';
  }).join('');
}

el('idxsub').textContent = data.index.length + ' countries ranked on ' +
  data.categories.length + ' categories · reference ' + def.reference_year +
  ' · trend ' + def.trend_window;

document.querySelectorAll('.sortbtn').forEach((b) => {
  b.addEventListener('click', () => {
    document.querySelectorAll('.sortbtn').forEach((o) => {
      o.className = 'sortbtn rounded bg-slate-800 px-3 py-1.5 text-slate-300';
    });
    b.className = 'sortbtn rounded bg-sky-500/15 px-3 py-1.5 text-sky-300';
    drawTable(b.dataset.sort);
  });
});
drawTable('score');

// ------------------------------------------------------------- ranked by category
data.categories.forEach((c) => {
  const o = document.createElement('option');
  o.value = c.code; o.textContent = c.label;
  el('cat').appendChild(o);
});
data.years.slice().reverse().forEach((y) => {
  const o = document.createElement('option');
  o.value = y; o.textContent = y;
  el('year').appendChild(o);
});
el('year').value = def.reference_year;

let barChart = null;

function drawBars() {
  const code = el('cat').value, year = el('year').value;
  const cat = data.categories.find((c) => c.code === code);
  el('catnote').textContent = cat.note;
  const rows = Object.keys(data.series[code])
    .filter((g) => data.series[code][g][year] && data.series[code][g][year].rate != null)
    .map((g) => ({ g, name: data.countries[g], rate: data.series[code][g][year].rate }))
    .sort((a, b) => b.rate - a.rate);
  if (barChart) barChart.destroy();
  barChart = new Chart(el('bars'), {
    type: 'bar',
    data: {
      labels: rows.map((r) => r.name),
      datasets: [{
        data: rows.map((r) => r.rate),
        backgroundColor: rows.map((r) => (r.g === 'DE' ? DE_COLOUR : OTHER)),
        borderRadius: 2,
      }],
    },
    options: {
      plugins: { legend: { display: false },
        tooltip: { callbacks: { label: (c) => c.parsed.y.toLocaleString() + ' per 100k' } } },
      scales: {
        x: { ticks: { maxRotation: 90, minRotation: 60, font: { size: 9 } }, grid: { display: false } },
        y: { grid: { color: GRID }, title: { display: true, text: 'per 100,000 inhabitants' } },
      },
    },
  });
}
el('cat').addEventListener('change', drawBars);
el('year').addEventListener('change', drawBars);
drawBars();

// --------------------------------------------------------- Germany, indexed
function indexed(code, geo) {
  const row = data.series[code][geo] || {};
  const pts = data.years.filter((y) => row[y] && row[y].rate != null);
  if (!pts.length) return null;
  const base = row[pts[0]].rate;
  return data.years.map((y) => (row[y] && row[y].rate != null ? round1(100 * row[y].rate / base) : null));
}
const round1 = (v) => Math.round(v * 10) / 10;

new Chart(el('detrend'), {
  type: 'line',
  data: {
    labels: data.years,
    datasets: data.categories.map((c, i) => ({
      label: c.label,
      data: indexed(c.code, 'DE'),
      borderColor: LINES[i % LINES.length],
      backgroundColor: LINES[i % LINES.length],
      borderWidth: 2, pointRadius: 0, spanGaps: true, tension: 0.25,
    })).filter((d) => d.data),
  },
  options: {
    plugins: { legend: { labels: { boxWidth: 10, font: { size: 11 } } },
      tooltip: { callbacks: { label: (c) => c.dataset.label + ': ' + c.parsed.y + ' (first year = 100)' } } },
    scales: { y: { grid: { color: GRID }, title: { display: true, text: 'first reported year = 100' } },
      x: { grid: { display: false } } },
  },
});

// ------------------------------------------------------------------- peers
const peerCode = 'ICCS0502';
el('peernote').textContent = 'Theft per 100,000 inhabitants. Levels are the part Eurostat warns about: '
  + 'a country that records every reported bicycle theft will sit above one that does not. '
  + 'The shape of each line over time is the safer comparison.';

new Chart(el('peers'), {
  type: 'line',
  data: {
    labels: data.years,
    datasets: PEERS.map((g, i) => ({
      label: data.countries[g] || g,
      data: data.years.map((y) => {
        const r = (data.series[peerCode][g] || {})[y];
        return r && r.rate != null ? r.rate : null;
      }),
      borderColor: g === 'DE' ? DE_COLOUR : LINES[(i + 1) % LINES.length],
      borderWidth: g === 'DE' ? 3 : 1.5,
      pointRadius: 0, spanGaps: true, tension: 0.25,
    })),
  },
  options: {
    plugins: { legend: { labels: { boxWidth: 10, font: { size: 11 } } } },
    scales: { y: { grid: { color: GRID }, title: { display: true, text: 'theft per 100,000' } },
      x: { grid: { display: false } } },
  },
});

// ------------------------------------------- Germany, from the national statistic
// A second dataset from a second authority, kept in its own panel. Nothing here
// touches data/crime.json and no value from one is ever placed on a chart with a
// value from the other.
const de = await fetch('data/germany.json').then((r) => r.json());
const dm = de.meta;
const SHOP = '*26*00';

el('bkaprov').textContent = 'Source: ' + dm.source + ', reporting year ' + dm.reporting_year +
  ' · ' + dm.versions.national_time_series + ' (national), ' + dm.versions.laender_table + ' (Bundesländer)' +
  ' · rate is the Häufigkeitszahl, cases per 100,000 inhabitants';
el('bkacite').textContent = 'Germany panel: ' + dm.source + ', ' + dm.reporting_year + '. ' +
  dm.versions.national_time_series + ', ' + dm.versions.laender_table + '. ' + dm.reuse_terms;

el('bkalimits').innerHTML = de.limits.map((t) => '<li>' + t + '</li>').join('');

const shop = de.national[SHOP];
const shopNow = shop[shop.length - 1];
const shopPrev = shop[shop.length - 2];
const shopMove = 100 * (shopNow.per100k - shopPrev.per100k) / shopPrev.per100k;
const shopLand = de.laender.order
  .map((n) => ({ n, v: de.laender.values[n][SHOP].per100k }))
  .sort((a, b) => b.v - a.v);
const euLatest = data.years[data.years.length - 1];

function card(kicker, value, note) {
  return '<div class="rounded-lg border border-slate-800 bg-slate-900/60 p-4">' +
    '<p class="text-xs uppercase tracking-wider text-violet-400">' + kicker + '</p>' +
    '<p class="mt-1 text-2xl font-semibold text-white">' + value + '</p>' +
    '<p class="mt-1 text-xs text-slate-400">' + note + '</p></div>';
}

el('bkahead').innerHTML = [
  card('Shoplifting ' + shopNow.year,
    shopNow.per100k.toLocaleString() + ' per 100k',
    (shopMove > 0 ? '+' : '') + shopMove.toFixed(1) + '% on ' + shopPrev.year + '. The harmonised ICCS list ' +
    'Eurostat publishes has no code for shoplifting at all, so this figure cannot appear anywhere above.'),
  card('Spread across the sixteen',
    shopLand[0].v.toLocaleString() + ' to ' + shopLand[shopLand.length - 1].v.toLocaleString(),
    shopLand[0].n + ' against ' + shopLand[shopLand.length - 1].n + ' — a ' +
    (shopLand[0].v / shopLand[shopLand.length - 1].v).toFixed(1) + '× gap inside one country. ' +
    'Eurostat publishes Germany as a single number.'),
  card('Reporting lag',
    'BKA ' + dm.reporting_year + ' vs Eurostat ' + euLatest,
    'The national statistic runs about a year ahead of the harmonised one. That is the reason ' +
    'this panel exists, and the reason it has to stay separate.'),
].join('');

de.categories.forEach((c) => {
  const o = document.createElement('option');
  o.value = c.key; o.textContent = c.label;
  el('bkacat').appendChild(o);
});
el('bkacat').value = SHOP;

let bkaChart = null;

function drawBka() {
  const key = el('bkacat').value;
  const cat = de.categories.find((c) => c.key === key);
  el('bkacatnote').textContent = cat.note;

  const rows = de.laender.order
    .map((n) => ({ n, ...de.laender.values[n][key] }))
    .sort((a, b) => b.per100k - a.per100k);
  el('bkabody').innerHTML = rows.map((r, i) =>
    '<tr>' +
    '<td class="px-4 py-2.5 text-slate-500">' + (i + 1) + '</td>' +
    '<td class="px-4 py-2.5 text-slate-200">' + r.n + '</td>' +
    '<td class="px-4 py-2.5 text-right font-medium text-white">' + r.per100k.toLocaleString() + '</td>' +
    '<td class="px-4 py-2.5 text-right text-slate-400">' + r.cases.toLocaleString() + '</td>' +
    '<td class="px-4 py-2.5 text-right text-slate-400">' + r.clearance.toFixed(1) + '%</td>' +
    '</tr>').join('');

  const nat = de.laender.national_row[key];
  el('bkafoot').innerHTML = '<tr class="bg-slate-900/70">' +
    '<td class="px-4 py-2.5"></td>' +
    '<td class="px-4 py-2.5 font-semibold text-violet-300">Germany</td>' +
    '<td class="px-4 py-2.5 text-right font-semibold text-white">' + nat.per100k.toLocaleString() + '</td>' +
    '<td class="px-4 py-2.5 text-right">' + nat.cases.toLocaleString() + '</td>' +
    '<td class="px-4 py-2.5 text-right">' + nat.clearance.toFixed(1) + '%</td>' +
    '</tr>';

  const series = de.national[key];
  if (bkaChart) bkaChart.destroy();
  bkaChart = new Chart(el('bkatrend'), {
    type: 'line',
    data: {
      labels: series.map((p) => p.year),
      datasets: [
        { label: cat.label + ', per 100,000', data: series.map((p) => p.per100k),
          borderColor: '#a78bfa', borderWidth: 2.5, pointRadius: 0, tension: 0.25, yAxisID: 'y' },
        { label: 'Cleared, % of cases', data: series.map((p) => p.clearance),
          borderColor: '#fbbf24', borderWidth: 1.5, borderDash: [4, 3], pointRadius: 0, tension: 0.25, yAxisID: 'y1' },
      ],
    },
    options: {
      interaction: { mode: 'index', intersect: false },
      plugins: { legend: { labels: { boxWidth: 10, font: { size: 11 } } } },
      scales: {
        y: { position: 'left', grid: { color: GRID }, title: { display: true, text: 'per 100,000 inhabitants' } },
        y1: { position: 'right', min: 0, max: 100, grid: { display: false }, title: { display: true, text: 'cleared, %' } },
        x: { grid: { display: false } },
      },
    },
  });
}
el('bkacat').addEventListener('change', drawBka);
drawBka();

window.SHRINK = { data, germany: de, drawTable, drawBars, drawBka };
