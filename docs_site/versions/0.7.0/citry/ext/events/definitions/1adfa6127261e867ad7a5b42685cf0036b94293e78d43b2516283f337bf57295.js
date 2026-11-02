(function() {

      // Page markup can hide a document's or form's members behind named elements. The core runtime's helper
      // reads the built-in ones; Citry before 0.7.0 have no helper, so the fallback reads members directly.
      const builtIn = globalThis[Symbol.for("citry:built-in-members")] ?? (target => target);

      const guardButtonActivation = (root, configuration, event) => {
        const isLink = root.localName === "a";
        if (
          !configuration.loading
          && !(isLink && configuration.disabled)
          && !root.matches(":disabled")
        ) {
          return true;
        }
        event.preventDefault();
        event.stopImmediatePropagation();
        return false;
      };
      // Skip unchanged writes: they still report a change, and a component
      // that repairs its markup from an observer would never go idle.
      const setAttribute = (element, name, value) => {
        if (element.getAttribute(name) !== value) element.setAttribute(name, value);
      };
      const applyButtonConfiguration = (root, indicator, data, next, { writesLoadingState = true } = {}) => {
        const isLink = root.localName === "a";
        if (isLink) {
          if (next.disabled || next.loading) {
            root.removeAttribute("href");
          } else {
            setAttribute(root, "href", data.href);
          }
          const tabIndex = next.disabled
            ? -1
            : next.loading
              ? (data.tabIndex ?? 0)
              : data.tabIndex;
          if (tabIndex === null || tabIndex === undefined) {
            root.removeAttribute("tabindex");
          } else {
            setAttribute(root, "tabindex", String(tabIndex));
          }
        } else {
          if (root.disabled !== next.disabled) {
            root.disabled = next.disabled;
          }
        }
        root.toggleAttribute("data-disabled", next.disabled);
        if (root.dataset.variant !== next.variant) root.dataset.variant = next.variant;
        if (root.dataset.intent !== next.intent) root.dataset.intent = next.intent;
        if (root.dataset.size !== next.size) root.dataset.size = next.size;
        // A split button's menu trigger never shows loading and uses native
        // `disabled`, so its caller skips these.
        if (writesLoadingState) {
          root.toggleAttribute("data-loading", next.loading);
          root.toggleAttribute("data-block", next.block);
          if (root.dataset.loadingPosition !== next.loadingPosition) {
            root.dataset.loadingPosition = next.loadingPosition;
          }
          if (next.loading) {
            setAttribute(root, "aria-busy", "true");
          } else {
            root.removeAttribute("aria-busy");
          }
          if (next.disabled || next.loading) {
            setAttribute(root, "aria-disabled", "true");
          } else {
            root.removeAttribute("aria-disabled");
          }
        }
        if (indicator && indicator.hidden !== !next.loading) {
          indicator.hidden = !next.loading;
        }
      };
      const createButtonResolver = (componentName, root, data, props, allowed) => {
        const invalid = new Map();
        const describe = (value) => {
          try {
            return JSON.stringify(value) ?? String(value);
          } catch {
            return String(value);
          }
        };
        const report = (name, value) => {
          const shown = describe(value);
          const fingerprint = `${typeof value}:${shown}`;
          if (invalid.get(name) === fingerprint) return;
          invalid.set(name, fingerprint);
          console.error(
            `[citry-ui] ${componentName} ${name} received invalid client value ${shown}; `
              + "using the server-rendered fallback.",
            root,
          );
        };
        const value = (name) => props[name] === undefined ? data[name] : props[name];
        return {
          boolean(name) {
            const next = value(name);
            if (typeof next === "boolean") {
              invalid.delete(name);
              return next;
            }
            report(name, next);
            return data[name];
          },
          choice(name) {
            const next = value(name);
            if (allowed[name].includes(next)) {
              invalid.delete(name);
              return next;
            }
            report(name, next);
            return data[name];
          },
        };
      };
      const applyCompoundButtonConfiguration = (
        root,
        primary,
        trigger,
        indicator,
        formDisabled,
        next,
      ) => {
        const commonDisabled = next.disabled || formDisabled;
        applyButtonConfiguration(primary, indicator, { href: null, tabIndex: null }, {
          ...next,
          disabled: commonDisabled || next.primaryDisabled,
          block: false,
        });
        applyButtonConfiguration(trigger, null, { href: null, tabIndex: null }, {
          ...next,
          disabled: commonDisabled || next.menuDisabled,
          loading: false,
          block: false,
        }, { writesLoadingState: false });
        for (const name of ["aria-busy", "aria-disabled", "data-block", "data-loading", "data-loading-position"]) {
          trigger.removeAttribute(name);
        }
        for (const name of ["variant", "intent", "size"]) {
          if (root.dataset[name] !== next[name]) root.dataset[name] = next[name];
        }
        if (root.dataset.loadingPosition !== next.loadingPosition) {
          root.dataset.loadingPosition = next.loadingPosition;
        }
        for (const [name, enabled] of [
          ["data-block", next.block],
          ["data-disabled", next.disabled],
          ["data-loading", next.loading],
          ["data-primary-disabled", primary.matches(":disabled")],
          ["data-menu-disabled", trigger.matches(":disabled")],
        ]) {
          root.toggleAttribute(name, enabled);
        }
      };

      
      (() => {
        const runtimeKey = Symbol.for('citry-ui:button-runtime');
        const installed = globalThis[runtimeKey];
        if (installed !== undefined) {
          if (installed.generation !== 1 || installed.fingerprint !== 'a0929332151b429fc0a1b77eec31aea444ebe3662ed7b3ee9b7c841fd790f292') {
            throw new Error(
              "[citry-ui] cannot replace an incompatible CButton runtime; "
                + "a full page reload is required.",
            );
          }
          return;
        }
        const definition = {
        helpers: {
          applyConfiguration: applyButtonConfiguration,
          applyCompoundConfiguration: applyCompoundButtonConfiguration,
          createResolver: createButtonResolver,
          guardActivation: guardButtonActivation,
        },
        props: {
          disabled: {},
          loading: {},
          variant: {},
          intent: {},
          size: {},
          block: {},
          loadingPosition: {},
        },
        inject: {formService: {from: Symbol.for("citry-ui:form"), default: null}},
        onServerRender: ({component}) => {
          const root = component.$el;
          const server = {
            ...component.serverDefaults,
            href: component.href,
            tabIndex: component.tabIndex,
          };
          const props = component.$props;
          const indicator = root.querySelector('[data-citry-ui-part="loading-indicator"]');
          const formContext = component.formService;
          const isLink = root.localName === "a";
          const allowedValues = {
            variant: ["solid", "outline", "ghost"],
            intent: ["primary", "neutral", "success", "warn", "danger"],
            size: ["sm", "md", "lg"],
            loadingPosition: ["start", "center", "end"],
          };
          const resolver = createButtonResolver("CButton", root, server, props, allowedValues);
          let configuration = {
            disabled: server.disabled,
            loading: server.loading,
            variant: server.variant,
            intent: server.intent,
            size: server.size,
            block: server.block,
            loadingPosition: server.loadingPosition,
          };

          const applyConfiguration = (next) => {
            configuration = next;
            applyButtonConfiguration(root, indicator, server, next);
          };
          const blockUnavailableActivation = (event) => {
            guardButtonActivation(root, configuration, event);
          };
          const blockLoadingSubmitter = (event) => {
            if (!configuration.loading || event.submitter !== root) {
              return;
            }
            event.preventDefault();
            event.stopImmediatePropagation();
          };
          const nativeForm = isLink ? null : root.form;

          root.addEventListener("click", blockUnavailableActivation, true);
          if (nativeForm) builtIn(nativeForm).addEventListener("submit", blockLoadingSubmitter, true);
          Citry.vue.watchEffect(() => {
            const localDisabled = resolver.boolean("disabled");
            applyConfiguration({
              disabled: Boolean(formContext?.disabled) || localDisabled,
              loading: resolver.boolean("loading"),
              variant: resolver.choice("variant"),
              intent: resolver.choice("intent"),
              size: resolver.choice("size"),
              block: resolver.boolean("block"),
              loadingPosition: resolver.choice("loadingPosition"),
            });
          });
          root.setAttribute("data-citry-button-initialized", "");

          return () => {
            root.removeEventListener("click", blockUnavailableActivation, true);
            if (nativeForm) builtIn(nativeForm).removeEventListener("submit", blockLoadingSubmitter, true);
            root.removeAttribute("data-citry-button-initialized");
          };
        },
      };
        globalThis[runtimeKey] = {
          generation: 1,
          fingerprint: 'a0929332151b429fc0a1b77eec31aea444ebe3662ed7b3ee9b7c841fd790f292',
          definition,
          
          helpers: definition.helpers ?? {},
        };
      })();

})();