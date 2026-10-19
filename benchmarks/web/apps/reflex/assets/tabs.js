document.addEventListener("click", event => {
  const button = event.target.closest("#project-tabs button[data-tab-target]");
  if (!button) return;
  const tabs = button.closest("#project-tabs");
  const target = button.dataset.tabTarget;
  for (const candidate of tabs.querySelectorAll("button[data-tab-target]")) {
    candidate.setAttribute("aria-selected", String(candidate === button));
  }
  for (const panel of tabs.querySelectorAll("[data-tab-panel]")) {
    panel.hidden = panel.id !== target;
  }
});
