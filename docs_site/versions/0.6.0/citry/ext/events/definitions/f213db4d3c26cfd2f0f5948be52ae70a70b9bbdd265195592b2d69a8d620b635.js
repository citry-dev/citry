(function() {

const readyAttribute = "data-citry-command-palette-initialized";
const ownerKey = Symbol.for("citry-ui:command-palette-owner");
const handoffKey = Symbol.for("citry-ui:command-palette-handoff");
const scopeManagers = globalThis[
  Symbol.for("citry-ui:command-palette-mutation-scopes")
] ??= new WeakMap();

const watchPalette = (root, entry) => {
  let scope;
  let manager;
  let active = true;
  const detach = () => {
    if (manager?.entries.get(root) !== entry) return;
    manager.entries.delete(root);
    if (manager.entries.size === 0) {
      manager.observer.disconnect();
      scopeManagers.delete(scope);
    }
  };
  const attach = () => {
    scope = root.getRootNode();
    manager = scopeManagers.get(scope);
    if (!manager) {
      const entries = new Map();
      const observer = new MutationObserver((records) => {
        for (const record of records) {
          for (const node of record.addedNodes) {
            if (!(node instanceof Element)) continue;
            const candidates = node.hasAttribute(readyAttribute)
              ? [node, ...node.querySelectorAll(`[${readyAttribute}]`)]
              : [...node.querySelectorAll(`[${readyAttribute}]`)];
            for (const candidate of candidates) {
              if (!candidate[ownerKey]?.active) {
                candidate.removeAttribute(readyAttribute);
                candidate.querySelector(":scope > dialog")?.removeAttribute("data-open");
              }
            }
          }
        }
        for (const [candidate, registration] of [...entries]) {
          if (records.some((record) => record.target === candidate
            || candidate.contains(record.target)
            || [...record.addedNodes, ...record.removedNodes].some((node) =>
              node === candidate || node.contains?.(candidate)))) registration.notify();
        }
      });
      observer.observe(scope instanceof Document ? scope.documentElement : scope, {
        subtree: true,
        childList: true,
        attributes: true,
      });
      manager = { entries, observer };
      scopeManagers.set(scope, manager);
    }
    manager.entries.set(root, entry);
  };
  attach();
  return {
    refresh() {
      if (active && root.getRootNode() !== scope) {
        detach();
        attach();
      }
    },
    cleanup() {
      active = false;
      detach();
    },
  };
};

__citryRuntime.registerTypeOptions.bind(null, "CCommandPalette_28a050", "50881806c03528fb53d6ecd9db29db1611efc710b9d045d6d4a8663cecccfcd1")({
  props: {
    open: {},
    query: {},
    disabled: {},
    loop: {},
    closeOnAction: {},
    size: {},
    onOpenChange: {},
    onQueryChange: {},
    onAction: {},
  },
  onServerRender: ({component}) => {
    const host = component.$el;
    const data = component;
    const defaults = component.serverDefaults;
    const props = component.$props;
    const effect = Citry.vue.watchEffect;
    const dialogRuntime = globalThis[Symbol.for("citry-ui:dialog-controller-runtime")];
    const activeRuntime = globalThis[Symbol.for("citry-ui:active-descendant-runtime")];
    if (dialogRuntime?.generation !== 1 || activeRuntime?.generation !== 1) {
      throw new Error("[citry-ui] CCommandPalette private runtime dependency did not load.");
    }
    const dialog = host.querySelector(
      ':scope > dialog[data-citry-command-palette-root]',
    );
    const surface = dialog?.querySelector(
      ':scope > [data-citry-ui-part="command-palette-surface"]',
    );
    const header = surface?.querySelector(
      ':scope > [data-citry-ui-part="command-palette-header"]',
    );
    const title = header?.querySelector(
      ':scope > [data-citry-ui-part="command-palette-title"]',
    );
    const closeButton = header?.querySelector(
      ':scope > [data-citry-ui-part="command-palette-close"]',
    );
    const search = surface?.querySelector(
      ':scope > [data-citry-ui-part="command-palette-search"]',
    );
    const input = search?.querySelector(
      ':scope > [data-citry-ui-part="command-palette-input"]',
    );
    const listbox = surface?.querySelector(
      ':scope > [data-citry-ui-part="command-palette-listbox"]',
    );
    const empty = surface?.querySelector(
      ':scope > [data-citry-ui-part="command-palette-empty"]',
    );
    host?.[ownerKey]?.transfer?.();
    const previous = host?.[handoffKey] ?? null;
    const abortPrevious = () => {
      if (!previous) return;
      previous.abort();
      if (host[handoffKey] === previous) delete host[handoffKey];
    };
    if (
      !(host instanceof HTMLDivElement)
      || !(dialog instanceof HTMLDialogElement)
      || !(surface instanceof HTMLElement)
      || !(header instanceof HTMLElement)
      || !(title instanceof HTMLHeadingElement)
      || !(closeButton instanceof HTMLButtonElement)
      || !(search instanceof HTMLElement)
      || !(input instanceof HTMLInputElement)
      || !(listbox instanceof HTMLElement)
      || !(empty instanceof HTMLElement)
    ) {
      abortPrevious();
      console.error(
        "[citry-ui] CCommandPalette received invalid native anatomy; "
          + "leaving the server fallback unchanged.",
      );
      return () => {};
    }

    const flattened = data.regions.flatMap((region) => region.commands);
    const commandElements = [...listbox.querySelectorAll(
      '[data-citry-ui-part="command-palette-command"]',
    )];
    const optionByValue = new Map(commandElements.map((element) => [
      element.dataset.value,
      element,
    ]));
    // Each child is a group or separator element that the palette hides or shows.
    const regionElements = /** @type {HTMLElement[]} */ ([...listbox.children]);
    const documentOwner = host.ownerDocument;
    let actualRoot = host.getRootNode();
    const activators = [...host.children].filter((element) => element !== dialog);
    const ownedElements = [
      host, dialog, surface, header, title, closeButton, search, input, listbox, empty,
      ...regionElements, ...commandElements,
    ];
    // Citry's reserved event and component markers never belong on the
    // anatomy below the host, and must not change while this client owns it.
    const frameworkMarker = (attribute) => attribute.name.startsWith("data-cid")
      || attribute.name.startsWith("data-cev");
    const markersAbsent = () => ownedElements.every((element, index) => ![...element.attributes]
      .some((attribute) => attribute.name.startsWith("data-cev") || (index > 0 && frameworkMarker(attribute))));
    const frameworkBaseline = ownedElements.map((element) => JSON.stringify(
      [...element.attributes]
        .filter(frameworkMarker)
        .map((attribute) => [attribute.name, attribute.value])
        .sort(([left], [right]) => left.localeCompare(right)),
    ));
    const frameworkMarkersValid = () => ownedElements.every((element, index) => JSON.stringify(
      [...element.attributes]
        .filter(frameworkMarker)
        .map((attribute) => [attribute.name, attribute.value])
        .sort(([left], [right]) => left.localeCompare(right)),
    ) === frameworkBaseline[index]);
    const runtimeAttributesValid = (element, allowed = []) => [...element.attributes].every(
      (attribute) => !attribute.name.startsWith("data-citry-")
        || attribute.name === "data-citry-ui-part"
        || allowed.includes(attribute.name),
    );
    const interactiveSelector = [
      "a[href]", "area[href]", "button", "details", "embed", "iframe", "input",
      "label", "object", "select", "summary", "textarea", "audio[controls]",
      "video[controls]", "[contenteditable]:not([contenteditable='false'])", "[tabindex]",
    ].join(",");
    const visualValid = (visual) => {
      if (!(visual instanceof Element)) return true;
      if (visual.querySelector(interactiveSelector)) return false;
      return [...visual.querySelectorAll("*")].every((element) => (
        !element.localName.includes("-")
        && !element.hasAttribute("is")
        && element.shadowRoot === null
        && (
          !(element instanceof HTMLImageElement)
          || (element.hasAttribute("alt") && element.alt === "")
        )
      ));
    };
    const structureValid = (requireReady = false) => {
      if (
        !(surface instanceof HTMLElement)
        || surface.localName !== "section"
        || header.localName !== "header"
        || title.localName !== "h2"
        || closeButton.type !== "button"
        || search.localName !== "search"
        || listbox.localName !== "div"
        || empty.localName !== "div"
        || host.ownerDocument !== documentOwner
        || dialog.ownerDocument !== documentOwner
        || host.getRootNode() !== actualRoot
        || host.getRootNode() !== dialog.getRootNode()
        || !markersAbsent()
        || !frameworkMarkersValid()
        || !host.hasAttribute("data-citry-command-palette-host")
        || (requireReady && !host.hasAttribute(readyAttribute))
        || !runtimeAttributesValid(host, [
          "data-citry-command-palette-host",
          readyAttribute,
        ])
        || dialog.id !== data.dialogId
        || dialog.getAttribute("aria-labelledby") !== title.id
        || dialog.dataset.citryUiPart !== "command-palette"
        || !dialog.hasAttribute("data-citry-command-palette-root")
        || ["role", "aria-modal", "tabindex", "inert", "popover", "hidden"]
          .some((name) => dialog.hasAttribute(name))
        || !runtimeAttributesValid(dialog, ["data-citry-command-palette-root"])
        || ![surface, header, title, search, input, listbox]
          .every((element) => runtimeAttributesValid(element))
        || !runtimeAttributesValid(closeButton, ["data-citry-command-palette-close"])
        || !runtimeAttributesValid(empty, ["data-citry-command-palette-visual"])
        || dialog.parentElement !== host
        || surface.parentElement !== dialog
        || header.parentElement !== surface
        || search.parentElement !== surface
        || listbox.parentElement !== surface
        || empty.parentElement !== surface
        || title.id !== data.titleId
        || input.id !== data.inputId
        || listbox.id !== data.listboxId
        || input.type !== "text"
        || input.getAttribute("role") !== "combobox"
        || input.getAttribute("aria-controls") !== listbox.id
        || input.getAttribute("aria-autocomplete") !== "list"
        || input.getAttribute("autocomplete") !== "off"
        || !input.hasAttribute("autofocus")
        || listbox.getAttribute("role") !== "listbox"
        || commandElements.length !== flattened.length
        || regionElements.length !== data.regions.length
        || activators.length !== Number(data.hasActivator)
        || !visualValid(empty)
      ) return false;
      for (const activator of activators) {
        if (
          !(activator instanceof HTMLElement)
          || activator instanceof HTMLUnknownElement
          || activator.localName.includes("-")
          || activator.hasAttribute("is")
          || activator.shadowRoot !== null
          || !activator.hasAttribute("data-citry-command-palette-trigger")
          || activator.getAttribute("aria-haspopup") !== "dialog"
          || activator.getAttribute("aria-controls") !== dialog.id
        ) return false;
      }
      for (let index = 0; index < data.regions.length; index += 1) {
        const region = data.regions[index];
        const element = regionElements[index];
        if (!(element instanceof HTMLElement)) return false;
        if (region.kind === "separator") {
          if (
            element.localName !== "hr"
            || element.dataset.citryUiPart !== "command-palette-separator"
            || element.getAttribute("aria-hidden") !== "true"
          ) return false;
          continue;
        }
        if (region.kind === "group") {
          if (
            element.localName !== "section"
            || element.getAttribute("role") !== "group"
            || element.dataset.citryUiPart !== "command-palette-group"
          ) return false;
        } else if (
          region.kind !== "command"
          || element.getAttribute("role") !== "option"
          || element.dataset.citryUiPart !== "command-palette-command"
        ) return false;
      }
      for (const command of flattened) {
        const element = optionByValue.get(command.value);
        if (
          !(element instanceof HTMLDivElement)
          || element.id !== command.id
          || element.getAttribute("role") !== "option"
          || element.dataset.intent !== command.intent
          || element.hasAttribute("data-disabled") !== command.disabled
          || !runtimeAttributesValid(element)
        ) return false;
        for (const visual of element.querySelectorAll(
          ':scope > [data-citry-command-palette-visual]',
        )) {
          if (
            visual.getAttribute("aria-hidden") !== "true"
            || !visual.hasAttribute("inert")
            || !runtimeAttributesValid(visual, ["data-citry-command-palette-visual"])
            || !visualValid(visual)
          ) return false;
        }
      }
      return true;
    };
    if (!structureValid()) {
      abortPrevious();
      console.error(
        "[citry-ui] CCommandPalette received invalid owned anatomy; "
          + "leaving the server fallback unchanged.",
      );
      return () => {};
    }

    const retained = Boolean(previous
      && previous.host === host
      && previous.dialog === dialog
      && previous.surface === surface
      && previous.title === title
      && previous.closeButton === closeButton
      && previous.input === input
      && previous.listbox === listbox
      && previous.documentOwner === host.ownerDocument
      && previous.actualRoot === actualRoot);
    if (previous && !retained) abortPrevious();
    if (retained) {
      previous.adopt();
      delete host[handoffKey];
    }

    const owner = { active: true, token: Symbol(), transfer: null };
    host[ownerKey] = owner;
    const invalid = new Set();
    const callbacks = { open: null, query: null, action: null };
    const tasks = new Set();
    const listeners = [];
    let active = true;
    let watcher = null;
    let controller = null;
    let collection = null;
    let configuration = {
      disabled: defaults.disabled,
      loop: defaults.loop,
      closeOnAction: defaults.closeOnAction,
      size: defaults.size,
    };
    // A kept palette keeps its own open state only while the server's
    // `open` input is unchanged since the previous run; a changed input
    // opens or closes it to match, as CDialog does.
    const sameServerOpen = retained && previous.serverOpen === defaults.open;
    let internalOpen = sameServerOpen ? previous.internalOpen : defaults.open;
    let logicalOpen = retained ? previous.logicalOpen : false;
    let openControlled = false;
    let queryControlled = false;
    let fallbackQuery = retained ? previous.fallbackQuery : defaults.query;
    let query = retained ? previous.query : defaults.query;
    let suppliedQuery = retained ? previous.suppliedQuery : null;
    let activeValue = retained ? previous.activeValue : null;
    let previousOrder = retained ? previous.previousOrder : flattened.map((item) => item.value);
    let composing = retained ? previous.composing : false;
    let compositionPending = false;
    let compositionGeneration = 0;
    let actionGeneration = 0;
    let closeGeneration = 0;
    let pendingControlledClose = null;
    let formGuard = null;
    let effectStarted = false;
    const queue = (work) => {
      const marker = {};
      tasks.add(marker);
      queueMicrotask(() => {
        if (!tasks.delete(marker) || !active || host[ownerKey] !== owner) return;
        work();
      });
    };
    const report = (name) => {
      if (invalid.has(name)) return;
      invalid.add(name);
      console.error(
        `[citry-ui] CCommandPalette ${name} received an invalid client value; `
          + "retaining the last valid value.",
      );
    };
    const resolveCallback = (name, current) => {
      const value = props[name];
      if (value === undefined) {
        invalid.delete(name);
        return null;
      }
      if (value === null || typeof value === "function") {
        invalid.delete(name);
        return value;
      }
      report(name);
      return current;
    };
    const resolveBoolean = (name, fallback) => {
      const value = props[name] === undefined || props[name] === null
        ? defaults[name]
        : props[name];
      if (typeof value === "boolean") {
        invalid.delete(name);
        return value;
      }
      report(name);
      return fallback;
    };
    const resolveSize = () => {
      const value = props.size === undefined || props.size === null ? defaults.size : props.size;
      if (["sm", "md", "lg"].includes(value)) {
        invalid.delete("size");
        return value;
      }
      report("size");
      return configuration.size;
    };
    const add = (target, type, listener, options) => {
      target.addEventListener(type, listener, options);
      listeners.push(() => target.removeEventListener(type, listener, options));
    };
    const commandFor = (value) => flattened.find((command) => command.value === value) ?? null;
    const optionFor = (value) => optionByValue.get(value) ?? null;
    const eligibleItems = () => flattened.map((command) => ({
      value: command.value,
      disabled: command.disabled,
      visible: !optionFor(command.value).hidden,
    }));
    const removeFormGuard = () => {
      if (!formGuard) return;
      clearTimeout(formGuard.timer);
      formGuard.form.removeEventListener("submit", formGuard.listener, true);
      formGuard = null;
    };
    const armFormGuard = () => {
      removeFormGuard();
      const form = input.closest("form");
      if (!(form instanceof HTMLFormElement)) return;
      const generation = compositionGeneration;
      const listener = (event) => {
        if (
          event.target === form
          && generation === compositionGeneration
          && dialogRuntime.deepActive(input.ownerDocument) === input
        ) event.preventDefault();
      };
      form.addEventListener("submit", listener, true);
      const timer = setTimeout(removeFormGuard, 0);
      formGuard = { form, listener, timer };
    };
    const reflect = () => {
      dialog.toggleAttribute("data-open", logicalOpen);
      dialog.toggleAttribute("data-disabled", configuration.disabled);
      dialog.dataset.size = configuration.size;
      input.setAttribute("aria-expanded", logicalOpen ? "true" : "false");
      input.disabled = configuration.disabled;
      closeButton.disabled = configuration.disabled;
      for (const activator of host.querySelectorAll(
        ':scope > [data-citry-command-palette-trigger]',
      )) {
        activator.setAttribute("aria-expanded", logicalOpen ? "true" : "false");
        if ("disabled" in activator) activator.disabled = configuration.disabled;
        activator.toggleAttribute("data-disabled", configuration.disabled);
      }
    };
    const filter = ({ preserveActive = true } = {}) => {
      const needle = activeRuntime.canonicalText(query);
      const visibleValues = new Set();
      for (const command of flattened) {
        const haystacks = [command.label, ...command.keywords]
          .map((value) => activeRuntime.canonicalText(value));
        const visible = needle === "" || haystacks.some((value) => value.includes(needle));
        const option = optionFor(command.value);
        option.hidden = !visible;
        if (visible) visibleValues.add(command.value);
      }
      const contentVisibility = new Map();
      for (let index = 0; index < data.regions.length; index += 1) {
        const region = data.regions[index];
        if (region.kind === "separator") continue;
        const visible = region.commands.some((command) => visibleValues.has(command.value));
        contentVisibility.set(index, visible);
        regionElements[index].hidden = !visible;
      }
      let hasVisibleContent = false;
      let pendingSeparator = null;
      for (let index = 0; index < data.regions.length; index += 1) {
        const region = data.regions[index];
        if (region.kind === "separator") {
          regionElements[index].hidden = true;
          if (hasVisibleContent && pendingSeparator === null) pendingSeparator = index;
          continue;
        }
        if (!contentVisibility.get(index)) continue;
        if (hasVisibleContent && pendingSeparator !== null) {
          regionElements[pendingSeparator].hidden = false;
        }
        hasVisibleContent = true;
        pendingSeparator = null;
      }
      const items = eligibleItems();
      activeValue = logicalOpen
        ? collection.nearest(items, preserveActive ? activeValue : null, previousOrder)
        : null;
      collection.sync({
        items,
        activeValue,
        open: logicalOpen,
        optionFor,
        activeAttribute: "data-active",
      });
      const hasResults = visibleValues.size > 0;
      dialog.toggleAttribute("data-empty", !hasResults);
      listbox.hidden = !hasResults;
      empty.hidden = hasResults;
      previousOrder = flattened.map((command) => command.value);
    };
    const notifyQuery = (next, reason, closeReason, source, controlled) => {
      callbacks.query?.(next, { reason, closeReason, controlled, source });
    };
    const settleCloseQuery = (reason, source) => {
      const generation = ++closeGeneration;
      activeValue = null;
      collection.sync({
        items: eligibleItems(),
        activeValue: null,
        open: false,
        optionFor,
        activeAttribute: "data-active",
      });
      fallbackQuery = "";
      if (queryControlled) {
        if (query !== "") notifyQuery("", "close", reason, source, true);
      } else if (query !== "") {
        query = "";
        input.value = "";
        filter({ preserveActive: false });
        notifyQuery("", "close", reason, source, false);
      }
      if (generation !== closeGeneration) return;
    };
    const commitVisibility = (nextOpen, reason, source, { notify = false } = {}) => {
      const next = Boolean(nextOpen) && !configuration.disabled;
      const wasOpen = logicalOpen;
      controller.setOpen(next, source);
      logicalOpen = controller.isOpen();
      internalOpen = logicalOpen;
      reflect();
      filter({ preserveActive: wasOpen });
      if (notify && wasOpen !== logicalOpen) {
        callbacks.open?.(logicalOpen, { reason, controlled: false, source });
      }
      if (wasOpen && !logicalOpen) settleCloseQuery(reason, source);
      return wasOpen !== logicalOpen;
    };
    const requestVisibility = (nextOpen, reason, source) => {
      if (Boolean(nextOpen) === logicalOpen) return false;
      if (openControlled) {
        const closeRequest = nextOpen ? null : { reason, source };
        pendingControlledClose = closeRequest;
        callbacks.open?.(Boolean(nextOpen), { reason, controlled: true, source });
        if (props.open === Boolean(nextOpen)) {
          const wasOpen = logicalOpen;
          controller.setOpen(Boolean(nextOpen) && !configuration.disabled, source);
          logicalOpen = controller.isOpen();
          reflect();
          filter({ preserveActive: wasOpen });
          if (wasOpen && !logicalOpen) settleCloseQuery(reason, source);
        }
        if (closeRequest) queue(() => {
          if (
            pendingControlledClose === closeRequest
            && logicalOpen
            && props.open === logicalOpen
          ) pendingControlledClose = null;
        });
        return false;
      }
      return commitVisibility(nextOpen, reason, source, { notify: true });
    };
    const commitUserQuery = (requested, source) => {
      if (requested === query) {
        input.value = query;
        return;
      }
      const selectionStart = input.selectionStart;
      const selectionEnd = input.selectionEnd;
      if (queryControlled) {
        notifyQuery(requested, "input", null, input, true);
        const supplied = props.query;
        if (supplied === requested) {
          query = requested;
          fallbackQuery = requested;
          suppliedQuery = requested;
          filter();
          return;
        }
        if (supplied === undefined || supplied === null) queryControlled = false;
        input.value = query;
        if (selectionStart !== null && selectionEnd !== null) {
          input.setSelectionRange(
            Math.min(selectionStart, query.length),
            Math.min(selectionEnd, query.length),
          );
        }
        filter();
        return;
      }
      query = requested;
      fallbackQuery = requested;
      input.value = requested;
      filter();
      notifyQuery(requested, "input", null, source, false);
    };
    const act = (command, option, event, source) => {
      if (
        !active
        || configuration.disabled
        || command.disabled
        || option.hidden
        || !logicalOpen
      ) return;
      const generation = ++actionGeneration;
      activeValue = command.value;
      collection.sync({
        items: eligibleItems(),
        activeValue,
        open: true,
        optionFor,
        activeAttribute: "data-active",
      });
      if (source === "click" && dialogRuntime.isFocusable(input)) {
        input.focus({ preventScroll: true });
      }
      const close = command.closeOnAction ?? configuration.closeOnAction;
      callbacks.action?.(command.value, {
        query,
        source,
        item: option,
        event,
        closeOnAction: close,
      });
      if (
        generation !== actionGeneration
        || !active
        || host[ownerKey] !== owner
        || !option.isConnected
      ) return;
      if (close) requestVisibility(false, "action", option);
    };

    collection = activeRuntime.create({
      input,
      listbox,
      idPrefix: `${data.listboxId}-command`,
    });
    collection.retain(flattened.map((command) => command.value));
    input.disabled = configuration.disabled;
    controller = dialogRuntime.create({
      host,
      dialog,
      surface,
      title,
      closeButton,
      signature: "CCommandPalette:command-input",
      policy: () => ({ dismissible: true, closeOnEscape: true, closeOnOutside: true }),
      initialFocus: () => input,
      containmentFallback: () => input,
      escapeBlocked: () => composing,
      interceptDialogSubmit: () => false,
      requestClose: (reason, source) => requestVisibility(false, reason, source),
      nativeClosed: (reason, source) => {
        const wasOpen = logicalOpen;
        logicalOpen = false;
        internalOpen = false;
        reflect();
        filter();
        if (wasOpen) {
          callbacks.open?.(false, { reason, controlled: openControlled, source });
          settleCloseQuery(reason, source);
        }
      },
      forceClose: (reason, source) => {
        const wasOpen = logicalOpen;
        logicalOpen = false;
        internalOpen = false;
        reflect();
        filter();
        if (wasOpen) {
          callbacks.open?.(false, { reason, controlled: openControlled, source });
          settleCloseQuery(reason, source);
        }
      },
      failed: () => {
        logicalOpen = false;
        host.removeAttribute(readyAttribute);
        reflect();
        console.error("[citry-ui] CCommandPalette could not enter modal state.");
      },
      handoffAborted: () => {
        logicalOpen = false;
        host.removeAttribute(readyAttribute);
        reflect();
      },
    });
    if (retained) logicalOpen = controller.isOpen();
    // The controller closed a palette this run would have kept open,
    // because an enclosing dialog closed first; report it once the
    // callback is known.
    const ancestorClose = controller.closedByAncestor;
    if (ancestorClose) internalOpen = false;

    add(host, "click", (event) => {
      const trigger = event.target.closest?.("[data-citry-command-palette-trigger]");
      if (trigger && trigger.parentElement === host && !configuration.disabled) {
        requestVisibility(true, "trigger", trigger);
        return;
      }
      const close = event.target.closest?.("[data-citry-command-palette-close]");
      if (close === closeButton && !configuration.disabled) {
        requestVisibility(false, "close-button", closeButton);
      }
    });
    add(input, "input", (event) => {
      if (composing || event.isComposing || compositionPending) return;
      commitUserQuery(input.value, input);
    });
    add(input, "compositionstart", () => {
      composing = true;
      compositionPending = false;
      compositionGeneration += 1;
    });
    add(input, "compositionend", () => {
      composing = false;
      compositionPending = true;
      const generation = ++compositionGeneration;
      queue(() => {
        if (generation !== compositionGeneration || !compositionPending) return;
        compositionPending = false;
        removeFormGuard();
        commitUserQuery(input.value, input);
      });
    });
    add(input, "keydown", (event) => {
      const isComposition = composing || event.isComposing || event.keyCode === 229;
      if (isComposition) {
        if (event.key === "Enter") armFormGuard();
        return;
      }
      if (configuration.disabled) return;
      if (event.key === "ArrowDown" || event.key === "ArrowUp") {
        event.preventDefault();
        activeValue = collection.move(
          eligibleItems(),
          activeValue,
          event.key === "ArrowDown" ? 1 : -1,
          configuration.loop,
        );
        collection.sync({
          items: eligibleItems(),
          activeValue,
          open: logicalOpen,
          optionFor,
          activeAttribute: "data-active",
        });
        return;
      }
      if (event.key === "Enter") {
        event.preventDefault();
        const command = commandFor(activeValue);
        const option = optionFor(activeValue);
        if (command && option) act(command, option, event, "keyboard");
      }
    });
    add(listbox, "pointerdown", (event) => {
      const option = event.target.closest?.(
        '[data-citry-ui-part="command-palette-command"]',
      );
      if (
        optionByValue.get(option?.dataset.value) === option
        && event.button === 0
        && !event.altKey
        && !event.ctrlKey
        && !event.metaKey
        && !event.shiftKey
      ) event.preventDefault();
    });
    add(listbox, "pointermove", (event) => {
      const option = event.target.closest?.(
        '[data-citry-ui-part="command-palette-command"]',
      );
      const command = commandFor(option?.dataset.value);
      if (!command || command.disabled || option.hidden) return;
      activeValue = command.value;
      collection.sync({
        items: eligibleItems(),
        activeValue,
        open: logicalOpen,
        optionFor,
        activeAttribute: "data-active",
      });
    });
    add(listbox, "click", (event) => {
      if (
        event.button !== 0
        || event.altKey
        || event.ctrlKey
        || event.metaKey
        || event.shiftKey
      ) return;
      const option = event.target.closest?.(
        '[data-citry-ui-part="command-palette-command"]',
      );
      const command = commandFor(option?.dataset.value);
      if (command && optionByValue.get(command.value) === option) {
        act(command, option, event, "click");
      }
    });
    add(input, "blur", removeFormGuard);

    const registration = {
      notify() {
        if (!active) return;
        if (!host.isConnected) {
          teardown(false);
          return;
        }
        if (host.ownerDocument !== dialog.ownerDocument) {
          teardown(true);
          return;
        }
        const nextRoot = host.getRootNode();
        if (nextRoot !== actualRoot) {
          const supported = nextRoot === documentOwner
            || (nextRoot instanceof ShadowRoot
              && nextRoot.mode === "open"
              && nextRoot.host.ownerDocument === documentOwner
              && nextRoot.host.shadowRoot === nextRoot);
          if (!supported || dialog.getRootNode() !== nextRoot || !controller.refreshRoot()) {
            teardown(true);
            return;
          }
          actualRoot = nextRoot;
          watcher.refresh();
        }
        if (!structureValid(true)) {
          teardown(true);
          return;
        }
        watcher.refresh();
      },
    };
    watcher = watchPalette(host, registration);

    effect(() => {
      const priorDisabled = configuration.disabled;
      configuration = {
        disabled: resolveBoolean("disabled", configuration.disabled),
        loop: resolveBoolean("loop", configuration.loop),
        closeOnAction: resolveBoolean("closeOnAction", configuration.closeOnAction),
        size: resolveSize(),
      };
      callbacks.open = resolveCallback("onOpenChange", callbacks.open);
      callbacks.query = resolveCallback("onQueryChange", callbacks.query);
      callbacks.action = resolveCallback("onAction", callbacks.action);

      const nextQuery = props.query;
      if (nextQuery === undefined || nextQuery === null) {
        if (queryControlled) query = fallbackQuery;
        queryControlled = false;
        suppliedQuery = null;
        invalid.delete("query");
      } else if (typeof nextQuery === "string") {
        queryControlled = true;
        if (nextQuery !== suppliedQuery) {
          query = nextQuery;
          fallbackQuery = nextQuery;
          suppliedQuery = nextQuery;
        }
        invalid.delete("query");
      } else {
        report("query");
        if (queryControlled) query = fallbackQuery;
        queryControlled = false;
        suppliedQuery = null;
      }
      input.value = query;

      const nextOpen = props.open;
      let ownerOpen = internalOpen;
      if (nextOpen === undefined || nextOpen === null) {
        if (openControlled) internalOpen = logicalOpen;
        openControlled = false;
        ownerOpen = internalOpen;
        pendingControlledClose = null;
        invalid.delete("open");
      } else if (typeof nextOpen === "boolean") {
        openControlled = true;
        ownerOpen = nextOpen;
        invalid.delete("open");
      } else {
        report("open");
        if (openControlled) internalOpen = logicalOpen;
        openControlled = false;
        ownerOpen = internalOpen;
        pendingControlledClose = null;
      }
      if (configuration.disabled && logicalOpen) {
        const wasControlled = openControlled;
        controller.setOpen(false, dialog);
        logicalOpen = false;
        internalOpen = false;
        callbacks.open?.(false, {
          reason: "disabled",
          controlled: wasControlled,
          source: dialog,
        });
        settleCloseQuery("disabled", dialog);
      } else if (!configuration.disabled) {
        const expected = Boolean(ownerOpen);
        if (expected !== logicalOpen) {
          const wasOpen = logicalOpen;
          controller.setOpen(expected, null);
          logicalOpen = controller.isOpen();
          internalOpen = logicalOpen;
          if (wasOpen && !logicalOpen) {
            const close = pendingControlledClose ?? { reason: "owner", source: null };
            settleCloseQuery(close.reason, close.source);
          }
        }
      }
      if (!configuration.disabled && priorDisabled && openControlled && props.open === true) {
        controller.setOpen(true, null);
        logicalOpen = controller.isOpen();
      }
      pendingControlledClose = logicalOpen ? pendingControlledClose : null;
      reflect();
      filter({ preserveActive: effectStarted });
      effectStarted = true;
    });
    if (ancestorClose) {
      callbacks.open?.(false, { reason: "ancestor", controlled: openControlled, source: ancestorClose });
      settleCloseQuery("ancestor", ancestorClose);
    }

    const teardown = (diagnose = false) => {
      if (!active) return;
      active = false;
      owner.active = false;
      actionGeneration += 1;
      compositionGeneration += 1;
      closeGeneration += 1;
      removeFormGuard();
      tasks.clear();
      watcher?.cleanup();
      listeners.splice(0).forEach((remove) => remove());
      // Lost anatomy fails closed at once. Only an ordinary cleanup can
      // hand its open state to the next server-render callback.
      const canHandoff = !diagnose
        && host.isConnected
        && host.ownerDocument === documentOwner
        && host.getRootNode() === actualRoot
        && dialog.isConnected
        && dialog.parentElement === host
        && surface.parentElement === dialog
        && title.isConnected
        && closeButton.isConnected
        && input.isConnected
        && listbox.isConnected;
      const handedOff = controller.cleanup({ handoff: canHandoff });
      if (host[ownerKey] === owner) delete host[ownerKey];
      if (handedOff) {
        let handoffObserver = null;
        const record = {
          host,
          dialog,
          surface,
          title,
          closeButton,
          input,
          listbox,
          documentOwner: host.ownerDocument,
          actualRoot: host.getRootNode(),
          internalOpen,
          logicalOpen,
          serverOpen: defaults.open,
          query,
          fallbackQuery,
          suppliedQuery,
          activeValue,
          previousOrder,
          composing,
          collection,
          timer: null,
          adopt() {
            if (this.timer !== null) {
              clearTimeout(this.timer);
              this.timer = null;
            }
            handoffObserver?.disconnect();
            handoffObserver = null;
          },
          abort() {
            this.adopt();
            dialogRuntime.abortHandoff(dialog);
            collection.cleanup();
            host.removeAttribute(readyAttribute);
            dialog.removeAttribute("data-open");
            input.removeAttribute("aria-activedescendant");
          },
        };
        // The runtime runs this cleanup before it knows whether the
        // revision keeps or unmounts this host, so the ready marker goes
        // now. A retained host restores it when its next server-render
        // callback adopts this record.
        host.removeAttribute(readyAttribute);
        // A host removed outside a Vue unmount, after the microtask
        // below has run, still releases its handoff as soon as it
        // leaves the DOM. adopt() disconnects this observer.
        const handoffRoot = host.getRootNode();
        handoffObserver = new MutationObserver(() => {
          if (host.isConnected || host[handoffKey] !== record) return;
          record.abort();
          delete host[handoffKey];
        });
        handoffObserver.observe(
          handoffRoot instanceof Document ? handoffRoot.documentElement : handoffRoot,
          {childList: true, subtree: true},
        );
        host[handoffKey] = record;
        record.timer = setTimeout(() => {
          if (host[handoffKey] !== record || host[ownerKey]?.active) return;
          record.abort();
          delete host[handoffKey];
        }, 1000);
        // An unmount has no next callback to adopt the record. Vue
        // removes the host right after this cleanup, so release the
        // modal and the scroll lock then instead of after the timer.
        queueMicrotask(() => {
          if (host[handoffKey] !== record || host.isConnected) return;
          clearTimeout(record.timer);
          record.abort();
          delete host[handoffKey];
        });
      } else {
        collection.cleanup();
        host.removeAttribute(readyAttribute);
        dialog.removeAttribute("data-open");
      }
      if (diagnose) {
        console.error(
          "[citry-ui] CCommandPalette lost its owned anatomy; component behavior was removed.",
        );
      }
    };

    owner.transfer = () => teardown(false);

    reflect();
    filter({ preserveActive: retained });
    input.disabled = configuration.disabled;
    host.setAttribute(readyAttribute, "");

    return () => teardown(false);
  },
});

})();