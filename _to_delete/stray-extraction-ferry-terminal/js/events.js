/* =====================================================================
   FERRY TERMINAL — notices and interpretive safeguards
   ---------------------------------------------------------------------
   The warning system of §15, expressed as pure rules over the current
   configuration and result. Kept out of the rendering code so that
   "which warnings are showing" is a testable property of the state and
   not an accident of DOM order.

   A notice is never dismissible when the specification says it is not.
   ===================================================================== */
(function (global) {
  "use strict";
  var C = global.FerryConfig;

  /* level: "mark" persistent framing · "notice" informative ·
            "warn" the reading is compromised · "block" the run cannot proceed */
  function notices(state) {
    var cfg = state.config, res = state.result, out = [];

    /* Persistent, non-dismissible. Blocker (1) of the Stage 02 handoff. */
    out.push({
      id: "EXPLORATORY_MARKER", level: "mark", dismissible: false,
      title: "Exploratory instrument",
      text: C.COPY.exploratoryBody
    });

    if (state.invalidReason) {
      out.push({
        id: "CAPACITY_GUARD", level: "block", dismissible: false,
        title: "The run cannot proceed", text: state.invalidReason
      });
      return out;
    }
    if (!res) return out;

    if (!res.stable) {
      out.push({
        id: "STABILITY_WARNING", level: "warn", dismissible: false,
        title: "Unstable region · load ratio " + res.loadRatio.toFixed(2),
        text: C.COPY.unstable
      });
    }
    if (res.censoredFraction > C.HEAVY_CENSORING_THRESHOLD) {
      out.push({
        id: "HEAVY_CENSORING_NOTICE", level: "warn", dismissible: false,
        title: "Heavy censoring · " + (res.censoredFraction * 100).toFixed(1) + "% never sailed",
        text: C.COPY.heavyCensoringBody
      });
    }
    if (cfg.warmup > 0) {
      out.push({
        id: "WARM_UP_NOTICE", level: "notice", dismissible: false,
        title: "Warm-up " + cfg.warmup + " min", text: C.COPY.warmupNotice
      });
    }
    out.push({
      id: "SINGLE_RUN_NOTICE", level: "notice", dismissible: false,
      title: "Single replicate", text: C.COPY.singleRun
    });
    if (state.seedClearedComparison) {
      out.push({
        id: "SEED_CHANGED_NOTICE", level: "warn", dismissible: true,
        title: "Comparison cleared", text: C.COPY.seedClearedBody
      });
    }
    if (cfg.lengthDist === "MIXED") {
      out.push({
        id: "LENGTH_SET_NOTICE", level: "notice", dismissible: false,
        title: "Mixed length set",
        text: "An exploratory set spanning the documented Ro-Ro range. It is not an empirical distribution for a small terminal."
      });
    }
    return out;
  }

  /* Which run is allowed to be described how. Used by the readouts so that
     a prohibited phrasing has no code path, rather than being caught in review. */
  function claimGuard(res) {
    return {
      mayShowBareMean: false,
      mayShowObservedOnlyAlone: false,
      mustPairCompositionWithAnyTimeStatistic: true,
      mayCompareObservedOnlyAcrossPolicies: false,
      heavyCensoring: !!res && res.censoredFraction > C.HEAVY_CENSORING_THRESHOLD
    };
  }

  global.FerryEvents = { notices: notices, claimGuard: claimGuard };
})(typeof window !== "undefined" ? window : globalThis);
