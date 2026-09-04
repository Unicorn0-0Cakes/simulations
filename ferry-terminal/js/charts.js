/* =====================================================================
   FERRY TERMINAL — charts
   ---------------------------------------------------------------------
   Plain canvas. No chart library, in keeping with the rest of the Atlas.

   TWO STRUCTURAL RULES ARE ENFORCED HERE RATHER THAN IN REVIEW.

   1. There is no function that draws the observed-only distribution on
      its own. `observedPair` takes BOTH canvases and draws the
      composition beside the histogram in a single call. A caller cannot
      render one without the other, because no code path exists to do it.

   2. There is no function that draws two policies' observed-only
      distributions together. `comparePolicies` draws survival curves and
      composition bars as one unit. The configuration that made
      SIZE_AWARE look superior is unreachable, not merely discouraged.

   Overlaid comparisons share one y-scale, so a difference cannot be
   exaggerated by independent scaling.
   ===================================================================== */
(function (global) {
  "use strict";
  var CFG = global.FerryConfig;

  function col(n) {
    return (global.Orbital && global.Orbital.color) ? global.Orbital.color(n) : "#888";
  }
  function reduced() {
    return global.matchMedia && global.matchMedia("(prefers-reduced-motion: reduce)").matches;
  }

  function prep(cv) {
    var dpr = global.devicePixelRatio || 1;
    var w = cv.clientWidth || 600;
    var h = parseInt(cv.getAttribute("data-h"), 10) || 200;
    if (cv.width !== Math.round(w * dpr) || cv.height !== Math.round(h * dpr)) {
      cv.width = Math.round(w * dpr); cv.height = Math.round(h * dpr);
      cv.style.height = h + "px";
    }
    var g = cv.getContext("2d");
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, w, h);
    return { g: g, w: w, h: h };
  }

  function axes(g, w, h, pad, xlab, ylab) {
    g.strokeStyle = col("scope-line"); g.lineWidth = 1;
    g.beginPath();
    g.moveTo(pad.l, pad.t); g.lineTo(pad.l, h - pad.b); g.lineTo(w - pad.r, h - pad.b);
    g.stroke();
    g.fillStyle = col("muted");
    g.font = '10px ' + '"IBM Plex Mono", monospace';
    if (xlab) { g.textAlign = "right"; g.fillText(xlab, w - pad.r, h - 4); }
    if (ylab) {
      g.save(); g.translate(9, pad.t); g.rotate(-Math.PI / 2);
      g.textAlign = "right"; g.fillText(ylab, 0, 0); g.restore();
    }
  }

  function ticks(g, w, h, pad, x0, x1, y0, y1, xfmt, yfmt) {
    g.fillStyle = col("muted");
    g.font = '9.5px "IBM Plex Mono", monospace';
    g.strokeStyle = col("scope-line");
    var i, v, px, py;
    g.textAlign = "center"; g.textBaseline = "top";
    for (i = 0; i <= 4; i++) {
      v = x0 + (x1 - x0) * i / 4;
      px = pad.l + (w - pad.l - pad.r) * i / 4;
      g.fillText(xfmt(v), px, h - pad.b + 5);
    }
    g.textAlign = "right"; g.textBaseline = "middle";
    for (i = 0; i <= 4; i++) {
      v = y0 + (y1 - y0) * i / 4;
      py = (h - pad.b) - (h - pad.t - pad.b) * i / 4;
      g.fillText(yfmt(v), pad.l - 6, py);
      g.globalAlpha = 0.35; g.beginPath();
      g.moveTo(pad.l, py); g.lineTo(w - pad.r, py); g.stroke(); g.globalAlpha = 1;
    }
    g.textBaseline = "alphabetic";
  }

  /* ---- 1. the censoring-aware survival unit -----------------------
     PRIMARY time-to-service display. Censoring ticks are drawn, never
     hidden, and the region where the estimate is unreliable is hatched
     rather than smoothed to look continuous.                           */
  function survivalCurve(g, w, h, pad, km, xmax, colour, dashed, drawTicks) {
    if (!km.length) return;
    var X = function (t) { return pad.l + (w - pad.l - pad.r) * Math.min(t, xmax) / xmax; };
    var Y = function (s) { return (h - pad.b) - (h - pad.t - pad.b) * s; };
    g.strokeStyle = colour; g.lineWidth = dashed ? 1.4 : 2;
    if (dashed) g.setLineDash([4, 3]);
    g.beginPath(); g.moveTo(X(0), Y(1));
    var prev = 1, i;
    for (i = 0; i < km.length; i++) {
      g.lineTo(X(km[i].t), Y(prev));
      g.lineTo(X(km[i].t), Y(km[i].survival));
      prev = km[i].survival;
    }
    g.lineTo(X(xmax), Y(prev));
    g.stroke(); g.setLineDash([]);

    if (drawTicks) {
      /* every censoring event gets a mark. This is the honest part of
         the plot and is not a decoration. */
      g.strokeStyle = colour; g.lineWidth = 1;
      for (i = 0; i < km.length; i++) {
        if (!km[i].censored) continue;
        var x = X(km[i].t), y = Y(km[i].survival);
        g.beginPath(); g.moveTo(x, y - 4); g.lineTo(x, y + 4); g.stroke();
      }
    }
  }

  function unreliableRegion(g, w, h, pad, km, xmax) {
    /* Where fewer than 10% of the original sample remains at risk, the
       estimate is not to be read as a smooth curve. */
    if (!km.length) return null;
    var n0 = km[0].atRisk, cut = null, i;
    for (i = 0; i < km.length; i++) if (km[i].atRisk < 0.10 * n0) { cut = km[i].t; break; }
    if (cut === null) return null;
    var x = pad.l + (w - pad.l - pad.r) * Math.min(cut, xmax) / xmax;
    g.save();
    g.beginPath(); g.rect(x, pad.t, (w - pad.r) - x, h - pad.t - pad.b); g.clip();
    g.strokeStyle = col("muted"); g.globalAlpha = 0.30; g.lineWidth = 1;
    for (var k = -h; k < w; k += 7) {
      g.beginPath(); g.moveTo(x + k, h - pad.b); g.lineTo(x + k + h, pad.t); g.stroke();
    }
    g.restore();
    g.globalAlpha = 1;
    g.fillStyle = col("muted"); g.font = '9.5px "IBM Plex Mono", monospace';
    var label = "FEWER THAN 10% STILL AT RISK";
    var tw = g.measureText(label).width;
    if (x + 5 + tw > w - pad.r) { label = "UNRELIABLE"; tw = g.measureText(label).width; }
    if (x + 5 + tw > w - pad.r) { g.textAlign = "right"; g.fillText(label, x - 5, pad.t + 11); }
    else { g.textAlign = "left"; g.fillText(label, x + 5, pad.t + 11); }
    return cut;
  }

  function compositionBar(cv, res, ghost) {
    var p = prep(cv), g = p.g, w = p.w, h = p.h;
    var rows = [{ label: "This run", r: res }];
    if (ghost) rows.push({ label: "Baseline", r: ghost });
    var barH = Math.min(30, (h - 20) / rows.length - 8);
    rows.forEach(function (row, i) {
      var y = 16 + i * (barH + 16);
      var sf = row.r.servedFraction, cf = row.r.censoredFraction;
      /* a reserved text column on the right, so the figures are never
         drawn on top of the hatching they describe */
      var x0 = 74, textW = Math.min(210, Math.max(150, w * 0.32));
      var ww = Math.max(60, w - x0 - textW - 12);
      g.fillStyle = col("teal"); g.fillRect(x0, y, ww * sf, barH);
      g.fillStyle = col("oxide"); g.globalAlpha = i ? 0.4 : 1;
      g.fillRect(x0 + ww * sf, y, ww * cf, barH);
      g.globalAlpha = 1;
      /* pattern on the censored block, so nothing is encoded by colour alone */
      g.save();
      g.beginPath(); g.rect(x0 + ww * sf, y, ww * cf, barH); g.clip();
      g.strokeStyle = col("bg"); g.globalAlpha = 0.55; g.lineWidth = 1;
      for (var k = -barH; k < ww; k += 5) {
        g.beginPath(); g.moveTo(x0 + ww * sf + k, y + barH); g.lineTo(x0 + ww * sf + k + barH, y); g.stroke();
      }
      g.restore(); g.globalAlpha = 1;
      g.strokeStyle = col("line"); g.lineWidth = 1; g.strokeRect(x0, y, ww, barH);
      g.fillStyle = col("ink-dim"); g.font = '10px "IBM Plex Mono", monospace';
      g.textAlign = "left"; g.textBaseline = "middle";
      g.fillText(row.label.toUpperCase(), 4, y + barH / 2);
      g.font = '10.5px "IBM Plex Mono", monospace';
      g.textAlign = "left";
      g.fillStyle = col("teal");
      g.fillText((sf * 100).toFixed(1) + "% SAILED", x0 + ww + 10, y + barH / 2 - 6);
      g.fillStyle = col("oxide");
      g.fillText((cf * 100).toFixed(1) + "% NEVER SAILED", x0 + ww + 10, y + barH / 2 + 7);
      g.textBaseline = "alphabetic";
    });
  }

  /* THE PRIMARY UNIT. Both canvases are required. */
  function survivalUnit(cvCurve, cvComp, res, ghost) {
    var p = prep(cvCurve), g = p.g, w = p.w, h = p.h;
    var pad = { l: 46, r: 14, t: 14, b: 26 };
    var all = res.timeToServiceKM.concat(ghost ? ghost.timeToServiceKM : []);
    var xmax = all.length ? Math.max.apply(null, all.map(function (d) { return d.t; })) : 1;
    xmax = Math.max(xmax, 1);
    axes(g, w, h, pad, "TIME TO SERVICE, MIN", "P(STILL WAITING)");
    ticks(g, w, h, pad, 0, xmax, 0, 1,
      function (v) { return v.toFixed(0); },
      function (v) { return v.toFixed(1); });
    var cut = unreliableRegion(g, w, h, pad, res.timeToServiceKM, xmax);
    if (ghost) survivalCurve(g, w, h, pad, ghost.timeToServiceKM, xmax, col("muted"), true, false);
    survivalCurve(g, w, h, pad, res.timeToServiceKM, xmax, col(CFG.POLICY_HUE[res.config.policy] || "teal"), false, true);
    compositionBar(cvComp, res, ghost);
    return { xmax: xmax, unreliableFrom: cut };
  }

  /* THE DEMOTED SECONDARY. Both canvases are required, by construction. */
  function observedPair(cvHist, cvComp, res, ghost) {
    var p = prep(cvHist), g = p.g, w = p.w, h = p.h;
    var pad = { l: 46, r: 14, t: 14, b: 26 };
    var a = res.timeToServiceObserved, b = ghost ? ghost.timeToServiceObserved : [];
    var xmax = Math.max(1, Math.max.apply(null, a.concat(b).concat([1])));
    var NB = 24, i;
    function hist(arr) {
      var bins = new Array(NB).fill(0);
      arr.forEach(function (t) { bins[Math.min(NB - 1, Math.floor(t / xmax * NB))]++; });
      return bins;
    }
    var ha = hist(a), hb = ghost ? hist(b) : null;
    var ymax = Math.max(1, Math.max.apply(null, ha.concat(hb || [])));
    axes(g, w, h, pad, "TIME TO SERVICE, MIN — SERVED VEHICLES ONLY", "COUNT");
    ticks(g, w, h, pad, 0, xmax, 0, ymax,
      function (v) { return v.toFixed(0); }, function (v) { return v.toFixed(0); });
    var bw = (w - pad.l - pad.r) / NB;
    for (i = 0; i < NB; i++) {
      var x = pad.l + i * bw;
      if (hb) {
        g.fillStyle = col("muted"); g.globalAlpha = 0.35;
        g.fillRect(x + 1, (h - pad.b) - (h - pad.t - pad.b) * hb[i] / ymax, bw - 2, (h - pad.t - pad.b) * hb[i] / ymax);
        g.globalAlpha = 1;
      }
      g.fillStyle = col(CFG.POLICY_HUE[res.config.policy] || "teal");
      g.fillRect(x + 1, (h - pad.b) - (h - pad.t - pad.b) * ha[i] / ymax, bw - 2, (h - pad.t - pad.b) * ha[i] / ymax);
    }
    compositionBar(cvComp, res, ghost);
  }

  /* ---- 2. queue-length timeline. The epochs are the spine. --------- */
  function queueTimeline(cv, res, ghost) {
    var p = prep(cv), g = p.g, w = p.w, h = p.h;
    var pad = { l: 46, r: 14, t: 14, b: 26 };
    var T = res.config.horizon;
    var series = [res.queueSeries].concat(ghost ? [ghost.queueSeries] : []);
    var ymax = 1;
    series.forEach(function (s) { s.forEach(function (pt) { if (pt[1] > ymax) ymax = pt[1]; }); });
    axes(g, w, h, pad, "MINUTES", "VEHICLES QUEUEING");
    ticks(g, w, h, pad, 0, T, 0, ymax,
      function (v) { return v.toFixed(0); }, function (v) { return v.toFixed(0); });

    var X = function (t) { return pad.l + (w - pad.l - pad.r) * Math.min(t, T) / T; };
    var Y = function (q) { return (h - pad.b) - (h - pad.t - pad.b) * q / ymax; };

    /* DEPARTURE EPOCHS — the strongest visual element in this chart. */
    g.lineWidth = 1.5;
    res.sailings.forEach(function (s) {
      var st = s.status;
      g.strokeStyle = st === "CANCELLED" ? col("oxide") : (st === "NORMAL" ? col("line") : col("amber"));
      g.setLineDash(st === "CANCELLED" ? [3, 3] : []);
      g.beginPath(); g.moveTo(X(s.scheduledTime), pad.t); g.lineTo(X(s.scheduledTime), h - pad.b); g.stroke();
    });
    g.setLineDash([]);

    function step(s, colour, dashed) {
      g.strokeStyle = colour; g.lineWidth = dashed ? 1.3 : 2;
      if (dashed) g.setLineDash([4, 3]);
      g.beginPath();
      var started = false, py = Y(0);
      s.forEach(function (pt) {
        var x = X(pt[0]), y = Y(pt[1]);
        if (!started) { g.moveTo(x, y); started = true; }
        else { g.lineTo(x, py); g.lineTo(x, y); }
        py = y;
      });
      g.stroke(); g.setLineDash([]);
    }
    if (ghost) step(ghost.queueSeries, col("muted"), true);
    step(res.queueSeries, col(CFG.POLICY_HUE[res.config.policy] || "teal"), false);
  }

  /* ---- 3. per-sailing load, capacity and residual ------------------
     Residual is drawn as visible empty space, not as an absence.       */
  function loadStrip(cv, res) {
    var p = prep(cv), g = p.g, w = p.w, h = p.h;
    var n = res.sailings.length || 1;
    var pad = { l: 46, r: 14, t: 14, b: 26 };
    var capMax = Math.max.apply(null, res.sailings.map(function (s) { return s.capacityCm; }).concat([1]));
    axes(g, w, h, pad, "SAILING", "LANE-METRES");
    ticks(g, w, h, pad, 0, n, 0, capMax / 100,
      function (v) { return v.toFixed(0); }, function (v) { return v.toFixed(0); });
    var bw = (w - pad.l - pad.r) / n;
    res.sailings.forEach(function (s, i) {
      var x = pad.l + i * bw + 1, bwi = bw - 2;
      var full = (h - pad.t - pad.b);
      var capH = full * (s.capacityCm / capMax);
      var ldH = full * (s.loadedCm / capMax);
      /* capacity outline: the residual is the gap you can see */
      g.strokeStyle = col("line"); g.lineWidth = 1;
      g.strokeRect(x, (h - pad.b) - capH, bwi, capH);
      g.fillStyle = col(CFG.POLICY_HUE[res.config.policy] || "teal");
      g.fillRect(x, (h - pad.b) - ldH, bwi, ldH);
      if (s.status === "CANCELLED") {
        g.strokeStyle = col("oxide"); g.lineWidth = 1.5;
        g.beginPath();
        g.moveTo(x, h - pad.b - capH); g.lineTo(x + bwi, h - pad.b);
        g.moveTo(x + bwi, h - pad.b - capH); g.lineTo(x, h - pad.b);
        g.stroke();
      }
    });
  }

  /* ---- 4. bars, shared scale with any ghost ------------------------ */
  function bars(cv, values, ghostValues, hue, xlab, ylab) {
    var p = prep(cv), g = p.g, w = p.w, h = p.h;
    var pad = { l: 46, r: 14, t: 14, b: 26 };
    var n = values.length || 1;
    var ymax = Math.max(1, Math.max.apply(null, values.concat(ghostValues || [])));
    axes(g, w, h, pad, xlab, ylab);
    ticks(g, w, h, pad, 0, n, 0, ymax,
      function (v) { return v.toFixed(0); }, function (v) { return v.toFixed(0); });
    var bw = (w - pad.l - pad.r) / n, full = h - pad.t - pad.b;
    values.forEach(function (v, i) {
      var x = pad.l + i * bw + 1;
      if (ghostValues && ghostValues[i] !== undefined) {
        g.fillStyle = col("muted"); g.globalAlpha = 0.35;
        g.fillRect(x, (h - pad.b) - full * ghostValues[i] / ymax, bw - 2, full * ghostValues[i] / ymax);
        g.globalAlpha = 1;
      }
      g.fillStyle = col(hue);
      g.fillRect(x + 2, (h - pad.b) - full * v / ymax, bw - 6, full * v / ymax);
    });
  }

  /* ---- 5. throughput against the analytic bound -------------------- */
  function throughput(cv, res, ghost) {
    var p = prep(cv), g = p.g, w = p.w, h = p.h;
    var pad = { l: 46, r: 14, t: 14, b: 26 };
    var T = res.config.horizon;
    function cumulative(r) {
      var pts = [[0, 0]], c = 0;
      r.sailings.slice().sort(function (a, b) { return a.scheduledTime - b.scheduledTime; })
        .forEach(function (s) { c += s.manifest.length; pts.push([s.scheduledTime, c]); });
      return pts;
    }
    var a = cumulative(res), b = ghost ? cumulative(ghost) : null;
    /* min(lambda, C/h) in vehicles per minute, using expected length */
    var M = global.FerryModel;
    var perSail = (res.config.capacityM * 100) / M.expectedLengthCm(res.config);
    var boundRate = Math.min(res.config.lam / 60, perSail / res.config.headway);
    var ymax = Math.max(1, a[a.length - 1][1], b ? b[b.length - 1][1] : 0, boundRate * T);
    axes(g, w, h, pad, "MINUTES", "CUMULATIVE SAILED");
    ticks(g, w, h, pad, 0, T, 0, ymax,
      function (v) { return v.toFixed(0); }, function (v) { return v.toFixed(0); });
    var X = function (t) { return pad.l + (w - pad.l - pad.r) * t / T; };
    var Y = function (v) { return (h - pad.b) - (h - pad.t - pad.b) * v / ymax; };
    g.strokeStyle = col("muted"); g.setLineDash([2, 4]); g.lineWidth = 1.2;
    g.beginPath(); g.moveTo(X(0), Y(0)); g.lineTo(X(T), Y(boundRate * T)); g.stroke();
    g.setLineDash([]);
    function line(pts, colour, dashed) {
      g.strokeStyle = colour; g.lineWidth = dashed ? 1.3 : 2;
      if (dashed) g.setLineDash([4, 3]);
      g.beginPath();
      pts.forEach(function (pt, i) { i ? g.lineTo(X(pt[0]), Y(pt[1])) : g.moveTo(X(pt[0]), Y(pt[1])); });
      g.stroke(); g.setLineDash([]);
    }
    if (b) line(b, col("muted"), true);
    line(a, col(CFG.POLICY_HUE[res.config.policy] || "teal"), false);
    return { boundRate: boundRate, boundTotal: boundRate * T };
  }

  /* ---- 6. policy comparison, as ONE unit --------------------------
     Survival curves AND composition together. There is no variant of
     this function that omits the composition, and no variant that
     shows observed-only distributions side by side.                    */
  function comparePolicies(cvCurve, cvComp, runs) {
    var p = prep(cvCurve), g = p.g, w = p.w, h = p.h;
    var pad = { l: 46, r: 14, t: 14, b: 26 };
    var xmax = 1;
    runs.forEach(function (r) {
      r.timeToServiceKM.forEach(function (d) { if (d.t > xmax) xmax = d.t; });
    });
    axes(g, w, h, pad, "TIME TO SERVICE, MIN", "P(STILL WAITING)");
    ticks(g, w, h, pad, 0, xmax, 0, 1,
      function (v) { return v.toFixed(0); }, function (v) { return v.toFixed(1); });
    runs.forEach(function (r) {
      survivalCurve(g, w, h, pad, r.timeToServiceKM, xmax, col(CFG.POLICY_HUE[r.config.policy] || "teal"), false, true);
    });
    /* Name every curve on the plot. Two policies can produce the SAME
       curve — booked-first is first-come when nobody holds a booking —
       and a reader must not mistake coincidence for a missing series. */
    var sigs = runs.map(function (r) {
      return r.timeToServiceKM.map(function (d) { return d.t.toFixed(6) + ":" + d.survival.toFixed(9); }).join("|");
    });
    var lx = pad.l + 8, ly = pad.t + 12;
    /* a plate behind the key, so it never sits on top of a curve */
    g.save();
    g.globalAlpha = 0.88; g.fillStyle = col("panel");
    g.fillRect(lx - 6, pad.t + 2, Math.min(300, w - pad.l - pad.r - 12), runs.length * 14 + 8);
    g.globalAlpha = 1; g.strokeStyle = col("line-soft"); g.lineWidth = 1;
    g.strokeRect(lx - 6, pad.t + 2, Math.min(300, w - pad.l - pad.r - 12), runs.length * 14 + 8);
    g.restore();
    runs.forEach(function (r, i) {
      var same = [];
      sigs.forEach(function (sg, j) { if (j !== i && sg === sigs[i]) same.push(runs[j].config.policy.replace("_", " ").toLowerCase()); });
      g.strokeStyle = col(CFG.POLICY_HUE[r.config.policy] || "teal"); g.lineWidth = 2;
      g.beginPath(); g.moveTo(lx, ly - 3); g.lineTo(lx + 16, ly - 3); g.stroke();
      g.fillStyle = col("ink-dim"); g.font = '10px "IBM Plex Mono", monospace'; g.textAlign = "left";
      g.fillText(r.config.policy.replace("_", " ") + (same.length ? "  — identical to " + same.join(" and ") : ""), lx + 22, ly);
      ly += 14;
    });

    /* composition by LENGTH CLASS, as small multiples — required
       whenever policies are compared. */
    var q = prep(cvComp), g2 = q.g, w2 = q.w, h2 = q.h;
    var classes = ["short", "medium", "long"];
    var cw = w2 / runs.length;
    runs.forEach(function (r, ri) {
      var x0 = ri * cw + 8, ww = cw - 16;
      g2.fillStyle = col("ink"); g2.font = '10px "IBM Plex Mono", monospace';
      g2.textAlign = "left";
      g2.fillText(r.config.policy.replace("_", " "), x0, 12);
      classes.forEach(function (cl, ci) {
        var c = r.censoringCompositionByLengthClass[cl];
        var tot = c.served + c.censored;
        var y = 24 + ci * 20, bh = 13;
        g2.strokeStyle = col("line"); g2.lineWidth = 1;
        g2.strokeRect(x0 + 62, y, ww - 62, bh);
        if (tot) {
          g2.fillStyle = col("teal");
          g2.fillRect(x0 + 62, y, (ww - 62) * c.served / tot, bh);
        }
        g2.fillStyle = col("muted"); g2.font = '9px "IBM Plex Mono", monospace';
        g2.textAlign = "left";
        g2.fillText(cl.toUpperCase(), x0, y + 10);
        g2.fillStyle = col("ink-dim");
        g2.textAlign = "right";
        g2.fillText(tot ? (100 * c.served / tot).toFixed(0) + "%" : "—", x0 + ww, y + 10);
      });
    });
  }

  global.FerryCharts = {
    survivalUnit: survivalUnit,
    observedPair: observedPair,
    queueTimeline: queueTimeline,
    loadStrip: loadStrip,
    bars: bars,
    throughput: throughput,
    comparePolicies: comparePolicies,
    reducedMotion: reduced
  };
})(typeof window !== "undefined" ? window : globalThis);
