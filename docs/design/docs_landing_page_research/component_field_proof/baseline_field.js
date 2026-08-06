$component(({ els }) => {
  const root = els[0];
  const trigger = root.querySelector("[data-field-trigger]");
  const pause = root.querySelector("[data-field-pause]");
  const status = root.querySelector("[data-field-status]");
  const sessionKey = "citry-component-field-paused";
  let paused = false;

  try {
    paused = sessionStorage.getItem(sessionKey) === "true";
  } catch (_error) {
    paused = false;
  }

  const renderPause = () => {
    pause.setAttribute("aria-pressed", paused ? "true" : "false");
    pause.textContent = paused ? "Resume motion" : "Pause motion";
  };
  const runWave = async () => ({ renderer: "baseline", skipped: "baseline" });
  const setPaused = (value) => {
    paused = Boolean(value);
    try {
      sessionStorage.setItem(sessionKey, String(paused));
    } catch (_error) {
      // Storage is optional. The in-page control still works.
    }
    renderPause();
    status.textContent = paused ? "Motion paused." : "Component field ready.";
  };
  const onTrigger = () => {
    status.textContent = "Baseline has no field animation.";
  };
  const onPause = () => setPaused(!paused);

  trigger.addEventListener("click", onTrigger);
  pause.addEventListener("click", onPause);
  renderPause();

  const api = {
    renderer: "baseline",
    ready: true,
    runWave,
    runFiveRipples: async () => [],
    seek: () => null,
    setPaused,
    snapshot: () => ({
      activeAnimationHandles: 0,
      cellCount: 0,
      descriptorSha256: root.dataset.descriptorSha256,
      paused,
      scheduledFrames: 0,
      visible: true,
      waveRuns: 0,
    }),
  };
  window.__fieldResearch = api;
  root.dataset.fieldReady = "true";
  window.dispatchEvent(new Event("field-research-ready"));

  return () => {
    trigger.removeEventListener("click", onTrigger);
    pause.removeEventListener("click", onPause);
    if (window.__fieldResearch === api) {
      delete window.__fieldResearch;
    }
  };
});

