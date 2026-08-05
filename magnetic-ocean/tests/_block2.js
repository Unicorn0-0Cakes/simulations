  /* ==================================================================
     8. THE SEARCH

     Why this is not one grid over (axis, rate).

     A chronology with two dozen boundaries is a very long ruler. A rate
     error of one part in fifty displaces the outermost boundary of a
     100 km profile by four kilometres — wider than the short subchrons
     out there — and the residual jumps from the noise floor to the full
     variance of the data. The misfit surface is a needle. A grid coarse
     enough to be quick steps straight over it; a grid fine enough to
     catch it has of order a million nodes, and three million if the two
     flanks are allowed to differ.

     So the search works outward from the axis, the way a person works:

       A  For each candidate ridge position, treat the two flanks
          separately. On each flank, sweep the whole rate range against
          a window holding roughly 1.7 Ma of crust on that side, and
          keep that flank's best rate. Score the position by how much of
          the variance the two flanks together explain. Over that short
          a window the misfit is a smooth function of the rate, so a
          coarse sweep finds the neighbourhood.

          Because each candidate rate brings its own window with it, the
          scores are divided by the residual of a nuisance-only fit on
          exactly the same samples. Comparing a raw residual from a
          40 km window with one from a 100 km window would be
          meaningless, and the code never does it.

       B  Open the window to about seventy per cent of the profile and
          refine the axis and both rates together. Unequal flanks make
          those three strongly coupled: move the axis a kilometre and
          both rates want to follow, so refining them one at a time
          converges on a compromise that fits neither side.

       C  Open the window to the whole profile — the pass where the long
          ruler finally bites — and refine again, ten times finer.

       D  Rescore every survivor on the whole profile, so candidates that
          took different routes are compared on the same data.

       E  A last joint refinement of the winner.

     Every candidate WITHIN a stage is scored on the same samples, or on
     a normalised statistic when it cannot be.

     Exposed as a stepped object so the interface can run it across
     animation frames and never freeze the page.
     =============================================================== */
  function makeSearch(data, opts) {
    opts = opts || {};
    var g = geometry(opts.sensorAltitudeKm, opts.layerThicknessKm, opts.effInclinationDeg);
    var table = edgeTable(g, 420, 0.02);
    var chronKey = opts.chronology || "published";
    var baseMask = opts.fitMask || data.w;
    var asymmetric = !!opts.asymmetric;
    var TOPK = asymmetric ? 2 : 3;

    var RATE_MIN = 0.5, RATE_MAX = 8.0;

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
      return k >= 24 ? m : null;
    }

    /* ---- scoring -------------------------------------------------- */
    function scoreAt(axis, rL, rR, mask, normalise) {
      var cand = {
        generator: "spreading", axisKm: axis,
        halfRateLeftCmYr: rL, halfRateRightCmYr: rR,
        effInclinationDeg: opts.effInclinationDeg,
        layerThicknessKm: opts.layerThicknessKm,
        chronology: chronKey, seed: opts.chronologySeed || 1
      };
      var col = structuralColumn(data, cand, table, mask);
      var f = fitLinear(data, [col], mask);
      if (!f) return null;
      var st = evaluateCandidateModel(data.y, f.pred, mask, data.tid);
      if (!isFinite(st.rss)) return null;
      var rank = st.rss;
      if (normalise) {
        var f0 = fitLinear(data, [], mask);
        if (!f0) return null;
        var st0 = evaluateCandidateModel(data.y, f0.pred, mask, data.tid);
        if (!(st0.rss > 0)) return null;
        rank = st.rss / st0.rss;
      }
      return { cand: cand, fit: f, stats: st, rss: rank, rawRss: st.rss, column: col };
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
    function harvest(list, k, sepKm) {
      list.sort(function (a, b) { return a.rss - b.rss; });
      var keep = [];
      for (var j = 0; j < list.length && keep.length < k; j++) {
        var clash = false;
        for (var m = 0; m < keep.length; m++) {
          if (Math.abs(keep[m].cand.axisKm - list[j].cand.axisKm) < (sepKm || 0)) { clash = true; break; }
        }
        if (!clash) keep.push(list[j]);
      }
      return keep;
    }

    /* ---- state ---------------------------------------------------- */
    var stage = "A", queue = [], qi = 0, stageMask = null, stageBest = [],
        pool = [], best = null, done = false, seen = 0, planned = 1;
    var parentIndex = 0, pass = 0;

    /* Stage A is organised as one job per candidate ridge position; each
       job runs both flank sweeps itself, because the two sweeps have to
       be added together before the position means anything. */
    var A_RATES = geomSeq(RATE_MIN, RATE_MAX, 1.045);
    var A_STRIDE = data.used > 500 ? 3 : (data.used > 260 ? 2 : 1);

    function buildA() {
      var step = Math.max(1.0, span / 110);
      queue = [];
      for (var a = xmin + 0.04 * span; a <= xmax - 0.04 * span; a += step) queue.push({ kind: "A", axis: a });
      qi = 0; stageBest = [];
      planned = queue.length * A_RATES.length * 2 * 1.5;
    }

    function runA(job) {
      var a = job.axis, k, s;
      var bestL = null, bestR = null;
      for (k = 0; k < A_RATES.length; k++) {
        var r = A_RATES[k];
        var half = Math.max(25, Math.min(0.55 * span, 10 * r * 1.7));
        var mL = windowMask(a, half, -1, A_STRIDE);
        if (mL) { s = scoreAt(a, r, 2, mL, true); if (s && (!bestL || s.rss < bestL.rss)) bestL = s; }
        var mR = windowMask(a, half, +1, A_STRIDE);
        if (mR) { s = scoreAt(a, 2, r, mR, true); if (s && (!bestR || s.rss < bestR.rss)) bestR = s; }
        seen += 2;
      }
      if (!bestL && !bestR) return null;
      var rL = bestL ? bestL.cand.halfRateLeftCmYr : bestR.cand.halfRateRightCmYr;
      var rR = bestR ? bestR.cand.halfRateRightCmYr : rL;
      if (!asymmetric) {
        /* tie the flanks: take whichever side explained more, so a
           symmetric candidate is not handed the average of a good side
           and a bad one */
        var use = (!bestR || (bestL && bestL.rss <= bestR.rss)) ? rL : rR;
        rL = rR = use;
      }
      return {
        cand: { axisKm: a, halfRateLeftCmYr: rL, halfRateRightCmYr: rR },
        rss: (bestL ? bestL.rss : 1) + (bestR ? bestR.rss : 1)
      };
    }

    /* Refinement passes. Window as a fraction of the profile; rate
       tolerance and step chosen so that the step displaces the outermost
       boundary by roughly half a kilometre, and the range covers five
       steps of the pass before. */
    var PASS_FRAC = [0.36, 0.55];
    var PASS_AX   = [2.6, 0.9];
    var PASS_AXN  = [11, 9];
    var PASS_TOL  = [0.032, 0.005];
    var PASS_N    = [asymmetric ? 9 : 17, asymmetric ? 11 : 21];

    function buildRefine(p, frac, axHalf, axN, tol, nRate) {
      stageMask = windowMask(p.cand.axisKm, frac > 0 ? frac * span : 0, 0, 1) || baseMask;
      var axes = linSeq(p.cand.axisKm, axHalf, axN);
      var ls = linSeq(p.cand.halfRateLeftCmYr, tol * p.cand.halfRateLeftCmYr, nRate);
      var rs = asymmetric ? linSeq(p.cand.halfRateRightCmYr, tol * p.cand.halfRateRightCmYr, nRate) : null;
      queue = [];
      for (var a = 0; a < axes.length; a++) {
        for (var l = 0; l < ls.length; l++) {
          if (!asymmetric) queue.push({ kind: "R", axis: axes[a], rL: ls[l], rR: ls[l] });
          else for (var q = 0; q < rs.length; q++)
            queue.push({ kind: "R", axis: axes[a], rL: ls[l], rR: rs[q] });
        }
      }
      qi = 0; stageBest = [];
    }

    function buildB() {
      buildRefine(pool[parentIndex], PASS_FRAC[pass], PASS_AX[pass], PASS_AXN[pass],
                  PASS_TOL[pass], PASS_N[pass]);
    }

    function buildD() {
      stageMask = baseMask;
      queue = [];
      for (var j = 0; j < pool.length; j++) {
        queue.push({ kind: "R", axis: pool[j].cand.axisKm,
                     rL: pool[j].cand.halfRateLeftCmYr, rR: pool[j].cand.halfRateRightCmYr });
      }
      qi = 0; stageBest = [];
    }

    function buildE() {
      stageMask = baseMask;
      var axes = linSeq(best.cand.axisKm, 0.35, 9);
      var ls = linSeq(best.cand.halfRateLeftCmYr, 0.0012 * best.cand.halfRateLeftCmYr, 11);
      var rs = asymmetric ? linSeq(best.cand.halfRateRightCmYr, 0.0012 * best.cand.halfRateRightCmYr, 11) : null;
      queue = [];
      for (var a = 0; a < axes.length; a++)
        for (var l = 0; l < ls.length; l++) {
          if (!asymmetric) queue.push({ kind: "R", axis: axes[a], rL: ls[l], rR: ls[l] });
          else for (var q = 0; q < rs.length; q++)
            queue.push({ kind: "R", axis: axes[a], rL: ls[l], rR: rs[q] });
        }
      qi = 0; stageBest = [];
    }

    function run(job) {
      if (job.kind === "A") return runA(job);
      return scoreAt(job.axis, job.rL, job.rR, stageMask, false);
    }

    function advance() {
      var top;
      switch (stage) {
        case "A":
          pool = harvest(stageBest, TOPK, Math.max(6, 0.04 * span));
          if (!pool.length) { done = true; return; }
          parentIndex = 0; pass = 0; stage = "B"; buildB();
          return;
        case "B":
          top = harvest(stageBest, 1)[0];
          if (top) pool[parentIndex] = { cand: {
            axisKm: top.cand.axisKm,
            halfRateLeftCmYr: top.cand.halfRateLeftCmYr,
            halfRateRightCmYr: top.cand.halfRateRightCmYr }, rss: top.rss };
          pass++;
          if (pass < PASS_FRAC.length) { buildB(); return; }
          parentIndex++;
          if (parentIndex < pool.length) { pass = 0; buildB(); return; }
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

    buildA();

    return {
      progress: function () { return done ? 1 : Math.min(0.98, seen / planned); },
      done: function () { return done; },
      best: function () { return best; },
      stage: function () { return stage; },
      step: function (budget) {
        var count = 0;
        while (!done && count < budget) {
          if (qi >= queue.length) { advance(); continue; }
          var job = queue[qi++];
          var s = run(job);
          count += (job.kind === "A") ? A_RATES.length * 2 : 1;
          if (job.kind !== "A") seen++;
          if (s) stageBest.push(s);
        }
        return done;
      },
      runToCompletion: function (maxIter) {
        var guard = maxIter || 100000;
        while (!done && guard-- > 0) this.step(600);
        return best;
      }
    };
  }
