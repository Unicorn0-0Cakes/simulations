/* =====================================================================
   FERRY TERMINAL — controller
   ---------------------------------------------------------------------
   State, wiring and the comparison rule.

   THE COMPARISON RULE IS THE CENTRE OF THIS FILE.
   Changing a non-seed control keeps the previous run as the ghost
   baseline, because both runs share one arrival realisation and the
   difference is attributable to the control that moved. Changing the
   seed clears the comparison and says why. That is not a nicety: a
   contrast between two random streams is uninterpretable, and the
   interface refuses to display one.
   ===================================================================== */
(function (global) {
  "use strict";
  var CFG = global.FerryConfig, M = global.FerryModel,
      CH = global.FerryCharts, S = global.FerryScreens, EV = global.FerryEvents;

  var state = {
    phase: "INITIAL",        /* INITIAL READY RUNNING PAUSED COMPLETE COMPARING INVALID ERROR */
    config: CFG.clone(CFG.BASELINE),
    result: null,
    ghost: null,
    ghostLabel: "",
    seedClearedComparison: false,
    invalidReason: null,
    revealedEpochs: Infinity,   /* how many departure epochs are shown */
    timer: null,
    compareRuns: null,          /* policy comparison, all on one seed */
    dirtyKeys: {}
  };

  function $(s, r) { return (r || document).querySelector(s); }
  function sameAsCurrent(key, value) {
    if (key === "disruptionMode") {
      return (state.config.disruption ? state.config.disruption.mode : "NONE") === value;
    }
    if (key === "disruptionSailing") {
      return !!state.config.disruption && state.config.disruption.sailing === (parseInt(value, 10) || 0);
    }
    if (key === "policy" || key === "lengthDist") return state.config[key] === value;
    var v = parseFloat(value);
    return !isNaN(v) && state.config[key] === v;
  }
  function $$(s, r) { return Array.prototype.slice.call((r || document).querySelectorAll(s)); }
  function say(msg) { var l = $("#live"); if (l) l.textContent = msg; }

  /* ---- the run ----------------------------------------------------- */
  function compute() {
    try {
      state.result = M.run(CFG.clone(state.config));
      state.invalidReason = null;
      state.phase = state.result.stable ? "COMPLETE" : "COMPLETE";
      return true;
    } catch (e) {
      state.result = null;
      state.invalidReason = e.message;
      state.phase = "INVALID";
      return false;
    }
  }

  /* A run that has been partially revealed, for step-to-epoch. The model
     is not re-run; the view is truncated. */
  function visible() {
    var r = state.result;
    if (!r || state.revealedEpochs === Infinity) return r;
    var n = Math.max(0, Math.min(state.revealedEpochs, r.sailings.length));
    var cut = n ? r.sailings.slice().sort(function (a, b) { return a.scheduledTime - b.scheduledTime; })[n - 1].scheduledTime : 0;
    var v = Object.create(r);
    v.sailings = r.sailings.filter(function (s) { return s.scheduledTime <= cut; });
    v.queueSeries = r.queueSeries.filter(function (p) { return p[0] <= cut; });
    v.deniedBoardingPerSailing = v.sailings.map(function (s) { return s.denied; });
    return v;
  }

  /* ---- comparison rule --------------------------------------------- */
  function applyChange(key, value) {
    var before = state.result;
    var seedChanged = (key === "seed");

    /* A control can emit more than one event for a single edit — a number
       field commits with `input` and then `change`. Applying the second one
       would set the baseline to a run with the SAME configuration, and the
       comparison would silently become a comparison of a run with itself.
       A change that changes nothing is not a change. */
    if (sameAsCurrent(key, value)) return;

    if (key === "disruptionMode") {
      state.config.disruption = value === "NONE" ? null
        : { sailing: (state.config.disruption && state.config.disruption.sailing) || 0, mode: value, factor: 0.5, delay: 45 };
    } else if (key === "disruptionSailing") {
      if (state.config.disruption) state.config.disruption.sailing = Math.max(0, parseInt(value, 10) || 0);
    } else if (key === "policy" || key === "lengthDist") {
      state.config[key] = value;
    } else {
      state.config[key] = parseFloat(value);
    }

    /* keep D strictly below h, as the register requires */
    if (state.config.leadTimeMean >= state.config.headway) {
      state.config.leadTimeMean = Math.max(0, state.config.headway - 1);
    }

    state.dirtyKeys[key] = true;

    if (seedChanged) {
      state.ghost = null; state.ghostLabel = "";
      state.seedClearedComparison = true;
      say(CFG.COPY.seedCleared);
    } else if (before) {
      state.ghost = before;
      state.ghostLabel = "previous run";
      state.seedClearedComparison = false;
    }
    state.compareRuns = null;
    state.revealedEpochs = Infinity;
    compute();
    render();
  }

  /* ---- policy comparison, always as one unit ----------------------- */
  function comparePolicies() {
    var runs = [];
    ["FCFS", "CLASS_PRIORITY", "SIZE_AWARE"].forEach(function (p) {
      var c = CFG.clone(state.config); c.policy = p;
      try { runs.push(M.run(c)); } catch (e) { /* guarded elsewhere */ }
    });
    state.compareRuns = runs.length === 3 ? runs : null;
    state.phase = "COMPARING";
    render();
    say("Comparing three loading policies on one arrival realisation. Survival curves and who was served are shown together.");
  }

  /* ---- stepping ---------------------------------------------------- */
  function stepEpoch() {
    if (!state.result) return;
    if (state.revealedEpochs === Infinity) state.revealedEpochs = 0;
    state.revealedEpochs = Math.min(state.result.sailings.length, state.revealedEpochs + 1);
    state.phase = state.revealedEpochs >= state.result.sailings.length ? "COMPLETE" : "PAUSED";
    render();
    say("Departure epoch " + state.revealedEpochs + " of " + state.result.sailings.length + ".");
  }
  function play() {
    if (!state.result) return;
    if (state.revealedEpochs === Infinity) state.revealedEpochs = 0;
    stop();
    state.phase = "RUNNING";
    if (CH.reducedMotion()) { state.revealedEpochs = Infinity; state.phase = "COMPLETE"; render(); return; }
    state.timer = setInterval(function () {
      if (state.revealedEpochs >= state.result.sailings.length) { stop(); state.phase = "COMPLETE"; render(); return; }
      state.revealedEpochs++;
      render();
    }, 320);
    render();
  }
  function stop() { if (state.timer) { clearInterval(state.timer); state.timer = null; } }

  /* ---- export / import --------------------------------------------- */
  function exportConfig() {
    var blob = JSON.stringify({ instrument: "ferry-terminal", config: state.config }, null, 2);
    var el = $("#ioText");
    el.value = blob;
    openModal("Configuration", "Copy this to keep the run. Importing it restores the same run exactly, seed included.", true);
  }
  function importConfig() {
    var el = $("#ioText");
    el.value = "";
    openModal("Import configuration", "Paste a configuration exported from this instrument.", true, function () {
      try {
        var o = JSON.parse(el.value);
        var c = o.config || o;
        Object.keys(CFG.BASELINE).forEach(function (k) { if (c[k] !== undefined) state.config[k] = c[k]; });
        state.ghost = null; state.seedClearedComparison = false; state.compareRuns = null;
        state.revealedEpochs = Infinity;
        compute(); render(true);
        say("Configuration imported. The run has been restored.");
      } catch (e) { say("That is not a configuration this instrument can read."); }
    });
  }

  /* ---- modal ------------------------------------------------------- */
  var modalConfirm = null;
  function openModal(title, body, showIO, onConfirm) {
    $("#modalTitle").textContent = title;
    $("#modalKicker").textContent = "Ferry terminal";
    var mb = $("#modalBody") || $(".modal .mb");
    var para = mb && (mb.querySelector("p") || mb.insertBefore(document.createElement("p"), mb.firstChild));
    if (para) para.textContent = body;
    $("#ioText").style.display = showIO ? "" : "none";
    modalConfirm = onConfirm || null;
    $("#modalOk").style.display = onConfirm ? "" : "none";
    $("#veil").classList.add("on");
    ($("#modalOk").style.display === "" && onConfirm ? $("#modalOk") : $("#modalClose")).focus();
  }
  function closeModal() { $("#veil").classList.remove("on"); modalConfirm = null; }

  /* ---- render ------------------------------------------------------ */
  /* Rebuilding the rail on every input replaced the very element the user was
     typing into or dragging, so focus was lost after one keystroke and a slider
     moved one step per interaction. The rail is now rebuilt only when its
     STRUCTURE changes — a field appearing or disappearing — and is otherwise
     updated in place. Nothing about the control register changed; only when the
     markup is thrown away. */
  function railStructure() {
    return [state.config.lengthDist,
            state.config.disruption ? state.config.disruption.mode : "NONE"].join("|");
  }
  var lastRailStructure = null;

  function syncRail() {
    var cfg = state.config;
    CFG.CONTROLS.forEach(function (c) {
      var el = document.getElementById("ctl-" + c.key);
      var out = document.getElementById("v-" + c.key);
      if (out) out.textContent = String(cfg[c.key]);
      if (!el) return;
      if (c.kind === "segmented") {
        $$("button", el).forEach(function (b) {
          var on = b.getAttribute("data-val") === cfg[c.key];
          b.classList.toggle("on", on);
          b.setAttribute("aria-checked", String(on));
        });
      } else if (document.activeElement !== el && String(el.value) !== String(cfg[c.key])) {
        /* never overwrite the field the user is currently editing */
        el.value = cfg[c.key];
      }
    });
    var dk = document.getElementById("ctl-disruption-k");
    if (dk && state.config.disruption && document.activeElement !== dk) dk.value = state.config.disruption.sailing;
    $$("[data-for]").forEach(function (f) {
      f.classList.toggle("changed", !!state.dirtyKeys[f.getAttribute("data-for")]);
    });
  }

  function render(rebuildRail) {
    var r = visible();
    var struct = railStructure();

    $("#notices").innerHTML = S.renderNotices(state);
    if (rebuildRail || struct !== lastRailStructure || !$("#ctl-lam")) {
      var focusId = document.activeElement ? document.activeElement.id : null;
      var selStart = null;
      try { selStart = document.activeElement && document.activeElement.selectionStart; } catch (e) {}
      $("#rail").innerHTML = S.renderRail(state);
      lastRailStructure = struct;
      if (focusId) {
        var back = document.getElementById(focusId);
        if (back) {
          back.focus();
          try { if (selStart !== null && back.setSelectionRange) back.setSelectionRange(selStart, selStart); } catch (e) {}
        }
      }
    }
    syncRail();
    $("#inspector").innerHTML = S.renderInspector(state);

    var compareOn = state.phase === "COMPARING" && state.compareRuns;
    $("#compareScope").classList.toggle("hide", !compareOn);
    $("#mainScopes").classList.toggle("hide", !!compareOn);

    $("#btnPlay").disabled = !state.result;
    $("#btnStep").disabled = !state.result;
    $("#btnCompare").disabled = !state.result;
    $("#tbPhase").textContent = state.phase;

    if (!r) {
      $("#srSummary").textContent = state.invalidReason || "No run.";
      $("#tables").innerHTML = "";
      return;
    }

    if (compareOn) {
      CH.comparePolicies($("#cmpCurveCv"), $("#cmpCompCv"), state.compareRuns);
      $("#tables").innerHTML = state.compareRuns.map(function (x) {
        return "<h4>" + x.config.policy.replace("_", " ") + "</h4>" + S.tableComposition(x);
      }).join("");
      $("#srSummary").textContent = state.compareRuns.map(function (x) {
        var lr = M.longVehicleServiceRate(x);
        return x.config.policy.replace("_", " ") + ": " + (x.servedFraction * 100).toFixed(1) +
          " per cent of vehicles sailed" +
          (lr === null ? "" : ", and " + (lr * 100).toFixed(1) + " per cent of long vehicles") + ".";
      }).join(" ");
      return;
    }

    /* PRIMARY: the survival unit. Both canvases, one call. */
    CH.survivalUnit($("#survCv"), $("#compCv"), r, state.ghost);
    CH.queueTimeline($("#queueCv"), r, state.ghost);
    CH.loadStrip($("#loadCv"), r);
    CH.bars($("#deniedCv"), r.deniedBoardingPerSailing,
      state.ghost ? state.ghost.deniedBoardingPerSailing : null, "amber", "SAILING", "DENIED BOARDINGS");
    CH.bars($("#carryCv"), r.carryOverDepth,
      state.ghost ? state.ghost.carryOverDepth : null, "slate", "SAILING", "QUEUE AFTER EPOCH");
    CH.throughput($("#thruCv"), r, state.ghost);
    /* SECONDARY, demoted: the observed-only histogram, and its composition. */
    CH.observedPair($("#histCv"), $("#histCompCv"), r, state.ghost);

    $("#unservedFig").textContent = r.unservedAtHorizon;
    $("#srSummary").textContent = S.srSummary({ result: r, config: state.config });
    $("#tables").innerHTML =
      S.tableSurvival(r) + S.tableComposition(r) + S.tableDeciles(r) +
      S.tableQueue(r) + S.tableLoad(r) + S.tableThroughput(r);
  }

  /* ---- wiring ------------------------------------------------------ */
  function onInput(e) {
    var t = e.target, key = t.getAttribute("data-key");
    if (!key) return;
    applyChange(key, t.value);
  }
  function onClick(e) {
    var t = e.target.closest("[data-act], [data-key][data-val]");
    if (!t) return;
    var val = t.getAttribute("data-val");
    if (val !== null && t.getAttribute("data-key")) { applyChange(t.getAttribute("data-key"), val); return; }
    switch (t.getAttribute("data-act")) {
      case "begin":
        document.body.classList.add("launched");
        compute(); render(true);
        say("Run complete. " + CFG.COPY.firstChange);
        break;
      case "home": document.body.classList.remove("launched"); stop(); break;
      case "play": state.phase === "RUNNING" ? (stop(), state.phase = "PAUSED", render()) : play(); break;
      case "step": stop(); stepEpoch(); break;
      case "reset":
        if (state.ghost) {
          openModal("Discard the comparison?", "Resetting clears the baseline run you are comparing against.", false, null);
          $("#modalOk").style.display = "";
          modalConfirm = function () { doReset(); };
        } else doReset();
        break;
      case "replay": state.revealedEpochs = Infinity; compute(); render(); say("Replayed on seed " + state.config.seed + ". Identical run."); break;
      case "reseed": applyChange("seed", String(Math.floor(Math.random() * 999999) + 1)); break;
      case "baseline":
        state.config = CFG.clone(CFG.BASELINE); state.ghost = null; state.dirtyKeys = {};
        state.seedClearedComparison = false; state.compareRuns = null; state.revealedEpochs = Infinity;
        compute(); render(true); break;
      case "compare": comparePolicies(); break;
      case "single": state.compareRuns = null; state.phase = "COMPLETE"; render(); break;
      case "export": exportConfig(); break;
      case "import": importConfig(); break;
      case "modal-ok": if (modalConfirm) { var f = modalConfirm; closeModal(); f(); } else closeModal(); break;
      case "modal-close": closeModal(); break;
    }
  }
  function doReset() {
    closeModal(); stop();
    state.ghost = null; state.compareRuns = null; state.revealedEpochs = Infinity;
    state.seedClearedComparison = false; state.dirtyKeys = {};
    compute(); render(true);
    say("Reset.");
  }

  function boot() {
    /* `input` only. Binding `change` as well made a committed number field
       apply twice; the guard in applyChange now makes that harmless, but the
       duplicate binding has no purpose and is removed. */
    document.addEventListener("input", onInput);
    document.addEventListener("click", onClick);
    document.addEventListener("keydown", function (e) {
      if (/^(input|textarea|select)$/i.test((document.activeElement || {}).tagName || "")) return;
      if (e.key === "Escape") closeModal();
      if (e.key === "s" || e.key === "S") { stop(); stepEpoch(); }
      if (e.key === " " && document.body.classList.contains("launched")) { e.preventDefault(); state.phase === "RUNNING" ? (stop(), state.phase = "PAUSED", render()) : play(); }
    });
    global.addEventListener("resize", function () { if (state.result) render(); });
    if (global.Orbital) global.Orbital.onThemeChange(function () { if (state.result) render(); });
    compute();
    render(true);
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();

  global.FerryApp = { state: state, render: render, applyChange: applyChange, comparePolicies: comparePolicies };
})(typeof window !== "undefined" ? window : globalThis);
