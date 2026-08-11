(function () {
  "use strict";

  const FORMAT = "citry-i18n-provider-research/1";
  const SERVICE_KEY = "citry_i18n";
  let configuration = null;

  function reject(code, message) {
    const error = new TypeError(`[Citry] i18n provider: ${message}`);
    error.code = code;
    throw error;
  }

  function exactObject(value, code, name) {
    if (value === null || typeof value !== "object" || Array.isArray(value)) {
      reject(code, `${name} must be an object.`);
    }
    return value;
  }

  function immutableContext(value) {
    const record = exactObject(value, "I18N_PROVIDER_CONTEXT_INVALID", "the locale context");
    if (
      typeof record.locale !== "string"
      || (record.direction !== "ltr" && record.direction !== "rtl")
      || !(record.timeZone === null || typeof record.timeZone === "string")
    ) {
      reject("I18N_PROVIDER_CONTEXT_INVALID", "the locale context has invalid fields.");
    }
    return Object.freeze({
      direction: record.direction,
      locale: record.locale,
      timeZone: record.timeZone,
    });
  }

  function validateFieldPolicy(value, field) {
    const policy = exactObject(value, "I18N_PROVIDER_POLICY_INVALID", `${field} policy`);
    if (!(["clear", "explicit", "inherit"].includes(policy.mode))) {
      reject("I18N_PROVIDER_POLICY_INVALID", `${field} policy has an unknown mode.`);
    }
    if (policy.mode === "explicit" && typeof policy.value !== "string") {
      reject("I18N_PROVIDER_POLICY_INVALID", `${field} explicit policy needs a string value.`);
    }
    if (policy.mode !== "explicit" && Object.hasOwn(policy, "value")) {
      reject("I18N_PROVIDER_POLICY_INVALID", `${field} ${policy.mode} policy cannot carry a value.`);
    }
    return Object.freeze(policy.mode === "explicit" ? { mode: policy.mode, value: policy.value } : { mode: policy.mode });
  }

  function validatePolicy(value) {
    const policy = exactObject(value, "I18N_PROVIDER_POLICY_INVALID", "the provider policy");
    const validated = {
      direction: validateFieldPolicy(policy.direction, "direction"),
      locale: validateFieldPolicy(policy.locale, "locale"),
      timeZone: validateFieldPolicy(policy.timeZone, "timeZone"),
    };
    if (validated.locale.mode === "clear" || validated.direction.mode === "clear") {
      reject("I18N_PROVIDER_POLICY_INVALID", "locale and direction do not support an explicit clear.");
    }
    return Object.freeze(validated);
  }

  function contextForLocale(locale) {
    const value = configuration.manifest.contexts[locale];
    if (value === undefined) reject("I18N_PROVIDER_LOCALE_INVALID", `locale '${locale}' is not selectable.`);
    return immutableContext(value);
  }

  function resolvePolicy(parentContext, policy) {
    let locale;
    if (policy.locale.mode === "explicit") locale = policy.locale.value;
    else if (policy.locale.mode === "inherit" && parentContext !== null) locale = parentContext.locale;
    else reject("I18N_PROVIDER_POLICY_INVALID", "a root provider needs an explicit locale.");

    const localeDefault = contextForLocale(locale);
    let direction;
    if (policy.direction.mode === "explicit") direction = policy.direction.value;
    else if (policy.locale.mode === "explicit") direction = localeDefault.direction;
    else direction = parentContext === null ? localeDefault.direction : parentContext.direction;
    if (direction !== "ltr" && direction !== "rtl") {
      reject("I18N_PROVIDER_POLICY_INVALID", "an explicit direction must be 'ltr' or 'rtl'.");
    }

    let timeZone;
    if (policy.timeZone.mode === "explicit") timeZone = policy.timeZone.value;
    else if (policy.timeZone.mode === "clear") timeZone = null;
    else timeZone = parentContext === null ? localeDefault.timeZone : parentContext.timeZone;
    return immutableContext({ direction, locale, timeZone });
  }

  function contextsEqual(left, right) {
    return left.locale === right.locale
      && left.direction === right.direction
      && left.timeZone === right.timeZone;
  }

  function validateArtifact(artifact, locale) {
    const value = exactObject(artifact, "I18N_PROVIDER_ARTIFACT_INVALID", "the locale artifact");
    if (value.revision !== configuration.manifest.revision || value.locale !== locale) {
      reject("I18N_PROVIDER_ARTIFACT_INVALID", "the locale artifact revision or locale does not match.");
    }
    exactObject(value.catalogs, "I18N_PROVIDER_ARTIFACT_INVALID", "the locale artifact catalogs");
    return value;
  }

  function stageTree(root, rootContext, artifact) {
    const staged = [];
    function visit(internal, context) {
      const catalog = artifact.catalogs[context.locale];
      if (catalog === undefined) {
        reject("I18N_PROVIDER_ARTIFACT_INVALID", `the artifact lacks locale '${context.locale}'.`);
      }
      const sinkValues = internal.sinks.map((sink) => {
        if (!Object.hasOwn(catalog, sink.id) || typeof catalog[sink.id] !== "string") {
          reject("I18N_PROVIDER_MESSAGE_INVALID", `message '${sink.id}' is absent from '${context.locale}'.`);
        }
        return { sink, value: catalog[sink.id] };
      });
      staged.push({ context, internal, sinkValues });
      for (const child of internal.children) visit(child, resolvePolicy(context, child.policy));
    }
    visit(root, rootContext);
    return staged;
  }

  function commitTree(staged) {
    for (const item of staged) {
      item.internal.wrapper.setAttribute("lang", item.context.locale);
      item.internal.wrapper.setAttribute("dir", item.context.direction);
      for (const { sink, value } of item.sinkValues) {
        if (!sink.element.isConnected || !item.internal.wrapper.contains(sink.element)) {
          reject("I18N_PROVIDER_SINK_STALE", `message sink '${sink.id}' is no longer owned by its provider.`);
        }
        sink.element.textContent = value;
      }
      item.internal.state.context = item.context;
      item.internal.state.status = Object.freeze({ phase: "ready" });
      for (const callback of item.internal.subscribers) callback(item.context);
    }
  }

  function createService(internal) {
    const service = {
      bindMessage(id, element) {
        if (typeof id !== "string" || !configuration.manifest.clientMessages.includes(id)) {
          reject("I18N_PROVIDER_MESSAGE_INVALID", "bindMessage() received an undeclared message ID.");
        }
        if (!(element instanceof HTMLElement) || !internal.wrapper.contains(element)) {
          reject("I18N_PROVIDER_SINK_INVALID", "bindMessage() needs an owned live element.");
        }
        const sink = { element, id };
        internal.sinks.push(sink);
        const initial = configuration.manifest.catalogs[internal.state.context.locale]?.[id];
        if (typeof initial !== "string") {
          reject("I18N_PROVIDER_MESSAGE_INVALID", `the initial catalog lacks message '${id}'.`);
        }
        element.textContent = initial;
        return Object.freeze({ dispose: () => {
          const index = internal.sinks.indexOf(sink);
          if (index !== -1) internal.sinks.splice(index, 1);
        } });
      },
      subscribe(callback) {
        if (typeof callback !== "function") reject("I18N_PROVIDER_SUBSCRIBER_INVALID", "subscribe() needs a function.");
        internal.subscribers.add(callback);
        callback(internal.state.context);
        return () => internal.subscribers.delete(callback);
      },
      async switchLocale(input) {
        if (typeof input !== "string" || !Object.hasOwn(configuration.manifest.aliases, input)) {
          reject("I18N_PROVIDER_LOCALE_INVALID", `locale alias '${String(input)}' is not selectable.`);
        }
        const locale = configuration.manifest.aliases[input];
        internal.generation += 1;
        const generation = internal.generation;
        internal.state.status = Object.freeze({ phase: "loading", target: locale });
        let artifact;
        try {
          artifact = validateArtifact(await configuration.load(locale, generation), locale);
        } catch (error) {
          if (generation !== internal.generation) return Object.freeze({ status: "stale" });
          internal.state.status = Object.freeze({ error: error.code || error.message, phase: "error" });
          throw error;
        }
        if (generation !== internal.generation) return Object.freeze({ status: "stale" });
        const rootContext = immutableContext({
          ...contextForLocale(locale),
          timeZone: internal.state.context.timeZone,
        });
        const staged = stageTree(internal, rootContext, artifact);
        commitTree(staged);
        return Object.freeze({ context: internal.state.context, status: "committed" });
      },
    };
    Object.defineProperties(service, {
      context: { enumerable: true, get: () => internal.state.context },
      status: { enumerable: true, get: () => internal.state.status },
    });
    return Object.freeze(service);
  }

  function mount(context) {
    if (configuration === null) reject("I18N_PROVIDER_NOT_CONFIGURED", "configure() must run before mount().");
    const data = exactObject(context.data, "I18N_PROVIDER_DATA_INVALID", "provider browser data");
    const wrapper = Array.isArray(context.els) && context.els.length === 1 ? context.els[0] : null;
    if (!(wrapper instanceof HTMLElement) || !wrapper.isConnected) {
      reject("I18N_PROVIDER_WRAPPER_INVALID", "a client provider needs one live real-element wrapper.");
    }
    const parentService = context.inject(SERVICE_KEY, null);
    const parentInternal = parentService === null ? null : configuration.internals.get(parentService);
    if (parentService !== null && parentInternal === undefined) {
      reject("I18N_PROVIDER_PARENT_INVALID", "the inherited i18n service is not owned by this runtime.");
    }
    const policy = validatePolicy(data.policy);
    const resolved = resolvePolicy(parentInternal?.state.context || null, policy);
    const serverResolved = immutableContext(data.resolved);
    if (!contextsEqual(resolved, serverResolved)) {
      reject("I18N_PROVIDER_CONTEXT_MISMATCH", "the server and browser provider contexts differ.");
    }
    const state = context.reactive({
      context: resolved,
      status: Object.freeze({ phase: "ready" }),
    });
    const internal = {
      children: new Set(),
      generation: 0,
      name: data.name,
      parent: parentInternal || null,
      policy,
      service: null,
      sinks: [],
      state,
      subscribers: new Set(),
      wrapper,
    };
    const service = createService(internal);
    internal.service = service;
    configuration.internals.set(service, internal);
    if (parentInternal) parentInternal.children.add(internal);
    context.provide(SERVICE_KEY, service);
    configuration.publicServices[data.name] = service;
    return () => {
      if (parentInternal) parentInternal.children.delete(internal);
      delete configuration.publicServices[data.name];
    };
  }

  function configure(options) {
    if (configuration !== null) reject("I18N_PROVIDER_ALREADY_CONFIGURED", "configure() may run only once.");
    const value = exactObject(options, "I18N_PROVIDER_CONFIG_INVALID", "provider configuration");
    const manifest = exactObject(value.manifest, "I18N_PROVIDER_CONFIG_INVALID", "the client manifest");
    if (typeof value.load !== "function" || typeof manifest.revision !== "string") {
      reject("I18N_PROVIDER_CONFIG_INVALID", "the client manifest or loader is invalid.");
    }
    configuration = {
      internals: new WeakMap(),
      load: value.load,
      manifest,
      publicServices: value.publicServices,
    };
  }

  globalThis.CitryI18nProviderCandidate = Object.freeze({ FORMAT, SERVICE_KEY, configure, mount });
})();
