$component(({ els }) => {
  const root = els[0];
  const cells = Array.from(root.querySelectorAll("[data-field-cell]"));
  const trigger = root.querySelector("[data-field-trigger]");
  const pause = root.querySelector("[data-field-pause]");
  const status = root.querySelector("[data-field-status]");
  const reducedQuery = matchMedia("(prefers-reduced-motion: reduce)");
  const sessionKey = "citry-component-field-paused";
  const rippleOrigins = [
    [0.2, 0.25],
    [0.8, 0.25],
    [0.5, 0.5],
    [0.25, 0.8],
    [0.8, 0.75],
  ];
  let animations = [];
  let destroyed = false;
  let paused = false;
  let visible = true;
  let documentVisible = document.visibilityState === "visible";
  let waveRuns = 0;
  let rippleIndex = 0;
  let sequence = 0;
  let api = null;

  try {
    paused = sessionStorage.getItem(sessionKey) === "true";
  } catch (_error) {
    paused = false;
  }

  const normalizedPosition = (cell) => ({
    x: Number.parseFloat(cell.style.getPropertyValue("--cell-x")),
    y: Number.parseFloat(cell.style.getPropertyValue("--cell-y")),
  });
  const delayFor = (cell, origin, frontMs) => {
    const position = normalizedPosition(cell);
    return (Math.hypot(position.x - origin[0], position.y - origin[1]) / Math.SQRT2) * frontMs;
  };
  const stopAnimations = () => {
    sequence += 1;
    for (const animation of animations) {
      animation.cancel();
    }
    animations = [];
  };
  const settleCells = () => {
    for (const cell of cells) {
      cell.style.opacity = "0.34";
      cell.style.transform = "scale(0.86)";
    }
  };
  const canAnimate = () => !destroyed && !paused && visible && documentVisible && !reducedQuery.matches;
  const renderPause = () => {
    pause.setAttribute("aria-pressed", paused ? "true" : "false");
    pause.textContent = paused ? "Resume motion" : "Pause motion";
  };
  const setPaused = (value) => {
    paused = Boolean(value);
    try {
      sessionStorage.setItem(sessionKey, String(paused));
    } catch (_error) {
      // Storage is optional. The in-page control still works.
    }
    for (const animation of animations) {
      if (paused) {
        animation.pause();
      } else if (visible && documentVisible && !reducedQuery.matches) {
        animation.play();
      }
    }
    renderPause();
    status.textContent = paused ? "Motion paused." : "Component field ready.";
  };
  const runWave = async ({ origin = [0, 0], frontMs = 1600 } = {}) => {
    if (!canAnimate()) {
      settleCells();
      return { renderer: "dom", skipped: reducedQuery.matches ? "reduced-motion" : "inactive" };
    }

    stopAnimations();
    const ownSequence = sequence;
    waveRuns += 1;
    status.textContent = "Wave moving through the component field.";
    animations = cells.map((cell) =>
      cell.animate(
        [
          { opacity: 0.2, transform: "scale(0.72)" },
          { opacity: 0.94, transform: "scale(1)" },
          { opacity: 0.34, transform: "scale(0.86)" },
        ],
        {
          delay: delayFor(cell, origin, frontMs),
          duration: 350,
          easing: "cubic-bezier(0.22, 1, 0.36, 1)",
          fill: "forwards",
        },
      ),
    );
    await Promise.allSettled(animations.map((animation) => animation.finished));
    if (destroyed || ownSequence !== sequence) {
      return { renderer: "dom", skipped: "superseded" };
    }
    for (const animation of animations) {
      animation.commitStyles();
      animation.cancel();
    }
    animations = [];
    status.textContent = "Component field settled.";
    return { renderer: "dom", skipped: null };
  };
  const runFiveRipples = async () => {
    const results = [];
    for (const origin of rippleOrigins) {
      results.push(await runWave({ origin, frontMs: 550 }));
      await new Promise((resolve) => setTimeout(resolve, 100));
    }
    return results;
  };
  const seek = (progress, origin = [0, 0]) => {
    stopAnimations();
    const bounded = Math.max(0, Math.min(1, Number(progress)));
    const elapsed = bounded * 1950;
    for (const cell of cells) {
      const local = (elapsed - delayFor(cell, origin, 1600)) / 350;
      const pulse = local <= 0 || local >= 1 ? 0 : Math.sin(Math.PI * local);
      cell.style.opacity = String(0.34 + pulse * 0.6);
      cell.style.transform = `scale(${0.86 + pulse * 0.14})`;
    }
    return bounded;
  };
  const onTrigger = () => {
    const origin = rippleOrigins[rippleIndex % rippleOrigins.length];
    rippleIndex += 1;
    void runWave({ origin, frontMs: 550 });
  };
  const onPause = () => setPaused(!paused);
  const onVisibility = () => {
    documentVisible = document.visibilityState === "visible";
    for (const animation of animations) {
      if (documentVisible && visible && !paused && !reducedQuery.matches) {
        animation.play();
      } else {
        animation.pause();
      }
    }
  };
  const onReducedMotion = () => {
    if (reducedQuery.matches) {
      stopAnimations();
      settleCells();
    }
  };
  const intersection = new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting;
    for (const animation of animations) {
      if (visible && documentVisible && !paused && !reducedQuery.matches) {
        animation.play();
      } else {
        animation.pause();
      }
    }
  });

  trigger.addEventListener("click", onTrigger);
  pause.addEventListener("click", onPause);
  document.addEventListener("visibilitychange", onVisibility);
  reducedQuery.addEventListener("change", onReducedMotion);
  intersection.observe(root);
  renderPause();
  settleCells();

  const cleanup = () => {
    if (destroyed) {
      return;
    }
    destroyed = true;
    stopAnimations();
    intersection.disconnect();
    trigger.removeEventListener("click", onTrigger);
    pause.removeEventListener("click", onPause);
    document.removeEventListener("visibilitychange", onVisibility);
    reducedQuery.removeEventListener("change", onReducedMotion);
    if (window.__fieldResearch === api) {
      delete window.__fieldResearch;
    }
  };
  api = {
    renderer: "dom",
    ready: true,
    destroyForTest: cleanup,
    runWave,
    runFiveRipples,
    seek,
    setPaused,
    snapshot: () => ({
      activeAnimationHandles: animations.filter((animation) => animation.playState !== "finished").length,
      cellCount: cells.length,
      descriptorSha256: root.dataset.descriptorSha256,
      paused,
      reducedMotion: reducedQuery.matches,
      scheduledFrames: 0,
      visible,
      waveRuns,
    }),
  };
  window.__fieldResearch = api;
  root.dataset.fieldReady = "true";
  window.dispatchEvent(new Event("field-research-ready"));

  return cleanup;
});
