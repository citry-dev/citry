import { simulatePageLoad } from "storybook/preview-api";

const activeByCanvas = new WeakMap();
const pendingByCanvas = new WeakMap();
let generation = 0;

function abortError() {
  return new DOMException("The Citry Canvas render was aborted.", "AbortError");
}

function assertCurrent(token) {
  if (
    token.signal.aborted ||
    pendingByCanvas.get(token.canvas) !== token
  ) {
    throw abortError();
  }
}

function nextTask() {
  return new Promise((resolve) => setTimeout(resolve, 0));
}

function destroyCanvasAlpine(canvas) {
  const destroyTree = globalThis.Alpine?.destroyTree;
  if (typeof destroyTree !== "function") {
    return;
  }
  for (const child of Array.from(canvas.children)) {
    destroyTree(child);
  }
}

function destroyMount(record) {
  destroyCanvasAlpine(record.mount);
  record.mount.remove();
}

function teardownFor(canvas, record) {
  return async () => {
    if (activeByCanvas.get(canvas) !== record) {
      return;
    }
    activeByCanvas.delete(canvas);
    destroyMount(record);
    await nextTask();
  };
}

function waitForReady(canvas, selector, timeoutMs, signal) {
  if (signal.aborted) {
    return Promise.reject(abortError());
  }
  if (canvas.querySelector(selector)) {
    return Promise.resolve();
  }
  return new Promise((resolve, reject) => {
    let timeout;
    const dispose = () => {
      clearTimeout(timeout);
      observer.disconnect();
      signal.removeEventListener("abort", onAbort);
    };
    const onAbort = () => {
      dispose();
      reject(abortError());
    };
    const observer = new MutationObserver(() => {
      if (!canvas.querySelector(selector)) {
        return;
      }
      dispose();
      resolve();
    });
    observer.observe(canvas, {
      attributes: true,
      childList: true,
      subtree: true,
    });
    signal.addEventListener("abort", onAbort, { once: true });
    timeout = setTimeout(() => {
      dispose();
      reject(
        new Error(
          `Citry scenario did not reach readiness selector ${selector} within ${timeoutMs} ms.`,
        ),
      );
    }, timeoutMs);
  });
}

export function beginCitryCanvasRender(context, canvas) {
  pendingByCanvas.get(canvas)?.controller.abort();
  const controller = new AbortController();
  const token = {
    canvas,
    controller,
    generation: generation += 1,
    signal: AbortSignal.any([
      context.storyContext.abortSignal,
      controller.signal,
    ]),
  };
  pendingByCanvas.set(canvas, token);
  return token;
}

export async function mountCitryCanvasHtml(context, token, html) {
  assertCurrent(token);
  const { canvas } = token;
  const previous = activeByCanvas.get(canvas);
  if (typeof html !== "string") {
    if (pendingByCanvas.get(canvas) === token) {
      pendingByCanvas.delete(canvas);
    }
    const error = new TypeError(
      `Citry scenario ${context.id} did not return an HTML string.`,
    );
    if (previous) {
      context.showError({
        title: `Citry scenario ${context.id} did not return HTML.`,
        description: error.message,
      });
      throw error;
    }
    context.showError({
      title: `Citry scenario ${context.id} did not return HTML.`,
      description: "The private Citry scenario renderer must return an HTML string.",
    });
    throw error;
  }

  const mount = document.createElement("div");
  mount.hidden = true;
  mount.setAttribute("data-citry-storybook-generation", String(token.generation));
  mount.innerHTML = html;
  canvas.append(mount);
  const record = {
    generation: token.generation,
    mount,
    scenarioId: context.storyContext.parameters.citry?.scenarioId,
  };

  // The candidate must be connected for Citry's document observer to activate
  // it, but it stays hidden until it reaches the declared readiness state.
  simulatePageLoad(mount);

  try {
    const citry = context.storyContext.parameters.citry;
    if (citry?.clientInteractive) {
      if (!citry.readySelector) {
        throw new Error(`Interactive Citry scenario ${context.id} has no readiness selector.`);
      }
      await waitForReady(
        mount,
        citry.readySelector,
        citry.readyTimeoutMs ?? 10_000,
        token.signal,
      );
    }
    assertCurrent(token);
    if (previous) {
      destroyMount(previous);
    }
    activeByCanvas.set(canvas, record);
    pendingByCanvas.delete(canvas);
    mount.hidden = false;
    mount.style.display = "contents";
    context.showMain();
  } catch (error) {
    const isCurrent = pendingByCanvas.get(canvas) === token;
    if (isCurrent) {
      pendingByCanvas.delete(canvas);
    }
    destroyMount(record);
    await nextTask();
    if (
      isCurrent &&
      (pendingByCanvas.has(canvas) ||
        (previous && activeByCanvas.get(canvas) !== previous))
    ) {
      throw abortError();
    }
    if (
      isCurrent &&
      !(error instanceof DOMException && error.name === "AbortError") &&
      previous &&
      activeByCanvas.get(canvas) === previous &&
      !pendingByCanvas.has(canvas)
    ) {
      context.showError({
        title: `Citry scenario ${context.id} did not become ready.`,
        description: error instanceof Error ? error.message : String(error),
      });
      throw error;
    }
    throw error;
  }

  return teardownFor(canvas, record);
}
