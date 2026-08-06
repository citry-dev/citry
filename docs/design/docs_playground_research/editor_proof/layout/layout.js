const MIN_SPLIT = 30;
const MAX_SPLIT = 70;
const DEFAULT_SPLIT = 50;
const STORAGE_KEY = "citry-playground-proof:split";

const root = document.documentElement;
const workspace = document.querySelector(".workspace");
const separator = document.querySelector("#workspace-separator");
const codePanel = document.querySelector("#code-panel");
const resultPanel = document.querySelector("#result-panel");
const codeButton = document.querySelector("#show-code");
const resultButton = document.querySelector("#show-result");
const announcer = document.querySelector("#announcer");
const mobileMenuButton = document.querySelector(".mobile-menu-button");
const primaryNavigation = document.querySelector("#primary-navigation");
const mobileQuery = matchMedia("(max-width: 56rem), (max-height: 28rem)");

if (new URLSearchParams(location.search).get("dir") === "rtl") {
  root.dir = "rtl";
}

function clampSplit(value) {
  if (!Number.isFinite(value)) return DEFAULT_SPLIT;
  return Math.min(MAX_SPLIT, Math.max(MIN_SPLIT, value));
}

function readStoredSplit() {
  try {
    return clampSplit(Number.parseFloat(localStorage.getItem(STORAGE_KEY) ?? ""));
  } catch {
    return DEFAULT_SPLIT;
  }
}

function setSplit(value, { announce = false, persist = true } = {}) {
  const next = Math.round(clampSplit(value) * 100) / 100;
  root.style.setProperty("--code-size", `${next}%`);
  separator.setAttribute("aria-valuenow", String(Math.round(next)));
  separator.setAttribute("aria-valuetext", `Code panel ${Math.round(next)} percent`);
  if (persist) {
    try {
      localStorage.setItem(STORAGE_KEY, String(next));
    } catch {
      // The layout remains usable when storage is unavailable.
    }
  }
  if (announce) announcer.textContent = `Code panel ${Math.round(next)} percent`;
}

function currentSplit() {
  return Number.parseFloat(separator.getAttribute("aria-valuenow") ?? String(DEFAULT_SPLIT));
}

function splitFromPointer(clientX) {
  const bounds = workspace.getBoundingClientRect();
  const usableWidth = bounds.width - separator.getBoundingClientRect().width;
  const physicalWidth = root.dir === "rtl" ? bounds.right - clientX : clientX - bounds.left;
  return (physicalWidth / usableWidth) * 100;
}

separator.addEventListener("pointerdown", (event) => {
  if (event.button !== 0 && event.pointerType !== "touch") return;
  separator.dataset.dragging = "true";
  separator.setPointerCapture(event.pointerId);
  setSplit(splitFromPointer(event.clientX));
  event.preventDefault();
});

separator.addEventListener("pointermove", (event) => {
  if (separator.dataset.dragging !== "true") return;
  setSplit(splitFromPointer(event.clientX));
});

function finishPointerDrag(event) {
  if (separator.dataset.dragging !== "true") return;
  delete separator.dataset.dragging;
  if (separator.hasPointerCapture(event.pointerId)) separator.releasePointerCapture(event.pointerId);
  setSplit(splitFromPointer(event.clientX), { announce: true });
}

separator.addEventListener("pointerup", finishPointerDrag);
separator.addEventListener("pointercancel", finishPointerDrag);
separator.addEventListener("dblclick", () => setSplit(DEFAULT_SPLIT, { announce: true }));

separator.addEventListener("keydown", (event) => {
  let next = currentSplit();
  const step = event.shiftKey ? 10 : 1;
  const rtlFactor = root.dir === "rtl" ? -1 : 1;

  if (event.key === "ArrowLeft") next -= step * rtlFactor;
  else if (event.key === "ArrowRight") next += step * rtlFactor;
  else if (event.key === "Home") next = MIN_SPLIT;
  else if (event.key === "End") next = MAX_SPLIT;
  else if (event.key === "Enter") next = DEFAULT_SPLIT;
  else return;

  event.preventDefault();
  setSplit(next, { announce: true });
});

document.querySelector("#equal-panes-button").addEventListener("click", () => {
  setSplit(DEFAULT_SPLIT, { announce: true });
  separator.focus();
});

function setActivePane(name) {
  const showCode = name === "code";
  workspace.dataset.activePane = name;
  codeButton.setAttribute("aria-pressed", String(showCode));
  resultButton.setAttribute("aria-pressed", String(!showCode));

  if (mobileQuery.matches) {
    codePanel.hidden = !showCode;
    resultPanel.hidden = showCode;
  } else {
    codePanel.hidden = false;
    resultPanel.hidden = false;
  }
}

codeButton.addEventListener("click", () => setActivePane("code"));
resultButton.addEventListener("click", () => setActivePane("result"));

function syncResponsiveState() {
  if (mobileQuery.matches) {
    const focusedPanel = document.activeElement?.closest?.(".panel");
    if (focusedPanel === resultPanel) workspace.dataset.activePane = "result";
    if (focusedPanel === codePanel) workspace.dataset.activePane = "code";
    setActivePane(workspace.dataset.activePane || "code");
    primaryNavigation.hidden = mobileMenuButton.getAttribute("aria-expanded") !== "true";
  } else {
    codePanel.hidden = false;
    resultPanel.hidden = false;
    primaryNavigation.hidden = false;
    mobileMenuButton.setAttribute("aria-expanded", "false");
  }
}

mobileQuery.addEventListener("change", syncResponsiveState);

mobileMenuButton.addEventListener("click", () => {
  const expanded = mobileMenuButton.getAttribute("aria-expanded") === "true";
  mobileMenuButton.setAttribute("aria-expanded", String(!expanded));
  primaryNavigation.hidden = expanded;
});

document.querySelectorAll(".copy-diagnostic").forEach((button) => {
  button.addEventListener("click", async () => {
    const text = button.closest(".diagnostic").querySelector("pre").textContent;
    try {
      await navigator.clipboard.writeText(text);
      announcer.textContent = "Diagnostic copied";
    } catch {
      announcer.textContent = "Copy failed. Select the diagnostic text instead.";
    }
  });
});

function updateViewportHeight() {
  const height = window.visualViewport?.height ?? window.innerHeight;
  root.style.setProperty("--app-height", `${height}px`);
}

window.visualViewport?.addEventListener("resize", updateViewportHeight);
window.addEventListener("resize", updateViewportHeight);

setSplit(readStoredSplit(), { persist: false });
updateViewportHeight();
syncResponsiveState();

window.layoutProof = {
  setActivePane,
  setSplit,
};
