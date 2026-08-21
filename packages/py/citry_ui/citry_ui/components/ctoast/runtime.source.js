const toastRegistryKey = Symbol.for("citry-ui:toast-region-runtime");
const toastRegistry = globalThis[toastRegistryKey] ?? new WeakMap();
globalThis[toastRegistryKey] = toastRegistry;

$component({
  props: {
    items: {}, placement: {}, limit: {}, durationMs: {}, pauseOnHover: {},
    pauseOnFocus: {}, pauseOnHidden: {}, onDismiss: {}, onAction: {},
  },
  init: ({ els, data, props, effect, i18n }) => {
    const region = els[0];
    const scope = region.getRootNode();
    const ownerDocument = region.ownerDocument;
    const existing = toastRegistry.get(scope);
    if (existing?.isConnected && existing !== region) {
      console.error("[citry-ui] CToastRegion permits only one initialized Region per root.", region);
      region.inert = true;
      return;
    }
    toastRegistry.set(scope, region);

    const list = region.querySelector("[data-citry-toast-list]");
    const polite = region.querySelector('[data-citry-ui-part="announcer-polite"]');
    const assertive = region.querySelector('[data-citry-ui-part="announcer-assertive"]');
    if (!list || !polite || !assertive) {
      console.error("[citry-ui] CToastRegion could not resolve its owned anatomy.", region);
      toastRegistry.delete(scope);
      return;
    }
    // A retained Region can be reinitialized while the previous
    // generation's short live-region dwell is still active. Its cleanup
    // cancels that generation's clear task, so normalize inherited text
    // before rebuilding the queue rather than leaving it live forever.
    polite.textContent = "";
    assertive.textContent = "";

    const placements = [
      "block-start-start", "block-start-end", "block-end-start", "block-end-end",
    ];
    const intents = ["neutral", "info", "success", "warn", "error"];
    const priorities = ["polite", "assertive"];
    const runtimeState = region.__citryUiToastRuntime ?? {
      entries: [], suppressedIds: [], timers: {}, focusReturn: null,
      focusedId: null, focusedPart: null, nodeCounter: 0,
      announcedFingerprints: new Map(),
    };
    region.__citryUiToastRuntime = runtimeState;
    const invalidEpisodes = new Set();
    const suppressedIds = new Set(runtimeState.suppressedIds ?? []);
    const announcedFingerprints = runtimeState.announcedFingerprints instanceof Map
      ? new Map(runtimeState.announcedFingerprints)
      : new Map();
    const nodes = new Map();
    const timerRecords = new Map(
      Object.entries(runtimeState.timers ?? {}).map(([id, record]) => [
        id, { remaining: record.remaining, started: 0, handle: null },
      ]),
    );
    const taskHandles = new Set();
    const modalObserver = new MutationObserver((records) => {
      const relevant = records.some((record) => record.type === "attributes"
        || [...record.addedNodes, ...record.removedNodes].some((node) => node instanceof Element
          && (node.matches("dialog") || node.querySelector("dialog") || node.shadowRoot)));
      if (relevant) refreshModalState();
    });
    let entries = (runtimeState.entries ?? []).map((entry) => ({
      message: { ...entry.message },
      announcePending: announcedFingerprints.get(entry.message.id)
        !== entry.message.fingerprint,
    }));
    let config = {
      placement: data.placement,
      limit: data.limit,
      durationMs: data.durationMs,
      pauseOnHover: data.pauseOnHover,
      pauseOnFocus: data.pauseOnFocus,
      pauseOnHidden: data.pauseOnHidden,
    };
    let onDismiss = null;
    let onAction = null;
    let hovering = false;
    let focusWithin = false;
    let modalPaused = false;
    let focusReturn = runtimeState.focusReturn?.isConnected ? runtimeState.focusReturn : null;
    let pendingFocusId = runtimeState.focusedId ?? null;
    let pendingFocusPart = runtimeState.focusedPart ?? null;
    let generation = 0;
    let disposed = false;
    let announcementQueue = [];
    let announcementRunning = false;
    let nodeCounter = runtimeState.nodeCounter ?? 0;

    const composedParent = (node) => {
      if (node?.parentNode) return node.parentNode;
      const root = node?.getRootNode?.();
      return root instanceof ShadowRoot ? root.host : null;
    };
    const composedContains = (ancestor, node) => {
      for (let current = node; current; current = composedParent(current)) {
        if (current === ancestor) return true;
      }
      return false;
    };
    const deepActiveElement = () => {
      let active = ownerDocument.activeElement;
      while (active?.shadowRoot?.activeElement) active = active.shadowRoot.activeElement;
      return active;
    };
    const isFocusable = (element) => element instanceof HTMLElement
      && element.isConnected
      && !element.hidden
      && !element.matches(":disabled,[inert]")
      && !element.closest("[inert]")
      && element.getClientRects().length > 0;
    const focusBody = () => {
      const body = ownerDocument.body;
      if (!body) return;
      const hadTabIndex = body.hasAttribute("tabindex");
      const previousTabIndex = body.getAttribute("tabindex");
      if (!hadTabIndex) body.tabIndex = -1;
      body.focus({ preventScroll: true });
      if (!hadTabIndex) body.removeAttribute("tabindex");
      else if (previousTabIndex !== null) body.setAttribute("tabindex", previousTabIndex);
    };
    const publicMessage = (message) => ({
      id: message.id,
      title: message.title,
      description: message.description,
      intent: message.intent,
      priority: message.priority,
      durationMs: message.durationMs,
      actionLabel: message.actionLabel,
      closeOnAction: message.closeOnAction,
      dismissible: message.dismissible,
    });
    const persistRuntimeState = () => {
      const now = performance.now();
      const active = deepActiveElement();
      const focusedRoot = active?.closest?.("[data-citry-toast-id]");
      runtimeState.entries = entries.map((entry) => ({
        message: { ...entry.message, fingerprint: entry.message.fingerprint },
      }));
      runtimeState.suppressedIds = [...suppressedIds];
      runtimeState.announcedFingerprints = new Map(announcedFingerprints);
      runtimeState.timers = Object.fromEntries(
        [...timerRecords].map(([id, record]) => [id, {
          remaining: record.handle === null
            ? record.remaining
            : Math.max(0, record.remaining - (now - record.started)),
        }]),
      );
      runtimeState.focusReturn = focusReturn?.isConnected ? focusReturn : null;
      runtimeState.focusedId = focusedRoot?.dataset.citryToastId ?? null;
      runtimeState.focusedPart = active?.matches?.("[data-citry-toast-action]")
        ? "action"
        : active?.matches?.("[data-citry-toast-dismiss]") ? "dismiss" : "toast";
      runtimeState.nodeCounter = nodeCounter;
    };
    const reportInvalid = (name, value) => {
      if (invalidEpisodes.has(name)) return;
      invalidEpisodes.add(name);
      let shown;
      try { shown = JSON.stringify(value) ?? String(value); } catch { shown = String(value); }
      console.error(
        `[citry-ui] CToastRegion ${name} received invalid client value ${shown}; retaining its fallback.`,
        region,
      );
    };
    const resolveBoolean = (name) => {
      const value = props[name] === undefined ? data[name] : props[name];
      if (typeof value === "boolean") { invalidEpisodes.delete(name); return value; }
      reportInvalid(name, value);
      return data[name];
    };
    const resolveInteger = (name, fallback, valid) => {
      const value = props[name] === undefined ? fallback : props[name];
      if (Number.isInteger(value) && valid(value)) {
        invalidEpisodes.delete(name);
        return value;
      }
      reportInvalid(name, value);
      return fallback;
    };
    const resolveCallback = (name) => {
      const value = props[name];
      if (value === undefined || value === null || typeof value === "function") {
        invalidEpisodes.delete(name);
        return value ?? null;
      }
      reportInvalid(name, value);
      return null;
    };
    const text = (name, value, { optional = false, identity = false } = {}) => {
      if (value === null && optional) return null;
      if (typeof value !== "string") throw new TypeError(`${name} must be a string.`);
      const normalized = value.replace(/\r\n?/g, "\n");
      if (normalized.includes("\0")) throw new TypeError(`${name} cannot contain U+0000.`);
      if (!normalized.trim()) throw new TypeError(`${name} cannot be blank.`);
      if (identity && /[\t\n\f\r ]/.test(normalized)) {
        throw new TypeError(`${name} cannot contain ASCII whitespace.`);
      }
      return normalized;
    };
    const formatPattern = (pattern, name, value) => pattern.split(`{${name}}`).join(value);
    const inlineTranslationValue = (value) => value
      .replace(/[\n\r\u001c-\u001e\u0085\u2029]/gu, " ")
      .replace(/[\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]/gu, "");
    const normalizeMessage = (raw, index) => {
      if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
        throw new TypeError(`items[${index}] must be an object.`);
      }
      const duration = raw.durationMs === undefined || raw.durationMs === null
        ? null : raw.durationMs;
      if (duration !== null && (!Number.isInteger(duration)
        || (duration !== 0 && (duration < 1000 || duration > 120000)))) {
        throw new TypeError(`items[${index}].durationMs is invalid.`);
      }
      const intent = raw.intent ?? "neutral";
      const priority = raw.priority ?? "polite";
      if (!intents.includes(intent) || !priorities.includes(priority)) {
        throw new TypeError(`items[${index}] intent or priority is invalid.`);
      }
      const closeOnAction = raw.closeOnAction ?? true;
      const dismissible = raw.dismissible ?? true;
      if (typeof closeOnAction !== "boolean" || typeof dismissible !== "boolean") {
        throw new TypeError(`items[${index}] Boolean field is invalid.`);
      }
      const value = {
        id: text(`items[${index}].id`, raw.id, { identity: true }),
        title: text(`items[${index}].title`, raw.title),
        description: raw.description === undefined
          ? null : text(`items[${index}].description`, raw.description, { optional: true }),
        intent,
        priority,
        durationMs: duration,
        actionLabel: raw.actionLabel === undefined
          ? null : text(`items[${index}].actionLabel`, raw.actionLabel, { optional: true }),
        closeOnAction,
        dismissible,
        dismissLabel: raw.dismissLabel === undefined
          ? null : text(`items[${index}].dismissLabel`, raw.dismissLabel, { optional: true }),
        actionAnnouncement: raw.actionAnnouncement === undefined
          ? null : text(
              `items[${index}].actionAnnouncement`,
              raw.actionAnnouncement,
              { optional: true },
            ),
      };
      value.fingerprint = JSON.stringify(value);
      return value;
    };
    const normalizeItems = (raw) => {
      if (!Array.isArray(raw)) throw new TypeError("items must be an Array.");
      const seen = new Set();
      const result = raw.map((item, index) => {
        const normalized = normalizeMessage(item, index);
        if (seen.has(normalized.id)) throw new TypeError("items require unique ids.");
        seen.add(normalized.id);
        return normalized;
      });
      invalidEpisodes.delete("items");
      return result;
    };
    const activeEntries = () => entries.slice(0, config.limit);
    const effectiveDuration = (entry) => entry.message.durationMs ?? config.durationMs;
    const timersPaused = () => modalPaused
      || (config.pauseOnHover && hovering)
      || (config.pauseOnFocus && focusWithin)
      || (config.pauseOnHidden && ownerDocument.hidden);
    const stopTimer = (entry) => {
      const record = timerRecords.get(entry.message.id);
      if (!record) return;
      if (record.handle !== null) {
        clearTimeout(record.handle);
        taskHandles.delete(record.handle);
        record.remaining = Math.max(0, record.remaining - (performance.now() - record.started));
        record.handle = null;
      }
    };
    const dismiss = (entry, reason, source) => {
      if (disposed || !entries.includes(entry)) return;
      const active = deepActiveElement();
      const node = nodes.get(entry.message.id)?.root;
      const focused = node && composedContains(node, active);
      const oldActive = activeEntries();
      const oldIndex = oldActive.indexOf(entry);
      suppressedIds.add(entry.message.id);
      entries = entries.filter((candidate) => candidate !== entry);
      announcementQueue = announcementQueue.filter((item) => item.id !== entry.message.id);
      stopTimer(entry);
      timerRecords.delete(entry.message.id);
      syncVisible();
      if (focused && (active === deepActiveElement() || !isFocusable(deepActiveElement()))) {
        const survivors = activeEntries();
        const next = survivors[oldIndex] ?? survivors[oldIndex - 1];
        if (next) nodes.get(next.message.id)?.root.focus({ preventScroll: true });
        else if (isFocusable(focusReturn)) focusReturn.focus({ preventScroll: true });
        else focusBody();
      }
      onDismiss?.(entry.message.id, { reason, source, message: publicMessage(entry.message) });
    };
    const scheduleTimer = (entry) => {
      if (!activeEntries().includes(entry) || timersPaused()) return;
      const duration = effectiveDuration(entry);
      if (duration === 0) return;
      let record = timerRecords.get(entry.message.id);
      if (!record) {
        record = { remaining: duration, started: 0, handle: null };
        timerRecords.set(entry.message.id, record);
      }
      if (record.handle !== null) return;
      if (record.remaining <= 0) { dismiss(entry, "timeout", region); return; }
      record.started = performance.now();
      record.handle = setTimeout(() => {
        taskHandles.delete(record.handle);
        record.handle = null;
        record.remaining = 0;
        dismiss(entry, "timeout", region);
      }, record.remaining);
      taskHandles.add(record.handle);
    };
    const syncTimers = () => {
      const active = new Set(activeEntries());
      for (const entry of entries) {
        if (!active.has(entry) || timersPaused()) stopTimer(entry);
        else scheduleTimer(entry);
      }
    };
    const actionAnnouncement = (message) => {
      if (!message.actionLabel) return null;
      if (data.catalogActionAnnouncement) {
        return i18n
          ? i18n.tr("citry-ui-toast-action-available", {
              action_label: inlineTranslationValue(message.actionLabel),
            })
          : formatPattern(
              data.actionAnnouncementPattern,
              "action_label",
              inlineTranslationValue(message.actionLabel),
            );
      }
      return formatPattern(data.actionAnnouncementPattern, "action_label", message.actionLabel);
    };
    const announcementText = (message) => [
      message.title,
      message.description,
      actionAnnouncement(message),
    ].filter(Boolean).join(" ");
    const drainAnnouncements = () => {
      if (announcementRunning || disposed || modalPaused
        || (config.pauseOnHidden && ownerDocument.hidden) || announcementQueue.length === 0) return;
      announcementRunning = true;
      const item = announcementQueue.shift();
      const target = item.priority === "assertive" ? assertive : polite;
      target.textContent = "";
      const token = generation;
      const commitHandle = setTimeout(() => {
        taskHandles.delete(commitHandle);
        const current = entries.find((entry) => entry.message.id === item.id);
        if (disposed || token !== generation
          || !current || current.message.fingerprint !== item.fingerprint) {
          announcementRunning = false;
          drainAnnouncements();
          return;
        }
        if (modalPaused || (config.pauseOnHidden && ownerDocument.hidden)) {
          announcementQueue.unshift(item);
          announcementRunning = false;
          return;
        }
        target.textContent = item.text;
        announcedFingerprints.set(item.id, item.fingerprint);
        persistRuntimeState();
        const nextHandle = setTimeout(() => {
          taskHandles.delete(nextHandle);
          target.textContent = "";
          announcementRunning = false;
          drainAnnouncements();
        }, 250);
        taskHandles.add(nextHandle);
      }, 20);
      taskHandles.add(commitHandle);
    };
    const queueAnnouncement = (entry) => {
      announcementQueue = announcementQueue.filter((item) => item.id !== entry.message.id);
      announcementQueue.push({
        id: entry.message.id,
        fingerprint: entry.message.fingerprint,
        priority: entry.message.priority,
        text: announcementText(entry.message),
      });
      drainAnnouncements();
    };
    const createNode = (entry) => {
      nodeCounter += 1;
      const root = ownerDocument.createElement("div");
      const content = ownerDocument.createElement("div");
      const title = ownerDocument.createElement("div");
      const description = ownerDocument.createElement("div");
      const actions = ownerDocument.createElement("div");
      const action = ownerDocument.createElement("button");
      const dismissButton = ownerDocument.createElement("button");
      const titleId = `${region.id}-title-client-${nodeCounter}`;
      const descriptionId = `${region.id}-description-client-${nodeCounter}`;
      root.className = "cui-toast";
      root.setAttribute("role", "group");
      root.tabIndex = 0;
      root.setAttribute("aria-labelledby", titleId);
      root.setAttribute("data-citry-ui-part", "toast");
      root.setAttribute("data-citry-toast-id", entry.message.id);
      content.className = "cui-toast__content";
      content.setAttribute("data-citry-ui-part", "content");
      title.id = titleId;
      title.className = "cui-toast__title";
      title.setAttribute("data-citry-ui-part", "title");
      description.id = descriptionId;
      description.className = "cui-toast__description";
      description.setAttribute("data-citry-ui-part", "description");
      actions.className = "cui-toast__actions";
      actions.setAttribute("data-citry-ui-part", "actions");
      action.type = "button";
      action.setAttribute("data-citry-toast-action", "");
      action.setAttribute("data-citry-ui-part", "action");
      dismissButton.type = "button";
      dismissButton.textContent = "\u00d7";
      dismissButton.setAttribute("data-citry-toast-dismiss", "");
      dismissButton.setAttribute("data-citry-ui-part", "dismiss");
      content.append(title, description);
      actions.append(action, dismissButton);
      root.append(content, actions);
      const value = {
        root, title, description, actions, action, dismissButton, descriptionId,
        dismissBinding: null,
      };
      nodes.set(entry.message.id, value);
      return value;
    };
    const updateNode = (entry) => {
      const value = nodes.get(entry.message.id) ?? createNode(entry);
      const message = entry.message;
      value.root.dataset.intent = message.intent;
      value.root.dataset.priority = message.priority;
      value.title.textContent = message.title;
      value.description.textContent = message.description ?? "";
      value.description.hidden = message.description === null;
      if (message.description) value.root.setAttribute("aria-describedby", value.descriptionId);
      else value.root.removeAttribute("aria-describedby");
      value.action.textContent = message.actionLabel ?? "";
      value.action.hidden = message.actionLabel === null;
      value.dismissButton.hidden = !message.dismissible;
      if (data.catalogDismiss && i18n) {
        if (value.dismissBinding === null) {
          value.dismissBinding = i18n.bind({
            message: "citry-ui-toast-dismiss",
            values: () => ({title: inlineTranslationValue(entry.message.title)}),
            onChange: (text) => value.dismissButton.setAttribute("aria-label", text),
          });
        } else {
          value.dismissBinding.refresh();
        }
      } else if (data.catalogDismiss) {
        value.dismissButton.setAttribute(
          "aria-label",
          formatPattern(
            data.dismissPattern,
            "title",
            inlineTranslationValue(message.title),
          ),
        );
      } else {
        value.dismissButton.setAttribute(
          "aria-label",
          formatPattern(data.dismissPattern, "title", inlineTranslationValue(message.title)),
        );
      }
      value.actions.hidden = message.actionLabel === null && !message.dismissible;
      return value;
    };
    const recoverFocusAfterSync = (oldActive, focusedId) => {
      if (!focusedId || nodes.has(focusedId)) return;
      const oldIndex = oldActive.findIndex((entry) => entry.message.id === focusedId);
      const candidates = activeEntries();
      const nextId = (candidates[oldIndex] ?? candidates[oldIndex - 1])?.message.id ?? null;
      const token = generation;
      const handle = setTimeout(() => {
        taskHandles.delete(handle);
        if (disposed || token !== generation) return;
        const active = deepActiveElement();
        if (active !== ownerDocument.body && isFocusable(active)) return;
        const next = nextId ? nodes.get(nextId)?.root : null;
        if (isFocusable(next)) next.focus({ preventScroll: true });
        else if (isFocusable(focusReturn)) focusReturn.focus({ preventScroll: true });
        else focusBody();
      }, 0);
      taskHandles.add(handle);
    };
    function syncVisible() {
      const oldActive = [...nodes.keys()];
      const activeElement = deepActiveElement();
      const focusedId = oldActive.find((id) => composedContains(nodes.get(id).root, activeElement));
      const active = activeEntries();
      const activeIds = new Set(active.map((entry) => entry.message.id));
      for (const [id, value] of nodes) {
        if (activeIds.has(id)) continue;
        value.dismissBinding?.dispose();
        value.root.remove();
        nodes.delete(id);
      }
      for (const entry of active) {
        const value = updateNode(entry);
        list.append(value.root);
        if (entry.announcePending) {
          entry.announcePending = false;
          queueAnnouncement(entry);
        }
      }
      recoverFocusAfterSync(
        oldActive.map((id) => ({ message: { id } })),
        focusedId,
      );
      if (pendingFocusId && nodes.has(pendingFocusId)) {
        const pendingId = pendingFocusId;
        const pendingPart = pendingFocusPart;
        pendingFocusId = null;
        pendingFocusPart = null;
        const token = generation;
        const handle = setTimeout(() => {
          taskHandles.delete(handle);
          if (disposed || token !== generation) return;
          const value = nodes.get(pendingId);
          if (!value) return;
          const target = pendingPart === "action" ? value.action
            : pendingPart === "dismiss" ? value.dismissButton : value.root;
          if (isFocusable(target)) target.focus({ preventScroll: true });
        }, 0);
        taskHandles.add(handle);
      }
      syncTimers();
      persistRuntimeState();
    }
    const reconcileItems = (incoming) => {
      const previous = new Map(entries.map((entry) => [entry.message.id, entry]));
      const incomingIds = new Set(incoming.map((message) => message.id));
      for (const id of [...suppressedIds]) {
        if (incomingIds.has(id)) continue;
        suppressedIds.delete(id);
        announcedFingerprints.delete(id);
      }
      const next = [];
      for (const message of incoming) {
        if (suppressedIds.has(message.id)) continue;
        const retained = previous.get(message.id);
        if (retained && retained.message.fingerprint === message.fingerprint) {
          next.push(retained);
          continue;
        }
        if (retained) {
          stopTimer(retained);
          timerRecords.delete(message.id);
          retained.message = message;
          retained.announcePending = true;
          next.push(retained);
        } else {
          next.push({
            message,
            announcePending: announcedFingerprints.get(message.id) !== message.fingerprint,
          });
        }
      }
      for (const entry of entries) {
        if (next.includes(entry)) continue;
        stopTimer(entry);
        timerRecords.delete(entry.message.id);
        announcementQueue = announcementQueue.filter((item) => item.id !== entry.message.id);
        if (!incomingIds.has(entry.message.id)) announcedFingerprints.delete(entry.message.id);
      }
      entries = next;
      syncVisible();
    };
    const openRoots = () => {
      const roots = [ownerDocument];
      for (let index = 0; index < roots.length; index += 1) {
        for (const element of roots[index].querySelectorAll("*")) {
          if (element.shadowRoot) roots.push(element.shadowRoot);
        }
      }
      return roots;
    };
    const observeModalRoots = () => {
      modalObserver.disconnect();
      for (const root of openRoots()) {
        modalObserver.observe(root, {
          subtree: true, childList: true, attributes: true, attributeFilter: ["open"],
        });
      }
    };
    function refreshModalState() {
      observeModalRoots();
      const next = openRoots().flatMap((root) => [...root.querySelectorAll("dialog:modal")])
        .some((modal) => !composedContains(modal, region));
      if (next === modalPaused) return;
      modalPaused = next;
      region.toggleAttribute("data-citry-toast-modal-paused", modalPaused);
      region.inert = modalPaused;
      syncPausedState();
      if (!modalPaused) drainAnnouncements();
    }
    const syncPausedState = () => {
      region.toggleAttribute("data-paused", timersPaused());
      syncTimers();
      persistRuntimeState();
    };
    const onPointerEnter = () => { hovering = true; syncPausedState(); };
    const onPointerLeave = () => { hovering = false; syncPausedState(); };
    const onFocusIn = () => { focusWithin = true; syncPausedState(); persistRuntimeState(); };
    const onFocusOut = () => {
      queueMicrotask(() => {
        if (disposed) return;
        focusWithin = composedContains(region, deepActiveElement());
        syncPausedState();
        persistRuntimeState();
      });
    };
    const onVisibilityChange = () => { syncPausedState(); if (!ownerDocument.hidden) drainAnnouncements(); };
    const onClick = (event) => {
      const toast = event.target.closest?.("[data-citry-toast-id]");
      if (!toast || !composedContains(region, toast)) return;
      const entry = entries.find((candidate) => candidate.message.id === toast.dataset.citryToastId);
      if (!entry) return;
      if (event.target.closest("[data-citry-toast-dismiss]")) {
        dismiss(entry, "dismiss", event.target);
        return;
      }
      if (!event.target.closest("[data-citry-toast-action]")) return;
      const token = generation;
      onAction?.(entry.message.id, { source: event.target, message: publicMessage(entry.message) });
      if (disposed || token !== generation || !region.isConnected) return;
      if (entry.message.closeOnAction) dismiss(entry, "action", event.target);
    };
    const onKeyDown = (event) => {
      if (event.defaultPrevented || event.key !== "F6" || event.altKey || event.ctrlKey || event.metaKey) return;
      const active = deepActiveElement();
      if (composedContains(region, active)) {
        event.preventDefault();
        if (isFocusable(focusReturn)) focusReturn.focus({ preventScroll: true });
        else focusBody();
        persistRuntimeState();
        return;
      }
      const first = activeEntries()[0];
      const node = first && nodes.get(first.message.id)?.root;
      if (!node || modalPaused) return;
      event.preventDefault();
      focusReturn = active;
      node.focus({ preventScroll: true });
      persistRuntimeState();
    };

    list.replaceChildren();
    region.addEventListener("pointerenter", onPointerEnter);
    region.addEventListener("pointerleave", onPointerLeave);
    region.addEventListener("focusin", onFocusIn);
    region.addEventListener("focusout", onFocusOut);
    region.addEventListener("click", onClick);
    scope.addEventListener("keydown", onKeyDown, true);
    ownerDocument.addEventListener("visibilitychange", onVisibilityChange);
    refreshModalState();

    effect(() => {
      const placement = props.placement === undefined ? data.placement : props.placement;
      if (placements.includes(placement)) {
        config.placement = placement;
        invalidEpisodes.delete("placement");
      } else reportInvalid("placement", placement);
      config.limit = resolveInteger("limit", data.limit, (value) => value >= 1 && value <= 10);
      const nextDuration = resolveInteger(
        "durationMs", data.durationMs,
        (value) => value === 0 || (value >= 1000 && value <= 120000),
      );
      if (nextDuration !== config.durationMs) {
        config.durationMs = nextDuration;
        for (const entry of entries) {
          if (entry.message.durationMs !== null) continue;
          stopTimer(entry);
          timerRecords.delete(entry.message.id);
        }
      }
      config.pauseOnHover = resolveBoolean("pauseOnHover");
      config.pauseOnFocus = resolveBoolean("pauseOnFocus");
      config.pauseOnHidden = resolveBoolean("pauseOnHidden");
      onDismiss = resolveCallback("onDismiss");
      onAction = resolveCallback("onAction");
      region.dataset.placement = config.placement;
      const supplied = props.items === undefined ? data.items : props.items;
      try { reconcileItems(normalizeItems(supplied)); }
      catch (error) { reportInvalid("items", supplied); }
      syncPausedState();
      persistRuntimeState();
    });
    region.setAttribute("data-citry-toast-initialized", "");

    return () => {
      for (const entry of entries) stopTimer(entry);
      persistRuntimeState();
      disposed = true;
      generation += 1;
      modalObserver.disconnect();
      for (const handle of taskHandles) clearTimeout(handle);
      taskHandles.clear();
      timerRecords.clear();
      for (const value of nodes.values()) value.dismissBinding?.dispose();
      region.removeEventListener("pointerenter", onPointerEnter);
      region.removeEventListener("pointerleave", onPointerLeave);
      region.removeEventListener("focusin", onFocusIn);
      region.removeEventListener("focusout", onFocusOut);
      region.removeEventListener("click", onClick);
      scope.removeEventListener("keydown", onKeyDown, true);
      ownerDocument.removeEventListener("visibilitychange", onVisibilityChange);
      if (toastRegistry.get(scope) === region) toastRegistry.delete(scope);
      region.removeAttribute("data-citry-toast-initialized");
    };
  },
});
