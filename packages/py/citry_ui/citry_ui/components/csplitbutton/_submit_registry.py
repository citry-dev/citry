"""Private submit-scope registry for Split Button primary submitters."""

from citry.ext.dependencies import Script

_SPLIT_BUTTON_SUBMIT_RUNTIME_KEY = "citry-ui:split-button-submit-runtime"
_SPLIT_BUTTON_SUBMIT_RUNTIME_GENERATION = 1

_SPLIT_BUTTON_SUBMIT_RUNTIME_SOURCE = r"""
      (() => {
        const runtimeKey = Symbol.for("citry-ui:split-button-submit-runtime");
        const generation = 1;
        const installed = globalThis[runtimeKey];
        if (installed !== undefined) {
          if (installed.generation !== generation) {
            throw new Error(
              "[citry-ui] cannot replace an incompatible SplitButton submit runtime; "
                + "a full page reload is required.",
            );
          }
          return;
        }

        const managers = new WeakMap();
        const stats = {
          scopes: 0,
          registrations: 0,
        };
        const isOpenShadowRoot = (value) => (
          value instanceof ShadowRoot && value.host.shadowRoot === value
        );
        const actualRoot = (element) => {
          const root = element?.getRootNode?.() ?? null;
          return root instanceof Document || isOpenShadowRoot(root) ? root : null;
        };
        const releaseManager = (root, manager) => {
          if (manager.entries.size > 0) {
            return;
          }
          root.removeEventListener("submit", manager.onSubmit, true);
          root.removeEventListener("invalid", manager.onInvalid, true);
          manager.observer.disconnect();
          managers.delete(root);
          stats.scopes -= 1;
        };
        const managerFor = (root) => {
          let manager = managers.get(root);
          if (manager) {
            return manager;
          }
          const entries = new Map();
          const onSubmit = (event) => {
            const entry = entries.get(event.submitter);
            if (!entry) {
              return;
            }
            if (!entry.hasAcceptedClick() && !entry.available(event)) {
              event.preventDefault();
              event.stopImmediatePropagation();
              return;
            }
            entry.observe(event);
          };
          const onInvalid = (event) => {
            const form = event.target?.form ?? null;
            if (!form) return;
            for (const entry of entries.values()) {
              if (entry.primary.form === form && !entry.hasAcceptedClick()) {
                entry.noteInvalid(event.target);
              }
            }
          };
          let refreshScheduled = false;
          const observer = new MutationObserver(() => {
            if (refreshScheduled) {
              return;
            }
            refreshScheduled = true;
            queueMicrotask(() => {
              refreshScheduled = false;
              for (const entry of [...entries.values()]) {
                entry.refresh();
              }
            });
          });
          observer.observe(root, { subtree: true, childList: true });
          root.addEventListener("submit", onSubmit, true);
          root.addEventListener("invalid", onInvalid, true);
          manager = { entries, observer, onInvalid, onSubmit };
          managers.set(root, manager);
          stats.scopes += 1;
          return manager;
        };
        const register = (primary, options) => {
          let active = true;
          let root = null;
          let manager = null;
          let invalidFocus = null;
          let invalidTimer = null;
          const entry = {
            primary,
            available: options.available,
            hasAcceptedClick: options.hasAcceptedClick,
            observe: options.observe,
            noteInvalid(target) {
              invalidFocus ??= target;
              if (invalidTimer !== null) clearTimeout(invalidTimer);
              invalidTimer = setTimeout(() => {
                invalidFocus = null;
                invalidTimer = null;
              }, 0);
            },
            refresh: () => refresh(),
          };
          const detach = () => {
            if (!manager) {
              return;
            }
            if (manager.entries.get(primary) === entry) {
              manager.entries.delete(primary);
              stats.registrations -= 1;
            }
            const previousRoot = root;
            const previousManager = manager;
            root = null;
            manager = null;
            releaseManager(previousRoot, previousManager);
          };
          const refresh = () => {
            if (!active) {
              return;
            }
            const nextRoot = actualRoot(primary);
            if (!nextRoot || nextRoot === root) {
              return;
            }
            detach();
            root = nextRoot;
            manager = managerFor(root);
            manager.entries.set(primary, entry);
            stats.registrations += 1;
          };
          refresh();
          return {
            refresh,
            consumeInvalidFocus(target) {
              if (target !== invalidFocus) return false;
              invalidFocus = null;
              if (invalidTimer !== null) clearTimeout(invalidTimer);
              invalidTimer = null;
              return true;
            },
            cleanup() {
              active = false;
              invalidFocus = null;
              if (invalidTimer !== null) clearTimeout(invalidTimer);
              detach();
            },
          };
        };
        globalThis[runtimeKey] = {
          generation,
          register,
          stats,
        };
      })();
"""

SPLIT_BUTTON_SUBMIT_RUNTIME_DEPENDENCY = Script(
    content=_SPLIT_BUTTON_SUBMIT_RUNTIME_SOURCE,
)

__all__: list[str] = []
