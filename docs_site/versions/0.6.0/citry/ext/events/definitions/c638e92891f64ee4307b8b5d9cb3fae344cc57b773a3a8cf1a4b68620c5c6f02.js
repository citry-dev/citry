(function() {

const anchoredLayerRuntimeCompatible = globalThis[
  Symbol.for("citry-ui:anchored-layer-runtime-compatible")
] === true;
const anchoredLayerRuntime = globalThis[
  Symbol.for("citry-ui:anchored-layer-runtime")
];

__citryRuntime.registerTypeOptions.bind(null, "CDisclosure_c778df", "79d55c3381d2ffc9175e7be58a9105bfa028c8ca3e1fc698a2fc13058cd32f3b")({
  props: {
    open: {},
    onOpenChange: {},
    disabled: {},
    variant: {},
    size: {},
    indicator: {},
    indicatorPosition: {},
  },
  inject: {formService: {from: Symbol.for("citry-ui:form"), default: null}},
  onServerRender: ({component}) => {
    if (!anchoredLayerRuntimeCompatible) return;
    const root = component.$el;
    const data = component;
    const defaults = data.serverDefaults;
    const props = component.$props;
    const effect = Citry.vue.watchEffect;
    const rootSelector = "[data-citry-disclosure-root]";
    const form = component.formService;
    const layerCoordinator = anchoredLayerRuntime.coordinatorFor(root);
    const allowedParts = new Set(["popover", "tooltip", "menu", "popup", "hover-card"]);
    const titleHtml = new Set([
      "abbr", "b", "bdi", "bdo", "br", "cite", "code", "data", "del", "dfn",
      "em", "i", "img", "ins", "kbd", "mark", "picture", "q", "rp", "rt",
      "ruby", "s", "samp", "small", "source", "span", "strong", "sub", "sup",
      "svg", "time", "u", "var", "wbr",
    ]);
    const titleSvg = new Set([
      "svg", "g", "path", "polyline", "line", "circle", "rect", "ellipse", "polygon",
    ]);
    const titleRejected = new Set([
      "role", "tabindex", "contenteditable", "autofocus", "href", "xlink:href",
      "controls", "usemap", "form", "popover", "is", "hidden", "inert", "focusable",
    ]);
    const vueDirectivePrefixes = ["v-", ":", ".", "^", "@", "#"];
    const allowedChoices = {
      variant: ["outline", "soft", "plain"],
      size: ["sm", "md", "lg"],
      indicatorPosition: ["start", "end"],
    };
    const invalidInputs = new Set();
    let anatomy = null;
    let structureValid = false;
    let invalidStructureEpisode = false;
    let activationInstalled = false;
    let fieldsetObserver = null;
    let animation = null;
    let active = true;
    let rawInputs = null;
    let controlled = false;
    let onOpenChange = null;
    let configuration = {
      disabled: defaults.disabled,
      variant: defaults.variant,
      size: defaults.size,
      indicator: defaults.indicator,
      indicatorPosition: defaults.indicatorPosition,
    };
    const retained = root.__citryUiDisclosureRuntime ?? null;
    const sameServer = retained?.serverFingerprint === data.serverFingerprint;
    let baselineOpen = sameServer ? Boolean(retained.baselineOpen) : Boolean(defaults.open);
    let logicalOpen = sameServer ? Boolean(retained.logicalOpen) : baselineOpen;
    const runtimeState = retained ?? {};
    root.__citryUiDisclosureRuntime = runtimeState;
    let reconciledOnce = false;

    const describe = (value) => {
      try {
        return JSON.stringify(value) ?? String(value);
      } catch {
        return String(value);
      }
    };
    const reportInput = (name, value, fallback) => {
      if (invalidInputs.has(name)) {
        return;
      }
      invalidInputs.add(name);
      console.error(
        `[citry-ui] CDisclosure ${name} received invalid client value `
          + `${describe(value)}; using ${fallback}.`,
        root,
      );
    };
    const isVueDirective = (name) => vueDirectivePrefixes.some((prefix) => name.startsWith(prefix));
    const isListener = (name) => name.startsWith("on") || name.startsWith("@")
      || name === "v-on" || name.startsWith("v-on:");
    const bindingTarget = (name) => {
      let target = null;
      if (name.startsWith("v-bind:")) {
        target = name.slice(7).split(".", 1)[0];
      } else if (name.startsWith(":") || name.startsWith(".")) {
        target = name.slice(1).split(".", 1)[0];
      }
      // A dynamic argument such as `:[name]` has no fixed target to check.
      return target === null || target.startsWith("[") ? null : target;
    };
    const nearestRootOwns = (element) => element?.closest?.(rootSelector) === root;
    const directPart = (owner, part) => Array.from(owner?.children ?? []).find(
      (child) => child.getAttribute("data-citry-ui-part") === part,
    ) ?? null;
    const resolveAnatomy = () => {
      const header = directPart(root, "disclosure-header");
      const panel = directPart(root, "disclosure-panel");
      const heading = directPart(header, "disclosure-heading");
      const actions = directPart(header, "disclosure-actions");
      const trigger = directPart(heading, "disclosure-trigger");
      const title = directPart(trigger, "disclosure-title");
      const indicator = directPart(trigger, "disclosure-indicator");
      const body = directPart(panel, "disclosure-body");
      return { header, panel, heading, actions, trigger, title, indicator, body };
    };
    const titleAttributeProblem = (element) => {
      const tag = element.localName;
      for (const attribute of element.attributes) {
        const name = attribute.name.toLowerCase();
        if (tag === "svg" && name === "aria-hidden" && attribute.value === "true") {
          continue;
        }
        if (tag === "svg" && name === "focusable" && attribute.value === "false") {
          continue;
        }
        if (titleRejected.has(name) || name.startsWith("aria-")) {
          return `<${tag}> cannot use ${attribute.name}`;
        }
        // This mirrors the server title check so a title changed after
        // render meets the same contract.
        if (isListener(name)) {
          return `<${tag}> cannot use event attribute ${attribute.name}`;
        }
        if (!isVueDirective(name)) {
          continue;
        }
        const target = bindingTarget(name);
        if (target === null) {
          return `<${tag}> cannot use Vue directive ${attribute.name}`;
        }
        if (titleRejected.has(target) || target.startsWith("aria-")) {
          return `<${tag}> cannot dynamically bind ${target}`;
        }
      }
      if (tag === "img" && (!element.hasAttribute("alt") || element.getAttribute("alt") !== "")) {
        return "title images require empty alt text";
      }
      if (tag === "svg" && (
        element.getAttribute("aria-hidden") !== "true"
        || element.getAttribute("focusable") !== "false"
      )) {
        return "title SVG requires aria-hidden=true and focusable=false";
      }
      return null;
    };
    const titleProblem = (title) => {
      if (!(title instanceof HTMLElement)) {
        return "the title wrapper is missing";
      }
      let text = "";
      const visit = (node, inSvg = false, hidden = false) => {
        if (node.nodeType === Node.TEXT_NODE) {
          if (!inSvg && !hidden) {
            text += node.data;
          }
          return null;
        }
        if (node.nodeType !== Node.ELEMENT_NODE) {
          return null;
        }
        const element = node;
        const tag = element.localName;
        const svg = inSvg || tag === "svg";
        if (!(inSvg ? titleSvg : titleHtml).has(tag)) {
          return `unsupported <${tag}> title element`;
        }
        const attributeProblem = titleAttributeProblem(element);
        if (attributeProblem) {
          return attributeProblem;
        }
        const excluded = hidden || element.getAttribute("aria-hidden") === "true";
        for (const child of element.childNodes) {
          const problem = visit(child, svg, excluded);
          if (problem) {
            return problem;
          }
        }
        return null;
      };
      for (const child of title.childNodes) {
        const problem = visit(child);
        if (problem) {
          return problem;
        }
      }
      return /[^\t\n\f\r ]/.test(text) ? null : "title text is empty";
    };
    const contentProblem = (owner, actions) => {
      if (!owner) {
        return null;
      }
      for (const element of owner.querySelectorAll("*")) {
        const tag = element.localName;
        const part = element.getAttribute("data-citry-ui-part");
        if (actions && (part === "disclosure" || part === "accordion")) {
          return "nested Disclosure or Accordion roots are allowed only in panel content";
        }
        if (tag === "dialog") {
          return "native dialog descendants are not accepted";
        }
        if (tag.includes("-")) {
          return `unresolved custom element <${tag}> is not accepted`;
        }
        if (element.hasAttribute("is")) {
          return "customized built-ins are not accepted";
        }
        if (element.shadowRoot !== null) {
          return "authored ShadowRoot descendants are not accepted";
        }
        if (element.hasAttribute("popover") && !(
          element.getAttribute("popover") === "manual" && allowedParts.has(part)
        )) {
          return "raw or unrecognized native popovers are not accepted";
        }
      }
      return null;
    };
    const structureProblem = () => {
      const next = resolveAnatomy();
      if (
        !(next.header instanceof HTMLDivElement)
        || !(next.panel instanceof HTMLDivElement)
        || !(next.heading instanceof HTMLHeadingElement)
        || !(next.trigger instanceof HTMLButtonElement)
        || !(next.title instanceof HTMLSpanElement)
        || !(next.indicator instanceof HTMLSpanElement)
        || !(next.body instanceof HTMLDivElement)
      ) {
        return "owned anatomy is missing or has the wrong native element";
      }
      if (next.actions !== null && !(next.actions instanceof HTMLDivElement)) {
        return "the actions wrapper has the wrong native element";
      }
      if (
        next.header.parentElement !== root
        || next.panel.parentElement !== root
        || next.heading.parentElement !== next.header
        || next.trigger.parentElement !== next.heading
        || next.title.parentElement !== next.trigger
        || next.indicator.parentElement !== next.trigger
        || next.body.parentElement !== next.panel
        || (next.actions && next.actions.parentElement !== next.header)
      ) {
        return "owned anatomy has an invalid parent relationship";
      }
      if (
        root.id !== data.rootId
        || root.getAttribute("data-citry-ui-part") !== "disclosure"
        || !root.hasAttribute("data-citry-disclosure-root")
        || next.heading.localName !== data.headingTag
        || next.trigger.id !== data.triggerId
        || next.panel.id !== data.panelId
        || Boolean(next.actions) !== data.hasActions
        || root.children.length !== 2
        || root.firstElementChild !== next.header
        || root.lastElementChild !== next.panel
        || next.header.children.length !== (data.hasActions ? 2 : 1)
        || next.header.firstElementChild !== next.heading
        || (next.actions && next.header.lastElementChild !== next.actions)
        || next.heading.children.length !== 1
        || next.trigger.children.length !== 2
        || next.trigger.firstElementChild !== next.title
        || next.trigger.lastElementChild !== next.indicator
        || next.panel.children.length !== 1
        || next.trigger.type !== "button"
        || next.trigger.getAttribute("aria-controls") !== next.panel.id
        || next.trigger.id === ""
      ) {
        return "owned trigger relationship is invalid";
      }
      if (
        data.region
          ? next.panel.getAttribute("role") !== "region"
            || next.panel.getAttribute("aria-labelledby") !== next.trigger.id
          : next.panel.hasAttribute("role") || next.panel.hasAttribute("aria-labelledby")
      ) {
        return "owned region relationship is invalid";
      }
      if (next.actions && (
        data.actionsLabel === null
          ? next.actions.hasAttribute("role") || next.actions.hasAttribute("aria-label")
          : next.actions.getAttribute("role") !== "group"
            || next.actions.getAttribute("aria-label") !== data.actionsLabel
      )) {
        return "owned actions relationship is invalid";
      }
      const titleIssue = titleProblem(next.title);
      if (titleIssue) {
        return titleIssue;
      }
      const actionIssue = contentProblem(next.actions, true);
      if (actionIssue) {
        return actionIssue;
      }
      const panelIssue = contentProblem(next.body, false);
      if (panelIssue) {
        return panelIssue;
      }
      anatomy = next;
      return null;
    };

    const durationMs = () => {
      if (matchMedia("(prefers-reduced-motion: reduce)").matches) {
        return 0;
      }
      const raw = getComputedStyle(root)
        .getPropertyValue("--_cui-disclosure-duration")
        .trim();
      if (raw.endsWith("ms")) {
        return Math.max(0, Number.parseFloat(raw) || 0);
      }
      if (raw.endsWith("s")) {
        return Math.max(0, (Number.parseFloat(raw) || 0) * 1000);
      }
      return 0;
    };
    const clearAnimationStyles = () => {
      anatomy?.panel?.style.removeProperty("block-size");
      anatomy?.panel?.style.removeProperty("overflow");
    };
    const cancelAnimation = ({ preserveGeometry = false } = {}) => {
      if (!animation) {
        return;
      }
      const height = anatomy.panel.getBoundingClientRect().height;
      animation.cancel();
      animation = null;
      if (preserveGeometry) {
        anatomy.panel.style.blockSize = `${height}px`;
      } else {
        clearAnimationStyles();
      }
    };
    const settlePresence = (open) => {
      cancelAnimation();
      clearAnimationStyles();
      if (open) {
        anatomy.panel.hidden = false;
        anatomy.panel.inert = false;
        anatomy.panel.removeAttribute("aria-hidden");
      } else {
        anatomy.panel.inert = true;
        anatomy.panel.setAttribute("aria-hidden", "true");
        anatomy.panel.hidden = true;
      }
    };
    const composedParent = (node) => {
      if (node?.parentNode) {
        return node.parentNode;
      }
      if (node instanceof ShadowRoot) {
        return node.host;
      }
      const nodeRoot = node?.getRootNode?.();
      return nodeRoot instanceof ShadowRoot ? nodeRoot.host : null;
    };
    const containingModal = (start) => {
      let current = start;
      while (current) {
        if (current instanceof HTMLDialogElement && current.matches(":modal")) {
          return current;
        }
        current = composedParent(current);
      }
      return null;
    };
    const renderedTrigger = () => {
      if (!anatomy.trigger.isConnected || anatomy.trigger.matches(":disabled")) {
        return false;
      }
      const style = getComputedStyle(anatomy.trigger);
      return style.display !== "none"
        && style.visibility !== "hidden"
        && anatomy.trigger.getClientRects().length > 0;
    };
    const recoverPanelFocus = () => {
      let focused = layerCoordinator.deepActiveElement();
      if (!anchoredLayerRuntime.composedContains(anatomy.panel, focused)) {
        return;
      }
      if (renderedTrigger()) {
        anatomy.trigger.focus({ preventScroll: true });
      }
      focused = layerCoordinator.deepActiveElement();
      if (!anchoredLayerRuntime.composedContains(anatomy.panel, focused)) {
        return;
      }
      const target = containingModal(root) ?? root.ownerDocument.body;
      const prior = target.getAttribute("tabindex");
      if (!target.hasAttribute("tabindex")) {
        target.setAttribute("tabindex", "-1");
      }
      target.focus({ preventScroll: true });
      if (prior === null) {
        target.removeAttribute("tabindex");
      } else {
        target.setAttribute("tabindex", prior);
      }
    };
    const reflectState = () => {
      const state = logicalOpen ? "open" : "closed";
      root.dataset.state = state;
      anatomy.trigger.dataset.state = state;
      anatomy.panel.dataset.state = state;
      anatomy.trigger.setAttribute("aria-expanded", logicalOpen ? "true" : "false");
    };
    const animatePresence = (open) => {
      const panel = anatomy.panel;
      const wasHidden = panel.hidden;
      cancelAnimation({ preserveGeometry: true });
      const start = wasHidden && open ? 0 : panel.getBoundingClientRect().height;
      if (open) {
        panel.hidden = false;
        panel.inert = false;
        panel.removeAttribute("aria-hidden");
      } else {
        panel.inert = true;
        panel.setAttribute("aria-hidden", "true");
      }
      const duration = durationMs();
      if (duration === 0 || typeof panel.animate !== "function") {
        settlePresence(open);
        return;
      }
      if (open && wasHidden) {
        panel.style.blockSize = "auto";
      }
      const end = open ? panel.scrollHeight : 0;
      panel.style.blockSize = `${start}px`;
      panel.style.overflow = "clip";
      const easing = getComputedStyle(root)
        .getPropertyValue("--_cui-disclosure-easing")
        .trim() || "ease-out";
      const current = panel.animate(
        [{ blockSize: `${start}px` }, { blockSize: `${end}px` }],
        { duration, easing },
      );
      animation = current;
      current.finished.then(() => {
        if (!active || animation !== current) {
          return;
        }
        animation = null;
        clearAnimationStyles();
        if (!open) {
          panel.hidden = true;
        }
      }).catch(() => {});
    };
    const commitState = (next, { animate = true } = {}) => {
      if (logicalOpen === next) {
        if (!animate) {
          reflectState();
          settlePresence(next);
        }
        return;
      }
      const ancestorClose = next
        ? null
        : layerCoordinator.beginAncestorClose(anatomy.panel, anatomy.panel);
      try {
        if (!next) {
          recoverPanelFocus();
        }
        logicalOpen = next;
        reflectState();
        if (animate) {
          animatePresence(next);
        } else {
          settlePresence(next);
        }
        ancestorClose?.commit();
      } catch (error) {
        ancestorClose?.cancel();
        throw error;
      }
      runtimeState.logicalOpen = logicalOpen;
      runtimeState.baselineOpen = baselineOpen;
      runtimeState.serverFingerprint = data.serverFingerprint;
    };
    const applyDisabled = () => {
      if (!anatomy?.trigger) {
        return;
      }
      anatomy.trigger.disabled = Boolean(form?.disabled) || configuration.disabled;
      const disabled = anatomy.trigger.matches(":disabled");
      root.toggleAttribute("data-disabled", disabled);
      anatomy.trigger.toggleAttribute("data-disabled", disabled);
    };
    const rebuildFieldsets = () => {
      fieldsetObserver?.disconnect();
      fieldsetObserver = null;
      const fieldsets = [];
      for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
        if (ancestor.matches("fieldset")) {
          fieldsets.push(ancestor);
        }
      }
      if (fieldsets.length === 0) {
        return;
      }
      fieldsetObserver = new MutationObserver(() => {
        if (structureValid) {
          applyDisabled();
        }
      });
      fieldsets.forEach((fieldset) => fieldsetObserver.observe(fieldset, {
        attributes: true,
        attributeFilter: ["disabled"],
        childList: true,
      }));
    };

    const resolveBoolean = (name) => {
      const supplied = rawInputs[name];
      if (supplied === undefined) {
        invalidInputs.delete(name);
        return defaults[name];
      }
      if (typeof supplied === "boolean") {
        invalidInputs.delete(name);
        return supplied;
      }
      reportInput(name, supplied, "the Python fallback");
      return defaults[name];
    };
    const resolveChoice = (name) => {
      const supplied = rawInputs[name];
      if (supplied === undefined) {
        invalidInputs.delete(name);
        return defaults[name];
      }
      if (typeof supplied === "string" && allowedChoices[name].includes(supplied)) {
        invalidInputs.delete(name);
        return supplied;
      }
      reportInput(name, supplied, "the Python fallback");
      return defaults[name];
    };
    const resolveCallback = () => {
      const supplied = rawInputs.onOpenChange;
      if (supplied === undefined || supplied === null) {
        invalidInputs.delete("onOpenChange");
        return null;
      }
      if (typeof supplied === "function") {
        invalidInputs.delete("onOpenChange");
        return supplied;
      }
      reportInput("onOpenChange", supplied, "no callback");
      return null;
    };
    const resolveOpen = () => {
      const supplied = rawInputs.open;
      if (supplied === undefined || supplied === null) {
        invalidInputs.delete("open");
        return { controlled: false, value: baselineOpen };
      }
      if (typeof supplied === "boolean") {
        invalidInputs.delete("open");
        return { controlled: true, value: supplied };
      }
      reportInput("open", supplied, "the committed baseline");
      return { controlled: false, value: baselineOpen };
    };
    const applyRawInputs = ({ animate = true } = {}) => {
      configuration = {
        disabled: resolveBoolean("disabled"),
        variant: resolveChoice("variant"),
        size: resolveChoice("size"),
        indicator: resolveBoolean("indicator"),
        indicatorPosition: resolveChoice("indicatorPosition"),
      };
      onOpenChange = resolveCallback();
      root.dataset.variant = configuration.variant;
      root.dataset.size = configuration.size;
      root.dataset.indicatorPos = configuration.indicatorPosition;
      root.toggleAttribute("data-indicator", configuration.indicator);
      anatomy.indicator.hidden = !configuration.indicator;
      applyDisabled();
      const requested = resolveOpen();
      controlled = requested.controlled;
      commitState(requested.value, { animate });
    };

    const removeActivation = () => {
      if (!activationInstalled) {
        return;
      }
      root.removeEventListener("click", onClick, true);
      activationInstalled = false;
    };
    const installActivation = () => {
      if (activationInstalled) {
        return;
      }
      root.addEventListener("click", onClick, true);
      activationInstalled = true;
    };
    const enterInvalid = (problem) => {
      if (structureValid) {
        cancelAnimation();
        settlePresence(logicalOpen);
      }
      structureValid = false;
      removeActivation();
      fieldsetObserver?.disconnect();
      fieldsetObserver = null;
      root.removeAttribute("data-citry-disclosure-initialized");
      if (!invalidStructureEpisode) {
        invalidStructureEpisode = true;
        console.error(`[citry-ui] CDisclosure settled structure is invalid: ${problem}.`, root);
      }
    };
    const repair = () => {
      structureValid = true;
      invalidStructureEpisode = false;
      rebuildFieldsets();
      installActivation();
      applyRawInputs({ animate: false });
      reconciledOnce = true;
      root.setAttribute("data-citry-disclosure-initialized", "");
    };
    const preflight = () => {
      const problem = structureProblem();
      if (problem) {
        enterInvalid(problem);
        return false;
      }
      if (!structureValid) {
        repair();
      }
      return true;
    };
    function onClick(event) {
      const trigger = event.target.closest?.("[data-citry-disclosure-trigger]");
      if (trigger !== anatomy?.trigger || !nearestRootOwns(trigger)) {
        return;
      }
      if (!preflight() || anatomy.trigger.matches(":disabled")) {
        return;
      }
      const previous = logicalOpen;
      const next = !previous;
      const requestWasControlled = controlled;
      onOpenChange?.(next, {
        open: next,
        previousOpen: previous,
        source: "activation",
        controlled: requestWasControlled,
      });
      if (!preflight()) {
        return;
      }
      if (!requestWasControlled) {
        baselineOpen = next;
        commitState(next, { animate: true });
      }
    }
    const onBeforeToggle = (event) => {
      if (event.newState !== "open") {
        return;
      }
      const target = event.target;
      if (!(target instanceof Element) || target === root || !root.contains(target)) {
        return;
      }
      const part = target.getAttribute("data-citry-ui-part");
      const forbidden = target.localName === "dialog" || (
        target.hasAttribute("popover")
        && !(target.getAttribute("popover") === "manual" && allowedParts.has(part))
      );
      if (!forbidden) {
        return;
      }
      event.preventDefault();
      enterInvalid(
        target.localName === "dialog"
          ? "a descendant Dialog attempted to open"
          : "a raw descendant popover attempted to open",
      );
    };

    const titleObserver = new MutationObserver(() => {
      if (active) {
        preflight();
      }
    });
    const contentObserver = new MutationObserver(() => {
      if (active) {
        preflight();
      }
    });
    const observeStructure = () => {
      titleObserver.disconnect();
      contentObserver.disconnect();
      const current = resolveAnatomy();
      if (current.title) {
        titleObserver.observe(current.title, {
          attributes: true,
          childList: true,
          characterData: true,
          subtree: true,
        });
      }
      if (current.panel) {
        contentObserver.observe(current.panel, {
          attributes: true,
          attributeFilter: ["popover", "data-citry-ui-part", "is"],
          childList: true,
          subtree: true,
        });
      }
      if (current.actions) {
        contentObserver.observe(current.actions, {
          attributes: true,
          attributeFilter: ["popover", "data-citry-ui-part", "is"],
          childList: true,
          subtree: true,
        });
      }
    };

    root.addEventListener("beforetoggle", onBeforeToggle, true);
    observeStructure();
    const initialProblem = structureProblem();
    if (initialProblem) {
      enterInvalid(initialProblem);
    } else {
      structureValid = true;
      rebuildFieldsets();
      installActivation();
    }
    effect(() => {
      rawInputs = {
        open: props.open,
        onOpenChange: props.onOpenChange,
        disabled: props.disabled,
        variant: props.variant,
        size: props.size,
        indicator: props.indicator,
        indicatorPosition: props.indicatorPosition,
      };
      if (!structureValid || !preflight()) {
        return;
      }
      applyRawInputs({ animate: reconciledOnce });
      reconciledOnce = true;
      root.setAttribute("data-citry-disclosure-initialized", "");
    });

    return () => {
      active = false;
      runtimeState.baselineOpen = baselineOpen;
      runtimeState.logicalOpen = logicalOpen;
      runtimeState.serverFingerprint = data.serverFingerprint;
      removeActivation();
      root.removeEventListener("beforetoggle", onBeforeToggle, true);
      fieldsetObserver?.disconnect();
      titleObserver.disconnect();
      contentObserver.disconnect();
      cancelAnimation();
      clearAnimationStyles();
      root.removeAttribute("data-citry-disclosure-initialized");
    };
  },
});

})();