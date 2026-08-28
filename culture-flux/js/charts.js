/* Hand-rolled SVG. No plotting library, no network, no canvas — so the page
   works from the filesystem, prints, and reads correctly in both themes without
   a repaint hook. Colours are token references resolved by the browser, never
   sampled into JS, which is what lets the theme switch just work. */

const FMT = (v, dp) => (v === null || v === undefined || v !== v) ? "—" : v.toFixed(dp === undefined ? 3 : dp);

function esc(s){ return String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }

/* A strip plot: every run drawn as one mark, group means as a heavier rule.
   Individual runs rather than error bars because one arm is plausibly bimodal,
   and a mean with a standard error would describe a shape it does not have. */
function stripPlot(groups, opts) {
  opts = opts || {};
  const W = 1000, rowH = 54, m = { l: 168, r: 26, t: 34, b: 46 };
  const H = m.t + groups.length * rowH + m.b;

  let lo = Infinity, hi = -Infinity;
  groups.forEach(g => g.values.forEach(v => { if (v < lo) lo = v; if (v > hi) hi = v; }));
  if (opts.reference !== undefined && opts.reference !== null) {
    lo = Math.min(lo, opts.reference); hi = Math.max(hi, opts.reference);
  }
  if (!isFinite(lo)) { lo = 0; hi = 1; }
  const pad = (hi - lo) * 0.12 || 0.05;
  lo -= pad; hi += pad;
  if (opts.clamp01) { lo = Math.max(0, lo); hi = Math.min(1, hi); }

  const X = v => m.l + (v - lo) / (hi - lo) * (W - m.l - m.r);
  let g = "";

  /* gridlines and axis */
  for (let i = 0; i <= 4; i++) {
    const v = lo + (hi - lo) * i / 4, x = X(v);
    g += `<line x1="${x}" y1="${m.t - 10}" x2="${x}" y2="${H - m.b + 6}" stroke="var(--rf-line-soft)" stroke-width="1"/>`;
    g += `<text x="${x}" y="${H - m.b + 24}" text-anchor="middle" font-family="var(--rf-mono)" font-size="12" fill="var(--rf-muted)">${FMT(v, opts.dp === undefined ? 2 : opts.dp)}</text>`;
  }

  /* the compositional reference, if the metric has one */
  if (opts.reference !== undefined && opts.reference !== null) {
    const x = X(opts.reference);
    g += `<line x1="${x}" y1="${m.t - 14}" x2="${x}" y2="${H - m.b + 6}" stroke="var(--cf-baseline)" stroke-width="1.5" stroke-dasharray="5 4"/>`;
    g += `<text x="${x}" y="${m.t - 20}" text-anchor="middle" font-family="var(--rf-mono)" font-size="11.5" fill="var(--cf-baseline)">${esc(opts.referenceLabel || "baseline")}</text>`;
  }

  groups.forEach((grp, i) => {
    const y = m.t + i * rowH + rowH / 2;
    g += `<text x="${m.l - 14}" y="${y - 4}" text-anchor="end" font-family="var(--rf-sans)" font-size="13.5" fill="var(--rf-ink)">${esc(grp.label)}</text>`;
    g += `<text x="${m.l - 14}" y="${y + 13}" text-anchor="end" font-family="var(--rf-mono)" font-size="11" fill="var(--rf-muted)">${grp.values.length} runs</text>`;

    if (!grp.values.length) return;
    /* individual runs, semi-transparent so overlap reads as density */
    grp.values.forEach(v => {
      g += `<circle cx="${X(v)}" cy="${y}" r="4.5" fill="${grp.colour}" opacity="0.42"/>`;
    });
    const mean = grp.values.reduce((a, b) => a + b, 0) / grp.values.length;
    g += `<line x1="${X(mean)}" y1="${y - 15}" x2="${X(mean)}" y2="${y + 15}" stroke="${grp.colour}" stroke-width="2.5"/>`;
    g += `<title>${esc(grp.label)}: mean ${FMT(mean, 4)} over ${grp.values.length} runs</title>`;
  });

  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(opts.aria || "Distribution of runs by condition")}">${g}</svg>`;
}

