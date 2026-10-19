(function() {

const anchoredLayerRuntimeCompatible = globalThis[
  Symbol.for("citry-ui:anchored-layer-runtime-compatible")
] === true;
const anchoredLayerRuntime = globalThis[
  Symbol.for("citry-ui:anchored-layer-runtime")
];

__citryRuntime.registerTypeOptions.bind(null, "CMenuSubmenu_cba41f", "7ce6c914f48282236e974a03b04904c85d087c88bc77addf581a125ffe673554")({
  props: {
    disabled: {},
    intent: {},
    textValue: {},
  },
  inject: {menuContext: {from: Symbol.for("citry-ui:menu"), default: null}},
  setup() {
    const parent = Citry.vue.inject(Symbol.for("citry-ui:menu"), null);
    return {submenuService: Citry.vue.markRaw(parent?.child({
      surface: null, container: null, path: [], parentSubmenu: null, radioGroup: null,
    }) ?? {})};
  },
  provide() { return {[Symbol.for("citry-ui:menu")]: this.submenuService}; },
  onServerRender: ({component}) => {
    if (!anchoredLayerRuntimeCompatible) return;
    const wrapper = component.$el;
    const data = {key: component.key, value: component.value, ...component.serverDefaults};
    const props = component.$props;
    const effect = Citry.vue.watchEffect;
    const context = component.menuContext;
    if (!context) {
      console.error(
        "[citry-ui] CMenuSubmenu requires the nearest CMenu client context.",
        wrapper,
      );
      return;
    }
    // Each component script runs in its own scope, so the popover helper
    // that CMenu's shared runtime defines is read from the record that
    // runtime publishes. A menu context above (from CMenu, CContextMenu, or
    // CSplitButton) means that runtime loaded, because each lists it as a dependency.
    const hideNativePopover = globalThis[Symbol.for("citry-ui:menu-root-runtime")]
      ?.helpers?.hideNativePopover;
    if (typeof hideNativePopover !== "function") {
      console.error(
        "[citry-ui] CMenuSubmenu is inactive because the CMenu runtime script did not load.",
        wrapper,
      );
      return;
    }
    const trigger = wrapper.querySelector(
      ':scope > [data-citry-ui-part="menu-submenu-trigger"]',
    );
    const surface = wrapper.querySelector(':scope > [data-citry-ui-part="menu"]');
    const label = trigger?.querySelector(
      ':scope > .cui-menu__item-copy > [data-citry-ui-part="menu-item-label"]',
    );
    const description = trigger?.querySelector(
      ':scope > .cui-menu__item-copy > '
        + '[data-citry-ui-part="menu-item-description"]',
    );
    const probe = wrapper.querySelector(":scope > [data-citry-menu-measure]");
    if (!trigger || !surface || !label || !probe) {
      console.error("[citry-ui] CMenuSubmenu could not resolve its owned anatomy.", wrapper);
      return;
    }
    const layerCoordinator = anchoredLayerRuntime.coordinatorFor(surface);
    const anchorName = getComputedStyle(surface)
      .getPropertyValue("--_cui-menu-anchor")
      .trim();
    trigger.style.setProperty("anchor-name", anchorName);
    surface.style.setProperty("position-anchor", anchorName);
    const invalidEpisodes = new Set();
    let openTimer = null;
    let intentCleanup = null;
    let geometryStop = null;
    let latestGeometry = null;

    const reportInvalid = (name, value, fallback) => {
      if (invalidEpisodes.has(name)) {
        return;
      }
      invalidEpisodes.add(name);
      console.error(
        `[citry-ui] CMenuSubmenu ${name} received invalid client value `
          + `${JSON.stringify(value)}; ${fallback}.`,
        wrapper,
      );
    };
    const resolveBoolean = () => {
      const value = props.disabled === undefined ? data.disabled : props.disabled;
      if (typeof value === "boolean") {
        invalidEpisodes.delete("disabled");
        return value;
      }
      reportInvalid("disabled", value, "using the server-rendered fallback");
      return data.disabled;
    };
    const resolveIntent = () => {
      const value = props.intent === undefined ? data.intent : props.intent;
      if (["default", "danger"].includes(value)) {
        invalidEpisodes.delete("intent");
        return value;
      }
      reportInvalid("intent", value, "using the server-rendered fallback");
      return data.intent;
    };
    const resolveTextValue = () => {
      const value = props.textValue === undefined ? data.textValue : props.textValue;
      if (value === null) {
        invalidEpisodes.delete("textValue");
        return value;
      }
      if (typeof value === "string" && !value.includes("\0")) {
        invalidEpisodes.delete("textValue");
        return value.replace(/\r\n?/g, "\n");
      }
      reportInvalid("textValue", value, "using the server-rendered fallback");
      return data.textValue;
    };
    const choosePlacement = () => {
      const rect = trigger.getBoundingClientRect();
      const viewport = surface.ownerDocument.defaultView?.visualViewport;
      const left = viewport?.offsetLeft ?? 0;
      const top = viewport?.offsetTop ?? 0;
      const right = left + (viewport?.width ?? innerWidth);
      const bottom = top + (viewport?.height ?? innerHeight);
      const minimum = probe.getBoundingClientRect().width;
      const rtl = getComputedStyle(trigger).direction === "rtl";
      const inlineEnd = rtl ? rect.left - left : right - rect.right;
      const inlineStart = rtl ? right - rect.right : rect.left - left;
      let side;
      if (inlineEnd >= minimum) {
        side = "inline-end";
      } else if (inlineStart >= minimum) {
        side = "inline-start";
      } else {
        side = bottom - rect.bottom >= rect.top - top ? "block-end" : "block-start";
      }
      surface.dataset.citryMenuSide = side;
    };
    const updateGeometry = () => {
      if (!entry.open) {
        return;
      }
      const triggerRect = trigger.getBoundingClientRect();
      const surfaceRect = surface.getBoundingClientRect();
      const gap = 2;
      let side;
      if (surfaceRect.right <= triggerRect.left + gap) {
        side = "inline-start";
      } else if (surfaceRect.left >= triggerRect.right - gap) {
        side = "inline-end";
      } else if (surfaceRect.bottom <= triggerRect.top + gap) {
        side = "block-start";
      } else {
        side = "block-end";
      }
      latestGeometry = { trigger: triggerRect, surface: surfaceRect, side };
      wrapper.dataset.citryMenuPhysicalSide = side;
    };
    const geometryRuntime = (() => {
      anchoredLayerRuntime.menuGeometry ??= new WeakMap();
      const ownerDocument = surface.ownerDocument;
      let runtime = anchoredLayerRuntime.menuGeometry.get(ownerDocument);
      if (runtime) {
        return runtime;
      }
      runtime = {
        entries: new Set(),
        frame: null,
        start(item) {
          runtime.entries.add(item);
          if (runtime.frame !== null) {
            return;
          }
          const sample = () => {
            runtime.frame = null;
            for (const candidate of runtime.entries) {
              candidate.updateGeometry();
            }
            if (runtime.entries.size > 0) {
              runtime.frame = requestAnimationFrame(sample);
            }
          };
          runtime.frame = requestAnimationFrame(sample);
        },
        stop(item) {
          runtime.entries.delete(item);
          if (runtime.entries.size === 0 && runtime.frame !== null) {
            cancelAnimationFrame(runtime.frame);
            runtime.frame = null;
          }
        },
      };
      anchoredLayerRuntime.menuGeometry.set(ownerDocument, runtime);
      return runtime;
    })();
    const pointInPolygon = (point, points) => {
      let inside = false;
      for (let index = 0, previous = points.length - 1; index < points.length; previous = index++) {
        const currentPoint = points[index];
        const previousPoint = points[previous];
        const crosses = (currentPoint.y > point.y) !== (previousPoint.y > point.y)
          && point.x < (previousPoint.x - currentPoint.x)
            * (point.y - currentPoint.y)
            / (previousPoint.y - currentPoint.y)
            + currentPoint.x;
        if (crosses) {
          inside = !inside;
        }
      }
      return inside;
    };
    const corridor = (start, geometry) => {
      const rect = geometry.surface;
      const pad = 8;
      if (geometry.side === "inline-start") {
        return [
          start,
          { x: rect.right + pad, y: rect.top - pad },
          { x: rect.right + pad, y: rect.bottom + pad },
        ];
      }
      if (geometry.side === "inline-end") {
        return [start, { x: rect.left - pad, y: rect.top - pad }, { x: rect.left - pad, y: rect.bottom + pad }];
      }
      if (geometry.side === "block-start") {
        return [
          start,
          { x: rect.left - pad, y: rect.bottom + pad },
          { x: rect.right + pad, y: rect.bottom + pad },
        ];
      }
      return [start, { x: rect.left - pad, y: rect.top - pad }, { x: rect.right + pad, y: rect.top - pad }];
    };
    const cancelIntent = () => {
      if (openTimer !== null) {
        clearTimeout(openTimer);
        openTimer = null;
      }
      intentCleanup?.();
      intentCleanup = null;
    };
    const entry = {
      root: wrapper,
      wrapper,
      element: trigger,
      trigger,
      label,
      key: data.key,
      kind: "submenu",
      value: data.value,
      surface: context.surface,
      childSurface: surface,
      container: context.container,
      path: [...(context.path ?? [])],
      parent: context.parentSubmenu,
      radioGroup: null,
      open: false,
      ownDisabled: data.disabled,
      effectiveDisabled: data.disabled,
      intent: data.intent,
      textValue: data.textValue,
      choosePlacement,
      updateGeometry,
      startGeometry() {
        geometryRuntime.start(entry);
        geometryStop = () => geometryRuntime.stop(entry);
      },
      stopGeometry() {
        geometryStop?.();
        geometryStop = null;
      },
      scheduleOpen() {
        if (openTimer !== null) {
          return;
        }
        openTimer = setTimeout(() => {
          openTimer = null;
          context.openSubmenu(entry, { focus: null });
        }, 120);
      },
      cancelIntent,
      beginIntent(event) {
        cancelIntent();
        if (!latestGeometry) {
          context.closeSubmenu(entry, { restore: false });
          return;
        }
        const start = { x: event.clientX, y: event.clientY };
        const targetRoot = surface.getRootNode();
        const onMove = (moveEvent) => {
          if (moveEvent.pointerType !== event.pointerType) {
            cancelIntent();
            context.closeSubmenu(entry, { restore: false });
            return;
          }
          if (
            surface.contains(moveEvent.target)
            || pointInPolygon(
              { x: moveEvent.clientX, y: moveEvent.clientY },
              corridor(start, latestGeometry),
            )
          ) {
            return;
          }
          cancelIntent();
          context.closeSubmenu(entry, { restore: false });
        };
        targetRoot.addEventListener("pointermove", onMove, true);
        const timeout = setTimeout(() => {
          cancelIntent();
          if (!surface.matches(":hover")) {
            context.closeSubmenu(entry, { restore: false });
          }
        }, 300);
        intentCleanup = () => {
          clearTimeout(timeout);
          targetRoot.removeEventListener("pointermove", onMove, true);
        };
      },
      refresh() {
        const childHadFocus = entry.open && anchoredLayerRuntime.composedContains(
          surface,
          layerCoordinator.deepActiveElement(),
        );
        entry.effectiveDisabled = resolveBoolean();
        entry.intent = resolveIntent();
        entry.textValue = resolveTextValue();
        surface.dataset.size = context.size();
        trigger.toggleAttribute("data-disabled", entry.effectiveDisabled);
        trigger.toggleAttribute("aria-disabled", entry.effectiveDisabled);
        if (entry.effectiveDisabled) {
          trigger.setAttribute("aria-disabled", "true");
          context.closeSubmenu(entry, { restore: childHadFocus });
        } else {
          trigger.removeAttribute("aria-disabled");
        }
        trigger.dataset.intent = entry.intent;
      },
      validate() {
        const regions = [
          trigger.querySelector(':scope > [data-citry-ui-part="menu-item-start"]'),
          label,
          description,
          trigger.querySelector(':scope > [data-citry-ui-part="menu-item-end"]'),
        ].filter(Boolean);
        const forbidden = regions.some((region) => region.querySelector(
          "a[href], button, input, select, textarea, [contenteditable], [tabindex]",
        ));
        if (forbidden) {
          console.error("[citry-ui] CMenuSubmenu label must remain noninteractive.", wrapper);
          return false;
        }
        return context.entries(surface).filter((candidate) => candidate.kind !== "separator").length > 0;
      },
    };
    entry.layer = {
      surface,
      trigger,
      logicalParent: context.parentSubmenu?.layer ?? context.rootLayer,
      isEligible: () => (
        !entry.effectiveDisabled
        && !trigger.matches('[aria-disabled="true"]')
      ),
      isOpen: () => entry.open,
      requestDismiss: (reason, source) => context.dismissFromSubmenu(entry, reason, source),
      forceClose: (reason, source) => context.closeSubmenu(entry, {
        restore: false,
        reason,
        source,
      }),
      insideElements: [wrapper],
    };
    context.addSubmenu(entry);
    const unregister = context.register(entry);
    component.submenuService.setOptions({
        surface,
        container: surface,
        path: [...(context.path ?? []), data.value],
        parentSubmenu: entry,
        radioGroup: null,
      });
    effect(() => {
      entry.refresh();
      context.update(entry);
    });
    const onToggle = (event) => {
      if (event.target !== surface) {
        return;
      }
      const nativeOpen = surface.matches(":popover-open");
      if (nativeOpen === entry.open) {
        return;
      }
      if (nativeOpen) {
        hideNativePopover(surface);
        return;
      }
      context.closeSubmenu(entry, { restore: false });
    };
    surface.addEventListener("toggle", onToggle);
    return () => {
      if (openTimer !== null) {
        clearTimeout(openTimer);
      }
      cancelIntent();
      entry.stopGeometry();
      surface.removeEventListener("toggle", onToggle);
      context.closeSubmenu(entry, { restore: false });
      unregister();
    };
  },
});

})();