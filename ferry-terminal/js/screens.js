/* =====================================================================
   FERRY TERMINAL — panels, readouts and data tables
   ---------------------------------------------------------------------
   Markup generation only. Every chart on the page has a data-table
   alternative built here, reachable by keyboard, holding the same
   numbers the canvas draws.

   No function in this file can produce a bare mean time to service.
   There is no formatter for one.
   ===================================================================== */
(function (global) {
  "use strict";
  var CFG = global.FerryConfig, EV = global.FerryEvents, M = global.FerryModel;

  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]; }); }
  function n1(v) { return (Math.round(v * 10) / 10).toFixed(1); }
  function n0(v) { return Math.round(v).toString(); }
  function pct(v) { return (v * 100).toFixed(1) + "%"; }

  /* Quantiles of the OBSERVED distribution are only ever emitted together
     with the censored fraction — the signature enforces it. */
  function quantileRow(sorted, q) {
    if (!sorted.length) return null;
    var i = Math.min(sorted.length - 1, Math.max(0, Math.floor(q * (sorted.length - 1))));
    return sorted[i];
  }

  /* ---- controls ---------------------------------------------------- */
  function control(c, cfg) {
    if (c.showWhen && !c.showWhen(cfg)) return "";
    var v = cfg[c.key];
    var id = "ctl-" + c.key;
    var sym = c.symbol ? ' <span class="sym">' + esc(c.symbol) + "</span>" : "";
    var unit = c.unit ? ' <span class="unit">' + esc(c.unit) + "</span>" : "";
    var head = '<label for="' + id + '">' + esc(c.label) + sym + unit +
      '<span class="v" id="v-' + c.key + '">' + esc(String(v)) + "</span></label>";
    var body = "";

    if (c.kind === "range") {
      body = '<input type="range" id="' + id + '" data-key="' + c.key + '" min="' + c.min +
        '" max="' + c.max + '" step="' + c.step + '" value="' + v +
        '" aria-describedby="d-' + c.key + '">';
      if (c.ends) {
        body += '<div class="ends"><span>' + esc(c.ends[0]) + "</span><span>" + esc(c.ends[1]) + "</span></div>";
      }
    } else if (c.kind === "number") {
      body = '<input type="number" id="' + id + '" data-key="' + c.key + '" min="' + c.min +
        '" max="' + c.max + '" step="' + c.step + '" value="' + v +
        '" aria-describedby="d-' + c.key + '">';
    } else if (c.kind === "select") {
      body = '<select id="' + id + '" data-key="' + c.key + '" aria-describedby="d-' + c.key + '">' +
        c.options.map(function (o) {
          return '<option value="' + o.v + '"' + (o.v === v ? " selected" : "") + ">" + esc(o.t) + "</option>";
        }).join("") + "</select>";
    } else if (c.kind === "segmented") {
      body = '<div class="seg" role="radiogroup" aria-labelledby="' + id + '-lab" id="' + id + '">' +
        c.options.map(function (o) {
          return '<button type="button" role="radio" data-key="' + c.key + '" data-val="' + o.v + '"' +
            ' aria-checked="' + (o.v === v ? "true" : "false") + '"' +
            (o.v === v ? ' class="on"' : "") + ">" + esc(o.t) + "</button>";
        }).join("") + "</div>";
    }

    return '<div class="field" data-for="' + c.key + '">' + head + body +
      '<div class="note" id="d-' + c.key + '">' + esc(c.meaning) +
      (c.note ? " " + esc(c.note) : "") + "</div></div>";
  }

  function renderRail(state) {
    var cfg = state.config, groups = {}, order = [];
    CFG.CONTROLS.forEach(function (c) {
      if (!groups[c.group]) { groups[c.group] = []; order.push(c.group); }
      groups[c.group].push(c);
    });
    var h = "";
    h += '<div class="panel baseline"><div class="ptitle">Starting point</div>' +
      '<p class="note">' + esc(CFG.COPY.baselineLabel) + "</p>" +
      '<div class="rowbtns"><button class="btn sm" type="button" data-act="baseline">Restore starting point</button></div></div>';

    order.forEach(function (gname) {
      h += '<div class="panel"><div class="ptitle">' + esc(gname) + "</div>";
      groups[gname].forEach(function (c) { h += control(c, cfg); });
      if (gname === "Run") {
        var d = cfg.disruption;
        h += '<div class="field"><label for="ctl-disruption">Disruption</label>' +
          '<select id="ctl-disruption" data-key="disruptionMode">' +
          CFG.DISRUPTIONS.map(function (o) {
            var sel = (d ? d.mode : "NONE") === o.v ? " selected" : "";
            return '<option value="' + o.v + '"' + sel + ">" + esc(o.t) + "</option>";
          }).join("") + "</select>" +
          (d ? '<input type="number" id="ctl-disruption-k" data-key="disruptionSailing" min="0" step="1" value="' +
            d.sailing + '" aria-label="Which sailing is disrupted, counting from zero">' : "") +
          '<div class="note">Delay, reduce or cancel a single sailing and watch how the effect propagates.</div></div>';
      }
      h += "</div>";
    });

    h += '<div class="panel"><div class="ptitle">Reproducibility</div>' +
      '<div class="rowbtns">' +
      '<button class="btn sm" type="button" data-act="reseed">New seed</button>' +
      '<button class="btn sm" type="button" data-act="replay">Replay this seed</button>' +
      '</div><div class="rowbtns">' +
      '<button class="btn sm" type="button" data-act="export">Export configuration</button>' +
      '<button class="btn sm" type="button" data-act="import">Import configuration</button>' +
      '</div><div class="note">The configuration exports as JSON including the seed. Importing restores the run exactly.</div></div>';

    return h;
  }

  /* ---- notices ----------------------------------------------------- */
  function renderNotices(state) {
    return EV.notices(state).map(function (n) {
      return '<div class="callout lv-' + n.level + '" role="' + (n.level === "warn" || n.level === "block" ? "alert" : "note") + '">' +
        '<b>' + esc(n.title) + "</b> " + esc(n.text) + "</div>";
    }).join("");
  }

  /* ---- inspector --------------------------------------------------- */
  function renderInspector(state) {
    var r = state.result;
    if (!r) return '<div class="panel"><div class="ptitle">Readouts</div><p class="note">No run yet.</p></div>';
    var g = state.ghost;
    var h = "";

    h += '<div class="panel ' + (r.stable ? "" : "warn") + '"><div class="ptitle">Stability</div>' +
      '<div class="bigv">' + n1(r.loadRatio) + '</div>' +
      '<div class="note">Load ratio λ·h / (C / expected length). ' +
      (r.stable ? "Inside the stable region under these settings."
                : "At or above 1: the queue grows without bound and steady-state statistics are not meaningful.") +
      "</div></div>";

    /* Time to service — the censored fraction travels with EVERY statistic. */
    var obs = r.timeToServiceObserved;
    h += '<div class="panel"><div class="ptitle">Time to service</div>' +
      '<dl class="readout">' +
      '<dt>Sailed within the horizon</dt><dd>' + n0(obs.length) + " of " + n0(obs.length + r.timeToServiceCensoredLowerBounds.length) + " (" + pct(r.servedFraction) + ")</dd>" +
      '<dt>Never sailed (censored)</dt><dd>' + n0(r.timeToServiceCensoredLowerBounds.length) + " (" + pct(r.censoredFraction) + ")</dd>" +
      (obs.length ? '<dt>Median among those who sailed</dt><dd>' + n1(quantileRow(obs, 0.5)) + " min <span class=\"qual\">— of the " + pct(r.servedFraction) + " who sailed only</span></dd>" : "") +
      (obs.length ? '<dt>Upper decile among those who sailed</dt><dd>' + n1(quantileRow(obs, 0.9)) + " min <span class=\"qual\">— of the " + pct(r.servedFraction) + " who sailed only</span></dd>" : "") +
      "</dl>" +
      '<div class="note">' + esc(CFG.COPY.censoringPrimer) + "</div></div>";

    /* THE TWO MISSED-DEPARTURE MEASURES. Separate cards, different
       treatments, and no code path that adds them together. */
    var deniedTotal = r.deniedBoardingPerSailing.reduce(function (a, b) { return a + b; }, 0);
    h += '<div class="panel measure-a"><div class="ptitle">Denied boarding</div>' +
      '<div class="bigv">' + n0(deniedTotal) + '</div>' +
      '<div class="note">Vehicle-departures missed: a vehicle present at a sailing that did not board it. ' +
      'One vehicle can be counted at several sailings. This is a count of <b>events</b>.</div></div>';

    h += '<div class="panel measure-b"><div class="ptitle">Never sailed</div>' +
      '<div class="bigv">' + n0(r.unservedAtHorizon) + '</div>' +
      '<div class="note">Distinct vehicles still queueing when the horizon ended. This is a count of <b>vehicles</b>. ' +
      'It is a different quantity from denied boarding and the two are never combined.</div></div>';

    h += '<div class="panel"><div class="ptitle">Throughput</div>' +
      '<dl class="readout">' +
      '<dt>Vehicles sailed</dt><dd>' + n0(r.throughput) + "</dd>" +
      '<dt>Arrived</dt><dd>' + n0(r.nArrived) + "</dd>" +
      (g ? '<dt>Baseline sailed</dt><dd>' + n0(g.throughput) + "</dd>" : "") +
      "</dl></div>";

    if (r.config.lengthDist === "MIXED") {
      var c = r.censoringCompositionByLengthClass;
      h += '<div class="panel"><div class="ptitle">Who was served, by length</div><dl class="readout">';
      ["short", "medium", "long"].forEach(function (k) {
        var t = c[k].served + c[k].censored;
        h += "<dt>" + esc(CFG.LENGTH_CLASS_LABEL[k]) + "</dt><dd>" + (t ? pct(c[k].served / t) : "—") + " sailed <span class=\"qual\">(" + n0(t) + " vehicles)</span></dd>";
      });
      h += "</dl><div class=\"note\">A policy that serves a smaller, shorter subpopulation can show a shorter observed waiting time while serving fewer of the vehicles that arrived.</div></div>";
    }

    return h;
  }

  /* ---- data tables. One per chart, keyboard reachable. -------------- */
  function table(caption, headers, rows) {
    return '<div class="tablewrap"><table><caption>' + esc(caption) + "</caption><thead><tr>" +
      headers.map(function (x) { return "<th>" + esc(x) + "</th>"; }).join("") +
      "</tr></thead><tbody>" +
      rows.map(function (r) {
        return "<tr>" + r.map(function (x, i) { return '<td' + (i ? ' class="num"' : "") + ">" + esc(x) + "</td>"; }).join("") + "</tr>";
      }).join("") + "</tbody></table></div>";
  }

  function tableSurvival(r) {
    var rows = r.timeToServiceKM.slice(0, 400).map(function (p) {
      return [n1(p.t), n0(p.atRisk), n0(p.events), n0(p.censored), p.survival.toFixed(4)];
    });
    return table("Kaplan-Meier estimate of time to service, with at-risk counts and censoring indicators",
      ["Time, min", "At risk", "Sailed", "Censored", "P(still waiting)"], rows);
  }
  function tableComposition(r) {
    return table("Served and censored composition",
      ["Group", "Sailed", "Never sailed", "Share sailed"],
      [["All vehicles", n0(r.timeToServiceObserved.length), n0(r.timeToServiceCensoredLowerBounds.length), pct(r.servedFraction)]]
        .concat(["short", "medium", "long"].map(function (k) {
          var c = r.censoringCompositionByLengthClass[k], t = c.served + c.censored;
          return [CFG.LENGTH_CLASS_LABEL[k], n0(c.served), n0(c.censored), t ? pct(c.served / t) : "—"];
        })));
  }
  function tableQueue(r) {
    var rows = r.sailings.map(function (s) {
      return [n0(s.k), n1(s.scheduledTime), s.status, n0(s.manifest.length), n0(s.denied)];
    });
    return table("Queue at each departure epoch",
      ["Sailing", "Departs, min", "Status", "Boarded", "Still queueing after"], rows);
  }
  function tableLoad(r) {
    var rows = r.sailings.map(function (s) {
      return [n0(s.k), n1(s.loadedCm / 100), n1(s.capacityCm / 100), n1((s.capacityCm - s.loadedCm) / 100), n0(s.denied)];
    });
    return table("Per-sailing load against capacity, with residual",
      ["Sailing", "Loaded, m", "Capacity, m", "Residual, m", "Denied boarding"], rows);
  }
  function tableDeciles(r) {
    var o = r.timeToServiceObserved;
    if (!o.length) return table("Observed time to service", ["Decile", "Minutes"], []);
    var rows = [];
    for (var i = 1; i <= 9; i++) rows.push(["D" + i, n1(quantileRow(o, i / 10))]);
    return table("Deciles of observed time to service — these describe the " + pct(r.servedFraction) +
      " of vehicles that sailed, and exclude the " + pct(r.censoredFraction) + " that did not",
      ["Decile", "Minutes"], rows);
  }
  function tableThroughput(r) {
    var c = 0;
    var rows = r.sailings.slice().sort(function (a, b) { return a.scheduledTime - b.scheduledTime; })
      .map(function (s) { c += s.manifest.length; return [n0(s.k), n1(s.scheduledTime), n0(s.manifest.length), n0(c)]; });
    return table("Cumulative vehicles sailed", ["Sailing", "Departs, min", "Boarded", "Cumulative"], rows);
  }

  /* ---- text equivalent for assistive technology -------------------- */
  function srSummary(state) {
    var r = state.result;
    if (!r) return "No run has been made yet.";
    var s = [];
    s.push("Run with " + r.config.policy.replace("_", " ").toLowerCase() + " loading, arrival mixture " +
      r.config.rho.toFixed(2) + ", " + r.config.lam + " vehicles per hour, " + r.config.capacityM +
      " lane-metres every " + r.config.headway + " minutes, seed " + r.config.seed + ".");
    s.push(r.nArrived + " vehicles arrived. " + r.nSailed + " sailed, " + pct(r.servedFraction) +
      " of those counted after warm-up. " + r.unservedAtHorizon + " were still queueing at the horizon; " +
      "their time to service is censored, not missing.");
    if (r.timeToServiceObserved.length) {
      s.push("Among the vehicles that sailed, the median time to service was " +
        n1(quantileRow(r.timeToServiceObserved, 0.5)) + " minutes and the upper decile " +
        n1(quantileRow(r.timeToServiceObserved, 0.9)) + " minutes. Both describe only the " +
        pct(r.servedFraction) + " that sailed.");
    }
    s.push("Load ratio " + n1(r.loadRatio) + ". " + (r.stable ? "Inside the stable region." : "Above the stability boundary; the queue grows without bound."));
    var denied = r.deniedBoardingPerSailing.reduce(function (a, b) { return a + b; }, 0);
    s.push(denied + " denied-boarding events occurred across " + r.sailings.length +
      " sailings. That is a count of events and is a different quantity from the " +
      r.unservedAtHorizon + " vehicles that never sailed.");
    if (r.censoredFraction > CFG.HEAVY_CENSORING_THRESHOLD) s.push(CFG.COPY.heavyCensoring);
    return s.join(" ");
  }

  global.FerryScreens = {
    renderRail: renderRail,
    renderNotices: renderNotices,
    renderInspector: renderInspector,
    tableSurvival: tableSurvival,
    tableComposition: tableComposition,
    tableQueue: tableQueue,
    tableLoad: tableLoad,
    tableDeciles: tableDeciles,
    tableThroughput: tableThroughput,
    srSummary: srSummary,
    quantile: quantileRow
  };
})(typeof window !== "undefined" ? window : globalThis);
