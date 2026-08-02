/* =====================================================================
   ORBITAL — shared theme + site chrome
   ---------------------------------------------------------------------
   Load this in <head> WITHOUT defer, so the theme is set before the
   first paint and there is no flash of the wrong world.

     <link rel="stylesheet" href="../assets/orbital.css">
     <script src="../assets/orbital.js"
             data-title="EVOLUTION IN A FLASK"
             data-tag="LTEE / 12 POPULATIONS"></script>

   Options, all optional, read off the <script> tag:
     data-title   breadcrumb label for this page
     data-tag     small right-hand identifier
     data-chrome  "off" to suppress the injected bar

   Public API:
     Orbital.theme()          -> "day" | "night"
     Orbital.setTheme(t)
     Orbital.toggle()
     Orbital.color(name)      -> resolved value of --rf-<name>
     Orbital.onThemeChange(fn)
   Also dispatches "orbital:theme" on window.
   ===================================================================== */
(function () {
  "use strict";

  var KEY = "orbital-theme";
  var doc = document.documentElement;
  var script = document.currentScript;

  /* ---- 1. theme, applied immediately ---------------------------- */
  function preferred() {
    try {
      var saved = localStorage.getItem(KEY);
      if (saved === "day" || saved === "night") return saved;
    } catch (e) {}
    return (window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches)
      ? "night" : "day";
  }

  function setTheme(t, persist) {
    t = (t === "night") ? "night" : "day";
    doc.setAttribute("data-theme", t);
    if (persist !== false) { try { localStorage.setItem(KEY, t); } catch (e) {} }
    paintSwitch(t);
    window.dispatchEvent(new CustomEvent("orbital:theme", { detail: { theme: t } }));
  }

  doc.classList.add("rf-page");
  doc.setAttribute("data-theme", preferred());

  /* ---- 2. helpers ------------------------------------------------ */
  function color(name) {
    return getComputedStyle(doc).getPropertyValue("--rf-" + name).trim();
  }

  function theme() { return doc.getAttribute("data-theme") === "night" ? "night" : "day"; }
  function toggle() { setTheme(theme() === "night" ? "day" : "night"); }

  function onThemeChange(fn) {
    window.addEventListener("orbital:theme", function (e) { fn(e.detail.theme); });
  }

  window.Orbital = {
    theme: theme, setTheme: setTheme, toggle: toggle,
    color: color, onThemeChange: onThemeChange
  };

  /* ---- 3. chrome bar --------------------------------------------- */
  var SUN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="12" cy="12" r="4.2"/><path d="M12 1.6v2.6M12 19.8v2.6M4.6 4.6l1.9 1.9M17.5 17.5l1.9 1.9M1.6 12h2.6M19.8 12h2.6M4.6 19.4l1.9-1.9M17.5 6.5l1.9-1.9"/></svg>';
  var MOON = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.5 14.6A8.6 8.6 0 1 1 9.4 3.5a6.9 6.9 0 0 0 11.1 11.1z"/></svg>';
  var MARK = '<svg viewBox="0 0 22 22" width="15" height="15" fill="none" stroke="currentColor" stroke-width="1.6"><circle cx="11" cy="11" r="4"/><ellipse cx="11" cy="11" rx="10" ry="4.2" transform="rotate(-28 11 11)"/></svg>';

  function paintSwitch(t) {
    var sw = document.getElementById("rf-switch");
    if (sw) sw.setAttribute("aria-label", "Switch to " + (t === "night" ? "day" : "night") + " mode");
  }

  function rootPath() {
    // Pages live either at the site root or one directory below it.
    var parts = location.pathname.split("/").filter(Boolean);
    var file = parts[parts.length - 1] || "";
    var depth = /\.html?$/i.test(file) ? parts.length - 1 : parts.length;
    // Heuristic: a simulation page sits in exactly one folder of its own.
    return /\//.test(location.pathname) && depth > 0 && !/^index\.html?$/i.test(file)
      ? "../" : "./";
  }

  function build() {
    if (script && script.getAttribute("data-chrome") === "off") return;
    if (document.querySelector(".rf-chrome")) return;

    var title = (script && script.getAttribute("data-title")) || "";
    var tag = (script && script.getAttribute("data-tag")) || "";
    var isIndex = /(^|\/)(index\.html?)?$/i.test(location.pathname);
    var home = isIndex ? "#top" : rootPath() + "index.html";

    var bar = document.createElement("div");
    bar.className = "rf-chrome";
    bar.innerHTML =
      '<a class="rf-home" href="' + home + '">' + MARK +
        '<span>' + (isIndex ? "Simulations" : "All simulations") + '</span></a>' +
      (title ? '<span class="rf-sep">/</span><span class="rf-here">' + title + '</span>' : '') +
      '<span class="rf-spacer"></span>' +
      (tag ? '<span class="rf-idtag">' + tag + '</span>' : '') +
      '<button class="rf-switch" id="rf-switch" type="button">' +
        '<span class="rf-sw-day">' + SUN + 'Day</span>' +
        '<span class="rf-sw-night">' + MOON + 'Night</span>' +
      '</button>';

    document.body.insertBefore(bar, document.body.firstChild);
    document.getElementById("rf-switch").addEventListener("click", toggle);
    paintSwitch(theme());
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", build);
  } else {
    build();
  }

  /* ---- 4. keyboard: press "t" to flip the world ------------------- */
  document.addEventListener("keydown", function (e) {
    if (e.key !== "t" && e.key !== "T") return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    var el = document.activeElement;
    if (el && /^(input|textarea|select)$/i.test(el.tagName)) return;
    if (el && el.isContentEditable) return;
    toggle();
  });
})();
