/* Boot: tabs, then render each page once from DATA. */

(function () {
  const tabsEl = document.getElementById("tabs");
  tabsEl.innerHTML = TABS.map(([id, label], i) =>
    `<button type="button" role="tab" data-tab="${id}" aria-selected="${i === 0}" aria-controls="p-${id}">${label}</button>`
  ).join("");

  function show(id) {
    document.querySelectorAll("section.page").forEach(s => s.classList.toggle("on", s.id === "p-" + id));
    tabsEl.querySelectorAll("button").forEach(b => b.setAttribute("aria-selected", String(b.dataset.tab === id)));
    if (location.hash.slice(1) !== id) history.replaceState(null, "", "#" + id);
  }

  tabsEl.addEventListener("click", e => {
    const b = e.target.closest("button[data-tab]");
    if (b) show(b.dataset.tab);
  });
  tabsEl.addEventListener("keydown", e => {
    if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
    const ids = TABS.map(t => t[0]);
    const cur = ids.indexOf(document.querySelector("section.page.on").id.slice(2));
    const next = ids[(cur + (e.key === "ArrowRight" ? 1 : ids.length - 1)) % ids.length];
    show(next);
    tabsEl.querySelector(`button[data-tab="${next}"]`).focus();
  });

  /* Badges are read from the catalogue so this page can never claim a stronger
     status than the card that links to it. */
  const rec = typeof byId === "function" ? byId("culture-flux") : null;
  if (rec && window.Orbital) {
    document.getElementById("badges").innerHTML =
      Orbital.evidenceBadge(rec.evidence) + Orbital.basisBadge(rec.basis) +
      Orbital.stateBadge(rec.state) + Orbital.flagChips(rec.flags);
  }

  renderMechanisms();
  renderResults();
  renderProvenance();

  const initial = TABS.some(t => t[0] === location.hash.slice(1)) ? location.hash.slice(1) : TABS[0][0];
  show(initial);
})();
