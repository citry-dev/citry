(function() {

__citryRuntime.registerTypeOptions.bind(null, "CMenuRadioGroup_3c9281", "81a9eff11b3b32999da1e4176e55de804e9cadcfb2c4c0b5b5b8d906bdc3a641")({
  props: {
    value: {},
    onValueChange: {},
  },
  inject: {menuContext: {from: Symbol.for("citry-ui:menu"), default: null}},
  setup() {
    const parent = Citry.vue.inject(Symbol.for("citry-ui:menu"), null);
    const service = Citry.vue.markRaw(parent?.child({container: null, radioGroup: null}) ?? {});
    Citry.vue.onUnmounted(() => parent?.releaseRadioState(service.identity));
    return {radioService: service};
  },
  provide() { return {[Symbol.for("citry-ui:menu")]: this.radioService}; },
  onServerRender: ({component}) => {
    const root = component.$el;
    const data = {key: component.key, ...component.serverDefaults};
    const props = component.$props;
    const effect = Citry.vue.watchEffect;
    const context = component.menuContext;
    if (!context) {
      console.error(
        "[citry-ui] CMenuRadioGroup requires the nearest CMenu client context.",
        root,
      );
      return;
    }
    const label = root.querySelector(
      ':scope > [data-citry-ui-part="menu-group-label"]',
    );
    const invalidEpisodes = new Set();
    const runtimeState = context.claimRadioState(
      data.value, context.path ?? [], component.radioService.identity,
    );
    root.__citryUiMenuRadioGroupRuntime = runtimeState;
    let controlled = runtimeState.serverValue === data.value
      ? Boolean(runtimeState.controlled)
      : false;
    let committed = runtimeState.serverValue === data.value
      ? runtimeState.current
      : data.value;
    let current = committed;
    let onValueChange = null;
    let priorOrder = runtimeState.serverValue === data.value
      ? [...(runtimeState.priorOrder ?? [])]
      : [];
    let pendingRemoval = runtimeState.serverValue === data.value
      ? runtimeState.pendingRemoval
      : null;

    const reportInvalid = (name, value, fallback) => {
      if (invalidEpisodes.has(name)) {
        return;
      }
      invalidEpisodes.add(name);
      console.error(
        `[citry-ui] CMenuRadioGroup ${name} received invalid client value `
          + `${JSON.stringify(value)}; ${fallback}.`,
        root,
      );
    };
    const canonical = (value) => (
      typeof value === "string" && value.length > 0 && !value.includes("\0")
        ? value.replace(/\r\n?/g, "\n")
        : null
    );
    const radios = () => context.entries(root).filter((entry) => entry.kind === "radio");
    const apply = () => {
      for (const radio of radios()) {
        radio.setRadioChecked?.(radio.value === current);
      }
    };
    const notify = (requested, previous, reason, item, event, path) => {
      onValueChange?.(requested, {
        value: requested,
        previousValue: previous,
        reason,
        controlled,
        item,
        event,
        path: [...path],
      });
    };
    const removalFallback = (removed, values) => {
      const oldIndex = priorOrder.indexOf(removed);
      if (oldIndex < 0) {
        return values[0];
      }
      for (let distance = 1; distance <= priorOrder.length; distance += 1) {
        const following = priorOrder[oldIndex + distance];
        if (values.includes(following)) {
          return following;
        }
        const preceding = priorOrder[oldIndex - distance];
        if (values.includes(preceding)) {
          return preceding;
        }
      }
      return values[0];
    };
    const entry = {
      root,
      key: data.key,
      kind: "radio-group",
      value: null,
      serverValue: data.value,
      surface: context.surface,
      container: context.container,
      requestValue(radio, event, path) {
        if (radio.value === current) {
          // Re-activating the selected radio is still an accepted Menu
          // action. It skips only the value-change callback.
          return true;
        }
        const previous = current;
        if (!controlled) {
          committed = radio.value;
          current = radio.value;
          apply();
        }
        notify(radio.value, previous, "activation", radio.element, event, path);
        return true;
      },
      refresh() {
        const available = radios();
        const values = available.map((radio) => radio.value);
        const supplied = props.value;
        const callback = props.onValueChange;
        // Child components register later in the same client activation
        // turn. Defer membership checks until that collection exists.
        if (values.length === 0) {
          return;
        }
        if (supplied === undefined || supplied === null) {
          if (controlled || pendingRemoval) {
            committed = pendingRemoval?.requested ?? current;
          }
          controlled = false;
          current = committed;
          pendingRemoval = null;
          invalidEpisodes.delete("value");
        } else {
          const normalized = canonical(supplied);
          if (normalized !== null && values.includes(normalized)) {
            controlled = true;
            current = normalized;
            pendingRemoval = null;
            invalidEpisodes.delete("value");
            invalidEpisodes.delete("removal");
          } else if (
            pendingRemoval
            && normalized === pendingRemoval.removed
          ) {
            // A controlled owner may acknowledge a removal after a
            // later render. Preserve the one requested fallback and do
            // not drift or repeat the callback while waiting.
            controlled = true;
            current = "";
            invalidEpisodes.delete("value");
          } else if (controlled && normalized !== null && normalized === current) {
            // The previously valid controlled selection disappeared in
            // this settled collection. The removal branch below owns
            // the single fallback request and diagnostic semantics.
            invalidEpisodes.delete("value");
          } else {
            reportInvalid("value", supplied, "retaining the last valid selection");
          }
        }
        if (callback === undefined || callback === null || typeof callback === "function") {
          onValueChange = callback ?? null;
          invalidEpisodes.delete("onValueChange");
        } else {
          reportInvalid("onValueChange", callback, "ignoring the callback");
          onValueChange = null;
        }
        if (values.length > 0 && !values.includes(current)) {
          if (!pendingRemoval) {
            const previous = current;
            const requested = removalFallback(previous, values);
            if (!controlled) {
              committed = requested;
              current = requested;
            } else {
              pendingRemoval = { removed: previous, requested };
              current = "";
            }
            invalidEpisodes.add("removal");
            context.defer(() => {
              notify(requested, previous, "removal", null, null, context.path);
            });
          }
        } else if (values.includes(current)) {
          invalidEpisodes.delete("removal");
          pendingRemoval = null;
        }
        priorOrder = values;
        apply();
      },
      validate() {
        const forbidden = label?.querySelector(
          "a[href], button, input, select, textarea, [contenteditable], [tabindex]",
        );
        if (forbidden) {
          console.error(
            "[citry-ui] CMenuRadioGroup label must remain noninteractive.",
            root,
          );
          return false;
        }
        return radios().length > 0;
      },
    };
    const unregister = context.register(entry);
    component.radioService.setOptions({container: root, radioGroup: entry});
    effect(() => {
      // Root reconciliation runs after all direct radio registrations in
      // this activation turn, so a valid controlled value is never
      // diagnosed merely because its child registered later.
      void props.value;
      void props.onValueChange;
      context.update(entry);
    });
    return () => {
      runtimeState.current = current || committed;
      runtimeState.serverValue = data.value;
      runtimeState.priorOrder = priorOrder;
      runtimeState.pendingRemoval = pendingRemoval;
      runtimeState.controlled = controlled;
      unregister();
    };
  },
});

})();