/* A small multiples line: one metric against source count, one line per rule. */
function contrastLines(series, opts) {
  opts = opts || {};
  const W = 1000, H = 320, m = { l: 74, r: 130, t: 22, b: 44 };
  const xs = opts.x;
  let lo = Infinity, hi = -Infinity;
  series.forEach(s => s.points.forEach(p => {
    const a = p.mean - (p.se || 0), b = p.mean + (p.se || 0);
    if (a < lo) lo = a; if (b > hi) hi = b;
  }));
  if (opts.reference !== undefined && opts.reference !== null) {
    lo = Math.min(lo, opts.reference); hi = Math.max(hi, opts.reference);
  }
  if (!isFinite(lo)) { lo = 0; hi = 1; }
  const pad = (hi - lo) * 0.18 || 0.05;
  lo -= pad; hi += pad;

  const X = i => m.l + (xs.length === 1 ? 0.5 : i / (xs.length - 1)) * (W - m.l - m.r);
  const Y = v => m.t + (1 - (v - lo) / (hi - lo)) * (H - m.t - m.b);
  let g = "";

  for (let i = 0; i <= 4; i++) {
    const v = lo + (hi - lo) * i / 4, y = Y(v);
    g += `<line x1="${m.l}" y1="${y}" x2="${W - m.r}" y2="${y}" stroke="var(--rf-line-soft)"/>`;
    g += `<text x="${m.l - 10}" y="${y + 4}" text-anchor="end" font-family="var(--rf-mono)" font-size="12" fill="var(--rf-muted)">${FMT(v, opts.dp === undefined ? 2 : opts.dp)}</text>`;
  }
  xs.forEach((xv, i) => {
    g += `<text x="${X(i)}" y="${H - m.b + 24}" text-anchor="middle" font-family="var(--rf-mono)" font-size="12" fill="var(--rf-muted)">${esc(xv)}</text>`;
  });
  g += `<text x="${(m.l + W - m.r) / 2}" y="${H - 6}" text-anchor="middle" font-family="var(--rf-mono)" font-size="11.5" fill="var(--rf-muted)">${esc(opts.xlabel || "")}</text>`;

  if (opts.reference !== undefined && opts.reference !== null) {
    const y = Y(opts.reference);
    g += `<line x1="${m.l}" y1="${y}" x2="${W - m.r}" y2="${y}" stroke="var(--cf-baseline)" stroke-width="1.5" stroke-dasharray="5 4"/>`;
    g += `<text x="${W - m.r + 8}" y="${y + 4}" font-family="var(--rf-mono)" font-size="11.5" fill="var(--cf-baseline)">${esc(opts.referenceLabel || "baseline")}</text>`;
  }

  series.forEach(s => {
    let d = "";
    s.points.forEach((p, i) => {
      d += (i ? "L" : "M") + X(i) + " " + Y(p.mean);
      if (p.se) {
        g += `<line x1="${X(i)}" y1="${Y(p.mean - p.se)}" x2="${X(i)}" y2="${Y(p.mean + p.se)}" stroke="${s.colour}" stroke-width="1.5" opacity="0.65"/>`;
      }
    });
    g += `<path d="${d}" fill="none" stroke="${s.colour}" stroke-width="2.2"/>`;
    s.points.forEach((p, i) => {
      g += `<circle cx="${X(i)}" cy="${Y(p.mean)}" r="4" fill="${s.colour}"><title>${esc(s.label)} at ${esc(xs[i])}: ${FMT(p.mean, 4)} ± ${FMT(p.se, 4)}</title></circle>`;
    });
    const last = s.points[s.points.length - 1];
    g += `<text x="${W - m.r + 8}" y="${Y(last.mean) + 4}" font-family="var(--rf-mono)" font-size="12" fill="${s.colour}">${esc(s.short)}</text>`;
  });

  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="${esc(opts.aria || "Metric against source count, by transmission rule")}">${g}</svg>`;
}
