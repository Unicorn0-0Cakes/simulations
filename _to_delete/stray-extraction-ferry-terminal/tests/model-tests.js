/* =====================================================================
   FERRY TERMINAL — model tests
   ---------------------------------------------------------------------
   The regression suite VAL-FERRY-2026-09-02-B required to be preserved,
   re-expressed against the JavaScript model. Runs in a browser via
   model-tests.html and in node via `node tests/model-tests.js`.

   Every assertion states the property it protects. The arrival-count
   dispersion test is the one that would have caught the original
   BLOCKER at build time and MUST NOT be removed.
   ===================================================================== */
(function (global) {
  "use strict";
  var M = global.FerryModel;
  var pass = 0, fail = 0, lines = [];

  function ok(name, cond, detail) {
    if (cond) { pass++; lines.push(["ok", name, detail || ""]); }
    else { fail++; lines.push(["FAIL", name, detail || ""]); }
  }
  function base(over) {
    var c = {
      lam: 40, rho: 1, leadTimeMean: 10, headway: 30, capacityM: 60,
      horizon: 300, warmup: 0, lengthDist: "ALL_EQUAL", equalLengthM: 5,
      bookedFraction: 0, policy: "FCFS", seed: 1, disruption: null
    };
    for (var k in (over || {})) c[k] = over[k];
    return c;
  }
  function mean(a) { var s = 0; for (var i = 0; i < a.length; i++) s += a[i]; return a.length ? s / a.length : 0; }
  function variance(a) { var m = mean(a), s = 0; for (var i = 0; i < a.length; i++) s += (a[i] - m) * (a[i] - m); return a.length > 1 ? s / (a.length - 1) : 0; }
  /* lambda in vehicles/hour that puts the load ratio at u, for equal lengths */
  function lamFor(u, capM, headway, lenM) { return u * (capM / lenM) * 60 / headway; }

  /* == 1. D1 — arrival-count dispersion ==============================
     THE TEST THAT WOULD HAVE CAUGHT THE ORIGINAL BLOCKER.
     A genuine Poisson process has a random count with variance of order
     lambda*T. An order-statistics process has variance identically zero. */
  (function () {
    var counts = [];
    for (var s = 1; s <= 60; s++) counts.push(M.generateArrivals(base({ seed: s, rho: 1, lam: 60, horizon: 300 })).length);
    var lamT = (60 / 60) * 300;
    var v = variance(counts), m = mean(counts);
    ok("arrival count varies across seeds (D1)", v > 0.2 * lamT,
       "variance=" + v.toFixed(1) + " vs lambda*T=" + lamT.toFixed(1));
    ok("arrival count is centred on lambda*T (D1)", Math.abs(m - lamT) < 0.10 * lamT,
       "mean=" + m.toFixed(1));
    ok("arrival count is not constant (D1)", new Set(counts).size > 20,
       "distinct counts=" + new Set(counts).size);
  })();

  /* == 2. D1 — the TARGETED component is random too ================== */
  (function () {
    var counts = [];
    for (var s = 1; s <= 60; s++) counts.push(M.generateArrivals(base({ seed: s, rho: 0, lam: 60, horizon: 300 })).length);
    ok("targeted-component count is random (D1)", variance(counts) > 20,
       "variance=" + variance(counts).toFixed(1));
  })();

  /* == 3. policy isolation ==========================================
     Changing ONLY the policy must leave the arrival realisation
     bit-identical, or a comparison attributes randomness to the control. */
  (function () {
    var sig = {}, keys = ["FCFS", "CLASS_PRIORITY", "SIZE_AWARE"];
    keys.forEach(function (p) {
      var a = M.run(base({ policy: p, seed: 42, lengthDist: "MIXED", capacityM: 60 })).arrivals;
      sig[p] = a.map(function (v) { return v.vid + ":" + v.arrivalTime.toFixed(9) + ":" + v.lengthCm; }).join("|");
    });
    var distinct = new Set(keys.map(function (p) { return sig[p]; }));
    ok("all three policies share one arrival realisation", distinct.size === 1,
       "distinct realisations=" + distinct.size);
  })();

  /* == 4. seeded reproducibility ===================================== */
  (function () {
    var a = JSON.stringify(M.run(base({ seed: 99, lengthDist: "MIXED" })).timeToServiceObserved);
    var b = JSON.stringify(M.run(base({ seed: 99, lengthDist: "MIXED" })).timeToServiceObserved);
    var c = JSON.stringify(M.run(base({ seed: 100, lengthDist: "MIXED" })).timeToServiceObserved);
    ok("same seed reproduces the run exactly", a === b);
    ok("a different seed produces a different run", a !== c);
  })();

  /* == 5. degenerate capacity equivalence ============================
     With all vehicles equal, lane-metre capacity must reduce EXACTLY to
     unit-count capacity: 50 m / 5 m = 10 vehicles on a saturated sailing. */
  (function () {
    var r = M.run(base({ capacityM: 50, equalLengthM: 5, lam: 200, rho: 1, seed: 5 }));
    var saturated = r.sailings.filter(function (s) { return s.denied > 0; });
    var allTen = saturated.length > 0 && saturated.every(function (s) { return s.manifest.length === 10; });
    ok("lane-metre capacity reduces to unit count when lengths are equal",
       allTen, "saturated sailings=" + saturated.length +
       " loads=" + saturated.map(function (s) { return s.manifest.length; }).join(","));
  })();

  /* == 6. D2 — load ratio available under EVERY length distribution === */
  (function () {
    var r = M.run(base({ lengthDist: "MIXED", lam: 20, capacityM: 120, seed: 3 }));
    ok("load ratio is finite under MIXED lengths (D2)", isFinite(r.loadRatio) && r.loadRatio > 0,
       "loadRatio=" + r.loadRatio.toFixed(3));
    ok("a light MIXED run reports stable with nothing unserved (D2)",
       r.stable === true && r.unservedAtHorizon === 0,
       "stable=" + r.stable + " unserved=" + r.unservedAtHorizon);
    var eq = M.run(base({ lengthDist: "ALL_EQUAL", equalLengthM: 5, lam: 20, capacityM: 120, seed: 3 }));
    ok("expected-length load ratio reduces to the equal-length ratio",
       Math.abs(eq.loadRatio - (20 / 60) * 30 / (12000 / 500)) < 1e-9,
       "loadRatio=" + eq.loadRatio.toFixed(6));
  })();

  /* == 7. D3 — disruption chronology ================================
     A delay larger than one headway must not let a sailing be processed
     before one that departs earlier. Identity k is preserved. */
  (function () {
    var r = M.run(base({ headway: 30, horizon: 200, disruption: { sailing: 2, mode: "DELAYED", delay: 75 } }));
    var times = r.sailings.slice().sort(function (a, b) { return (a.scheduledTime - b.scheduledTime) || (a.k - b.k); })
      .map(function (s) { return s.scheduledTime; });
    ok("delayed sailing is processed in departure order (D3)",
       times.join(",") === "30,60,120,150,165,180", "order=" + times.join(","));
    var ks = r.sailings.map(function (s) { return s.k; });
    ok("sailing identity survives the reordering (D3)", ks.join(",") === "0,1,2,3,4,5", "k=" + ks.join(","));
  })();

  /* == 8. D4 — censoring recovery =================================== */
  (function () {
    var r = M.run(base({ lam: 200, rho: 1, capacityM: 40, seed: 11 }));
    var post = r.arrivals.filter(function (v) { return v.arrivalTime >= r.config.warmup; });
    var nCens = post.filter(function (v) { return v.sailTime === null; }).length;
    ok("a censored lower bound exists for every unserved vehicle (D4)",
       r.timeToServiceCensoredLowerBounds.length === nCens,
       "bounds=" + r.timeToServiceCensoredLowerBounds.length + " unserved=" + nCens);
    ok("censored bounds are all non-negative (D4)",
       r.timeToServiceCensoredLowerBounds.every(function (t) { return t >= 0; }));
    ok("served and censored fractions sum to one (D4)",
       Math.abs(r.servedFraction + r.censoredFraction - 1) < 1e-12);
  })();

  /* == 9. D4 — Kaplan-Meier monotonicity ============================ */
  (function () {
    var r = M.run(base({ lam: 200, rho: 1, capacityM: 40, seed: 13 }));
    var mono = true, prev = 1.0001;
    r.timeToServiceKM.forEach(function (p) { if (p.survival > prev + 1e-12) mono = false; prev = p.survival; });
    ok("the Kaplan-Meier estimate is monotonically non-increasing (D4)", mono);
    ok("the survival estimate starts at or below 1 (D4)",
       r.timeToServiceKM.length === 0 || r.timeToServiceKM[0].survival <= 1);
  })();

  /* == 10. D4 — KM reduces to the empirical distribution at zero censoring == */
  (function () {
    var r = M.run(base({ lam: 10, rho: 1, capacityM: 200, horizon: 300, seed: 17 }));
    ok("this control run has no censoring", r.censoredFraction === 0, "censored=" + r.censoredFraction);
    var obs = r.timeToServiceObserved, n = obs.length, worst = 0;
    r.timeToServiceKM.forEach(function (p) {
      var emp = obs.filter(function (t) { return t > p.t; }).length / n;
      worst = Math.max(worst, Math.abs(p.survival - emp));
    });
    ok("with zero censoring KM equals the empirical survivor function (D4)",
       worst < 1e-9, "max deviation=" + worst.toExponential(2));
  })();

  /* == 11. D4 — censoring composition by length class ================ */
  (function () {
    var r = M.run(base({ lengthDist: "MIXED", lam: 150, rho: 1, capacityM: 40, seed: 19 }));
    var c = r.censoringCompositionByLengthClass;
    var total = ["short", "medium", "long"].reduce(function (a, k) { return a + c[k].served + c[k].censored; }, 0);
    var post = r.arrivals.filter(function (v) { return v.arrivalTime >= r.config.warmup; }).length;
    ok("composition partitions every post-warm-up vehicle (D4)", total === post,
       "composition=" + total + " post-warm-up=" + post);
    ok("composition reports all three length classes (D4)",
       c.short !== undefined && c.medium !== undefined && c.long !== undefined);
  })();

  /* == 12. long-vehicle service rate whenever policies are compared ===
     This is the measure that exposed the SIZE_AWARE survivorship bias. */
  (function () {
    var cfgs = ["FCFS", "SIZE_AWARE"].map(function (p) {
      return M.run(base({ policy: p, lengthDist: "MIXED", lam: 150, rho: 1, capacityM: 40, seed: 23 }));
    });
    var rates = cfgs.map(M.longVehicleServiceRate);
    ok("a long-vehicle service rate is available for every compared policy",
       rates.every(function (x) { return x !== null; }),
       "rates=" + rates.map(function (x) { return x === null ? "null" : x.toFixed(4); }).join(" / "));
    ok("SIZE_AWARE does not serve long vehicles at FCFS's rate",
       rates[1] <= rates[0], "FCFS=" + rates[0].toFixed(4) + " SIZE_AWARE=" + rates[1].toFixed(4));
  })();

  /* == 13. conservation under adversarial disruption ==================
     First, middle and last sailing, across all three disruption modes. */
  (function () {
    var horizon = 200, headway = 30, n = Math.floor(horizon / headway);
    var idx = [0, Math.floor(n / 2), n - 1];
    var modes = [{ mode: "CANCELLED" }, { mode: "REDUCED", factor: 0.25 }, { mode: "DELAYED", delay: 75 }];
    var okAll = true, checked = 0, why = "";
    idx.forEach(function (k) {
      modes.forEach(function (m) {
        var d = { sailing: k, mode: m.mode, factor: m.factor, delay: m.delay };
        try {
          var r = M.run(base({ horizon: horizon, headway: headway, lam: 150, rho: 1, capacityM: 40, seed: 29, disruption: d, lengthDist: "MIXED" }));
          checked++;
          if (r.nSailed + r.unservedAtHorizon !== r.nArrived) { okAll = false; why = "k=" + k + " " + m.mode; }
        } catch (e) { okAll = false; why = "threw on k=" + k + " " + m.mode + ": " + e.message; }
      });
    });
    ok("conservation holds under nine adversarial disruption configurations",
       okAll && checked === 9, "checked=" + checked + (why ? " " + why : ""));
  })();

  /* == 14. stability signature ======================================
     The corrected criterion. Stage 05's first attempt asserted that
     unserved == 0 strictly below the boundary; that was wrong, because a
     finite horizon leaves vehicles in the queue at the edge. What holds
     is the SIGNATURE: a small, roughly flat count below the boundary and
     an order-of-magnitude climb above it. The initially mistaken
     expectation is preserved in the historical validation record. */
  (function () {
    var C = 60, h = 30, L = 5, T = 600;
    var below = [0.6, 0.8, 0.95].map(function (u) {
      return M.run(base({ lam: lamFor(u, C, h, L), rho: 1, capacityM: C, headway: h, equalLengthM: L, horizon: T, seed: 31 })).unservedAtHorizon;
    });
    var above = [1.1, 1.3, 1.8, 3.0].map(function (u) {
      return M.run(base({ lam: lamFor(u, C, h, L), rho: 1, capacityM: C, headway: h, equalLengthM: L, horizon: T, seed: 31 })).unservedAtHorizon;
    });
    var maxBelow = Math.max.apply(null, below), minAbove = Math.min.apply(null, above);
    ok("unserved count below the stability boundary stays small and flat",
       maxBelow <= 30, "below=[" + below.join(", ") + "]");
    ok("unserved count climbs by an order of magnitude above the boundary",
       minAbove > maxBelow && above[above.length - 1] > 5 * Math.max(1, maxBelow),
       "above=[" + above.join(", ") + "]");
    ok("the stability flag agrees with the load ratio at the boundary",
       M.run(base({ lam: lamFor(0.95, C, h, L), capacityM: C, headway: h, equalLengthM: L, horizon: T, seed: 31 })).stable === true &&
       M.run(base({ lam: lamFor(1.30, C, h, L), capacityM: C, headway: h, equalLengthM: L, horizon: T, seed: 31 })).stable === false);
  })();

  /* == 15. capacity guard =========================================== */
  (function () {
    var threw = false, msg = "";
    try { M.run(base({ capacityM: 3, equalLengthM: 5 })); } catch (e) { threw = true; msg = e.message; }
    ok("capacity below the maximum vehicle length blocks the run", threw, msg);
    var threwMixed = false;
    try { M.run(base({ lengthDist: "MIXED", capacityM: 10 })); } catch (e) { threwMixed = true; }
    ok("the guard uses the maximum of the MIXED set, not the mean", threwMixed);
  })();

  /* == 16. measure separation ======================================== */
  (function () {
    var r = M.run(base({ lam: 150, rho: 1, capacityM: 40, seed: 37 }));
    ok("denied boarding is reported per sailing", Array.isArray(r.deniedBoardingPerSailing));
    ok("unserved at horizon is a single distinct scalar", typeof r.unservedAtHorizon === "number");
    var summed = r.deniedBoardingPerSailing.reduce(function (a, b) { return a + b; }, 0);
    ok("the two missed-departure measures are distinct quantities",
       summed !== r.unservedAtHorizon,
       "sum(denied)=" + summed + " unserved=" + r.unservedAtHorizon);
  })();

  /* == 17. warm-up excludes the empty start ========================== */
  (function () {
    var a = M.run(base({ warmup: 0, seed: 41 }));
    var b = M.run(base({ warmup: 60, seed: 41 }));
    ok("warm-up removes early arrivals from the statistics",
       b.timeToServiceObserved.length <= a.timeToServiceObserved.length,
       "n=" + a.timeToServiceObserved.length + " -> " + b.timeToServiceObserved.length);
    ok("warm-up does not change the realisation",
       a.nArrived === b.nArrived, "arrived " + a.nArrived + " vs " + b.nArrived);
  })();

  var result = { pass: pass, fail: fail, lines: lines };
  global.FerryModelTests = result;

  if (typeof document === "undefined") {
    lines.forEach(function (l) { console.log((l[0] === "ok" ? "  ok  " : "  FAIL") + "  " + l[1] + (l[2] ? "   [" + l[2] + "]" : "")); });
    console.log("\n" + pass + " passed, " + fail + " failed");
    if (typeof process !== "undefined") process.exitCode = fail ? 1 : 0;
  }
})(typeof window !== "undefined" ? window : globalThis);
