$component(({ els }) => {
  const root = els[0];
  const plane = root.querySelector("[data-field-plane]");
  const canvas = root.querySelector("[data-field-canvas]");
  const descriptorBlock = root.querySelector("[data-field-descriptors]");
  const trigger = root.querySelector("[data-field-trigger]");
  const pause = root.querySelector("[data-field-pause]");
  const status = root.querySelector("[data-field-status]");
  const reducedQuery = matchMedia("(prefers-reduced-motion: reduce)");
  const sessionKey = "citry-component-field-paused";
  const maxBackingPixels = 8000000;
  const colors = ["#7784ff", "#55c9ff", "#9c72ff", "#5ee5c1"];
  const rippleOrigins = [
    [0.2, 0.25],
    [0.8, 0.25],
    [0.5, 0.5],
    [0.25, 0.8],
    [0.8, 0.75],
  ];
  let context = null;
  let descriptors = [];
  let destroyed = false;
  let paused = false;
  let visible = true;
  let documentVisible = document.visibilityState === "visible";
  let activeWave = null;
  let animationFrame = 0;
  let resizeFrame = 0;
  let waveRuns = 0;
  let rippleIndex = 0;
  let effectiveDpr = 1;
  let initializationError = null;
  let initialized = false;
  let actualDescriptorDigest = null;
  let api = null;

  try {
    paused = sessionStorage.getItem(sessionKey) === "true";
  } catch (_error) {
    paused = false;
  }

  const validateDescriptors = (value) => {
    const expected = Number(root.dataset.cellCount);
    if (!Array.isArray(value) || value.length !== expected) {
      throw new Error(`Expected ${expected} descriptors, received ${value?.length ?? "invalid data"}.`);
    }
    const ids = new Set();
    for (const descriptor of value) {
      if (!Array.isArray(descriptor) || descriptor.length !== 5 || !descriptor.every(Number.isFinite)) {
        throw new Error("Each canvas descriptor must contain five finite numbers.");
      }
      const [id, x, y, phase, palette] = descriptor;
      if (!Number.isInteger(id) || ids.has(id) || id < 0 || id >= expected) {
        throw new Error(`Invalid or duplicate canvas descriptor ID ${id}.`);
      }
      if (x < 0 || x > 1000000 || y < 0 || y > 1000000 || phase < 0 || phase > 1600) {
        throw new Error(`Canvas descriptor ${id} is outside the coordinate contract.`);
      }
      if (!Number.isInteger(palette) || palette < 0 || palette >= colors.length) {
        throw new Error(`Canvas descriptor ${id} has invalid palette ${palette}.`);
      }
      ids.add(id);
    }
    return value;
  };
  const descriptorDigest = async (value) => {
    if (!globalThis.crypto?.subtle) {
      throw new Error("Web Crypto SHA-256 is unavailable.");
    }
    const bytes = new TextEncoder().encode(JSON.stringify(value));
    const digest = await crypto.subtle.digest("SHA-256", bytes);
    return Array.from(new Uint8Array(digest), (byte) => byte.toString(16).padStart(2, "0")).join("");
  };
  const failInitialization = (error) => {
    initializationError = String(error);
    initialized = false;
    root.dataset.fieldReady = "fallback";
    root.dataset.fieldError = initializationError;
    trigger.disabled = true;
    pause.disabled = true;
    status.textContent = "Static component field fallback active.";
  };
  const sizeCanvas = () => {
    const bounds = plane.getBoundingClientRect();
    if (!context || bounds.width <= 0 || bounds.height <= 0) {
      return false;
    }
    const requestedDpr = Math.min(window.devicePixelRatio || 1, 2);
    const requestedPixels = bounds.width * bounds.height * requestedDpr * requestedDpr;
    effectiveDpr = requestedPixels > maxBackingPixels
      ? requestedDpr * Math.sqrt(maxBackingPixels / requestedPixels)
      : requestedDpr;
    const width = Math.max(1, Math.floor(bounds.width * effectiveDpr));
    const height = Math.max(1, Math.floor(bounds.height * effectiveDpr));
    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width;
      canvas.height = height;
    }
    context.setTransform(effectiveDpr, 0, 0, effectiveDpr, 0, 0);
    plane.dataset.effectiveDpr = effectiveDpr.toFixed(4);
    plane.dataset.backingPixels = String(width * height);
    return true;
  };
  const waveEnergy = (elapsed, descriptor, origin, frontMs) => {
    const x = descriptor[1] / 1000000;
    const y = descriptor[2] / 1000000;
    const delay = (Math.hypot(x - origin[0], y - origin[1]) / Math.SQRT2) * frontMs;
    const local = (elapsed - delay) / 350;
    return local <= 0 || local >= 1 ? 0 : Math.sin(Math.PI * local);
  };
  const draw = (elapsed = Number.POSITIVE_INFINITY, origin = [0, 0], frontMs = 1600) => {
    if (!sizeCanvas()) {
      return false;
    }
    const width = canvas.width / effectiveDpr;
    const height = canvas.height / effectiveDpr;
    const columns = Number(root.dataset.columns);
    const rows = Number(root.dataset.rows);
    const cellWidth = Math.max(2, width / columns - 2);
    const cellHeight = Math.max(2, height / rows - 2);
    context.clearRect(0, 0, width, height);
    for (const descriptor of descriptors) {
      const pulse = waveEnergy(elapsed, descriptor, origin, frontMs);
      const scale = 0.86 + pulse * 0.14;
      const x = (descriptor[1] / 1000000) * width;
      const y = (descriptor[2] / 1000000) * height;
      const drawWidth = cellWidth * scale;
      const drawHeight = cellHeight * scale;
      const drawX = x + (cellWidth - drawWidth) / 2;
      const drawY = y + (cellHeight - drawHeight) / 2;
      context.globalAlpha = 0.34 + pulse * 0.6;
      context.fillStyle = colors[descriptor[4]];
      context.strokeStyle = colors[descriptor[4]];
      context.lineWidth = 1;
      context.beginPath();
      context.roundRect(drawX, drawY, drawWidth, drawHeight, Math.min(4, drawWidth / 4, drawHeight / 4));
      context.fill();
      context.globalAlpha *= 0.65;
      context.stroke();
    }
    context.globalAlpha = 1;
    plane.dataset.canvasReady = "true";
    return true;
  };
  const canAnimate = () => !destroyed && !paused && visible && documentVisible && !reducedQuery.matches;
  const renderPause = () => {
    pause.setAttribute("aria-pressed", paused ? "true" : "false");
    pause.textContent = paused ? "Resume motion" : "Pause motion";
  };
  const cancelFrame = () => {
    if (animationFrame) {
      cancelAnimationFrame(animationFrame);
      animationFrame = 0;
    }
  };
  const settleActiveWave = (reason) => {
    cancelFrame();
    if (activeWave) {
      const wave = activeWave;
      activeWave = null;
      draw(Number.POSITIVE_INFINITY, wave.origin, wave.frontMs);
      wave.resolve({ renderer: "canvas", skipped: reason });
    }
  };
  const tick = (now) => {
    animationFrame = 0;
    if (!activeWave || destroyed) {
      return;
    }
    if (!canAnimate()) {
      activeWave.suspendedAt ??= now;
      return;
    }
    if (activeWave.suspendedAt !== null) {
      activeWave.startedAt += now - activeWave.suspendedAt;
      activeWave.suspendedAt = null;
    }
    const elapsed = now - activeWave.startedAt;
    draw(elapsed, activeWave.origin, activeWave.frontMs);
    if (elapsed >= activeWave.frontMs + 350) {
      settleActiveWave(null);
      status.textContent = "Component field settled.";
      return;
    }
    animationFrame = requestAnimationFrame(tick);
  };
  const resumeFrame = () => {
    if (activeWave && canAnimate() && !animationFrame) {
      animationFrame = requestAnimationFrame(tick);
    }
  };
  const setPaused = (value) => {
    paused = Boolean(value);
    try {
      sessionStorage.setItem(sessionKey, String(paused));
    } catch (_error) {
      // Storage is optional. The in-page control still works.
    }
    if (paused && activeWave && activeWave.suspendedAt === null) {
      activeWave.suspendedAt = performance.now();
      cancelFrame();
    } else {
      resumeFrame();
    }
    renderPause();
    status.textContent = initializationError
      ? "Static component field fallback active."
      : paused
        ? "Motion paused."
        : "Component field ready.";
  };
  const runWave = ({ origin = [0, 0], frontMs = 1600 } = {}) => {
    if (initializationError) {
      return Promise.resolve({ renderer: "canvas", skipped: "fallback" });
    }
    if (!initialized) {
      return Promise.resolve({ renderer: "canvas", skipped: "initializing" });
    }
    if (!canAnimate()) {
      draw();
      return Promise.resolve({ renderer: "canvas", skipped: reducedQuery.matches ? "reduced-motion" : "inactive" });
    }
    settleActiveWave("superseded");
    waveRuns += 1;
    status.textContent = "Wave moving through the component field.";
    return new Promise((resolve) => {
      activeWave = {
        frontMs,
        origin,
        resolve,
        startedAt: performance.now(),
        suspendedAt: null,
      };
      resumeFrame();
    });
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
    settleActiveWave("seek");
    const bounded = Math.max(0, Math.min(1, Number(progress)));
    draw(bounded * 1950, origin, 1600);
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
    if (!documentVisible && activeWave && activeWave.suspendedAt === null) {
      activeWave.suspendedAt = performance.now();
      cancelFrame();
    } else {
      resumeFrame();
    }
  };
  const onReducedMotion = () => {
    if (reducedQuery.matches) {
      settleActiveWave("reduced-motion");
      draw();
    }
  };
  const onResize = () => {
    if (resizeFrame) {
      return;
    }
    resizeFrame = requestAnimationFrame(() => {
      resizeFrame = 0;
      draw();
    });
  };
  const intersection = new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting;
    if (!visible && activeWave && activeWave.suspendedAt === null) {
      activeWave.suspendedAt = performance.now();
      cancelFrame();
    } else {
      resumeFrame();
    }
  });
  const resize = new ResizeObserver(onResize);
  const initialize = async () => {
    try {
      const parsed = validateDescriptors(JSON.parse(descriptorBlock.textContent));
      actualDescriptorDigest = await descriptorDigest(parsed);
      if (actualDescriptorDigest !== root.dataset.descriptorSha256) {
        throw new Error(`Canvas descriptor digest mismatch: ${actualDescriptorDigest}.`);
      }
      if (destroyed) {
        return;
      }
      descriptors = parsed;
      context = canvas.getContext("2d", { alpha: true });
      if (!context) {
        throw new Error("Canvas 2D context is unavailable.");
      }
      if (!draw()) {
        throw new Error("Canvas could not complete its first static draw.");
      }
      initialized = true;
      root.dataset.fieldReady = "true";
      status.textContent = "Component field ready.";
    } catch (error) {
      failInitialization(error);
    }
    window.dispatchEvent(new Event("field-research-ready"));
  };

  trigger.addEventListener("click", onTrigger);
  pause.addEventListener("click", onPause);
  document.addEventListener("visibilitychange", onVisibility);
  reducedQuery.addEventListener("change", onReducedMotion);
  intersection.observe(root);
  resize.observe(plane);
  renderPause();

  const cleanup = () => {
    if (destroyed) {
      return;
    }
    destroyed = true;
    settleActiveWave("cleanup");
    if (resizeFrame) {
      cancelAnimationFrame(resizeFrame);
    }
    intersection.disconnect();
    resize.disconnect();
    trigger.removeEventListener("click", onTrigger);
    pause.removeEventListener("click", onPause);
    document.removeEventListener("visibilitychange", onVisibility);
    reducedQuery.removeEventListener("change", onReducedMotion);
    if (window.__fieldResearch === api) {
      delete window.__fieldResearch;
    }
  };
  api = {
    renderer: "canvas",
    destroyForTest: cleanup,
    get ready() {
      return initialized && initializationError === null;
    },
    runWave,
    runFiveRipples,
    seek,
    setPaused,
    snapshot: () => ({
      activeAnimationHandles: activeWave ? 1 : 0,
      backingPixels: canvas.width * canvas.height,
      cellCount: descriptors.length,
      descriptorSha256: actualDescriptorDigest,
      effectiveDpr,
      initializationError,
      paused,
      reducedMotion: reducedQuery.matches,
      scheduledFrames: animationFrame ? 1 : 0,
      visible,
      waveRuns,
    }),
  };
  window.__fieldResearch = api;
  status.textContent = "Preparing component field.";
  void initialize();

  return cleanup;
});
