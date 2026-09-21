
      $component({
        props: {
          items: {},
          value: {},
          inputValue: {},
          open: {},
          required: {},
          disabled: {},
          readonly: {},
          invalid: {},
          loading: {},
          clearable: {},
          openOnFocus: {},
          autoHighlight: {},
          filter: {},
          minChars: {},
          debounceMs: {},
          variant: {},
          size: {},
          loadOptions: {},
          onValueChange: {},
          onInputValueChange: {},
          onOpenChange: {},
          onLoadError: {},
        },
        inject: {
          fieldService: {from: Symbol.for("citry-ui:field"), default: null},
          formService: {from: Symbol.for("citry-ui:form"), default: null},
        },
        onServerRender: ({component}) => {
          const root = component.$el;
          const data = component;
          const props = component.$props;
          const i18n = component.$i18n;
          const input = root.querySelector('[data-citry-ui-part="input"]');
          const hiddenInput = root.querySelector("[data-citry-combobox-form-value]");
          const clearButton = root.querySelector('[data-citry-ui-part="clear"]');
          const trigger = root.querySelector('[data-citry-ui-part="trigger"]');
          const popup = root.querySelector('[data-citry-ui-part="popup"]');
          const listbox = root.querySelector('[data-citry-ui-part="listbox"]');
          const loadingStatus = root.querySelector('[data-citry-ui-part="loading"]');
          const emptyStatus = root.querySelector('[data-citry-ui-part="empty"]');
          const field = component.fieldService;
          const form = component.formService;
          const nativeForm = hiddenInput.form;
          const activeRuntime = globalThis[Symbol.for("citry-ui:active-descendant-runtime")];
          if (activeRuntime?.generation !== 1) {
            throw new Error(
              "[citry-ui] CCombobox active-descendant runtime dependency did not load.",
            );
          }
          const activeCollection = activeRuntime.create({
            input,
            listbox,
            idPrefix: `${data.listboxId}-option`,
          });
          const allowedValues = {
            filter: ["contains", "starts_with", "none"],
            variant: ["outline", "filled", "plain"],
            size: ["sm", "md", "lg"],
          };
          const invalidEpisodes = new Map();
          const deferredTimers = new Set();
          const knownLabels = new Map();
          const maxKnownLabels = 1000;
          let items = data.items;
          let visibleItems = [];
          let selectedValue = data.value;
          let query = data.inputValue;
          let open = data.open;
          let highlightedValue = null;
          let querySelectionValue = data.inputValueExplicit ? null : data.value;
          let controlledValue = false;
          let controlledInput = false;
          let controlledOpen = false;
          let controlledOpenValue = null;
          let nativeInvalid = false;
          let composing = false;
          let suppressFocusOpen = false;
          let skipNextBlurHandling = false;
          let effectInitialized = false;
          let destroyed = false;
          let internalLoading = false;
          let remoteError = false;
          let debounceTimer = null;
          let requestController = null;
          let requestId = 0;
          let loader = null;
          let callbacks = {};
          let configuration = {
            required: data.required,
            disabled: data.disabled,
            readonly: data.readonly,
            invalid: data.invalid,
            loading: data.loading,
            clearable: data.clearable,
            openOnFocus: data.openOnFocus,
            autoHighlight: data.autoHighlight,
            filter: data.filter,
            minChars: data.minChars,
            debounceMs: data.debounceMs,
            variant: data.variant,
            size: data.size,
          };
          const ownsNode = (node) => (
            node instanceof Element
            && node.closest("[data-citry-combobox-root]") === root
          );

          const describeValue = (value) => {
            try {
              return JSON.stringify(value) ?? String(value);
            } catch {
              return String(value);
            }
          };
          const reportInvalid = (name, value) => {
            const describedValue = describeValue(value);
            const fingerprint = `${typeof value}:${describedValue}`;
            if (invalidEpisodes.get(name) === fingerprint) {
              return;
            }
            invalidEpisodes.set(name, fingerprint);
            console.error(
              `[citry-ui] CCombobox ${name} received invalid client value ${describedValue}; `
                + "using the previous valid or server-rendered fallback.",
              root,
            );
          };
          const reportFieldOwned = (name, value) => {
            const describedValue = describeValue(value);
            const fingerprint = `field:${typeof value}:${describedValue}`;
            if (invalidEpisodes.get(name) === fingerprint) {
              return;
            }
            invalidEpisodes.set(name, fingerprint);
            console.error(
              `[citry-ui] CCombobox ${name} is controlled by its enclosing CField; `
                + `ignoring client value ${describedValue}.`,
              root,
            );
          };
          const normalizeItems = (value, source) => {
            if (!Array.isArray(value)) {
              reportInvalid(source, value);
              return null;
            }
            const seen = new Set();
            const normalized = [];
            for (const item of value) {
              if (
                item === null
                || typeof item !== "object"
                || typeof item.value !== "string"
                || item.value.length === 0
                || typeof item.label !== "string"
                || item.label.length === 0
                || (
                  item.description !== undefined
                  && item.description !== null
                  && (typeof item.description !== "string" || item.description.length === 0)
                )
                || (item.disabled !== undefined && typeof item.disabled !== "boolean")
                || seen.has(item.value)
              ) {
                reportInvalid(source, value);
                return null;
              }
              seen.add(item.value);
              normalized.push({
                value: item.value,
                label: item.label,
                description: item.description ?? null,
                disabled: item.disabled ?? false,
              });
            }
            invalidEpisodes.delete(source);
            return normalized;
          };
          const resolveBoolean = (name, fallback) => {
            const value = props[name] === undefined ? fallback : props[name];
            if (typeof value === "boolean") {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value);
            return fallback;
          };
          const resolveInteger = (name, fallback) => {
            const value = props[name] === undefined ? fallback : props[name];
            if (Number.isInteger(value) && value >= 0) {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value);
            return fallback;
          };
          const resolveChoice = (name) => {
            const value = props[name] === undefined ? data[name] : props[name];
            if (allowedValues[name].includes(value)) {
              invalidEpisodes.delete(name);
              return value;
            }
            reportInvalid(name, value);
            return data[name];
          };
          const resolveFunction = (name) => {
            const value = props[name];
            if (value === undefined || value === null || typeof value === "function") {
              invalidEpisodes.delete(name);
              return value ?? null;
            }
            reportInvalid(name, value);
            return null;
          };
          const selectedOption = () => items.find((item) => item.value === selectedValue) ?? null;
          const selectedLabel = () => {
            if (selectedValue === null) {
              return "";
            }
            return selectedOption()?.label ?? knownLabels.get(selectedValue) ?? "";
          };
          const rememberLabels = (collection) => {
            collection.forEach((item) => {
              knownLabels.delete(item.value);
              knownLabels.set(item.value, item.label);
            });
            // Remote searches may expose unbounded identities over one long
            // component lifetime. Keep the current orphan selection but cap
            // every other historical label.
            while (knownLabels.size > maxKnownLabels) {
              let removed = false;
              for (const value of knownLabels.keys()) {
                if (value !== selectedValue) {
                  knownLabels.delete(value);
                  removed = true;
                  break;
                }
              }
              if (!removed) {
                break;
              }
            }
          };
          rememberLabels(items);
          const optionId = (value) => activeCollection.idFor(value);
          const queryLength = (value) => Array.from(value).length;
          const filterItems = () => {
            if (loader || configuration.filter === "none") {
              visibleItems = items;
              return;
            }
            if (selectedValue !== null && querySelectionValue === selectedValue) {
              visibleItems = items;
              return;
            }
            const needle = query.toLowerCase();
            visibleItems = items.filter((item) => {
              const label = item.label.toLowerCase();
              return configuration.filter === "starts_with"
                ? label.startsWith(needle)
                : label.includes(needle);
            });
          };
          const optionsUnavailable = () => (
            configuration.loading || internalLoading || remoteError
          );
          const updateOptionStates = () => {
            activeCollection.sync({
              items: visibleItems,
              activeValue: highlightedValue,
              selectedValue,
              open,
              unavailable: optionsUnavailable(),
              optionFor: (value) => Array.from(listbox.children)
                .find((element) => element.dataset.value === value),
              activeAttribute: "data-highlighted",
            });
          };
          const renderItems = ({ autoHighlight = false, highlightDirection = 1 } = {}) => {
            filterItems();
            listbox.replaceChildren();
            activeCollection.retain(visibleItems.map((item) => item.value));
            visibleItems.forEach((item) => {
              const option = document.createElement("li");
              const label = document.createElement("span");
              option.id = optionId(item.value);
              option.setAttribute("role", "option");
              option.dataset.value = item.value;
              option.dataset.citryUiPart = "option";
              option.toggleAttribute("data-disabled", item.disabled);
              if (item.disabled) {
                option.setAttribute("aria-disabled", "true");
              }
              label.dataset.citryUiPart = "option-label";
              label.textContent = item.label;
              option.append(label);
              if (item.description !== null) {
                const description = document.createElement("span");
                description.dataset.citryUiPart = "option-description";
                description.textContent = item.description;
                option.append(description);
              }
              listbox.append(option);
            });
            if (!visibleItems.some((item) => item.value === highlightedValue && !item.disabled)) {
              const enabledItems = visibleItems.filter((item) => !item.disabled);
              const highlightedItem = highlightDirection < 0
                ? enabledItems[enabledItems.length - 1]
                : enabledItems[0];
              highlightedValue = open && (autoHighlight || configuration.autoHighlight)
                ? highlightedItem?.value ?? null
                : null;
            }
            updateOptionStates();
            updatePresentation();
          };
          const idrefs = (...values) => {
            const result = [];
            values.forEach((value) => {
              if (typeof value !== "string") {
                return;
              }
              value.split(/\s+/).filter(Boolean).forEach((token) => {
                if (!result.includes(token)) {
                  result.push(token);
                }
              });
            });
            return result.join(" ") || null;
          };
          const syncRelationships = (invalid) => {
            const describedBy = idrefs(
              field?.hasDescription ? field.descriptionId : null,
              invalid && field?.hasError ? field.errorId : null,
              data.externalDescribedBy,
            );
            const errorMessage = invalid
              ? idrefs(field?.hasError ? field.errorId : null, data.externalErrorMessage)
              : null;
            if (describedBy) {
              input.setAttribute("aria-describedby", describedBy);
            } else {
              input.removeAttribute("aria-describedby");
            }
            if (errorMessage) {
              input.setAttribute("aria-errormessage", errorMessage);
            } else {
              input.removeAttribute("aria-errormessage");
            }
          };
          const updateValidity = () => {
            const missing = configuration.required && selectedValue === null;
            input.required = missing;
            input.setCustomValidity(missing ? data.requiredMessage : "");
            const invalid = configuration.invalid || nativeInvalid;
            root.toggleAttribute("data-invalid", invalid);
            if (invalid) {
              input.setAttribute("aria-invalid", "true");
            } else {
              input.removeAttribute("aria-invalid");
            }
            syncRelationships(invalid);
            field?.setNativeInvalid(nativeInvalid);
          };
          const updatePresentation = () => {
            const loading = configuration.loading || internalLoading;
            const empty = open && !loading && !remoteError && visibleItems.length === 0;
            root.toggleAttribute("data-open", open);
            root.toggleAttribute("data-loading", loading);
            root.toggleAttribute("data-empty", empty);
            root.toggleAttribute("data-error", remoteError);
            root.toggleAttribute("data-disabled", configuration.disabled);
            root.toggleAttribute("data-readonly", configuration.readonly);
            root.toggleAttribute("data-required", configuration.required);
            root.dataset.variant = configuration.variant;
            root.dataset.size = configuration.size;
            popup.hidden = !open;
            listbox.hidden = loading || remoteError || empty;
            loadingStatus.hidden = !loading;
            emptyStatus.hidden = !empty;
            clearButton.hidden = (
              !configuration.clearable
              || configuration.disabled
              || configuration.readonly
              || (!selectedValue && !query)
            );
            clearButton.disabled = configuration.disabled || configuration.readonly;
            trigger.disabled = configuration.disabled || configuration.readonly;
            input.setAttribute("aria-expanded", open ? "true" : "false");
            if (configuration.required) {
              input.setAttribute("aria-required", "true");
            } else {
              input.removeAttribute("aria-required");
            }
            trigger.setAttribute("aria-expanded", open ? "true" : "false");
            trigger.setAttribute("aria-label", open ? data.closeLabel : data.openLabel);
            listbox.setAttribute("aria-busy", loading ? "true" : "false");
            input.disabled = configuration.disabled;
            input.readOnly = configuration.readonly;
            hiddenInput.disabled = configuration.disabled;
            updateValidity();
          };
          const canOpen = () => (
            !configuration.disabled
            && !configuration.readonly
            && queryLength(query) >= configuration.minChars
          );
          const abortRequest = () => {
            if (debounceTimer !== null) {
              clearTimeout(debounceTimer);
              debounceTimer = null;
            }
            requestController?.abort();
            requestController = null;
            requestId += 1;
            internalLoading = false;
          };
          const applyOpen = (nextOpen) => {
            if (open === nextOpen) {
              return false;
            }
            open = nextOpen;
            if (!nextOpen) {
              abortRequest();
              highlightedValue = null;
              activeCollection.resetScroll();
            }
            updatePresentation();
            updateOptionStates();
            return true;
          };
          const requestOpen = (nextOpen, reason, source = null, { constraint = false } = {}) => {
            const requested = Boolean(nextOpen);
            const effective = requested && canOpen();
            if (controlledOpen) {
              if (constraint) {
                const changed = applyOpen(effective);
                if (changed && controlledOpenValue !== effective) {
                  callbacks.onOpenChange?.(effective, {
                    reason,
                    controlled: true,
                    source,
                  });
                }
                return changed;
              }
              if (requested === controlledOpenValue) {
                return applyOpen(requested && canOpen());
              }
              callbacks.onOpenChange?.(requested, {
                reason,
                controlled: true,
                source,
              });
              return false;
            }
            const changed = applyOpen(effective);
            if (changed) {
              callbacks.onOpenChange?.(effective, {
                reason,
                controlled: false,
                source,
              });
            }
            return changed;
          };
          const scheduleLoad = (
            openReason = "input",
            source = input,
            highlightDirection = 1,
          ) => {
            abortRequest();
            remoteError = false;
            highlightedValue = null;
            if (configuration.disabled || configuration.readonly) {
              applyOpen(false);
              renderItems();
              return;
            }
            if (queryLength(query) < configuration.minChars) {
              requestOpen(false, "minimum-characters", source, { constraint: true });
              renderItems();
              return;
            }
            if (!loader) {
              requestOpen(true, openReason, source);
              renderItems({
                autoHighlight: openReason === "keyboard",
                highlightDirection,
              });
              return;
            }
            const currentId = requestId;
            const requestedQuery = query;
            const controller = new AbortController();
            requestController = controller;
            internalLoading = true;
            updatePresentation();
            updateOptionStates();
            requestOpen(true, openReason, source);
            debounceTimer = setTimeout(async () => {
              debounceTimer = null;
              try {
                const result = await loader({
                  query: requestedQuery,
                  signal: controller.signal,
                  requestId: currentId,
                });
                if (controller.signal.aborted || requestId !== currentId) {
                  return;
                }
                const normalized = normalizeItems(result, "loadOptions result");
                if (normalized === null) {
                  throw new TypeError("loadOptions returned an invalid item collection.");
                }
                items = normalized;
                rememberLabels(items);
                if (
                  !controlledInput
                  && selectedValue !== null
                  && querySelectionValue === selectedValue
                ) {
                  query = selectedLabel();
                  input.value = query;
                }
                internalLoading = false;
                requestController = null;
                renderItems({
                  autoHighlight: openReason === "keyboard",
                  highlightDirection,
                });
              } catch (error) {
                if (controller.signal.aborted || requestId !== currentId) {
                  return;
                }
                internalLoading = false;
                requestController = null;
                remoteError = true;
                renderItems();
                callbacks.onLoadError?.(error, {
                  query: requestedQuery,
                  requestId: currentId,
                });
              }
            }, configuration.debounceMs);
          };
          const requestInputValue = (
            nextQuery,
            reason,
            source = null,
            { load = true, selectionValue = null } = {},
          ) => {
            if (nextQuery === query) {
              input.value = query;
              if (!controlledInput) {
                querySelectionValue = selectionValue;
              }
              return false;
            }
            if (controlledInput) {
              callbacks.onInputValueChange?.(nextQuery, {
                reason,
                controlled: true,
                source,
              });
              queueMicrotask(() => {
                if (!destroyed) {
                  input.value = query;
                }
              });
              return false;
            }
            query = nextQuery;
            input.value = query;
            querySelectionValue = selectionValue;
            callbacks.onInputValueChange?.(nextQuery, {
              reason,
              controlled: false,
              source,
            });
            if (load) {
              scheduleLoad("input", source ?? input);
            } else {
              renderItems();
            }
            return true;
          };
          const reconcileSelectedQuery = (source) => {
            const label = selectedLabel();
            if (selectedValue !== null && query !== label) {
              requestInputValue(label, "blur", source, {
                load: false,
                selectionValue: selectedValue,
              });
            }
          };
          const suppressNextBlur = () => {
            skipNextBlurHandling = true;
            const timer = setTimeout(() => {
              deferredTimers.delete(timer);
              skipNextBlurHandling = false;
            }, 0);
            deferredTimers.add(timer);
          };
          const requestValue = (nextValue, option, reason, source = null) => {
            if (nextValue === selectedValue) {
              return false;
            }
            if (controlledValue) {
              callbacks.onValueChange?.(nextValue, {
                reason,
                option,
                query,
                controlled: true,
                source,
              });
              return false;
            }
            selectedValue = nextValue;
            hiddenInput.value = nextValue ?? "";
            if (option) {
              knownLabels.set(option.value, option.label);
            }
            updateValidity();
            updateOptionStates();
            callbacks.onValueChange?.(nextValue, {
              reason,
              option,
              query,
              controlled: false,
              source,
            });
            return true;
          };
          const selectOption = (option, source = input) => {
            if (
              !option
              || option.disabled
              || configuration.disabled
              || configuration.readonly
              || optionsUnavailable()
            ) {
              return;
            }
            nativeInvalid = false;
            const committed = requestValue(option.value, option, "option", source);
            requestInputValue(option.label, "option", source, {
              load: false,
              selectionValue: option.value,
            });
            requestOpen(false, "selection", source);
            if (committed) {
              input.dispatchEvent(new Event("change", { bubbles: true }));
            }
          };
          const clearSelection = (source = clearButton) => {
            if (configuration.disabled || configuration.readonly) {
              return;
            }
            nativeInvalid = false;
            const committed = requestValue(null, null, "clear", source);
            requestInputValue("", "clear", source, { load: false });
            requestOpen(false, "selection", source);
            if (committed) {
              input.dispatchEvent(new Event("change", { bubbles: true }));
            }
            suppressFocusOpen = true;
            input.focus({ preventScroll: true });
            queueMicrotask(() => {
              suppressFocusOpen = false;
            });
          };
          const moveHighlight = (delta) => {
            if (optionsUnavailable()) {
              highlightedValue = null;
              updateOptionStates();
              return;
            }
            highlightedValue = activeCollection.move(
              visibleItems,
              highlightedValue,
              delta,
              true,
            );
            updateOptionStates();
          };
          const applyUserInput = (source) => {
            nativeInvalid = false;
            if (selectedValue !== null) {
              requestValue(null, null, "input", source);
            }
            requestInputValue(input.value, "input", source);
            updateValidity();
          };
          const onInput = (event) => {
            if (!composing) {
              applyUserInput(event.target);
            }
          };
          const onCompositionStart = () => {
            composing = true;
          };
          const onCompositionEnd = () => {
            composing = false;
            applyUserInput(input);
          };
          const onKeyDown = (event) => {
            if (configuration.disabled || configuration.readonly || composing) {
              return;
            }
            if (event.key === "ArrowDown" || event.key === "ArrowUp") {
              if (!canOpen()) {
                return;
              }
              event.preventDefault();
              if (!open) {
                if (loader) {
                  scheduleLoad(
                    "keyboard",
                    event.target,
                    event.key === "ArrowDown" ? 1 : -1,
                  );
                } else {
                  renderItems();
                  requestOpen(true, "keyboard", event.target);
                }
              }
              if (open) {
                moveHighlight(event.key === "ArrowDown" ? 1 : -1);
              }
              return;
            }
            if (
              event.key === "Enter"
              && open
              && !optionsUnavailable()
              && highlightedValue !== null
            ) {
              const option = visibleItems.find((item) => item.value === highlightedValue);
              if (option && !option.disabled) {
                event.preventDefault();
                selectOption(option, event.target);
              }
              return;
            }
            if (event.key === "Escape" && open) {
              event.preventDefault();
              requestOpen(false, "escape", event.target);
              return;
            }
            if (event.key === "Tab" && open) {
              reconcileSelectedQuery(event.target);
              suppressNextBlur();
              requestOpen(false, "blur", event.target);
              return;
            }
            if (
              open
              && !optionsUnavailable()
              && !event.altKey
              && !event.ctrlKey
              && !event.metaKey
              && (event.key === "Home" || event.key === "End")
            ) {
              event.preventDefault();
              highlightedValue = activeCollection.edge(
                visibleItems,
                event.key === "Home" ? 1 : -1,
              );
              updateOptionStates();
            }
          };
          const onInvalid = () => {
            nativeInvalid = true;
            updateValidity();
          };
          const onFocus = (event) => {
            if (
              suppressFocusOpen
              || !configuration.openOnFocus
              || !canOpen()
              || open
            ) {
              return;
            }
            if (loader) {
              scheduleLoad("focus", event.target);
            } else {
              requestOpen(true, "focus", event.target);
              renderItems();
            }
          };
          const onBlur = (event) => {
            const skipHandling = skipNextBlurHandling;
            skipNextBlurHandling = false;
            queueMicrotask(() => {
              if (destroyed || root.contains(document.activeElement)) {
                return;
              }
              if (!skipHandling) {
                reconcileSelectedQuery(event.target);
                requestOpen(false, "blur", event.target);
              }
            });
          };
          const onRootClick = (event) => {
            const clear = event.target.closest?.("[data-citry-combobox-clear]");
            if (clear && ownsNode(clear)) {
              clearSelection(clear);
              return;
            }
            const ownedTrigger = event.target.closest?.("[data-citry-combobox-trigger]");
            if (ownedTrigger && ownsNode(ownedTrigger)) {
              if (configuration.disabled || configuration.readonly) {
                return;
              }
              const nextOpen = !open;
              suppressFocusOpen = true;
              input.focus({ preventScroll: true });
              queueMicrotask(() => {
                suppressFocusOpen = false;
              });
              if (!nextOpen) {
                requestOpen(false, "trigger", ownedTrigger);
              } else if (loader) {
                scheduleLoad("trigger", ownedTrigger);
              } else {
                requestOpen(true, "trigger", ownedTrigger);
                renderItems();
              }
            }
          };
          const onListboxPointerDown = (event) => {
            const element = event.target.closest?.('[data-citry-ui-part="option"]');
            if (element && element.parentElement === listbox) {
              event.preventDefault();
            }
          };
          const onListboxPointerMove = (event) => {
            const element = event.target.closest?.('[data-citry-ui-part="option"]');
            if (
              !element
              || element.parentElement !== listbox
              || element.hasAttribute("data-disabled")
            ) {
              return;
            }
            highlightedValue = element.dataset.value;
            updateOptionStates();
          };
          const onListboxClick = (event) => {
            const element = event.target.closest?.('[data-citry-ui-part="option"]');
            if (!element || element.parentElement !== listbox) {
              return;
            }
            const option = visibleItems.find((item) => item.value === element?.dataset.value);
            selectOption(option, element);
          };
          const onDocumentPointerDown = (event) => {
            if (open && !root.contains(event.target)) {
              if (root.contains(document.activeElement)) {
                suppressNextBlur();
              }
              reconcileSelectedQuery(event.target);
              requestOpen(false, "outside", event.target);
            }
          };
          const onReset = (event) => {
            // The native reset event is cancelable. Defer component-owned
            // value restoration until every reset listener has run.
            const timer = setTimeout(() => {
              deferredTimers.delete(timer);
              if (event.defaultPrevented) {
                return;
              }
              abortRequest();
              remoteError = false;
              nativeInvalid = false;
              if (!controlledValue) {
                requestValue(data.value, items.find((item) => item.value === data.value) ?? null, "reset", nativeForm);
              } else {
                hiddenInput.value = selectedValue ?? "";
              }
              if (!controlledInput) {
                requestInputValue(data.inputValue, "reset", nativeForm, {
                  load: false,
                  selectionValue: data.inputValueExplicit ? null : data.value,
                });
              } else {
                input.value = query;
              }
              if (!controlledOpen) {
                requestOpen(false, "reset", nativeForm);
              } else {
                applyOpen(Boolean(controlledOpenValue) && canOpen());
              }
              renderItems();
              updateValidity();
            }, 0);
            deferredTimers.add(timer);
          };

          root.addEventListener("click", onRootClick);
          input.addEventListener("input", onInput);
          input.addEventListener("focus", onFocus);
          input.addEventListener("keydown", onKeyDown);
          input.addEventListener("invalid", onInvalid);
          input.addEventListener("blur", onBlur);
          input.addEventListener("compositionstart", onCompositionStart);
          input.addEventListener("compositionend", onCompositionEnd);
          listbox.addEventListener("pointerdown", onListboxPointerDown);
          listbox.addEventListener("pointermove", onListboxPointerMove);
          listbox.addEventListener("click", onListboxClick);
          document.addEventListener("pointerdown", onDocumentPointerDown, true);
          nativeForm?.addEventListener("reset", onReset);
          Citry.vue.watchEffect(() => {
            const firstRun = !effectInitialized;
            let collectionChanged = false;
            let loaderChanged = false;
            let ownerValueChanged = false;
            let ownerQueryChanged = false;
            let required;
            let disabled;
            let readonly;
            let invalid;
            if (field) {
              ["required", "disabled", "readonly", "invalid"].forEach((name) => {
                if (props[name] !== undefined) {
                  reportFieldOwned(name, props[name]);
                } else {
                  invalidEpisodes.delete(name);
                }
              });
              required = field.required;
              disabled = field.disabled;
              readonly = field.readonly;
              invalid = field.invalid;
            } else {
              required = resolveBoolean("required", data.required);
              disabled = Boolean(form?.disabled) || resolveBoolean("disabled", data.disabled);
              const readonlyFallback = data.inheritsReadonly && form ? form.readonly : data.readonly;
              readonly = resolveBoolean("readonly", readonlyFallback);
              invalid = resolveBoolean("invalid", data.invalid);
            }
            configuration = {
              required,
              disabled,
              readonly,
              invalid,
              loading: resolveBoolean("loading", data.loading),
              clearable: resolveBoolean("clearable", data.clearable),
              openOnFocus: resolveBoolean("openOnFocus", data.openOnFocus),
              autoHighlight: resolveBoolean("autoHighlight", data.autoHighlight),
              filter: resolveChoice("filter"),
              minChars: resolveInteger("minChars", data.minChars),
              debounceMs: resolveInteger("debounceMs", data.debounceMs),
              variant: resolveChoice("variant"),
              size: resolveChoice("size"),
            };
            const nextLoader = resolveFunction("loadOptions");
            if (effectInitialized && nextLoader !== loader) {
              loaderChanged = true;
              abortRequest();
              remoteError = false;
            }
            loader = nextLoader;
            callbacks = {
              onValueChange: resolveFunction("onValueChange"),
              onInputValueChange: resolveFunction("onInputValueChange"),
              onOpenChange: resolveFunction("onOpenChange"),
              onLoadError: resolveFunction("onLoadError"),
            };

            if (props.items === undefined) {
              invalidEpisodes.delete("items");
            } else {
              const normalized = normalizeItems(props.items, "items");
              if (normalized !== null) {
                items = normalized;
                rememberLabels(items);
                collectionChanged = true;
              }
            }

            const suppliedValue = props.value;
            if (suppliedValue === undefined) {
              controlledValue = false;
              invalidEpisodes.delete("value");
            } else if (
              suppliedValue === null
              || (typeof suppliedValue === "string" && suppliedValue.length > 0)
            ) {
              controlledValue = true;
              if (selectedValue !== suppliedValue) {
                selectedValue = suppliedValue;
                ownerValueChanged = true;
                nativeInvalid = false;
              }
              hiddenInput.value = suppliedValue ?? "";
              invalidEpisodes.delete("value");
            } else {
              controlledValue = false;
              reportInvalid("value", suppliedValue);
            }

            const suppliedInput = props.inputValue;
            if (suppliedInput === undefined || suppliedInput === null) {
              controlledInput = false;
              invalidEpisodes.delete("inputValue");
            } else if (typeof suppliedInput === "string") {
              controlledInput = true;
              querySelectionValue = null;
              if (query !== suppliedInput) {
                query = suppliedInput;
                input.value = suppliedInput;
                ownerQueryChanged = true;
                nativeInvalid = false;
              }
              invalidEpisodes.delete("inputValue");
            } else {
              controlledInput = false;
              reportInvalid("inputValue", suppliedInput);
            }

            // A parent commonly commits the selected value and its display
            // label together. Treat that as selection synchronization, not a
            // new search that should reopen the popup or call the loader.
            if (
              ownerValueChanged
              && ownerQueryChanged
              && suppliedInput === selectedLabel()
            ) {
              ownerQueryChanged = false;
            }

            if (!controlledInput && ownerValueChanged) {
              query = selectedLabel();
              input.value = query;
              querySelectionValue = selectedValue;
            } else if (
              !controlledInput
              && collectionChanged
              && selectedValue !== null
              && querySelectionValue === selectedValue
            ) {
              query = selectedLabel();
              input.value = query;
            }

            const suppliedOpen = props.open;
            if (suppliedOpen === undefined || suppliedOpen === null) {
              controlledOpen = false;
              controlledOpenValue = null;
              invalidEpisodes.delete("open");
            } else if (typeof suppliedOpen === "boolean") {
              controlledOpen = true;
              controlledOpenValue = suppliedOpen;
              invalidEpisodes.delete("open");
            } else {
              controlledOpen = false;
              controlledOpenValue = null;
              reportInvalid("open", suppliedOpen);
            }

            if (configuration.disabled || configuration.readonly) {
              abortRequest();
              highlightedValue = null;
              applyOpen(false);
            } else if (controlledOpen) {
              applyOpen(Boolean(controlledOpenValue) && canOpen());
            } else if (!canOpen() && open) {
              if (firstRun) {
                applyOpen(false);
              } else {
                requestOpen(false, "minimum-characters", input, { constraint: true });
              }
            }
            renderItems();
            input.value = query;
            hiddenInput.value = selectedValue ?? "";
            effectInitialized = true;
            const shouldLoadInitialQuery = firstRun && loader && open && canOpen();
            const shouldLoadReplacement = loaderChanged && loader && open && canOpen();
            if (
              (ownerQueryChanged && !firstRun)
              || shouldLoadInitialQuery
              || shouldLoadReplacement
            ) {
              const expectedQuery = query;
              queueMicrotask(() => {
                if (
                  !destroyed
                  && query === expectedQuery
                  && (!(shouldLoadInitialQuery || shouldLoadReplacement) || open)
                ) {
                  scheduleLoad("input", input);
                }
              });
            }
          });
          const i18nBindings = [];
          if (i18n && data.catalogRequiredMessage) {
            i18nBindings.push(i18n.bind({
              message: "citry-ui-combobox-required",
              onChange: (text) => {
                data.requiredMessage = text;
                updateValidity();
              },
            }));
          }
          if (i18n && data.catalogOpenLabel) {
            i18nBindings.push(i18n.bind({
              message: "citry-ui-combobox-open",
              onChange: (text) => {
                data.openLabel = text;
                updatePresentation();
              },
            }));
          }
          if (i18n && data.catalogCloseLabel) {
            i18nBindings.push(i18n.bind({
              message: "citry-ui-combobox-close",
              onChange: (text) => {
                data.closeLabel = text;
                updatePresentation();
              },
            }));
          }
          root.setAttribute("data-citry-combobox-initialized", "");

          return () => {
            destroyed = true;
            abortRequest();
            root.removeEventListener("click", onRootClick);
            input.removeEventListener("input", onInput);
            input.removeEventListener("focus", onFocus);
            input.removeEventListener("keydown", onKeyDown);
            input.removeEventListener("invalid", onInvalid);
            input.removeEventListener("blur", onBlur);
            input.removeEventListener("compositionstart", onCompositionStart);
            input.removeEventListener("compositionend", onCompositionEnd);
            listbox.removeEventListener("pointerdown", onListboxPointerDown);
            listbox.removeEventListener("pointermove", onListboxPointerMove);
            listbox.removeEventListener("click", onListboxClick);
            document.removeEventListener("pointerdown", onDocumentPointerDown, true);
            nativeForm?.removeEventListener("reset", onReset);
            for (const timer of deferredTimers) {
              clearTimeout(timer);
            }
            deferredTimers.clear();
            field?.setNativeInvalid(false);
            activeCollection.cleanup();
            i18nBindings.forEach((binding) => binding.dispose());
            listbox.replaceChildren();
            root.removeAttribute("data-citry-combobox-initialized");
          };
        },
      });
    