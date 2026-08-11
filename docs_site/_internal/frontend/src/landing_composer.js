const DRAG_THRESHOLD_PX = 5;
const DROP_PROXIMITY_PX = 88;
const AUTOSCROLL_EDGE_PX = 88;
const AUTOSCROLL_MAX_SPEED_PX_PER_SECOND = 960;
const ID_REFERENCE_ATTRIBUTES = [
  "aria-controls",
  "aria-describedby",
  "aria-errormessage",
  "aria-labelledby",
  "for",
  "form",
  "headers",
];
const INTERACTIVE_SELECTOR = "a[href], button, input, select, textarea, [tabindex], [contenteditable]";

function accepts(drop, kind) {
  return drop.dataset.composerAccepts?.split(/\s+/).includes(kind) ?? false;
}

function distanceToRect(x, y, rect) {
  const dx = Math.max(rect.left - x, 0, x - rect.right);
  const dy = Math.max(rect.top - y, 0, y - rect.bottom);
  return Math.hypot(dx, dy);
}

function createRootDrop() {
  const drop = document.createElement("button");
  drop.type = "button";
  drop.className = "landing-composer__drop landing-composer__drop--root";
  drop.dataset.composerDrop = "";
  drop.dataset.composerAccepts = "layout content action control";
  drop.innerHTML = `
    <span aria-hidden="true">+</span>
    <strong>Drop a component here</strong>
    <small>Start with a Card, Grid, or anything you like.</small>
  `;
  return drop;
}

function dropAxis(drop) {
  if (drop.dataset.composerDropAxis) return drop.dataset.composerDropAxis;
  const parent = drop.parentElement;
  if (!parent) return "block";
  const style = getComputedStyle(parent);
  if (style.display.includes("flex") && !style.flexDirection.startsWith("column")) return "inline";
  if (style.display.includes("grid") && style.gridAutoFlow.startsWith("column")) return "inline";
  return "block";
}

function createFlowDrop(reference, position, axis) {
  const drop = document.createElement("button");
  const logicalPosition = axis === "inline"
    ? position === "before" ? "start" : "end"
    : position;
  drop.type = "button";
  drop.className = "landing-composer__drop landing-composer__drop--flow";
  drop.dataset.composerDrop = "";
  drop.dataset.composerDropAxis = axis;
  drop.dataset.composerFlowPosition = logicalPosition;
  drop.dataset.composerAccepts = reference.dataset.composerAccepts;
  drop.setAttribute("aria-label", `Drop ${logicalPosition} of this component`);
  drop.innerHTML = `
    <span aria-hidden="true">+</span>
    <strong>Drop ${logicalPosition}</strong>
  `;
  return drop;
}

function rewriteIdentifiers(container, prefix) {
  const identifiers = new Map();
  for (const element of container.querySelectorAll("[id]")) {
    const previous = element.id;
    const next = `${prefix}-${previous}`;
    identifiers.set(previous, next);
    element.id = next;
  }
  for (const attribute of ID_REFERENCE_ATTRIBUTES) {
    for (const element of container.querySelectorAll(`[${attribute}]`)) {
      const tokens = element.getAttribute(attribute).split(/\s+/);
      element.setAttribute(attribute, tokens.map((token) => identifiers.get(token) || token).join(" "));
    }
  }
  for (const link of container.querySelectorAll('a[href^="#"]')) {
    const identifier = link.getAttribute("href").slice(1);
    if (identifiers.has(identifier)) link.setAttribute("href", `#${identifiers.get(identifier)}`);
  }
}

function readRecipeTemplates(root) {
  const bank = root.querySelector("script[data-composer-recipe-bank]");
  if (!bank) return new Map();
  const parser = document.createElement("template");
  parser.innerHTML = JSON.parse(bank.textContent);
  for (const style of parser.content.querySelectorAll("style[data-citry-css-class]")) {
    bank.before(style);
  }
  return new Map(
    [...parser.content.querySelectorAll("template[data-composer-recipe-template]")].map((template) => [
      template.dataset.composerRecipeTemplate,
      template,
    ]),
  );
}

