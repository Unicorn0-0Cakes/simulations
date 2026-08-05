  /* ==================================================================
     8. THE SEARCH

     Why this is not one grid over (axis, rate).

     A chronology with two dozen boundaries is a very long ruler. A rate
     error of one part in fifty displaces the outermost boundary of a
     100 km profile by four kilometres, which is wider than the short
     subchrons out there, and the residual jumps from the noise floor to
     the full variance of the data. The misfit surface is a needle. Any
     grid coarse enough to be quick steps straight over it, and a grid
     fine enough to catch it has of order a million nodes.

     So the search works outward from the axis, in the order a person
     works:

       A  Find the axial anomaly. Fit ONE normally magnetised block —
          the youngest chron — against the profile, scanning its centre
          and its width. Over one block the misfit is smooth and the
          scan is cheap. Keep the best few centres, not just the best,
          because a near-miss here is common.
       B  Let that block become two half-widths, one per flank, so an
          asymmetric axis is not forced to be symmetric.
       C  Bring in the full chronology one flank at a time, and grow the
          window outward in three passes: about 1.6 Ma of crust, then
          3.5 Ma, then everything. Each pass refines that flank's rate
          against the window the previous pass has already registered.
       D  Rescore every survivor on the whole profile, so that models
          which took different routes are compared on the same data.
       E  Refine axis and both rates jointly.

     Every candidate WITHIN a stage is scored on the same sample mask,
     so their residual sums are comparable. Comparing a fit on a narrow
     window against a fit on a wide one would be meaningless and the
     code never does it.

     Exposed as a stepped object so the interface can run it across
     animation frames and never freeze the page.
     =============================================================== */
  function makeSearch(data, opts) {
    opts = opts || {};
    var g = geometry(opts.sensorAltitudeKm, opts.layerThicknessKm, opts.effInclinationDeg);
    var table = edgeTable(g, 420, 0.02);
    var chronKey = opts.chronology || "published";
    var chron = chronologyByKey(chronKey, opts.chronologySeed || 1);
    var baseMask = opts.fitMask || data.w;
    var asymmetric = !!opts.asymmetric;
    var TOPK = 4;

    /* Duration of the youngest normal chron, which is what the
       single-block template in stage A is a template OF. Read from the
       chronology rather than hard-coded, so a synthetic sequence gets
       its own value. */
    var axialDurationMa = (chron.normalIntervals[0] && chron.normalIntervals[0].t1) || 0.78;

    var xmin = Infinity, xmax = -Infinity, i;
    for (i = 0; i < data.n; i++) {
      if (!baseMask[i]) continue;
      if (data.x[i] < xmin) xmin = data.x[i];
      if (data.x[i] > xmax) xmax = data.x[i];
    }
    var span = xmax - xmin;

    /* ---- masks --------------------------------------------------- */
    function windowMask(c, halfWidth, side, stride) {
      var m = new Uint8Array(data.n), k = 0;
      for (var j = 0; j < data.n; j++) {
        if (!baseMask[j]) continue;
        if (halfWidth > 0 && Math.abs(data.x[j] - c) > halfWidth) continue;
        if (side < 0 && data.x[j] >= c) continue;
        if (side > 0 && data.x[j] < c) continue;
        if (stride > 1 && (j % stride) !== 0) continue;
        m[j] = 1; k++;
      }
      return k >= 10 ? m : null;
    }
    function decimated(stride) {
      var m = new Uint8Array(data.n);
      for (var j = 0; j < data.n; j++) m[j] = (baseMask[j] && (j % stride) === 0) ? 1 : 0;
      return m;
    }

    /* ---- scoring ------------------------------------------------- */
    function scoreColumn(col, mask, cand) {
      var f = fitLinear(data, [col], mask);
      if (!f) return null;
      var st = evaluateCandidateModel(data.y, f.pred, mask, data.tid);
      if (!isFinite(st.rss)) return null;
      return { cand: cand, fit: f, stats: st, rss: st.rss, column: col };
    }

    /* One block, unit magnetisation: the axial-anomaly template. */
    function templateScore(axis, wL, wR, mask) {
      var blocks = [{ x1: axis - wL, x2: axis + wR, J: 1 }];
      var col = forwardMagneticProfileFast(blocks, data.x, table);
      return scoreColumn(col, mask, { axisKm: axis, wL: wL, wR: wR });
    }

    /* The full chronology. */
    function fullScore(axis, rL, rR, mask) {
      var cand = {
        generator: "spreading", axisKm: axis,
        halfRateLeftCmYr: rL, halfRateRightCmYr: rR,
        effInclinationDeg: opts.effInclinationDeg,
        layerThicknessKm: opts.layerThicknessKm,
        chronology: chronKey, seed: opts.chronologySeed || 1
      };
      return scoreColumn(structuralColumn(data, cand, table), mask, cand);
    }

    function geomSeq(lo, hi, ratio) {
      var out = [], v = lo;
      while (v <= hi * 1.0001 && out.length < 5000) { out.push(v); v *= ratio; }
      return out;
    }
    function linSeq(c, half, n) {
      var out = [];
      for (var k = 0; k < n; k++) out.push(c - half + (2 * half) * (n === 1 ? 0.5 : k / (n - 1)));
      return out;
    }
    function rateToWidth(r) { return 10 * r * axialDurationMa; }
    function widthToRate(w) { return w / (10 * axialDurationMa); }

    /* Keep the best few, forced apart, so four near-copies of one local
       minimum do not crowd out a genuinely different explanation. */
    function harvest(list, k, sepKm, sepRel) {
      list.sort(function (a, b) { return a.rss - b.rss; });
      var keep = [];
      for (var j = 0; j < list.length && keep.length < k; j++) {
        var c = list[j], clash = false;
        for (var m = 0; m < keep.length; m++) {
          var a = keep[m].cand, b = c.cand;
          var wa = (a.wL !== undefined) ? (a.wL + a.wR) : (a.halfRateLeftCmYr + a.halfRateRightCmYr);
          var wb = (b.wL !== undefined) ? (b.wL + b.wR) : (b.halfRateLeftCmYr + b.halfRateRightCmYr);
          if (Math.abs(a.axisKm - b.axisKm) < (sepKm || 5) &&
              Math.abs(wa - wb) < (sepRel || 0.10) * wa) { clash = true; break; }
        }
        if (!clash) keep.push(c);
      }
      return keep;
    }

    /* ---- state machine ------------------------------------------- */
    var stage = "A", queue = [], qi = 0, stageMask = null, stageBest = [],
        pool = [], best = null, done = false, seen = 0, planned = 1;
    var parentIndex = 0, flank = -1, pass = 0;

    function buildA() {
      stageMask = decimated(span > 120 ? 4 : 2);
      var widths = geomSeq(rateToWidth(0.5), rateToWidth(8.0), 1.05);
      var step = Math.max(0.5, span / 260);
      queue = [];
      for (var a = xmin - 0.06 * span; a <= xmax + 0.06 * span; a += step) {
        for (var k = 0; k < widths.length; k++) queue.push({ kind: "T", axis: a, wL: widths[k], wR: widths[k] });
      }
      qi = 0; stageBest = [];
      planned = queue.length * 1.6;
    }

    function buildB() {
      var p = pool[parentIndex];
      stageMask = decimated(2);
      var axes = linSeq(p.cand.axisKm, Math.max(1.5, 0.12 * p.cand.wL), 13);
      var wl = asymmetric ? linSeq(p.cand.wL, 0.32 * p.cand.wL, 13) : [p.cand.wL];
      var wr = asymmetric ? linSeq(p.cand.wR, 0.32 * p.cand.wR, 13) : [p.cand.wR];
      queue = [];
      for (var a = 0; a < axes.length; a++)
        for (var l = 0; l < wl.length; l++)
          for (var r = 0; r < wr.length; r++)
            queue.push({ kind: "T", axis: axes[a], wL: wl[l], wR: wr[r] });
      if (!asymmetric) {
        /* symmetric: sweep the shared width instead */
        var ws = linSeq(p.cand.wL, 0.32 * p.cand.wL, 41);
        queue = [];
        for (a = 0; a < axes.length; a++)
          for (l = 0; l < ws.length; l++)
            queue.push({ kind: "T", axis: axes[a], wL: ws[l], wR: ws[l] });
      }
      qi = 0; stageBest = [];
    }

    /* Pass windows, in Ma of crust. The last is the whole profile. */
    var PASS_MA = [1.7, 3.6, 0];
    var PASS_TOL = [0.22, 0.045, 0.012];
    var PASS_N = [61, 61, 41];

    function buildC() {
      var p = pool[parentIndex];
      var a0 = p.cand.axisKm;
      var rL = p.cand.halfRateLeftCmYr, rR = p.cand.halfRateRightCmYr;
      var r = flank < 0 ? rL : rR;
      var ma = PASS_MA[pass];
      var half = ma > 0 ? Math.min(span, 10 * r * ma) : 0;
      stageMask = windowMask(a0, half, asymmetric ? flank : 0, 1) || baseMask;
      var rates = linSeq(r, PASS_TOL[pass] * r, PASS_N[pass]);
      queue = [];
      for (var k = 0; k < rates.length; k++) {
        if (!asymmetric) queue.push({ kind: "F", axis: a0, rL: rates[k], rR: rates[k] });
        else if (flank < 0) queue.push({ kind: "F", axis: a0, rL: rates[k], rR: rR });
        else queue.push({ kind: "F", axis: a0, rL: rL, rR: rates[k] });
      }
      qi = 0; stageBest = [];
    }

    function buildD() {
      stageMask = baseMask;
      queue = [];
      for (var j = 0; j < pool.length; j++) {
        queue.push({ kind: "F", axis: pool[j].cand.axisKm,
                     rL: pool[j].cand.halfRateLeftCmYr, rR: pool[j].cand.halfRateRightCmYr });
      }
      qi = 0; stageBest = [];
    }

    function buildE() {
      stageMask = baseMask;
      var rL = best.cand.halfRateLeftCmYr, rR = best.cand.halfRateRightCmYr;
      var axes = linSeq(best.cand.axisKm, 1.2, 13);
      var ls = linSeq(rL, 0.008 * rL, asymmetric ? 9 : 13);
      var rs = asymmetric ? linSeq(rR, 0.008 * rR, 9) : null;
      queue = [];
      for (var a = 0; a < axes.length; a++) {
        for (var l = 0; l < ls.length; l++) {
          if (!asymmetric) queue.push({ kind: "F", axis: axes[a], rL: ls[l], rR: ls[l] });
          else for (var q = 0; q < rs.length; q++)
            queue.push({ kind: "F", axis: axes[a], rL: ls[l], rR: rs[q] });
        }
      }
      qi = 0; stageBest = [];
    }

    function run(job) {
      if (job.kind === "T") return templateScore(job.axis, job.wL, job.wR, stageMask);
      return fullScore(job.axis, job.rL, job.rR, stageMask);
    }

    /* Template results carry widths; convert them once, here, so the
       rest of the machine only ever sees rates. */
    function templateToRates(c) {
      return { axisKm: c.axisKm,
               halfRateLeftCmYr: Math.max(0.2, widthToRate(c.wL)),
               halfRateRightCmYr: Math.max(0.2, widthToRate(c.wR)) };
    }

    function advance() {
      var top;
      switch (stage) {
        case "A":
          pool = harvest(stageBest, TOPK, Math.max(4, 0.03 * span), 0.12);
          if (!pool.length) { done = true; return; }
          parentIndex = 0; stage = "B"; buildB();
          return;
        case "B":
          top = harvest(stageBest, 1)[0];
          if (top) pool[parentIndex] = { cand: templateToRates(top.cand), rss: top.rss };
          else pool[parentIndex] = { cand: templateToRates(pool[parentIndex].cand), rss: Infinity };
          parentIndex++;
          if (parentIndex < pool.length) { buildB(); }
          else { parentIndex = 0; flank = asymmetric ? -1 : 0; pass = 0; stage = "C"; buildC(); }
          return;
        case "C":
          top = harvest(stageBest, 1)[0];
          if (top) {
            pool[parentIndex].cand.axisKm = top.cand.axisKm;
            pool[parentIndex].cand.halfRateLeftCmYr = top.cand.halfRateLeftCmYr;
            pool[parentIndex].cand.halfRateRightCmYr = top.cand.halfRateRightCmYr;
          }
          if (asymmetric && flank < 0) { flank = 1; buildC(); return; }
          if (asymmetric) flank = -1;
          pass++;
          if (pass < PASS_MA.length) { buildC(); return; }
          parentIndex++;
          if (parentIndex < pool.length) { pass = 0; flank = asymmetric ? -1 : 0; buildC(); return; }
          stage = "D"; buildD();
          return;
        case "D":
          top = harvest(stageBest, 1)[0];
          if (!top) { done = true; return; }
          best = top; stage = "E"; buildE();
          return;
        default:
          top = harvest(stageBest, 1)[0];
          if (top && top.rss < best.rss) best = top;
          done = true;
          return;
      }
    }

    return {
      progress: function () { return done ? 1 : Math.min(0.98, seen / planned); },
      done: function () { return done; },
      best: function () { return best; },
      stage: function () { return stage; },
      step: function (budget) {
        var count = 0;
        while (!done && count < budget) {
          if (qi >= queue.length) { advance(); continue; }
          var s = run(queue[qi++]);
          count++; seen++;
          if (s) stageBest.push(s);
          if (stage === "A" && stageBest.length > 3000) stageBest = harvest(stageBest, TOPK * 5, 3, 0.06);
        }
        return done;
      },
      runToCompletion: function (maxIter) {
        var guard = maxIter || 100000;
        while (!done && guard-- > 0) this.step(800);
        return best;
      }
    };
  }
