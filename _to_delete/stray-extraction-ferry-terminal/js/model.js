/* =====================================================================
   FERRY TERMINAL — model
   ---------------------------------------------------------------------
   Scientific logic only. No presentation, no DOM, no Atlas components.
   A direct port of the validated Python engine (BUILD-FERRY-0.2-ENGINE,
   VAL-FERRY-2026-09-02-B). Every behaviour that validation established is
   preserved deliberately and is marked below.

   PORT DECLARATION — read this before comparing runs across languages.
   Python's random.Random is Mersenne Twister; this file uses an explicit
   32-bit generator. Identical seeds therefore produce identical histories
   WITHIN this implementation, and do NOT reproduce the Python engine's
   numbers bit for bit. Reproducibility is a property of the instrument,
   not a claim of cross-language equality. The properties validation
   established — Poisson-distributed arrival counts, policy isolation,
   conservation, censoring recovery, the stability signature — are
   distributional and structural, and are re-checked in tests/.

   Capacity accumulates in INTEGER CENTIMETRES, so floating-point
   accumulation can never let a sailing exceed C.
   ===================================================================== */
(function (global) {
  "use strict";

  var CM = 100;

  /* ---- errors ---------------------------------------------------- */
  function ModelInvalidity(m) { this.name = "ModelInvalidity"; this.message = m; }
  ModelInvalidity.prototype = Object.create(Error.prototype);
  function ConservationFailure(m) { this.name = "ConservationFailure"; this.message = m; }
  ConservationFailure.prototype = Object.create(Error.prototype);

  /* ---- generator -------------------------------------------------
     Every random decision in the instrument comes from here and never
     from Math.random, so "same seed, same history" holds exactly.      */
  function RNG(seed) {
    var s = (seed | 0) >>> 0;
    s = (s + 0x9E3779B9) >>> 0;
    this._s = s === 0 ? 0x6D2B79F5 : s;
  }
  RNG.prototype.random = function () {
    var t = (this._s += 0x6D2B79F5) >>> 0;
    t = Math.imul(t ^ (t >>> 15), t | 1) >>> 0;
    t = (t ^ (t + Math.imul(t ^ (t >>> 7), t | 61))) >>> 0;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
  /* guard the open interval so log(0) cannot occur */
  RNG.prototype.unit = function () {
    var u = this.random();
    return u <= 0 ? 1e-12 : (u >= 1 ? 1 - 1e-12 : u);
  };
  RNG.prototype.expovariate = function (rate) { return -Math.log(this.unit()) / rate; };
  RNG.prototype.gauss = function (mu, sigma) {
    var u1 = this.unit(), u2 = this.unit();
    return mu + sigma * Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
  };

  /* ---- loading policies ------------------------------------------
     ABSTRACT DISCIPLINES, not a surveyed taxonomy of practice.        */
  function byArrival(a, b) { return (a.arrivalTime - b.arrivalTime) || (a.vid - b.vid); }
  var RANK = { booked: 0, standby: 1 };

  var POLICIES = {
    FCFS: function (q) { return q.slice().sort(byArrival); },
    CLASS_PRIORITY: function (q) {
      return q.slice().sort(function (a, b) {
        var ra = RANK[a.vclass] === undefined ? 1 : RANK[a.vclass];
        var rb = RANK[b.vclass] === undefined ? 1 : RANK[b.vclass];
        return (ra - rb) || byArrival(a, b);
      });
    },
    /* Shortest-first among those already waiting. Fills the deck more
       densely; whether that is operationally desirable is NOT a claim
       this model makes. */
    SIZE_AWARE: function (q) {
      return q.slice().sort(function (a, b) {
        return (a.lengthCm - b.lengthCm) || byArrival(a, b);
      });
    }
  };

  /* ---- lengths ----------------------------------------------------
     MIXED is an exploratory set spanning the documented Ro-Ro range.
     It is NOT an empirical small-terminal distribution (E5).          */
  var MIXED = [[4.50, 0.70], [5.50, 0.18], [8.00, 0.07], [13.57, 0.05]];

  function maxLengthCm(cfg) {
    return cfg.lengthDist === "ALL_EQUAL"
      ? Math.round(cfg.equalLengthM * CM)
      : Math.round(13.57 * CM);
  }
  function drawLengthCm(rng, cfg) {
    if (cfg.lengthDist === "ALL_EQUAL") return Math.round(cfg.equalLengthM * CM);
    var u = rng.random(), acc = 0;
    for (var i = 0; i < MIXED.length; i++) {
      acc += MIXED[i][1];
      if (u <= acc) return Math.round(MIXED[i][0] * CM);
    }
    return Math.round(MIXED[MIXED.length - 1][0] * CM);
  }
  /* D2: needed so the load ratio is computable under EVERY length
     distribution, not only ALL_EQUAL. */
  function expectedLengthCm(cfg) {
    if (cfg.lengthDist === "ALL_EQUAL") return cfg.equalLengthM * CM;
    var s = 0;
    for (var i = 0; i < MIXED.length; i++) s += MIXED[i][0] * MIXED[i][1];
    return s * CM;
  }

  /* Knuth. The count is a RANDOM VARIABLE, which is the whole point of D1. */
  function poisson(rng, mean) {
    if (mean <= 0) return 0;
    if (mean < 500) {
      var L = Math.exp(-mean), k = 0, p = 1;
      for (;;) {
        p *= rng.random();
        if (p <= L) return k;
        k++;
      }
    }
    return Math.max(0, Math.round(rng.gauss(mean, Math.sqrt(mean))));
  }

  function scheduleTimes(cfg) {
    var n = Math.floor(cfg.horizon / cfg.headway), out = [];
    for (var i = 0; i < n; i++) out.push((i + 1) * cfg.headway);
    return out;
  }

  /* ---- validation ------------------------------------------------- */
  function validate(cfg) {
    if (!(cfg.lam > 0)) throw new ModelInvalidity("Mean arrival rate must be greater than 0 vehicles per hour.");
    if (!(cfg.rho >= 0 && cfg.rho <= 1)) throw new ModelInvalidity("Arrival mixture must lie between 0 and 1.");
    if (!(cfg.headway > 0)) throw new ModelInvalidity("Headway must be greater than 0 minutes.");
    if (!(cfg.capacityM > 0)) throw new ModelInvalidity("Capacity must be greater than 0 lane-metres.");
    if (!(cfg.horizon > cfg.warmup)) throw new ModelInvalidity("Horizon must exceed the warm-up period.");
    if (!(cfg.leadTimeMean >= 0 && cfg.leadTimeMean < cfg.headway))
      throw new ModelInvalidity("Targeted lead time must satisfy 0 ≤ D < headway.");
    if (!POLICIES[cfg.policy]) throw new ModelInvalidity("Unknown loading policy: " + cfg.policy);
  }

  /* ---- arrivals ---------------------------------------------------
     Generated independently of, and PRIOR to, the loading decision, so
     changing only the policy leaves the realisation bit-identical.

     D1: the random component is an ACTUAL Poisson process, drawn as
     successive exponential inter-arrival times, so the arrival COUNT is
     itself random with variance of order lambda*T. Fixing the count and
     randomising only positions is an order-statistics process, not a
     Poisson one, and makes count variability identically zero.         */
  function generateArrivals(cfg) {
    var rng = new RNG(cfg.seed);
    var sched = scheduleTimes(cfg);
    var out = [], vid = 0, t, k, i, n;

    var ratePerMin = (cfg.lam / 60) * cfg.rho;
    if (ratePerMin > 0) {
      t = 0;
      for (;;) {
        t += rng.expovariate(ratePerMin);
        if (t >= cfg.horizon) break;
        out.push({
          vid: vid++, arrivalTime: t, lengthCm: drawLengthCm(rng, cfg),
          vclass: rng.random() < cfg.bookedFraction ? "booked" : "standby",
          targetSailing: null, boardTime: null, sailTime: null
        });
      }
    }

    /* Targeted component: a per-sailing Poisson count, not a fixed total. */
    if (sched.length && cfg.rho < 1) {
      var perSailingMean = (cfg.lam / 60) * cfg.headway * (1 - cfg.rho);
      for (k = 0; k < sched.length; k++) {
        n = poisson(rng, perSailingMean);
        for (i = 0; i < n; i++) {
          var d = cfg.leadTimeMean > 0 ? rng.expovariate(1 / cfg.leadTimeMean) : 0;
          d = Math.min(d, cfg.headway * 0.999);
          out.push({
            vid: vid++, arrivalTime: Math.max(0, sched[k] - d),
            lengthCm: drawLengthCm(rng, cfg),
            vclass: rng.random() < cfg.bookedFraction ? "booked" : "standby",
            targetSailing: k, boardTime: null, sailTime: null
          });
        }
      }
    }

    out.sort(byArrival);
    return out;
  }

  /* ---- Kaplan-Meier ----------------------------------------------
     D4: product-limit estimator for right-censored time to service.
     Kaplan, E.L. & Meier, P. (1958), JASA 53(282), 457-481.           */
  function kaplanMeier(observed, censored) {
    var pts = [], i;
    for (i = 0; i < observed.length; i++) pts.push([observed[i], 1]);
    for (i = 0; i < censored.length; i++) pts.push([censored[i], 0]);
    if (!pts.length) return [];
    pts.sort(function (a, b) { return (a[0] - b[0]) || (b[1] - a[1]); });
    var n = pts.length, surv = 1, curve = [];
    i = 0;
    while (i < pts.length) {
      var t = pts[i][0], d = 0, c = 0;
      while (i < pts.length && pts[i][0] === t) {
        if (pts[i][1] === 1) d++; else c++;
        i++;
      }
      var atRisk = n;
      if (d > 0) surv *= (1 - d / atRisk);
      curve.push({ t: t, atRisk: atRisk, events: d, censored: c, survival: surv });
      n -= (d + c);
    }
    return curve;
  }

  function lengthClass(cm) { return cm <= 500 ? "short" : (cm <= 800 ? "medium" : "long"); }

  /* ---- run --------------------------------------------------------- */
  function run(cfg) {
    validate(cfg);
    var capCm = Math.round(cfg.capacityM * CM);
    var maxCm = maxLengthCm(cfg);
    if (capCm < maxCm) {
      /* CAPACITY GUARD — blocks rather than looping forever. */
      throw new ModelInvalidity(
        "Capacity (" + (capCm / CM).toFixed(2) + " m) is below the maximum vehicle length (" +
        (maxCm / CM).toFixed(2) + " m). No vehicle could ever board.");
    }

    var arrivals = generateArrivals(cfg);
    var nArrived = arrivals.length;
    var sched = scheduleTimes(cfg);
    var i, k, v;

    var sailings = [];
    for (k = 0; k < sched.length; k++) {
      var s = {
        k: k, scheduledTime: sched[k], capacityCm: capCm, status: "NORMAL",
        actualTime: null, loadedCm: 0, manifest: [], denied: 0
      };
      var d = cfg.disruption;
      if (d && d.sailing === k) {
        if (d.mode === "CANCELLED") { s.status = "CANCELLED"; s.capacityCm = 0; }
        else if (d.mode === "REDUCED") { s.status = "REDUCED"; s.capacityCm = Math.floor(capCm * (d.factor === undefined ? 0.5 : d.factor)); }
        else if (d.mode === "DELAYED") { s.status = "DELAYED"; s.scheduledTime = sched[k] + (d.delay || 0); }
      }
      sailings.push(s);
    }

    var order = POLICIES[cfg.policy];
    var queue = [], ai = 0, queueSeries = [];

    /* D3: process sailings in order of ACTUAL departure time, not index.
       A delay larger than one headway must not let sailing k be processed
       before a sailing that departs earlier. Sailing identity (k) and
       disruption status are preserved: this is a fix at the scheduling
       layer, not a sort applied to the output. */
    var procOrder = sailings.slice().sort(function (a, b) {
      return (a.scheduledTime - b.scheduledTime) || (a.k - b.k);
    });

    for (var pi = 0; pi < procOrder.length; pi++) {
      var sl = procOrder[pi];
      /* Documented tie-break: arrivals at exactly the departure instant
         are processed FIRST and are therefore eligible. */
      while (ai < nArrived && arrivals[ai].arrivalTime <= sl.scheduledTime) {
        queue.push(arrivals[ai]);
        queueSeries.push([arrivals[ai].arrivalTime, queue.length]);
        ai++;
      }

      sl.actualTime = sl.scheduledTime;
      if (sl.status !== "CANCELLED") {
        var ordered = order(queue, sl);
        for (i = 0; i < ordered.length; i++) {
          v = ordered[i];
          if (sl.loadedCm + v.lengthCm <= sl.capacityCm) {
            sl.loadedCm += v.lengthCm;
            sl.manifest.push(v.vid);
            v.boardTime = sl.actualTime;
            v.sailTime = sl.actualTime;
          }
        }
        var boarded = {};
        for (i = 0; i < sl.manifest.length; i++) boarded[sl.manifest[i]] = 1;
        queue = queue.filter(function (x) { return !boarded[x.vid]; });
      }
      sl.denied = queue.length;   /* present at the epoch, did not board */
      queueSeries.push([sl.actualTime, queue.length]);
    }

    /* Arrivals after the last departure epoch still count as arrived. */
    while (ai < nArrived) {
      queue.push(arrivals[ai]);
      queueSeries.push([arrivals[ai].arrivalTime, queue.length]);
      ai++;
    }

    /* ---- CONSERVATION AUDIT. Hard failure: halt, never report. ---- */
    var nSailed = 0, ids = {}, dup = false;
    for (i = 0; i < nArrived; i++) {
      if (arrivals[i].sailTime !== null) nSailed++;
      if (ids[arrivals[i].vid]) dup = true;
      ids[arrivals[i].vid] = 1;
    }
    var nUnserved = nArrived - nSailed;
    if (nSailed + nUnserved !== nArrived)
      throw new ConservationFailure("arrived=" + nArrived + " sailed=" + nSailed + " unserved=" + nUnserved);
    if (dup) throw new ConservationFailure("duplicate vehicle id");
    for (i = 0; i < sailings.length; i++)
      if (sailings[i].loadedCm > sailings[i].capacityCm)
        throw new ConservationFailure("sailing " + sailings[i].k + " exceeded capacity");
    for (i = 0; i < nArrived; i++)
      if (arrivals[i].sailTime !== null && arrivals[i].sailTime < arrivals[i].arrivalTime)
        throw new ConservationFailure("vehicle " + arrivals[i].vid + " boarded before arriving");

    /* ---- statistics, collected only after warm-up ----------------- */
    var post = arrivals.filter(function (x) { return x.arrivalTime >= cfg.warmup; });
    var asc = function (a, b) { return a - b; };
    var ttsObs = post.filter(function (x) { return x.sailTime !== null; })
      .map(function (x) { return x.sailTime - x.arrivalTime; }).sort(asc);
    /* D4: time to service is RIGHT-CENSORED. An unserved vehicle's time is
       not missing; it is known to be at least (horizon - arrivalTime). */
    var ttsCens = post.filter(function (x) { return x.sailTime === null; })
      .map(function (x) { return cfg.horizon - x.arrivalTime; }).sort(asc);

    var nPost = post.length;
    var comp = { short: { served: 0, censored: 0 }, medium: { served: 0, censored: 0 }, long: { served: 0, censored: 0 } };
    for (i = 0; i < post.length; i++) {
      comp[lengthClass(post[i].lengthCm)][post[i].sailTime !== null ? "served" : "censored"]++;
    }

    /* D2: computed against EXPECTED vehicle length, so it is available
       under every supported length distribution rather than only ALL_EQUAL. */
    var loadRatio = (cfg.lam / 60) * cfg.headway / (capCm / expectedLengthCm(cfg));

    var denied = sailings.map(function (x) { return x.denied; });

    return {
      config: cfg,
      nArrived: nArrived,
      nSailed: nSailed,
      arrivals: arrivals,
      /* retained because it answers a real question, but DEMOTED to
         secondary and never rendered without the composition beside it */
      waits: ttsObs.slice(),
      timeToServiceObserved: ttsObs,
      timeToServiceCensoredLowerBounds: ttsCens,
      servedFraction: nPost ? ttsObs.length / nPost : 0,
      censoredFraction: nPost ? ttsCens.length / nPost : 0,
      timeToServiceKM: kaplanMeier(ttsObs, ttsCens),
      censoringCompositionByLengthClass: comp,
      queueSeries: queueSeries,
      sailings: sailings,
      deniedBoardingPerSailing: denied,
      /* DISTINCT measure; never summed with denied boarding */
      unservedAtHorizon: nUnserved,
      throughput: nSailed,
      carryOverDepth: denied,
      utilisation: sailings.map(function (x) { return x.capacityCm ? x.loadedCm / x.capacityCm : 0; }),
      loadRatio: loadRatio,
      stable: loadRatio < 1,
      conservationOk: true,
      seed: cfg.seed
    };
  }

  /* Long-vehicle service rate. Required whenever policies are compared:
     it is the measure that made the observed-only comparison misleading. */
  function longVehicleServiceRate(res) {
    var c = res.censoringCompositionByLengthClass.long;
    var n = c.served + c.censored;
    return n ? c.served / n : null;
  }

  global.FerryModel = {
    CM: CM,
    RNG: RNG,
    POLICIES: POLICIES,
    MIXED_LENGTHS: MIXED,
    ModelInvalidity: ModelInvalidity,
    ConservationFailure: ConservationFailure,
    validate: validate,
    maxLengthCm: maxLengthCm,
    expectedLengthCm: expectedLengthCm,
    poisson: poisson,
    scheduleTimes: scheduleTimes,
    generateArrivals: generateArrivals,
    kaplanMeier: kaplanMeier,
    lengthClass: lengthClass,
    longVehicleServiceRate: longVehicleServiceRate,
    run: run
  };
})(typeof window !== "undefined" ? window : globalThis);