function activateComposer(root) {
  const templates = readRecipeTemplates(root);
  const paletteItems = [...root.querySelectorAll("[data-composer-palette-drag]")];
  const abort = new AbortController();
  const listen = (element, type, handler, options = {}) => {
    element.addEventListener(type, handler, { ...options, signal: abort.signal });
  };
  const elements = {
    board: root.querySelector("[data-composer-board]"),
    canvas: root.querySelector("[data-composer-canvas]"),
    reset: root.querySelector("[data-composer-reset]"),
  };
  if (
    Object.values(elements).some((element) => !element)
    || !paletteItems.length
    || paletteItems.some((item) => !templates.has(item.dataset.composerPaletteDrag))
  ) {
    throw new Error("The component showcase is incomplete.");
  }

  let selectedDrop = elements.canvas.querySelector("[data-composer-drop]");
  let drag = null;
  let instance = 0;
  let suppressedPaletteClick = null;

  function chooseDrop(drop) {
    for (const candidate of elements.canvas.querySelectorAll("[data-composer-drop]")) {
      candidate.classList.remove("is-selected");
      candidate.removeAttribute("aria-pressed");
    }
    selectedDrop = drop?.isConnected && elements.canvas.contains(drop) ? drop : null;
    if (!selectedDrop) return;
    selectedDrop.classList.add("is-selected");
    selectedDrop.setAttribute("aria-pressed", "true");
  }

  function prepareRecipe(wrapper) {
    instance += 1;
    rewriteIdentifiers(wrapper, `landing-recipe-${instance}`);
    for (const element of wrapper.querySelectorAll(INTERACTIVE_SELECTOR)) {
      if (element.matches("[data-composer-drop]")) continue;
      element.tabIndex = -1;
      element.dataset.composerInertControl = "";
    }
  }

  function destinationFor(kind) {
    if (selectedDrop && accepts(selectedDrop, kind)) return selectedDrop;
    return [...elements.canvas.querySelectorAll("[data-composer-drop]")].find((drop) => accepts(drop, kind)) || null;
  }

  function insertRecipe(recipeId, destination = null) {
    const template = templates.get(recipeId);
    const palette = root.querySelector(`[data-composer-palette-drag="${CSS.escape(recipeId)}"]`);
    const kind = palette?.dataset.composerKind;
    const drop = destination || destinationFor(kind);
    if (!template || !kind || !drop || !accepts(drop, kind)) return false;

    const fragment = template.content.cloneNode(true);
    const wrapper = fragment.querySelector("[data-composer-rendered-recipe]");
    if (!wrapper) throw new Error(`Recipe ${recipeId} has no rendered root.`);
    prepareRecipe(wrapper);
    const componentDrop = wrapper.querySelector("[data-composer-drop]");
    const axis = dropAxis(drop);
    const before = createFlowDrop(drop, "before", axis);
    const after = createFlowDrop(drop, "after", axis);
    drop.replaceWith(before, fragment, after);
    wrapper.classList.add("is-just-placed");
    requestAnimationFrame(() => wrapper.classList.remove("is-just-placed"));
    chooseDrop(componentDrop || after);
    return true;
  }

  function clearDrag() {
    if (!drag) return;
    if (drag.scrollFrame !== null) cancelAnimationFrame(drag.scrollFrame);
    drag.ghost?.remove();
    drag.visualSource.classList.remove("is-drag-pending", "is-drag-source");
    for (const drop of elements.canvas.querySelectorAll("[data-composer-drop]")) {
      drop.classList.remove("is-drag-available", "is-drag-unavailable", "is-drag-near", "is-drag-target");
    }
    delete root.dataset.composerDragging;
    drag = null;
  }

  function markDropAreas() {
    for (const drop of elements.canvas.querySelectorAll("[data-composer-drop]")) {
      drop.classList.add(accepts(drop, drag.kind) ? "is-drag-available" : "is-drag-unavailable");
    }
  }

  function activateDrag() {
    drag.active = true;
    drag.visualSource.classList.remove("is-drag-pending");
    drag.visualSource.classList.add("is-drag-source");
    root.dataset.composerDragging = drag.kind;
    markDropAreas();

    const ghost = document.createElement("div");
    ghost.className = "landing-composer__drag-ghost";
    ghost.innerHTML = `
      <span class="landing-composer__drag-ghost-grip" aria-hidden="true">⠿</span>
      <strong></strong>
      <small>Drop onto a glowing area</small>
    `;
    ghost.querySelector("strong").textContent = drag.label;
    document.body.append(ghost);
    drag.ghost = ghost;
  }

  function dragDestinationAt(x, y) {
    const drop = document.elementFromPoint(x, y)?.closest("[data-composer-drop]");
    return drop && elements.canvas.contains(drop) ? drop : null;
  }

  function nearestFlowDrop(x, y) {
    const boardRect = elements.board.getBoundingClientRect();
    const insideBoard = x >= boardRect.left && x <= boardRect.right && y >= boardRect.top && y <= boardRect.bottom;
    let nearest = null;
    let nearestDistance = DROP_PROXIMITY_PX;
    if (insideBoard) {
      for (const drop of elements.canvas.querySelectorAll(".landing-composer__drop--flow.is-drag-available")) {
        const distance = distanceToRect(x, y, drop.getBoundingClientRect());
        if (distance <= nearestDistance) {
          nearest = drop;
          nearestDistance = distance;
        }
      }
    }
    return nearest;
  }

  function showNearbyFlowDrop(nearest) {
    // One enlarged gap is enough to aim at and avoids stretching the whole composition.
    for (const drop of elements.canvas.querySelectorAll(".landing-composer__drop--flow")) {
      drop.classList.toggle("is-drag-near", drop === nearest);
    }
  }

  function updateDragTarget(x, y) {
    drag.target?.classList.remove("is-drag-target");
    const direct = dragDestinationAt(x, y);
    const directIsAvailable = direct && accepts(direct, drag.kind);
    const nearby = directIsAvailable && !direct.matches(".landing-composer__drop--flow")
      ? null
      : nearestFlowDrop(x, y);
    showNearbyFlowDrop(nearby);
    const destination = directIsAvailable ? direct : nearby;
    destination?.classList.add("is-drag-target");
    drag.target = destination;
  }

  function edgeScrollVelocity(x, y) {
    const rect = elements.board.getBoundingClientRect();
    if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) return 0;
    const edge = Math.min(AUTOSCROLL_EDGE_PX, rect.height / 3);
    let strength = 0;
    // Squaring the edge depth keeps the inner boundary calm and accelerates toward the edge.
    if (y < rect.top + edge) strength = -1 * ((rect.top + edge - y) / edge) ** 2;
    if (y > rect.bottom - edge) strength = ((y - (rect.bottom - edge)) / edge) ** 2;
    return strength * AUTOSCROLL_MAX_SPEED_PX_PER_SECOND;
  }

  function autoScroll(timestamp) {
    if (!drag?.active) return;
    drag.scrollFrame = null;
    const velocity = edgeScrollVelocity(drag.pointerX, drag.pointerY);
    if (!velocity) {
      drag.scrollTime = null;
      drag.scrollPosition = null;
      return;
    }
    const elapsed = Math.min(timestamp - (drag.scrollTime ?? timestamp), 32);
    if (drag.scrollPosition === null) drag.scrollPosition = elements.board.scrollTop;
    drag.scrollTime = timestamp;
    const previous = elements.board.scrollTop;
    // WebKit rounds scrollTop writes, so retain fractional movement until it reaches a whole pixel.
    drag.scrollPosition += velocity * (elapsed / 1000);
    elements.board.scrollTop = drag.scrollPosition;
    // Content moves under a stationary pointer, so its nearest gap can change without pointermove.
    if (elements.board.scrollTop !== previous) updateDragTarget(drag.pointerX, drag.pointerY);
    const canContinue = velocity < 0
      ? elements.board.scrollTop > 0
      : elements.board.scrollTop + elements.board.clientHeight < elements.board.scrollHeight - 1;
    if (canContinue) {
      drag.scrollFrame = requestAnimationFrame(autoScroll);
    } else {
      drag.scrollTime = null;
      drag.scrollPosition = null;
    }
  }

  function requestAutoScroll() {
    if (drag.scrollFrame === null && edgeScrollVelocity(drag.pointerX, drag.pointerY)) {
      drag.scrollTime = null;
      drag.scrollPosition = null;
      drag.scrollFrame = requestAnimationFrame(autoScroll);
    }
  }

  listen(root, "pointerdown", (event) => {
    const palette = event.target.closest("[data-composer-palette-drag]");
    if (!palette || event.button !== 0 || !event.isPrimary) return;
    const visualSource = palette.closest("[data-composer-palette-item]") || palette;
    visualSource.classList.add("is-drag-pending");
    drag = {
      pointerId: event.pointerId,
      startX: event.clientX,
      startY: event.clientY,
      recipeId: palette.dataset.composerPaletteDrag,
      kind: palette.dataset.composerKind,
      label: palette.querySelector("strong")?.textContent?.trim() || "Component",
      visualSource,
      active: false,
      target: null,
      ghost: null,
      pointerX: event.clientX,
      pointerY: event.clientY,
      scrollFrame: null,
      scrollPosition: null,
      scrollTime: null,
    };
    palette.setPointerCapture?.(event.pointerId);
  });

  listen(window, "pointermove", (event) => {
    if (!drag || event.pointerId !== drag.pointerId) return;
    if (
      !drag.active
      && Math.hypot(event.clientX - drag.startX, event.clientY - drag.startY) >= DRAG_THRESHOLD_PX
    ) {
      activateDrag();
    }
    if (!drag.active) return;
    event.preventDefault();
    drag.pointerX = event.clientX;
    drag.pointerY = event.clientY;
    drag.ghost.style.transform = `translate3d(${event.clientX + 16}px, ${event.clientY + 16}px, 0)`;
    updateDragTarget(event.clientX, event.clientY);
    requestAutoScroll();
  }, { passive: false });

  listen(window, "pointerup", (event) => {
    if (!drag || event.pointerId !== drag.pointerId) return;
    const finished = drag;
    const destination = finished.target;
    if (finished.active) {
      suppressedPaletteClick = { recipeId: finished.recipeId, until: performance.now() + 300 };
    }
    clearDrag();
    if (finished.active && destination && accepts(destination, finished.kind)) {
      insertRecipe(finished.recipeId, destination);
    }
  });
  listen(window, "pointercancel", clearDrag);

  listen(root, "click", (event) => {
    const palette = event.target.closest("[data-composer-palette-drag]");
    if (palette) {
      if (
        suppressedPaletteClick?.recipeId === palette.dataset.composerPaletteDrag
        && performance.now() < suppressedPaletteClick.until
      ) {
        suppressedPaletteClick = null;
        event.preventDefault();
        return;
      }
      suppressedPaletteClick = null;
      insertRecipe(palette.dataset.composerPaletteDrag);
      return;
    }
    const drop = event.target.closest("[data-composer-drop]");
    if (drop && elements.canvas.contains(drop)) chooseDrop(drop);
  });

  listen(elements.canvas, "pointerdown", (event) => {
    if (event.target.closest("[data-composer-drop]")) return;
    if (event.target.closest("[data-composer-inert-control]")) event.preventDefault();
  }, { capture: true });
  listen(elements.canvas, "click", (event) => {
    if (event.target.closest("[data-composer-drop]")) return;
    if (!event.target.closest("[data-composer-rendered-recipe]")) return;
    event.preventDefault();
    event.stopPropagation();
  }, { capture: true });
  listen(elements.canvas, "keydown", (event) => {
    if (event.target.closest("[data-composer-drop]")) return;
    if (event.target.closest("[data-composer-rendered-recipe]")) event.preventDefault();
  }, { capture: true });

  listen(elements.reset, "click", () => {
    clearDrag();
    instance = 0;
    const drop = createRootDrop();
    elements.canvas.replaceChildren(drop);
    chooseDrop(drop);
  });

  chooseDrop(selectedDrop);
  root.dataset.composerReady = "";

  listen(window, "pagehide", () => {
    clearDrag();
    abort.abort();
  }, { once: true });
}

for (const root of document.querySelectorAll("[data-landing-composer]")) {
  try {
    activateComposer(root);
  } catch (error) {
    root.dataset.composerFailed = "";
    console.error("Landing component showcase initialization failed.", error);
  }
}
