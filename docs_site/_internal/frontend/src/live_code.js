// Narrative pages load this small activator first. The CodeMirror and Pyodide
// coordinator is fetched only after a visitor chooses Try live.
const blocks = [...document.querySelectorAll("[data-citry-live-code]")];
// A page permits one active editor, but retains unsaved source per code block
// while the visitor moves between examples.
const drafts = new WeakMap();
let active = null;
let activationEpoch = 0;
let runtimePromise = null;
let importAttempt = 0;

function authoredSource(root) {
  return root.querySelector("[data-live-static] .highlight")?.textContent ?? "";
}

function setInactive(root, { focus = false } = {}) {
  const hasDraft = drafts.has(root);
  const activate = root.querySelector("[data-live-activate]");
  root.querySelector("[data-live-static]").hidden = false;
  root.querySelector("[data-live-workspace]").hidden = true;
  activate.hidden = false;
  activate.disabled = false;
  activate.removeAttribute("title");
  activate.textContent = hasDraft ? "Resume live" : "Try live";
  const draftLabel = root.querySelector("[data-live-draft]");
  draftLabel.hidden = !hasDraft;
  if (focus) activate.focus();
}

function retireActive({ saveDraft = true, focus = false } = {}) {
  if (!active) return;
  const { root, controller } = active;
  if (saveDraft) {
    const source = controller.getSource();
    if (source !== authoredSource(root)) drafts.set(root, source);
    else drafts.delete(root);
  }
  active = null;
  controller.dispose();
  setInactive(root, { focus });
}

// A failed dynamic import remains retryable, and the epoch prevents a slow
// import from activating a block the visitor has already left.
async function loadRuntime(epoch) {
  if (!runtimePromise) {
    importAttempt += 1;
    runtimePromise = import(`./live_code_runtime.js?attempt=${importAttempt}`).catch((error) => {
      runtimePromise = null;
      throw error;
    });
  }
  const module = await runtimePromise;
  if (epoch !== activationEpoch) return null;
  return module;
}

async function activate(root) {
  if (active?.root === root) return;
  const epoch = ++activationEpoch;
  const button = root.querySelector("[data-live-activate]");
  button.disabled = true;
  button.textContent = "Loading…";

  retireActive({ saveDraft: true });

  try {
    const runtime = await loadRuntime(epoch);
    if (!runtime || epoch !== activationEpoch) {
      if (active?.root !== root) setInactive(root);
      return;
    }
    const source = drafts.has(root) ? drafts.get(root) : authoredSource(root);
    const controller = runtime.createLiveCodeRuntime({
      root,
      initialSource: source,
      authoredSource: authoredSource(root),
      onClose() {
        if (active?.controller !== controller) return;
        ++activationEpoch;
        retireActive({ saveDraft: true, focus: true });
      },
      onReset() {
        drafts.delete(root);
      },
    });
    if (epoch !== activationEpoch) {
      controller.dispose();
      return;
    }
    active = { root, controller };
  } catch (error) {
    if (epoch !== activationEpoch) {
      if (active?.root !== root) setInactive(root);
      return;
    }
    button.disabled = false;
    button.hidden = false;
    button.textContent = "Retry live";
    button.title = String(error?.message || error);
    root.querySelector("[data-live-static]").hidden = false;
  }
}

// Server-rendered examples keep their static form until this script has made
// the activation control functional.
for (const root of blocks) {
  const button = root.querySelector("[data-live-activate]");
  button.hidden = false;
  button.addEventListener("click", () => void activate(root));
}

window.addEventListener("beforeunload", () => retireActive({ saveDraft: false }));
