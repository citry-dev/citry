/* Experimental private Citry/Vue runtime. Not a public package API. */
(function (global) {
  "use strict";
  const V = global.Vue;
  if (!V) throw new Error("Vue runtime must load before Citry's private Vue client");
  const citryNamespace = global.Citry === undefined ? {} : global.Citry;
  if ((typeof citryNamespace !== "object" || citryNamespace === null) && typeof citryNamespace !== "function")
    throw new TypeError("the global Citry namespace must be an object");
  if (Object.prototype.hasOwnProperty.call(citryNamespace, "vue")) {
    if (citryNamespace.vue !== V) throw new Error("the global Citry.vue namespace uses a different Vue runtime");
  } else {
    Object.defineProperty(citryNamespace, "vue", {value: V, enumerable: true, configurable: false, writable: false});
  }
  if (global.Citry === undefined) global.Citry = citryNamespace;
  const HELPER_CONTRACT = "b07c87b430051e17febc97559c81ee2384fec3608e510c7a517de3003e636ed5";
  if (global.CitryStable) {
    if (global.CitryStable.compilerRuntime?.helperContract !== HELPER_CONTRACT)
      throw new Error("an incompatible Citry Vue runtime is already loaded");
    return;
  }

  const apps = new Map();
  const registeredTypeOptions = new Map();
  const browserPluginFactories = new Map();
  const instanceRecords = new WeakMap();
  const publicEventsConfig = Object.create(null);
  const publicEventTransports = new Map();
  const publicTargetMatches = target => {
    const matches = [];
    for (const app of apps.values()) {
      const source = app.resolvePublicTarget?.(target);
      if (source) matches.push({app, source});
    }
    return matches;
  };
  let publicSend = (target, name, args, opts) => {
    const matches = publicTargetMatches(target);
    if (matches.length === 0)
      return Promise.reject(new Error("Citry.events.send found no current mounted prepared Vue component for its target."));
    if (matches.length > 1)
      return Promise.reject(new Error("Citry.events.send found multiple current mounted prepared Vue components for its target."));
    return matches[0].app.publicSend?.(matches[0].source, name, args, opts);
  };
  let publicApplyActions = actions => {
    let checked;
    try {
      checked = snapshotPublicActions(actions);
    } catch (error) {
      return Promise.reject(error);
    }
    const targets = checked.map(action => {
      if (!action || typeof action !== "object") return null;
      if (action.action === "state") return `render:${action.targetRenderId}`;
      return action.action === "render" || action.action === "event" ? action.target : null;
    }).filter(target => typeof target === "string");
    const owners = [];
    for (const target of targets) {
      // A marker is caller-relative: its first segment identifies the
      // component whose render response owns the marker.
      const marker = /^mark:([^:]+):/.exec(target);
      const lookup = marker ? `render:${marker[1]}` : target;
      const matches = publicTargetMatches(lookup);
      if (matches.length === 0)
        return Promise.reject(new Error(`Citry.events.applyActions target '${target}' is stale or retired.`));
      if (matches.length > 1)
        return Promise.reject(new Error(`Citry.events.applyActions target '${target}' matches multiple mounted prepared Vue components.`));
      owners.push(matches[0]);
    }
    if (owners.length) {
      const app = owners[0].app;
      if (owners.some(owner => owner.app !== app))
        return Promise.reject(new Error("Citry.events.applyActions cannot combine targets from different Vue apps."));
      return app.publicApplyActions?.(checked, owners[0].source);
    }
    return applyPublicActionsWithoutApp(checked);
  };
  const publicEvents = {
    send(target, name, args, opts) {
      return publicSend(target, name, args, opts);
    },
    on(name, callback) {
      if (typeof name !== "string" || name.length === 0) throw new TypeError("Citry.events.on needs a non-empty event name");
      if (typeof callback !== "function") throw new TypeError("Citry.events.on needs a callback function");
      const listener = event => callback(event.detail);
      document.addEventListener(name, listener);
      return () => document.removeEventListener(name, listener);
    },
    configure(options = {}) {
      plain(options, "Citry.events.configure options");
      if (options.csrf !== undefined) plain(options.csrf, "Citry.events.configure csrf");
      Object.assign(publicEventsConfig, options);
      if (options.csrf !== undefined)
        publicEventsConfig.csrf = {...options.csrf};
    },
    registerTransport(name, implementation) {
      if (typeof name !== "string" || name.length === 0) throw new TypeError("Citry.events.registerTransport needs a non-empty name");
      if (!implementation || typeof implementation.send !== "function")
        throw new TypeError("Citry.events.registerTransport needs an implementation with send(envelope)");
      publicEventTransports.set(name, implementation);
    },
    applyActions(actions) {
      return publicApplyActions(actions);
    },
  };
  if (Object.prototype.hasOwnProperty.call(citryNamespace, "events") && citryNamespace.events !== undefined) {
    if (!citryNamespace.events || typeof citryNamespace.events !== "object")
      throw new TypeError("the global Citry.events namespace must be an object");
    Object.assign(citryNamespace.events, publicEvents);
  } else {
    Object.defineProperty(citryNamespace, "events", {value: publicEvents, enumerable: true, configurable: true, writable: true});
  }
  const own = (value, key) => Object.prototype.hasOwnProperty.call(value, key);
  const plain = (value, name) => {
    if (!value || Object.getPrototypeOf(value) !== Object.prototype) throw new TypeError(name + " must be a plain object");
    return value;
  };
  const has = (value, key) => Object.prototype.hasOwnProperty.call(value, key);
  const knownActionKinds = new Set(["render", "data", "state", "event", "redirect", "url"]);
  const knownSwaps = new Set(["morph", "replace", "inner", "append", "prepend", "remove", "none"]);
  const knownRenderers = new Set(["html-fragment/1", "vue-prepared/1"]);
  const safeRenderId = value => typeof value === "string" && /^[a-z0-9_-]+$/.test(value);
  const strictPublicJson = (value, path = "", ancestors = new Set()) => {
    if (value === null || typeof value === "string" || typeof value === "boolean") return;
    if (typeof value === "number") {
      if (!Number.isFinite(value)) throw new TypeError(`Citry.events.applyActions received non-finite JSON at ${path || "/"}`);
      return;
    }
    if (typeof value !== "object") throw new TypeError(`Citry.events.applyActions received non-JSON data at ${path || "/"}`);
    const prototype = Object.getPrototypeOf(value);
    if (prototype !== Object.prototype && prototype !== null && !Array.isArray(value))
      throw new TypeError(`Citry.events.applyActions received a non-JSON object at ${path || "/"}`);
    if (Object.getOwnPropertySymbols(value).length)
      throw new TypeError(`Citry.events.applyActions received symbol-keyed data at ${path || "/"}`);
    if (ancestors.has(value)) throw new TypeError(`Citry.events.applyActions received cyclic data at ${path || "/"}`);
    for (const name of Object.getOwnPropertyNames(value)) {
      if (Array.isArray(value) && name === "length") continue;
      const descriptor = Object.getOwnPropertyDescriptor(value, name);
      if (!descriptor?.enumerable || !("value" in descriptor))
        throw new TypeError(`Citry.events.applyActions received accessor or non-enumerable data at ${path || "/"}`);
    }
    if (Array.isArray(value)) {
      const names = Object.keys(value);
      if (names.length !== value.length || names.some((name, index) => name !== String(index)))
        throw new TypeError(`Citry.events.applyActions received a sparse or named array at ${path || "/"}`);
    }
    ancestors.add(value);
    for (const [key, child] of Object.entries(value)) strictPublicJson(child, `${path}/${key}`, ancestors);
    ancestors.delete(value);
  };
  const publicTarget = (value, path) => {
    if (typeof value !== "string" || value.length === 0)
      throw new TypeError(`Citry.events.applyActions needs a non-empty target at ${path}`);
    if (value.startsWith("render:") && !safeRenderId(value.slice(7)))
      throw new TypeError(`Citry.events.applyActions needs a valid render target at ${path}`);
  };
  const publicTiming = (action, path) => {
    if (has(action, "delay") && (typeof action.delay !== "number" || !Number.isFinite(action.delay) || action.delay < 0))
      throw new TypeError(`Citry.events.applyActions needs a finite non-negative delay at ${path}/delay`);
    if (has(action, "wait") && action.wait !== false)
      throw new TypeError(`Citry.events.applyActions requires wait=false at ${path}/wait`);
  };
  const assertPublicActionList = actions => {
    if (!Array.isArray(actions)) throw new TypeError("Citry.events.applyActions needs an action array");
    strictPublicJson(actions);
    let dataActions = 0;
    for (let index = 0; index < actions.length; index += 1) {
      const action = actions[index];
      const path = `/actions/${index}`;
      if (!action || Array.isArray(action) || (Object.getPrototypeOf(action) !== Object.prototype && Object.getPrototypeOf(action) !== null))
        throw new TypeError(`Citry.events.applyActions received an invalid action at ${path}`);
      if (typeof action.action !== "string" || !knownActionKinds.has(action.action))
        throw new TypeError(`Citry.events.applyActions received an invalid action kind at ${path}`);
      const required = {
        render: ["target", "swap"],
        data: ["value"],
        state: ["targetRenderId", "stateToken"],
        event: ["eventName"],
        redirect: ["url"],
        url: ["url", "mode"],
      }[action.action];
      for (const name of required) if (!has(action, name)) throw new TypeError(`Citry.events.applyActions is missing ${path}/${name}`);
      const fields = {
        render: ["action", "target", "swap", "renderer", "html", "prepared", "delay", "wait"],
        data: ["action", "value", "delay"],
        state: ["action", "targetRenderId", "stateToken", "delay", "wait"],
        event: ["action", "eventName", "detail", "target", "delay", "wait"],
        redirect: ["action", "url", "delay", "wait"],
        url: ["action", "url", "mode", "delay", "wait"],
      }[action.action];
      for (const name of Object.keys(action)) if (!fields.includes(name)) throw new TypeError(`Citry.events.applyActions found an unknown field at ${path}/${name}`);
      if (action.action === "render") {
        publicTarget(action.target, `${path}/target`);
        if (!knownSwaps.has(action.swap)) throw new TypeError(`Citry.events.applyActions received an invalid render swap at ${path}/swap`);
        const renderer = has(action, "renderer") ? action.renderer : "html-fragment/1";
        if (!knownRenderers.has(renderer)) throw new TypeError(`Citry.events.applyActions received an invalid renderer at ${path}/renderer`);
        const content = renderer === "html-fragment/1" ? "html" : "prepared";
        const other = content === "html" ? "prepared" : "html";
        if (!has(action, content) || has(action, other)) throw new TypeError(`Citry.events.applyActions received invalid render content at ${path}`);
        if (content === "html" && typeof action.html !== "string") throw new TypeError(`Citry.events.applyActions needs string HTML at ${path}/html`);
        if (content === "prepared" && (!action.prepared || Array.isArray(action.prepared) || (Object.getPrototypeOf(action.prepared) !== Object.prototype && Object.getPrototypeOf(action.prepared) !== null)))
          throw new TypeError(`Citry.events.applyActions needs prepared object data at ${path}/prepared`);
      } else if (action.action === "data") {
        dataActions += 1;
      } else if (action.action === "state") {
        if (typeof action.targetRenderId !== "string" || !safeRenderId(action.targetRenderId)) throw new TypeError(`Citry.events.applyActions needs a valid state target at ${path}/targetRenderId`);
        if (typeof action.stateToken !== "string" || action.stateToken.length === 0) throw new TypeError(`Citry.events.applyActions needs a state token at ${path}/stateToken`);
      } else if (action.action === "event") {
        if (typeof action.eventName !== "string" || action.eventName.length === 0 || action.eventName.startsWith("citry:")) throw new TypeError(`Citry.events.applyActions needs a public event name at ${path}/eventName`);
        if (has(action, "target")) publicTarget(action.target, `${path}/target`);
      } else if (action.action === "redirect") {
        if (typeof action.url !== "string" || action.url.length === 0) throw new TypeError(`Citry.events.applyActions needs a redirect URL at ${path}/url`);
      } else {
        if (typeof action.url !== "string" || action.url.length === 0 || (action.mode !== "push" && action.mode !== "replace")) throw new TypeError(`Citry.events.applyActions needs a URL and mode at ${path}`);
      }
      publicTiming(action, path);
    }
    if (dataActions > 1) throw new TypeError("Citry.events.applyActions accepts at most one data action");
    return actions;
  };
  const snapshotPublicActions = actions => {
    const protocolValidator = global.CitryVueEvents?.assertValidActionList;
    if (typeof protocolValidator === "function") protocolValidator(actions);
    else assertPublicActionList(actions);
    return structuredClone(actions);
  };
  async function applyPublicActionsWithoutApp(actions) {
    let data;
    const apply = async action => {
      if (!action || typeof action !== "object" || typeof action.action !== "string")
        throw new TypeError("Citry.events.applyActions received an invalid action");
      if (typeof action.delay === "number" && action.delay > 0)
        await new Promise(resolve => setTimeout(resolve, action.delay * 1000));
      if (action.action === "data") data = action.value;
      else if (action.action === "redirect") global.location.assign(action.url);
      else if (action.action === "url") global.history[action.mode === "push" ? "pushState" : "replaceState"](global.history.state, "", action.url);
      else if (action.action === "event") {
        if (action.target !== undefined) throw new Error("Citry.events.applyActions needs a mounted component for targeted Event actions.");
        document.dispatchEvent(new CustomEvent(action.eventName, {detail: action.detail, bubbles: true}));
      } else throw new Error("Citry.events.applyActions needs a mounted component for Render and State actions.");
    };
    for (const action of actions) {
      if (action?.wait === false) void apply(action).catch(error => console.error("[Citry] applying a public action failed:", error));
      else await apply(action);
    }
    return data;
  }
  const clone = value => structuredClone(value);
  const freezeDetached = value => {
    if (value && typeof value === "object" && !Object.isFrozen(value)) {
      for (const child of Array.isArray(value) ? value : Object.values(value)) freezeDetached(child);
      Object.freeze(value);
    }
    return value;
  };
  const detached = value => freezeDetached(clone(value));
  const RESERVED_TEMPLATE_CONTEXT_NAMES = new Set([
    "$attrs", "$citryEvents", "$data", "$el", "$emit", "$error", "$event", "$forceUpdate", "$loading",
    "$nextTick", "$onEvent", "$options", "$parent", "$props", "$refs", "$root", "$sendEvent", "$slots", "$state", "$watch",
  ]);
  function templateContextNames(value, label) {
    if (!Array.isArray(value) || value.some(item => typeof item !== "string" || !/^\$[A-Za-z][A-Za-z0-9_]*$/.test(item) ||
        RESERVED_TEMPLATE_CONTEXT_NAMES.has(item)) ||
        new Set(value).size !== value.length || [...value].sort().some((item, index) => item !== value[index]))
      throw new TypeError(label + " must be a sorted unique array of public $ names");
    return Object.freeze([...value]);
  }
  function registerBrowserPlugin(name, schemaVersion, factory, contextNames = []) {
    if (typeof name !== "string" || !/^[a-z][a-z0-9_]*$/.test(name) ||
        !Number.isInteger(schemaVersion) || schemaVersion <= 0 || typeof factory !== "function")
      throw new TypeError("invalid Citry browser plugin registration");
    const normalizedNames = templateContextNames(contextNames, "browser plugin template context names");
    const prior = browserPluginFactories.get(name);
    if (prior && (prior.schemaVersion !== schemaVersion || prior.factory !== factory ||
        JSON.stringify(prior.templateContextNames) !== JSON.stringify(normalizedNames)))
      throw new Error("Citry browser plugin registration collision: " + name);
    browserPluginFactories.set(name, Object.freeze({schemaVersion, factory, templateContextNames: normalizedNames}));
  }
  function extensionEntries(value) {
    plain(value, "prepared extensions");
    return Object.keys(value).sort().map(name => {
      if (!/^[a-z][a-z0-9_]*$/.test(name)) throw new Error("invalid prepared extension name");
      const item = plain(value[name], "prepared extension");
      if (Object.keys(item).sort().join(",") !== "payload,schemaVersion,templateContextNames" ||
          !Number.isInteger(item.schemaVersion) || item.schemaVersion <= 0)
        throw new Error("invalid prepared extension wrapper");
      plain(item.payload, "prepared extension payload");
      return [name, {...item, templateContextNames: templateContextNames(item.templateContextNames, "extension template context names")}];
    });
  }
  const ORDINARY_TARGET = "ordinary-vnodes/1";
  const INPUT_MODEL_SITE = "__citryInputModelSite";
  let nextInputModelIdentity = 0;
  const inputModelObjectIds = new WeakMap();
  const inputModelSymbolIds = (() => {
    try {
      const values = new WeakMap(), probe = Symbol();
      values.set(probe, 0);
      return values;
    } catch {
      return null;
    }
  })();
  const inputModelFallbackSymbolIds = new WeakMap();
  const inputModelIdentityId = (values, value) => {
    let id = values.get(value);
    if (id === undefined) values.set(value, id = ++nextInputModelIdentity);
    return id;
  };
  const inputModelToken = (instance, value) => {
    if (value === undefined) return ["undefined"];
    if (value === null) return ["null"];
    if (typeof value === "string") return ["string", value];
    if (typeof value === "boolean") return ["boolean", value];
    if (typeof value === "number") return ["number", Number.isNaN(value) ? "NaN" : String(value)];
    if (typeof value === "bigint") return ["bigint", String(value)];
    if (typeof value === "symbol") {
      const registered = Symbol.keyFor(value);
      if (registered !== undefined) return ["registered-symbol", registered];
      if (inputModelSymbolIds) return ["symbol", inputModelIdentityId(inputModelSymbolIds, value)];
      let fallback = inputModelFallbackSymbolIds.get(instance);
      if (!fallback) inputModelFallbackSymbolIds.set(instance, fallback = new Map());
      return ["symbol", inputModelIdentityId(fallback, value)];
    }
    return ["object", inputModelIdentityId(inputModelObjectIds, value)];
  };
  const inputModelKey = (instance, site, type, authoredKey) => {
    return JSON.stringify([
      "\u0000citry-input-model",
      inputModelToken(instance, site),
      inputModelToken(instance, type),
      inputModelToken(instance, authoredKey),
    ]);
  };
  const vnodeProps = props => {
    if (props === null || props === undefined || !own(props, INPUT_MODEL_SITE)) return props;
    const site = props[INPUT_MODEL_SITE];
    if (typeof site !== "string" || site.length === 0) throw new Error("invalid input model lifecycle site");
    const prepared = {...props};
    delete prepared[INPUT_MODEL_SITE];
    const instance = V.getCurrentInstance();
    if (!instance) throw new Error("input model lifecycle key requires an active Vue render");
    const type = prepared.type === null || prepared.type === undefined ? "text" : prepared.type;
    prepared.key = inputModelKey(instance, site, type, prepared.key);
    return prepared;
  };
  const compilerRuntime = Object.create(V);
  Object.defineProperty(compilerRuntime, "openBlock", {value: () => null, enumerable: true});
  for (const name of ["createVNode", "createElementVNode", "createBlock", "createElementBlock"]) {
    Object.defineProperty(compilerRuntime, name, {
      value: (type, props, children) => V.createVNode(type, vnodeProps(props), children),
      enumerable: true,
    });
  }
  Object.defineProperty(compilerRuntime, "createTextVNode", {
    value: text => V.createTextVNode(text),
    enumerable: true,
  });
  for (const name of ["resolveDirective", "vModelCheckbox", "vModelDynamic", "vModelRadio", "vModelSelect", "vModelText"]) {
    if (V[name] === undefined) throw new Error("Vue runtime lacks required compiler helper: " + name);
    Object.defineProperty(compilerRuntime, name, {value: V[name], enumerable: true});
  }
  function runtimeForDynamicElements(entries) {
    if (!Array.isArray(entries)) throw new TypeError("dynamicElements must be an array");
    if (entries.length === 0) return compilerRuntime;
    const aliases = new Map();
    for (const entry of entries) {
      plain(entry, "dynamic element entry");
      if (Object.keys(entry).sort().join(",") !== "alias,sourceEnd,sourceStart,tag" ||
          typeof entry.alias !== "string" || !/^citry-dynamic-[0-9a-f]{16}$/.test(entry.alias) ||
          typeof entry.tag !== "string" || !/^[A-Za-z][A-Za-z0-9_.-]*$/.test(entry.tag) ||
          ["script", "style", "template"].includes(entry.tag.toLowerCase()) ||
          !Number.isInteger(entry.sourceStart) || !Number.isInteger(entry.sourceEnd) ||
          entry.sourceStart < 0 || entry.sourceEnd <= entry.sourceStart || aliases.has(entry.alias))
        throw new TypeError("invalid dynamic element entry");
      aliases.set(entry.alias, entry.tag);
    }
    const runtime = Object.create(compilerRuntime);
    for (const name of ["createVNode", "createElementVNode", "createBlock", "createElementBlock"])
      Object.defineProperty(runtime, name, {enumerable: true, value(type, props, children) {
        if (typeof type === "string" && type.startsWith("citry-dynamic-")) {
          if (!aliases.has(type)) throw new Error("unknown prepared dynamic element alias: " + type);
          type = aliases.get(type);
        }
        return V.createVNode(type, vnodeProps(props), children);
      }});
    return Object.freeze(runtime);
  }
  Object.defineProperty(compilerRuntime, "runtimeForDynamicElements", {
    value: runtimeForDynamicElements,
    enumerable: false,
  });
  Object.defineProperty(compilerRuntime, "helperContract", {value: HELPER_CONTRACT, enumerable: true});

  const opaqueHtmlComponent = Object.freeze({
    name: "CitryOpaqueHtml",
    props: {record: {type: Object, required: true}},
    setup(props) {
      return () => {
        const record = plain(props.record, "opaque HTML record");
        if (Object.keys(record).join(",") !== "html" || typeof record.html !== "string")
          throw new TypeError("invalid opaque HTML record");
        if (record.html === "") return V.h(V.Fragment, {key: record.html}, []);
        const vnode = V.createStaticVNode(record.html, 0);
        vnode.key = record.html;
        return vnode;
      };
    },
  });

  function normalizeDirectiveSignature(value) {
    if (!Array.isArray(value)) throw new TypeError("directiveSignature must be an array");
    const result = value.map(item => {
      plain(item, "directive signature entry");
      if (typeof item.siteId !== "string" || typeof item.name !== "string" || (item.arg !== null && typeof item.arg !== "string") || !Array.isArray(item.modifiers) || item.modifiers.some(x => typeof x !== "string")) throw new TypeError("invalid directive signature entry");
      const modifiers = [...item.modifiers];
      if (new Set(modifiers).size !== modifiers.length || modifiers.some((x, i) => i && modifiers[i - 1] > x)) throw new Error("directive modifiers must be unique and sorted");
      return Object.freeze({siteId: item.siteId, name: item.name, arg: item.arg, modifiers: Object.freeze(modifiers)});
    });
    const sites = new Set();
    for (const item of result) { if (sites.has(item.siteId)) throw new Error("duplicate directive site"); sites.add(item.siteId); }
    return Object.freeze(result);
  }
  const signatureKey = value => JSON.stringify(value);
  function normalizeReplacementSites(value) {
    if (!Array.isArray(value)) throw new TypeError("replacementSites must be an array");
    let prior = "";
    return Object.freeze(value.map(item => {
      plain(item, "replacement site");
      const key = item.replacementKey ?? item.key;
      const descendants = item.localDescendants ?? [];
      const descendantRuns = item.localDescendantRuns ?? [];
      if (typeof item.siteId !== "string" || typeof key !== "string" ||
          !Array.isArray(descendants) || descendants.some(id => typeof id !== "string") ||
          signatureKey(descendants) !== signatureKey([...new Set(descendants)].sort()) ||
          !Array.isArray(descendantRuns) || descendantRuns.some(id => typeof id !== "string") ||
          new Set(descendantRuns).size !== descendantRuns.length || item.siteId <= prior)
        throw new Error("replacement sites must be sorted and unique");
      prior = item.siteId;
      return Object.freeze({siteId: item.siteId, key, localDescendants: Object.freeze([...descendants]), localDescendantRuns: Object.freeze([...descendantRuns])});
    }));
  }

  function normalizeLocalCallRuns(value) {
    if (!Array.isArray(value)) throw new TypeError("localCallRuns must be an array");
    const ids = new Set();
    return Object.freeze(value.map(item => {
      plain(item, "local call run");
      const strings = ["runId", "typeKey", "componentTag", "collectionExpression", "idExpression", "keyExpression"];
      const offsets = ["sourceStart", "sourceEnd", "loopSourceStart", "loopSourceEnd"];
      if (Object.keys(item).length !== strings.length + offsets.length ||
          [...strings, ...offsets].some(key => !own(item, key)) || strings.some(key => typeof item[key] !== "string") ||
          offsets.some(key => !Number.isInteger(item[key]) || item[key] < 0) ||
          item.sourceEnd < item.sourceStart || item.loopSourceEnd < item.loopSourceStart ||
          ids.has(item.runId)) throw new TypeError("invalid local call run");
      ids.add(item.runId);
      return Object.freeze(Object.fromEntries([...strings, ...offsets].map(key => [key, item[key]])));
    }));
  }

  function normalizeLocalCalls(value) {
    if (!Array.isArray(value)) throw new TypeError("localCalls must be an array");
    const ids = new Set();
    return Object.freeze(value.map(item => {
      plain(item, "local call declaration");
      if (typeof item.localId !== "string" || typeof item.typeKey !== "string" ||
          typeof item.componentTag !== "string" || !Array.isArray(item.bindings) ||
          Object.keys(item).sort().join(",") !== "bindings,componentTag,localId,typeKey" ||
          ids.has(item.localId)) throw new TypeError("invalid local call declaration");
      const bindings = Object.freeze(item.bindings.map(binding => {
        plain(binding, "component call binding");
        if (Object.keys(binding).sort().join(",") !== "kind,name,sourceEnd,sourceStart,value" ||
            !["prop", "props-object", "event", "ref-static", "ref-expression"].includes(binding.kind) ||
            typeof binding.name !== "string" || typeof binding.value !== "string" ||
            !Number.isInteger(binding.sourceStart) || !Number.isInteger(binding.sourceEnd) ||
            binding.sourceStart < 0 || binding.sourceEnd <= binding.sourceStart)
          throw new TypeError("invalid component call binding");
        return Object.freeze({
          kind: binding.kind,
          name: binding.name,
          value: binding.value,
          sourceStart: binding.sourceStart,
          sourceEnd: binding.sourceEnd,
        });
      }));
      ids.add(item.localId);
      return Object.freeze({localId: item.localId, typeKey: item.typeKey, componentTag: item.componentTag, bindings});
    }));
  }

  function normalizeDynamicElements(value) {
    if (!Array.isArray(value)) throw new TypeError("dynamicElements must be an array");
    const aliases = new Set();
    return Object.freeze(value.map(item => {
      plain(item, "dynamic element entry");
      if (Object.keys(item).sort().join(",") !== "alias,sourceEnd,sourceStart,tag" ||
          typeof item.alias !== "string" || !/^citry-dynamic-[0-9a-f]{16}$/.test(item.alias) ||
          typeof item.tag !== "string" || !/^[A-Za-z][A-Za-z0-9_.-]*$/.test(item.tag) ||
          ["script", "style", "template"].includes(item.tag.toLowerCase()) || aliases.has(item.alias) ||
          !Number.isInteger(item.sourceStart) || !Number.isInteger(item.sourceEnd) ||
          item.sourceStart < 0 || item.sourceEnd <= item.sourceStart)
        throw new TypeError("invalid dynamic element entry");
      aliases.add(item.alias);
      return Object.freeze({
        alias: item.alias,
        tag: item.tag,
        sourceStart: item.sourceStart,
        sourceEnd: item.sourceEnd,
      });
    }));
  }

  function normalizeOpaqueHtmlSites(value) {
    if (!Array.isArray(value)) throw new TypeError("opaqueHtmlSites must be an array");
    const keys = new Set();
    return Object.freeze(value.map(item => {
      plain(item, "opaque HTML site");
      if (Object.keys(item).sort().join(",") !== "key,origin,sourceEnd,sourceStart" ||
          typeof item.key !== "string" || !/^citryOpaque[0-9A-Za-z]+$/.test(item.key) || keys.has(item.key) ||
          !["raw", "markup"].includes(item.origin) || !Number.isInteger(item.sourceStart) ||
          !Number.isInteger(item.sourceEnd) || item.sourceStart < 0 || item.sourceEnd <= item.sourceStart)
        throw new TypeError("invalid opaque HTML site");
      keys.add(item.key);
      return Object.freeze({
        key: item.key,
        sourceStart: item.sourceStart,
        sourceEnd: item.sourceEnd,
        origin: item.origin,
      });
    }));
  }
  function normalizeRuntimeEventSites(value) {
    if (!Array.isArray(value)) throw new TypeError("runtimeEventSites must be an array");
    const seen = new Set(), seenRoutes = new Set();
    return Object.freeze(value.map(site => {
      plain(site, "runtime event site");
      if (Object.keys(site).sort().join(",") !== "bindingKey,siteId,steps" ||
          typeof site.siteId !== "string" || !/^citryDirective[0-9a-f]+D[0-9]+$/.test(site.siteId) ||
          seen.has(site.siteId) ||
          typeof site.bindingKey !== "string" || !/^citryRuntimeEvents[0-9A-Za-z]+$/.test(site.bindingKey) ||
          !Array.isArray(site.steps)) throw new TypeError("runtime event site is invalid or duplicated");
      seen.add(site.siteId);
      const steps = site.steps.map(step => {
        plain(step, "runtime event site step");
        const keys = Object.keys(step).sort().join(",");
        if (step.kind === "branch" && keys === "index,key,kind" && typeof step.key === "string" &&
            /^citryIf[0-9]+$/.test(step.key) &&
            Number.isSafeInteger(step.index) && step.index >= 0)
          return Object.freeze({kind: step.kind, key: step.key, index: step.index});
        if ((step.kind === "each" || step.kind === "empty") && keys === "key,kind" &&
            typeof step.key === "string" && /^citryLoop[0-9]+$/.test(step.key))
          return Object.freeze({kind: step.kind, key: step.key});
        throw new TypeError("runtime event site step is invalid");
      });
      const routeKey = JSON.stringify([site.bindingKey,
        steps.map(step => [step.kind, step.key, step.kind === "branch" ? step.index : null])]);
      if (seenRoutes.has(routeKey)) throw new TypeError("runtime event site route and binding key are duplicated");
      seenRoutes.add(routeKey);
      return Object.freeze({siteId:site.siteId, bindingKey:site.bindingKey, steps:Object.freeze(steps)});
    }));
  }

  function validateRuntimeEventSiteDeclarations(directiveSignature, runtimeEventSites) {
    const runtimeDirectives = directiveSignature.filter(item => item.name === "v-citry-runtime-events");
    if (runtimeDirectives.some(item => item.arg !== null || item.modifiers.length !== 0))
      throw new Error("runtime event directive declaration has arguments or modifiers");
    const directiveIds = new Set(runtimeDirectives.map(item => item.siteId));
    const siteIds = new Set(runtimeEventSites.map(item => item.siteId));
    if (directiveIds.size !== siteIds.size || [...directiveIds].some(id => !siteIds.has(id)))
      throw new Error("runtime event sites do not exactly match runtime directive declarations");
  }

  function normalizeDefinitionAsset(asset) {
    plain(asset, "prepared definition asset");
    const keys = ["directiveSignature", "dynamicElements", "helperContract", "id", "localCallRuns",
      "localCalls", "opaqueHtmlSites", "replacementSites", "runtimeEventSites", "sha256", "target", "url"];
    if (Object.keys(asset).sort().join(",") !== [...keys].sort().join(",") ||
        typeof asset.id !== "string" || typeof asset.url !== "string" ||
        asset.target !== ORDINARY_TARGET || asset.helperContract !== HELPER_CONTRACT)
      throw new Error("invalid prepared definition asset");
    sriFromHex(asset.sha256);
    const directiveSignature = normalizeDirectiveSignature(asset.directiveSignature);
    const runtimeEventSites = normalizeRuntimeEventSites(asset.runtimeEventSites);
    validateRuntimeEventSiteDeclarations(directiveSignature, runtimeEventSites);
    return Object.freeze({
      id: asset.id, url: asset.url, sha256: asset.sha256, target: asset.target,
      helperContract: asset.helperContract,
      dynamicElements: normalizeDynamicElements(asset.dynamicElements),
      directiveSignature,
      replacementSites: normalizeReplacementSites(asset.replacementSites),
      localCalls: normalizeLocalCalls(asset.localCalls),
      localCallRuns: normalizeLocalCallRuns(asset.localCallRuns),
      opaqueHtmlSites: normalizeOpaqueHtmlSites(asset.opaqueHtmlSites),
      runtimeEventSites,
    });
  }

  function definitionMetadataKey(definition) {
    return signatureKey({target: definition.target, helperContract: definition.helperContract,
      dynamicElements: definition.dynamicElements, directiveSignature: definition.directiveSignature,
      replacementSites: definition.replacementSites, localCalls: definition.localCalls,
      localCallRuns: definition.localCallRuns, opaqueHtmlSites: definition.opaqueHtmlSites,
      runtimeEventSites: definition.runtimeEventSites});
  }

  function validateRuntimeEventSpec(id, spec, occurrence) {
    plain(spec, "runtime event binding");
    const timing = value => value === null || Number.isSafeInteger(value) && value >= 0;
    const descriptor = occurrence.eventContext?.descriptor;
    if (!/^citryRuntimeEvent[0-9a-f]+$/.test(id) ||
        Object.keys(spec).sort().join(",") !== "args,debounce,event,handler,id,key,once,prevent,self,stop,throttle" ||
        spec.id !== id || typeof spec.event !== "string" || spec.event === "" ||
        typeof spec.handler !== "string" || spec.handler === "" || spec.args !== null ||
        ![spec.prevent, spec.stop, spec.self, spec.once].every(value => typeof value === "boolean") ||
        spec.key !== null && (typeof spec.key !== "string" || spec.key === "") ||
        !timing(spec.debounce) || !timing(spec.throttle) || !descriptor ||
        !own(descriptor.eventHandlers, spec.handler))
      throw new Error("runtime event binding is missing, stale, or invalid");
  }

  function validateRuntimePollSpec(id, spec, occurrence) {
    plain(spec, "runtime poll binding");
    const descriptor = occurrence.eventContext?.descriptor;
    if (!/^citryRuntimePoll[0-9a-f]+$/.test(id) ||
        Object.keys(spec).sort().join(",") !== "args,handler,id,interval" ||
        spec.id !== id || typeof spec.handler !== "string" || spec.handler === "" ||
        spec.args !== null || !Number.isSafeInteger(spec.interval) || spec.interval <= 0 ||
        !descriptor || !own(descriptor.eventHandlers, spec.handler))
      throw new Error("runtime poll binding is missing, stale, or invalid");
  }

  function validateOccurrenceRuntimeEvents(occurrence, definition) {
    const referenced = new Set();
    const visit = (site, index, scope) => {
      if (index === site.steps.length) {
        if (!own(scope, site.bindingKey) || typeof scope[site.bindingKey] !== "string")
          throw new Error("runtime event site terminal is missing or invalid");
        const ids = scope[site.bindingKey] === "" ? [] : scope[site.bindingKey].split(",");
        if (new Set(ids).size !== ids.length || ids.some(id =>
          !/^citryRuntime(?:Event|Poll)[0-9a-f]+$/.test(id)))
          throw new Error("runtime event site references invalid or duplicate ids");
        for (const id of ids) referenced.add(id);
        return;
      }
      const step = site.steps[index];
      if (step.kind === "branch") {
        if (!own(scope, step.key) || !Number.isSafeInteger(scope[step.key]))
          throw new Error("runtime event branch selector is invalid");
        if (scope[step.key] === step.index) visit(site, index + 1, scope);
        return;
      }
      if (!own(scope, step.key) || !Array.isArray(scope[step.key]))
        throw new Error("runtime event loop selector is invalid");
      if (step.kind === "each") {
        for (const row of scope[step.key]) visit(site, index + 1, plain(row, "runtime event loop row"));
      } else if (scope[step.key].length === 0) visit(site, index + 1, scope);
    };
    for (const site of definition.runtimeEventSites) visit(site, 0, occurrence.preparedData);
    const eventTable = own(occurrence.preparedData, "eventBindings")
      ? plain(occurrence.preparedData.eventBindings, "preparedData.eventBindings") : {};
    const pollTable = own(occurrence.preparedData, "pollBindings")
      ? plain(occurrence.preparedData.pollBindings, "preparedData.pollBindings") : {};
    const runtimeEventIds = Object.keys(eventTable).filter(id => id.startsWith("citryRuntimeEvent"));
    const runtimePollIds = Object.keys(pollTable).filter(id => id.startsWith("citryRuntimePoll"));
    const eventRuntimeIds = Object.keys(eventTable).filter(id => id.startsWith("citryRuntime"));
    const pollRuntimeIds = Object.keys(pollTable).filter(id => id.startsWith("citryRuntime"));
    const runtimeIds = [...runtimeEventIds, ...runtimePollIds];
    if (eventRuntimeIds.length !== runtimeEventIds.length || pollRuntimeIds.length !== runtimePollIds.length ||
        runtimeIds.length !== referenced.size || runtimeIds.some(id => !referenced.has(id)))
      throw new Error("runtime event references do not match definition sites");
    for (const id of referenced) {
      if (/^citryRuntimeEvent[0-9a-f]+$/.test(id) && own(eventTable, id) && !own(pollTable, id))
        validateRuntimeEventSpec(id, eventTable[id], occurrence);
      else if (/^citryRuntimePoll[0-9a-f]+$/.test(id) && own(pollTable, id) && !own(eventTable, id))
        validateRuntimePollSpec(id, pollTable[id], occurrence);
      else throw new Error("runtime event site references a missing or swapped binding table entry");
    }
  }

  function preflightDefinitions(app, assets, occurrences, rootId) {
    const declared = new Map();
    for (const asset of assets) {
      const normalized = normalizeDefinitionAsset(asset);
      if (declared.has(normalized.id)) throw new Error("duplicate prepared definition asset");
      const prior = app.definitions.get(normalized.id);
      if (prior && definitionMetadataKey(prior) !== definitionMetadataKey(normalized))
        throw new Error("prepared definition metadata collision");
      declared.set(normalized.id, prior || normalized);
    }
    const occurrenceMap = new Map(occurrences.map(item => [item.id, item]));
    for (const occurrence of occurrences) {
      const definition = declared.get(occurrence.definitionId) || app.definitions.get(occurrence.definitionId);
      if (!definition) throw new Error("unknown prepared definition metadata");
      validateOccurrenceCallRuns(occurrenceMap, occurrence, definition);
      validateOccurrenceRuntimeEvents(occurrence, definition);
      const opaque = own(occurrence.preparedData, "opaqueHtml")
        ? plain(occurrence.preparedData.opaqueHtml, "preparedData.opaqueHtml") : {};
      const declaredOpaque = new Set(definition.opaqueHtmlSites.map(site => site.key));
      if (Object.keys(opaque).length !== declaredOpaque.size || Object.keys(opaque).some(key => !declaredOpaque.has(key)))
        throw new Error("prepared opaque HTML does not match definition declarations");
      for (const key of declaredOpaque) {
        const record = plain(opaque[key], "opaque HTML record");
        if (Object.keys(record).join(",") !== "html" || typeof record.html !== "string")
          throw new TypeError("invalid opaque HTML record");
      }
    }
    validateGraph(occurrenceMap, rootId);
    return declared;
  }

  function validateOccurrenceCallRuns(occurrences, occurrence, definition) {
    const calls = plain(occurrence.preparedData.calls, "preparedData.calls");
    const declarations = new Map(definition.localCallRuns.map(run => [run.runId, run]));
    const values = own(occurrence.preparedData, "callRuns")
      ? plain(occurrence.preparedData.callRuns, "preparedData.callRuns")
      : declarations.size === 0 ? {} : (() => { throw new Error("prepared call runs do not match definition declarations"); })();
    if (Object.keys(values).some(runId => !declarations.has(runId)) ||
        [...declarations.keys()].some(runId => !own(values, runId)))
      throw new Error("prepared call runs do not match definition declarations");
    if (Object.keys(calls).length !== definition.localCalls.length)
      throw new Error("prepared ordinary calls do not match definition declarations");
    const covered = new Set();
    for (const declaration of definition.localCalls) {
      if (!own(calls, declaration.localId))
        throw new Error("prepared ordinary local call does not match its declaration");
      const binding = calls[declaration.localId];
      const child = occurrences.get(binding.id);
      if (!child || child.parentId !== binding.parentId || child.typeKey !== declaration.typeKey || covered.has(child.id))
        throw new Error("prepared ordinary local call stable-type mismatch");
      covered.add(child.id);
    }
    for (const [runId, ids] of Object.entries(values)) {
      if (!Array.isArray(ids) || new Set(ids).size !== ids.length || ids.some(id => typeof id !== "string"))
        throw new TypeError("invalid prepared call run values");
      const declaration = declarations.get(runId);
      for (const id of ids) {
        const child = occurrences.get(id);
        if (!child || child.parentId !== occurrence.id || child.typeKey !== declaration.typeKey || covered.has(id))
          throw new Error("prepared local call run stable-type or ownership mismatch");
        covered.add(id);
      }
    }
  }

  function validateDefinitionCallRuns(app, definition) {
    const declared = new Set(definition.localCallRuns.map(run => run.runId));
    for (const site of definition.replacementSites) {
      if (site.localDescendantRuns.some(runId => !declared.has(runId)))
        throw new Error("replacement site references an unknown local call run");
    }
    const stagedTags = new Map(app.callRunTags);
    for (const run of [...definition.localCalls, ...definition.localCallRuns]) {
      const prior = stagedTags.get(run.componentTag);
      if (prior && prior !== run.typeKey) throw new Error("local call component tag stable-type mismatch");
      stagedTags.set(run.componentTag, run.typeKey);
    }
  }

  function validateGraph(occurrences, rootId) {
    if (typeof rootId !== "string" || !occurrences.has(rootId) || occurrences.get(rootId).parentId !== null || occurrences.get(rootId).placementKey !== null) throw new Error("invalid prepared root");
    let roots = 0;
    const placements = new Set();
    for (const item of occurrences.values()) {
      if (item.parentId === null) roots += 1;
      else {
        if (!occurrences.has(item.parentId)) throw new Error("unknown occurrence parent");
        if (typeof item.placementKey !== "string" || item.placementKey.length === 0) throw new Error("invalid occurrence placement key");
        const placement = JSON.stringify([item.parentId, item.placementKey]);
        if (placements.has(placement)) throw new Error("duplicate occurrence placement key within one parent");
        placements.add(placement);
      }
      const seen = new Set([item.id]); let cursor = item.parentId;
      while (cursor !== null) { if (seen.has(cursor)) throw new Error("cyclic occurrence graph"); seen.add(cursor); cursor = occurrences.get(cursor).parentId; }
    }
    if (roots !== 1) throw new Error("prepared graph must have exactly one root");
    const directCalls = [...occurrences.values()].some(item => own(item.preparedData, "calls"));
    if (directCalls) {
      const referenced = new Set();
      for (const owner of occurrences.values()) {
        plain(owner.preparedData.calls, "preparedData.calls");
        for (const binding of Object.values(owner.preparedData.calls)) {
          plain(binding, "prepared local call binding");
          if (Object.keys(binding).sort().join(",") !== "id,key,parentId" ||
              typeof binding.id !== "string" || typeof binding.key !== "string" ||
              typeof binding.parentId !== "string")
            throw new Error("invalid prepared local call binding");
          const child = occurrences.get(binding.id);
          if (!child || child.parentId !== binding.parentId || referenced.has(binding.id))
            throw new Error("prepared local call does not match occurrence placement");
          referenced.add(binding.id);
        }
        if (own(owner.preparedData, "callRuns")) {
          const runs = plain(owner.preparedData.callRuns, "preparedData.callRuns");
          for (const ids of Object.values(runs)) {
            if (!Array.isArray(ids) || ids.some(id => typeof id !== "string"))
              throw new Error("invalid prepared local call run values");
            for (const id of ids) {
              const child = occurrences.get(id);
              if (!child || child.parentId !== owner.id || referenced.has(id))
                throw new Error("prepared local call run does not match occurrence placement");
              referenced.add(id);
            }
          }
        }
      }
      for (const id of occurrences.keys()) {
        if (id !== rootId && !referenced.has(id)) throw new Error("prepared occurrence has no local call binding");
      }
    }
  }

  function definitionRegistry(appId) {
    const app = apps.get(appId);
    if (!app) throw new Error("unknown Citry Vue app: " + appId);
    return app;
  }

  const MARK_NAME = /^[A-Za-z][A-Za-z0-9_-]*$/;
  function normalizeMarkers(values, occurrences) {
    if (!Array.isArray(values)) throw new TypeError("prepared markers must be an array");
    if (values.length === 0) return new Map();
    const markers = new Map(), physical = new Set();
    let prior = null;
    for (const value of values) {
      plain(value, "prepared marker");
      if (Object.keys(value).sort().join(",") !== "name,occurrenceId,ownerId" ||
          typeof value.ownerId !== "string" || !occurrences.has(value.ownerId) ||
          typeof value.occurrenceId !== "string" || !occurrences.has(value.occurrenceId) ||
          typeof value.name !== "string" || !MARK_NAME.test(value.name))
        throw new Error("prepared marker metadata is invalid");
      const key = value.ownerId + "\0" + value.name;
      const order = key + "\0" + value.occurrenceId;
      if (markers.has(key) || physical.has(value.occurrenceId) || prior !== null && order <= prior)
        throw new Error("prepared marker metadata is duplicated or unsorted");
      markers.set(key, Object.freeze({...value}));
      physical.add(value.occurrenceId); prior = order;
    }
    return markers;
  }

  function configure(bootstrap, startAttempt = null) {
    plain(bootstrap, "bootstrap");
    if (bootstrap.protocol !== "citry-vue-prepared/1" || typeof bootstrap.appId !== "string" || !Number.isInteger(bootstrap.revision) || !Array.isArray(bootstrap.occurrences)) throw new TypeError("invalid bootstrap");
    if (apps.has(bootstrap.appId)) throw new Error("duplicate Citry Vue app");
    const occurrences = new Map();
    for (const item of bootstrap.occurrences) {
      plain(item, "occurrence");
      if (typeof item.id !== "string" || typeof item.typeKey !== "string" || typeof item.definitionId !== "string" || (item.parentId !== null && typeof item.parentId !== "string") || (item.placementKey !== null && typeof item.placementKey !== "string")) throw new TypeError("invalid occurrence identity");
      plain(item.serverData, "serverData");
      plain(item.preparedData, "preparedData");
      if (occurrences.has(item.id)) throw new Error("duplicate occurrence id");
      occurrences.set(item.id, Object.freeze({...clone(item), serverData: clone(item.serverData)}));
    }
    validateGraph(occurrences, bootstrap.rootId);
    const markers = normalizeMarkers(bootstrap.markers, occurrences);
    const initialLive = new Map([...occurrences].map(([id,item]) => [id, {...item, serverData: V.reactive(clone(item.serverData))}]));
    const definitionTypes = new Map();
    for (const item of occurrences.values()) { const prior = definitionTypes.get(item.definitionId); if (prior && prior !== item.typeKey) throw new Error("definition used by multiple stable types"); definitionTypes.set(item.definitionId, item.typeKey); }
    const app = {id: bootstrap.appId, startAttempt, rootId: bootstrap.rootId, revision: bootstrap.revision, occurrences, markers, snapshot: V.shallowRef(initialLive), definitions: new Map(), definitionTypes, callRunTags: new Map(), typeTags: new Map(), types: new Map(), browserPlugins: [], templateContextNames: [], initialPluginStages: [], vueApp: null, hostElement: null, mounted: new Map(), nextMountGeneration: 0, preparedHost: null, eventDispatch: null, eventDispatchComponent: null, initialTasks: new Set(), initialError: null, transaction: null, busy: false, terminal: false};
    apps.set(app.id, app);
    return app;
  }

  function registerDefinition(appId, definitionId, definition, expected = null) {
    plain(definition, "render definition");
    if (typeof definitionId !== "string" || typeof definition.render !== "function" || definition.target !== ORDINARY_TARGET || definition.helperContract !== HELPER_CONTRACT) throw new TypeError("invalid render definition");
    const normalized = Object.freeze({render: definition.render, target: definition.target, helperContract: definition.helperContract, dynamicElements:normalizeDynamicElements(definition.dynamicElements || []),directiveSignature: normalizeDirectiveSignature(definition.directiveSignature),replacementSites:normalizeReplacementSites(definition.replacementSites),localCalls:normalizeLocalCalls(definition.localCalls),localCallRuns:normalizeLocalCallRuns(definition.localCallRuns),opaqueHtmlSites:normalizeOpaqueHtmlSites(definition.opaqueHtmlSites),runtimeEventSites:normalizeRuntimeEventSites(definition.runtimeEventSites || [])});
    validateRuntimeEventSiteDeclarations(normalized.directiveSignature, normalized.runtimeEventSites);
    if (expected && definitionMetadataKey(expected) !== definitionMetadataKey(normalized))
      throw new Error("loaded definition metadata does not match its prepared declaration");
    const app = definitionRegistry(appId);
    validateDefinitionCallRuns(app, normalized);
    const prior = app.definitions.get(definitionId);
    if (prior && (prior.render !== normalized.render || prior.target !== normalized.target || prior.helperContract !== normalized.helperContract || signatureKey(prior.dynamicElements) !== signatureKey(normalized.dynamicElements) || signatureKey(prior.directiveSignature) !== signatureKey(normalized.directiveSignature)||signatureKey(prior.replacementSites)!==signatureKey(normalized.replacementSites)||signatureKey(prior.localCalls)!==signatureKey(normalized.localCalls)||signatureKey(prior.localCallRuns)!==signatureKey(normalized.localCallRuns)||signatureKey(prior.opaqueHtmlSites)!==signatureKey(normalized.opaqueHtmlSites)||signatureKey(prior.runtimeEventSites)!==signatureKey(normalized.runtimeEventSites))) throw new Error("definition id collision");
    for (const occurrence of app.occurrences.values()) if (occurrence.definitionId === definitionId)
      validateOccurrenceCallRuns(app.occurrences, occurrence, normalized);
    if (!prior) {
      app.definitions.set(definitionId, normalized);
      for (const call of [...normalized.localCalls, ...normalized.localCallRuns])
        app.callRunTags.set(call.componentTag, call.typeKey);
    }
  }

  function attachVueApp(appId, vueApp) {
    const app = definitionRegistry(appId), prior = vueApp.config.errorHandler;
    for (const occurrence of app.occurrences.values()) {
      const definition = app.definitions.get(occurrence.definitionId);
      if (!definition) throw new Error("missing render definition before Vue app attachment");
      validateOccurrenceCallRuns(app.occurrences, occurrence, definition);
    }
    app.vueApp = vueApp;
    vueApp.config.errorHandler = (error, instance, info) => {
      app.terminal = true;
      stopAppPolling(app);
      if (prior) prior(error, instance, info);
      else queueMicrotask(() => { throw error; });
    };
  }

  function attachPreparedHost(appId, host) {
    plain(host, "prepared host");
    if (
      typeof host.onOccurrenceMounted !== "function" ||
      typeof host.onOccurrenceUnmounted !== "function" ||
      typeof host.beforeServerCallbacks !== "function"
    ) throw new TypeError("invalid prepared host");
    const app = definitionRegistry(appId);
    if (app.preparedHost) throw new Error("prepared host is already attached");
    app.preparedHost = Object.freeze({onOccurrenceMounted: host.onOccurrenceMounted, onOccurrenceUnmounted: host.onOccurrenceUnmounted, beforeServerCallbacks: host.beforeServerCallbacks});
  }

  function installServerKey(instance, record, key) {
    if (key.startsWith("$") || key.startsWith("_")) throw new Error("reserved js_data key: " + key);
    Object.defineProperty(instance, key, {enumerable: true, configurable: true,
      get() { return record.live.value?.serverData[key]; },
      set(value) { record.live.value.serverData[key] = value; }});
  }

  function eventDescriptor(record) {
    return record.events.descriptor;
  }

  function requireEventHandler(record, name) {
    const descriptor = eventDescriptor(record);
    if (typeof name !== "string" || !descriptor || !own(descriptor.eventHandlers, name))
      throw new Error("Unknown event handler '" + String(name) + "'.");
    return name;
  }

  function cloneJsonValue(value, label) {
    const ancestors = new Set();
    const copy = item => {
      if (item === null || typeof item === "string" || typeof item === "boolean") return item;
      if (typeof item === "number" && Number.isFinite(item)) return item;
      if (!item || typeof item !== "object") throw new TypeError(label + " must contain only strict JSON");
      const raw = V.toRaw(item);
      if (!Array.isArray(raw) && Object.getPrototypeOf(raw) !== Object.prototype && Object.getPrototypeOf(raw) !== null ||
          ancestors.has(raw) || Object.getOwnPropertySymbols(raw).length)
        throw new TypeError(label + " must contain only strict JSON");
      const names = Object.getOwnPropertyNames(raw);
      if (Array.isArray(raw) && (Object.keys(raw).length !== raw.length ||
          Object.keys(raw).some((key, index) => key !== String(index))))
        throw new TypeError(label + " must contain only dense JSON arrays");
      for (const name of names) {
        if (Array.isArray(raw) && name === "length") continue;
        const descriptor = Object.getOwnPropertyDescriptor(raw, name);
        if (!descriptor?.enumerable || !("value" in descriptor))
          throw new TypeError(label + " must contain only strict JSON");
      }
      ancestors.add(raw);
      const result = Array.isArray(raw) ? [] : {};
      for (const key of Object.keys(raw)) {
        Object.defineProperty(result, key, {
          value: copy(raw[key]), enumerable: true, configurable: true, writable: true,
        });
      }
      ancestors.delete(raw);
      return result;
    };
    return copy(value);
  }
  const cloneStateValue = value => cloneJsonValue(value, "$state values");

  function writableStateFields(descriptor, publicState) {
    return new Set(own(descriptor, "writableStateFields") ? descriptor.writableStateFields : Object.keys(publicState));
  }

  function createStateFacade(record, initialContext) {
    const state = {values: null, pending: null, writable: null, current: true, nestedViews: null, contractEpoch: 0};
    const requireCurrent = key => {
      if (!state.current || record.app.mounted.get(record.occurrenceId)?.record !== record)
        throw new Error("Citry Events State source is stale or retired");
      if (typeof key !== "string" || !state.values || !own(state.values, key))
        throw new Error("Unknown $state field '" + String(key) + "'.");
      if (!state.writable.has(key)) throw new Error("$state field '" + key + "' is not client-writable.");
    };
    const nested = value => {
      const existing = state.nestedViews.get(value);
      if (existing) return existing;
      const epoch = state.contractEpoch;
      const proxy = new Proxy(value, {
      get(target, key) {
        if (!state.current || epoch !== state.contractEpoch)
          throw new Error("Citry Events State source is stale or retired");
        const child = Reflect.get(target, key);
        return child && typeof child === "object" ? nested(child) : child;
      },
      getOwnPropertyDescriptor(target, key) {
        const descriptor = Reflect.getOwnPropertyDescriptor(target, key);
        if (!descriptor || !descriptor.configurable || !("value" in descriptor) ||
            !descriptor.value || typeof descriptor.value !== "object") return descriptor;
        return {...descriptor, value: nested(descriptor.value)};
      },
      set() { throw new Error("Nested $state values are read-only; replace the whole top-level field instead."); },
      deleteProperty() { throw new Error("Nested $state values are read-only; replace the whole top-level field instead."); },
      defineProperty() { throw new Error("Nested $state values are read-only; replace the whole top-level field instead."); },
      preventExtensions() { throw new Error("Nested $state values are read-only; replace the whole top-level field instead."); },
      setPrototypeOf() { throw new Error("Nested $state values are read-only; replace the whole top-level field instead."); },
      });
      state.nestedViews.set(value, proxy);
      return proxy;
    };
    state.facade = new Proxy(Object.create(null), {
      get(_target, key) {
        if (!state.current) throw new Error("Citry Events State source is stale or retired");
        const value = state.values && own(state.values, key) ? state.values[key] : undefined;
        return value && typeof value === "object" ? nested(value) : value;
      },
      set(_target, key, value) {
        requireCurrent(key);
        const copied = cloneStateValue(value);
        const pending = cloneStateValue(copied);
        state.values[key] = copied;
        state.pending[key] = pending;
        return true;
      },
      deleteProperty() { throw new Error("State fields cannot be deleted through $state."); },
      defineProperty() { throw new Error("State fields cannot be defined through $state."); },
      preventExtensions() { throw new Error("State fields cannot be frozen, sealed, or made non-extensible."); },
      setPrototypeOf() { throw new Error("State prototypes cannot be changed through $state."); },
      has(_target, key) { return Boolean(state.values && own(state.values, key)); },
      ownKeys() { return state.values ? Reflect.ownKeys(state.values) : []; },
      getOwnPropertyDescriptor(_target, key) {
        return state.values && own(state.values, key)
          ? {configurable: true, enumerable: true, writable: true,
            value: state.values[key] && typeof state.values[key] === "object" ? nested(state.values[key]) : state.values[key]}
          : undefined;
      },
    });
    state.adopt = context => {
      if (!context) {
        state.contractEpoch += 1;
        state.values = null; state.pending = null; state.writable = null; state.nestedViews = null;
        return;
      }
      const incoming = context?.publicState || {};
      if (!state.values) {
        state.contractEpoch += 1;
        state.values = V.reactive(Object.assign(Object.create(null), clone(incoming)));
        state.pending = Object.create(null);
        state.nestedViews = new WeakMap();
      }
      state.writable = writableStateFields(context?.descriptor || {writableStateFields: []}, incoming);
      for (const key of Object.keys(state.pending)) if (!state.writable.has(key)) delete state.pending[key];
      for (const key of Object.keys(state.values)) if (!own(incoming, key) && !own(state.pending, key)) delete state.values[key];
      for (const [key, value] of Object.entries(incoming)) if (!own(state.pending, key)) state.values[key] = clone(value);
    };
    state.retire = () => {
      state.current = false; state.contractEpoch += 1;
      state.values = null; state.pending = null; state.writable = null; state.nestedViews = null;
    };
    state.adopt(initialContext);
    return state;
  }

  const controlLifetimes = new WeakMap();
  const eventTimingLifetimes = new WeakMap();
  const eventTimingDirectives = new WeakMap();
  const runtimeEventTimingDirectives = new WeakMap();
  const MAX_TIMER_DELAY = 2_147_483_647;
  function scheduleDelay(lifetime, milliseconds, callback) {
    let remaining = milliseconds;
    const schedule = () => {
      const chunk = Math.min(remaining, MAX_TIMER_DELAY);
      const started = performance.now();
      lifetime.timer = setTimeout(() => {
        lifetime.timer = 0;
        remaining -= Math.max(0, performance.now() - started);
        if (remaining <= 0) callback();
        else schedule();
      }, chunk);
    };
    schedule();
  }
  function releaseEventTiming(lifetime) {
    if (lifetime.timer) clearTimeout(lifetime.timer);
    lifetime.timer = 0;
    const byBinding = eventTimingLifetimes.get(lifetime.element);
    if (byBinding?.get(lifetime.bindingId) === lifetime) {
      byBinding.delete(lifetime.bindingId);
      if (byBinding.size === 0) eventTimingLifetimes.delete(lifetime.element);
    }
    lifetime.record.eventTimingLifetimes?.delete(lifetime);
    if (lifetime.kind === "poll") {
      const polling = lifetime.record.app.polling;
      polling?.lifetimes.delete(lifetime);
      if (polling?.lifetimes.size === 0) {
        document.removeEventListener("visibilitychange", polling.onVisibility);
        lifetime.record.app.polling = undefined;
      }
    }
  }
  function finishEventTiming(lifetime, value) {
    releaseEventTiming(lifetime);
    lifetime.resolve?.(value);
    lifetime.resolve = undefined;
  }
  function disposeEventTimings(record) {
    const lifetimes = record.eventTimingLifetimes;
    if (!lifetimes || lifetimes.size === 0) return;
    for (const lifetime of lifetimes) finishEventTiming(lifetime, undefined);
  }
  function stopAppPolling(app) {
    const polling = app.polling;
    if (!polling) return;
    for (const lifetime of polling.lifetimes) finishEventTiming(lifetime, undefined);
  }
  function eventTimingLifetime(record, element, bindingId, binding) {
    let byBinding = eventTimingLifetimes.get(element);
    if (!byBinding) {
      byBinding = new Map();
      eventTimingLifetimes.set(element, byBinding);
    }
    let lifetime = byBinding.get(bindingId);
    if (lifetime && (lifetime.record !== record || lifetime.binding !== binding)) {
      finishEventTiming(lifetime, undefined);
      lifetime = undefined;
      byBinding = eventTimingLifetimes.get(element);
      if (!byBinding) {
        byBinding = new Map();
        eventTimingLifetimes.set(element, byBinding);
      }
    }
    if (!lifetime) {
      lifetime = {record, element, bindingId, binding, timer: 0, last: -Infinity, resolve: undefined};
      byBinding.set(bindingId, lifetime);
      (record.eventTimingLifetimes ||= new Set()).add(lifetime);
    }
    return lifetime;
  }
  function disposeElementEventTimings(element, handles) {
    const byBinding = eventTimingLifetimes.get(element);
    if (byBinding) for (const handle of handles || []) {
      const lifetime = byBinding.get(handle.id);
      if (lifetime?.record === handle.record) finishEventTiming(lifetime, undefined);
    }
  }
  const timingDirectiveOwns = (element, record, bindingId, binding) =>
    [eventTimingDirectives.get(element), runtimeEventTimingDirectives.get(element)].some(handles =>
      handles?.some(handle => handle.record === record && handle.id === bindingId && handle.spec === binding),
    );
  const timedBindingIsCurrent = (record, element, bindingId, binding) =>
    record.app.mounted.get(record.occurrenceId)?.record === record && element.isConnected &&
    record.live.value?.preparedData?.eventBindings?.[bindingId] === binding;
  const pollBindingIsCurrent = lifetime =>
    !lifetime.record.app.terminal &&
    apps.get(lifetime.record.app.id) === lifetime.record.app &&
    lifetime.record.app.mounted.get(lifetime.record.occurrenceId)?.record === lifetime.record &&
    lifetime.element.isConnected &&
    eventTimingLifetimes.get(lifetime.element)?.get(lifetime.bindingId) === lifetime &&
    timingDirectiveOwns(lifetime.element, lifetime.record, lifetime.bindingId, lifetime.binding) &&
    lifetime.record.live.value?.preparedData?.pollBindings?.[lifetime.bindingId] === lifetime.binding;
  function reportPollFailure(lifetime, error) {
    const app = lifetime.record.app;
    const mounted = lifetime.record.app.mounted.get(lifetime.record.occurrenceId);
    finishEventTiming(lifetime, undefined);
    stopAppPolling(app);
    app.vueApp.config.errorHandler(error, mounted?.component, "Citry @c-poll");
  }
  function schedulePoll(lifetime) {
    if (lifetime.timer) clearTimeout(lifetime.timer);
    if (!pollBindingIsCurrent(lifetime)) { finishEventTiming(lifetime, undefined); return; }
    if (document.hidden) return;
    scheduleDelay(lifetime, lifetime.binding.interval, () => {
      if (!pollBindingIsCurrent(lifetime)) { finishEventTiming(lifetime, undefined); return; }
      if (document.hidden) return;
      schedulePoll(lifetime);
      if (lifetime.inFlight) return;
      let args;
      try {
        args = lifetime.args === undefined ? {} : lifetime.args();
        plain(args, "Citry polling arguments");
        args = cloneJsonValue(args, "Citry polling arguments");
      } catch (error) {
        reportPollFailure(lifetime, error);
        return;
      }
      if (!pollBindingIsCurrent(lifetime)) { finishEventTiming(lifetime, undefined); return; }
      lifetime.inFlight = true;
      Promise.resolve().then(() => {
        if (document.hidden) return undefined;
        if (!pollBindingIsCurrent(lifetime)) { finishEventTiming(lifetime, undefined); return undefined; }
        return lifetime.record.app.eventPoll(lifetime.record, lifetime.bindingId, args);
      })
        .catch(error => { if (!lifetime.record.app.terminal) reportPollFailure(lifetime, error); })
        .finally(() => { lifetime.inFlight = false; });
    });
  }
  function registerPoll(element, handle) {
    const lifetime = eventTimingLifetime(handle.record, element, handle.id, handle.spec);
    lifetime.kind = "poll";
    lifetime.args = handle.args;
    lifetime.inFlight = false;
    let polling = handle.record.app.polling;
    if (!polling) {
      polling = {lifetimes: new Set(), onVisibility: undefined};
      polling.onVisibility = () => {
        for (const current of polling.lifetimes) {
          if (document.hidden) {
            if (current.timer) clearTimeout(current.timer);
            current.timer = 0;
          } else schedulePoll(current);
        }
      };
      handle.record.app.polling = polling;
      document.addEventListener("visibilitychange", polling.onVisibility);
    }
    polling.lifetimes.add(lifetime);
    schedulePoll(lifetime);
  }
  const eventTimingSignature = handle => {
    const spec = handle.spec;
    return JSON.stringify([handle.record.occurrenceId, handle.record.generation, handle.id,
      spec.event, spec.handler, spec.args, spec.prevent, spec.stop, spec.self, spec.once,
      spec.key, spec.debounce, spec.throttle]);
  };
  function reconcileEventTimings(element, handles) {
    const prior = eventTimingDirectives.get(element) || [];
    const currentByKey = new Map(handles.map(handle => [handle.kind + ":" + handle.id, handle]));
    for (const old of prior) {
      const current = currentByKey.get(old.kind + ":" + old.id);
      if (current && current.record === old.record &&
          eventTimingSignature(current) === eventTimingSignature(old)) {
        const lifetime = eventTimingLifetimes.get(element)?.get(old.id);
        if (lifetime?.record === old.record && lifetime.binding === old.spec)
          lifetime.binding = current.spec;
        continue;
      }
      disposeElementEventTimings(element, [old]);
    }
    eventTimingDirectives.set(element, handles);
    const byBinding = eventTimingLifetimes.get(element);
    for (const handle of handles) {
      if (handle.kind !== "poll") continue;
      const old = prior.find(candidate => candidate.kind === "poll" && candidate.id === handle.id &&
        candidate.record === handle.record && candidate.spec === handle.spec);
      const lifetime = byBinding?.get(handle.id);
      if (old && lifetime?.record === handle.record && lifetime.binding === handle.spec) lifetime.args = handle.args;
      else registerPoll(element, handle);
    }
  }
  const textualInputTypes = new Set(["text","search","email","url","tel","password","date","datetime-local","month","time","week","color"]);
  const actionInputTypes = new Set(["button","submit","reset","image","file"]);
  function classifyControl(element, spec) {
    const tag = element.tagName.toLowerCase();
    if (tag === "input") {
      const raw = element.getAttribute("type");
      const type = raw == null || raw === "" ? "text" : raw.toLowerCase();
      if (type === "hidden") { if (spec.binding_mode !== "one-way") throw new Error("hidden controls support one-way State bindings only"); }
      else if (!textualInputTypes.has(type) && !["checkbox","radio","number","range"].includes(type))
        throw new Error(actionInputTypes.has(type) ? "action controls cannot be bound to State" : "unrecognized input type");
      if (spec.lazy && ["checkbox","radio"].includes(type)) throw new Error(".lazy has no effect on change controls");
      return {draft:["checkbox","radio"].includes(type)?"change":"input", flush:spec.on || (["checkbox","radio"].includes(type)||spec.lazy?"change":"input")};
    }
    if (tag === "select") { if (spec.lazy) throw new Error(".lazy has no effect on select controls"); return {draft:"change",flush:spec.on||"change"}; }
    if (tag === "textarea") return {draft:"input",flush:spec.on||(spec.lazy?"change":"input")};
    if (tag.includes("-")) {
      if (spec.binding_mode === "two-way" && !spec.on) throw new Error("two-way custom controls require .on:<event>");
      if (!customElements.get(tag)) return null;
      if (!("value" in element)) throw new Error("custom control has no value property");
      return {draft:spec.on,flush:spec.on};
    }
    throw new Error("element holds no value to bind");
  }
  function controlSignature(element, handles) {
    const tag = element.tagName.toLowerCase();
    const shape = tag === "input" ? element.getAttribute("type") || "text"
      : tag === "select" ? String(element.multiple) : tag;
    return shape + ":" + handles.map(handle => JSON.stringify(handle.spec)).join("|");
  }
  function controlEventName(element, spec) {
    if (spec.on) return spec.on;
    if (spec.lazy) return "change";
    const tag = element.tagName.toLowerCase();
    if (tag === "select" || tag === "input" && ["checkbox", "radio"].includes(element.type)) return "change";
    return "input";
  }
  function controlRead(element) {
    const tag = element.tagName.toLowerCase();
    if (tag === "select" && element.multiple)
      return [...element.selectedOptions].map(option => option.value);
    if (tag === "input" && element.type === "checkbox") return element.checked;
    if (tag === "input" && element.type === "radio") return element.checked;
    if (tag === "input" && ["number","range"].includes(element.type))
      return Number.isFinite(element.valueAsNumber) ? element.valueAsNumber : element.value;
    return element.value;
  }
  function controlWrite(element, value) {
    const tag = element.tagName.toLowerCase();
    const lifetime = controlLifetimes.get(element);
    if (lifetime) lifetime.writing = true;
    try {
    if (tag.includes("-")) { element.value = value; return; }
    if (tag === "input" && ["checkbox","radio"].includes(element.type)) {
      if (typeof value !== "boolean") throw new TypeError("checkbox and radio State values must be boolean");
      element.checked = value; return;
    }
    if (tag === "select" && element.multiple) {
      const selected = new Set(Array.isArray(value) && value.every(item => typeof item === "string") ? value : []);
      for (const option of element.options) option.selected = selected.has(option.value);
      return;
    }
    element.value = value == null ? "" : value;
    } finally { if (lifetime) lifetime.writing = false; }
  }
  function applyControlValue(element, value) {
    try { controlWrite(element, value); return true; }
    catch (error) { console.error("[Citry] could not apply State value to control:", error); return false; }
  }
  const controlReadFailures = new WeakMap();
  function adoptControlValue(element, record, field) {
    try {
      const value = controlRead(element);
      if (value === undefined) throw new TypeError("control value is unavailable");
      record.state.facade[field] = value;
      controlReadFailures.get(element)?.delete(field);
      return true;
    } catch (error) {
      let fields = controlReadFailures.get(element);
      if (!fields) { fields = new Set(); controlReadFailures.set(element, fields); }
      if (!fields.has(field)) {
        fields.add(field);
        console.error("[Citry] could not adopt control value into State:", error);
      }
      return false;
    }
  }
  function disposeControl(element) {
    const aggregate = controlLifetimes.get(element);
    if (!aggregate) return;
    aggregate.active = false;
    for (const token of aggregate.pending) { token.element = null; token.handles = null; token.aggregate = null; }
    aggregate.pending.clear();
    for (const lifetime of aggregate.children) {
      if (lifetime.listener) element.removeEventListener(lifetime.event, lifetime.listener);
      if (lifetime.draftListener) element.removeEventListener(lifetime.draftEvent, lifetime.draftListener);
      if (lifetime.timer) clearTimeout(lifetime.timer);
    }
    controlLifetimes.delete(element);
  }
  function installControl(element, handle, aggregate) {
    if (!handle || !handle.record || !handle.spec) throw new Error("Citry control binding is missing or stale");
    const {record, spec} = handle;
    let classification;
    try { classification = classifyControl(element, spec); }
    catch (error) { console.error("[Citry] invalid State control binding:", error); return; }
    if (classification === null) {
      const name = element.tagName.toLowerCase();
      const token = {element, handles:aggregate.handles, aggregate};
      aggregate.pending.add(token);
      customElements.whenDefined(name).then(() => {
        const target = token.element, handles = token.handles, owner = token.aggregate;
        token.element = null; token.handles = null; token.aggregate = null; owner?.pending.delete(token);
        if (target && handles && owner?.active && controlLifetimes.get(target) === owner && target.isConnected)
          installControls(target, handles);
      }, error => console.error("[Citry] custom control definition failed:", error));
      return;
    }
    const field = spec.field;
    applyControlValue(element, record.state.facade[field]);
    if (spec.binding_mode === "one-way") return;
    const event = classification.flush;
    const lifetime = {event, draftEvent:classification.draft, timer: 0, last: -Infinity, listener: null, draftListener:null, handle};
    aggregate.children.push(lifetime);
    const send = () => { void record.app.eventSend(record, spec.handler, {}).catch(() => {}); };
    const listener = domEvent => {
      if (aggregate.writing) return;
      if (spec.key && String(domEvent.key || "").toLowerCase() !== spec.key) return;
      if (!adoptControlValue(element, record, field)) return;
      if (spec.throttle !== null) {
        const now = performance.now();
        if (now - lifetime.last < spec.throttle) return;
        lifetime.last = now;
      }
      if (spec.debounce !== null) {
        if (lifetime.timer) clearTimeout(lifetime.timer);
        scheduleDelay(lifetime, spec.debounce, () => send());
      } else send();
    };
    lifetime.listener = listener;
    element.addEventListener(event, listener);
    if (classification.draft && classification.draft !== event) {
      lifetime.draftListener = () => {
        adoptControlValue(element, record, field);
      };
      element.addEventListener(classification.draft, lifetime.draftListener);
    }
  }
  function installControls(element, handles) {
    disposeControl(element);
    if (!Array.isArray(handles) || handles.length === 0) throw new Error("Citry control bindings are missing or stale");
    const aggregate = {handles,children:[],active:true,writing:false,signature:controlSignature(element, handles),pending:new Set()};
    controlLifetimes.set(element, aggregate);
    for (const handle of handles) installControl(element, handle, aggregate);
  }

  function createEventActivity(record, descriptor = null) {
    const view = V.reactive({
      total: 0,
      loading: Object.create(null),
      errors: Object.create(null),
      errorOrder: Object.create(null),
      nextStarted: 0,
      nextError: 0,
    });
    const activity = {
      descriptor,
      view,
      listeners: new Map(),
      loading(name) {
        if (name === undefined) return view.total > 0;
        return (view.loading[requireEventHandler(record, name)] ?? 0) > 0;
      },
      error(name) {
        if (name !== undefined) return view.errors[requireEventHandler(record, name)] || null;
        let selected = null, selectedOrder = -1;
        for (const [handler, error] of Object.entries(view.errors)) {
          const order = view.errorOrder[handler] ?? 0;
          if (order > selectedOrder) { selected = error; selectedOrder = order; }
        }
        return selected;
      },
      enqueue(handler) {
        requireEventHandler(record, handler);
        view.total += 1;
        view.loading[handler] = (view.loading[handler] ?? 0) + 1;
        return {handler, started: 0};
      },
      start(intent) {
        intent.started = ++view.nextStarted;
        activity.latestStarted[intent.handler] = intent.started;
      },
      succeed(intent) {
        if (activity.latestStarted[intent.handler] !== intent.started) return;
        delete view.errors[intent.handler];
        delete view.errorOrder[intent.handler];
      },
      fail(intent, error) {
        if (activity.latestStarted[intent.handler] !== intent.started) return;
        view.errors[intent.handler] = detached(error);
        view.errorOrder[intent.handler] = ++view.nextError;
      },
      finish(intent) {
        view.total = Math.max(0, view.total - 1);
        const count = (view.loading[intent.handler] ?? 0) - 1;
        if (count > 0) view.loading[intent.handler] = count;
        else delete view.loading[intent.handler];
      },
      subscribe(name, callback) {
        if (typeof name !== "string" || name.length === 0) throw new TypeError("$onEvent needs a non-empty event name");
        if (typeof callback !== "function") throw new TypeError("$onEvent needs a callback function");
        const listeners = activity.listeners.get(name) || new Set();
        listeners.add(callback);
        activity.listeners.set(name, listeners);
        let active = true;
        return () => {
          if (!active) return;
          active = false;
          listeners.delete(callback);
          if (!listeners.size) activity.listeners.delete(name);
        };
      },
      dispatch(name, detail) {
        const listeners = activity.listeners.get(name);
        if (!listeners) return;
        for (const callback of [...listeners]) {
          try { callback(detail); }
          catch (error) { queueMicrotask(() => { throw error; }); }
        }
      },
      dispose() {
        activity.listeners.clear();
      },
      latestStarted: Object.create(null),
    };
    return activity;
  }

  function typeOptions(appId, typeKey, userOptions) {
    userOptions = userOptions || {};
    if (userOptions.mixins || userOptions.extends) throw new Error("mixins and extends are unsupported by the js_data collision proof");
    const callback = userOptions.onServerRender;
    const userData = userOptions.data;
    const userSetup = userOptions.setup;
    const userBeforeCreate = userOptions.beforeCreate;
    const userCreated = userOptions.created;
    const userMounted = userOptions.mounted;
    const userBeforeUnmount = userOptions.beforeUnmount;
    const props = Array.isArray(userOptions.props) ? [...userOptions.props, "citryId"] : {...(userOptions.props || {}), citryId: {type: String, required: true}};
    const injectIsObject = userOptions.inject !== null && typeof userOptions.inject === "object" &&
      Object.getPrototypeOf(userOptions.inject) === Object.prototype;
    const injectedKeys = Array.isArray(userOptions.inject) ? userOptions.inject : injectIsObject ? Object.keys(userOptions.inject) : [];
    if (userOptions.inject !== undefined && (!Array.isArray(userOptions.inject) && !injectIsObject ||
        injectedKeys.some(key => typeof key !== "string")))
      throw new TypeError("inject must be a Vue array or plain object with string local names");
    const pluginContextNames = definitionRegistry(appId).templateContextNames;
    const propsKeys = Array.isArray(userOptions.props) ? userOptions.props : Object.keys(userOptions.props || {});
    const eventPublicNames = ["$loading", "$error", "$state", "$sendEvent", "$onEvent"];
    for (const name of eventPublicNames) if (propsKeys.includes(name) || injectedKeys.includes(name) ||
        own(userOptions.methods || {}, name) || own(userOptions.computed || {}, name))
      throw new Error("reserved Events public name collision: " + name);
    for (const name of pluginContextNames) {
      if (propsKeys.includes(name) || injectedKeys.includes(name) || own(userOptions.methods || {}, name) ||
          own(userOptions.computed || {}, name)) throw new Error("browser plugin template context collision: " + name);
    }
    const reservedOptionKeys = new Set([
      ...Object.keys(userOptions.methods || {}), ...Object.keys(userOptions.computed || {}), ...injectedKeys,
      ...pluginContextNames,
    ]);
    const reservedPublicNames = new Set(["preparedData", "$citryEvents", ...eventPublicNames, ...pluginContextNames]);
    const options = {...userOptions, name: userOptions.name || "CitryStable_" + typeKey, props};
    delete options.onServerRender;
    options.data = function () {
      const app = definitionRegistry(appId), occurrence = app.occurrences.get(this.citryId);
      if (!occurrence || occurrence.typeKey !== typeKey) throw new Error("unknown or wrong-type occurrence");
      const value = userData ? userData.call(this) : {};
      plain(value, "data() result");
      for (const key of Object.keys(value)) if (reservedPublicNames.has(key))
        throw new Error("reserved public data() collision: " + key);
      for (const key of Object.keys(occurrence.serverData)) if (own(value, key) || reservedOptionKeys.has(key)) throw new Error("js_data/local collision: " + key);
      return value;
    };
    if (userSetup) options.setup = function (props, context) {
      const value = userSetup(props, context);
      if (value === undefined) return undefined;
      if (typeof value === "function" || value instanceof Promise)
        throw new TypeError("setup must synchronously return a plain bindings object or undefined");
      plain(value, "setup() result");
      for (const key of Object.keys(value)) if (reservedPublicNames.has(key))
        throw new Error("reserved public setup() collision: " + key);
      return value;
    };
    options.beforeCreate = function () {
      const app = definitionRegistry(appId), occurrence = app.occurrences.get(this.citryId);
      if (!occurrence || occurrence.typeKey !== typeKey || app.mounted.has(occurrence.id)) throw new Error("invalid mounted occurrence");
      const generation = ++app.nextMountGeneration;
      const initialLive = app.snapshot.value.get(occurrence.id);
      const record = {app, occurrenceId: occurrence.id, parentId: occurrence.parentId, generation, live: V.shallowRef(initialLive), serverKeys: new Set(Object.keys(occurrence.serverData)), definition: V.shallowRef({id: occurrence.definitionId, render: null, cache: []}), callbackScope: undefined, callbackCleanup: undefined, callbackSubscriptions: undefined, applying: false, failed: false, events: null, state: null, controlHandles: new Map()};
      record.events = createEventActivity(record, occurrence.eventContext?.descriptor || null);
      record.state = createStateFacade(record, occurrence.eventContext);
      instanceRecords.set(this, record);
      const currentInstance = V.getCurrentInstance?.();
      if (currentInstance?.proxy) instanceRecords.set(currentInstance.proxy, record);
      if (currentInstance?.ctx) instanceRecords.set(currentInstance.ctx, record);
      for (const key of record.serverKeys) {
        if (reservedOptionKeys.has(key) || key in this) throw new Error("js_data/public instance collision: " + key);
        installServerKey(this, record, key);
      }
      if (reservedOptionKeys.has("preparedData") || "preparedData" in this) throw new Error("preparedData/public instance collision");
      Object.defineProperty(this, "preparedData", {enumerable: true, configurable: true, get() { return record.live.value?.preparedData || {}; }});
      Object.defineProperty(this, "$loading", {enumerable: false, configurable: true, value: record.events.loading});
      Object.defineProperty(this, "$error", {enumerable: false, configurable: true, value: record.events.error});
      Object.defineProperty(this, "$state", {enumerable: false, configurable: true, value: record.state.facade});
      Object.defineProperty(this, "$sendEvent", {enumerable: false, configurable: true, value: (name, args, opts) => {
        requireEventHandler(record, name);
        return record.app.eventSend(record, name, args, opts);
      }});
      Object.defineProperty(this, "$onEvent", {enumerable: false, configurable: true, value: (name, callback) => {
        if (!record.events?.descriptor)
          throw new Error("this component declares no Events class; $onEvent needs a component Events declaration");
        if (!record.events?.subscribe) throw new Error("Citry Events subscriptions are unavailable");
        return subscribeRecordEvent(record, name, callback);
      }});
      if (reservedOptionKeys.has("$citryEvents") || "$citryEvents" in this) throw new Error("$citryEvents/public instance collision");
      Object.defineProperty(this, "$citryEvents", {enumerable: false, configurable: true, value: Object.freeze({
        dispatch(bindingId, event, authoredArgs) {
          if (typeof record.app.eventDispatch !== "function") throw new Error("Citry Events bridge is unavailable");
          return record.app.eventDispatch(record, bindingId, event, authoredArgs);
        },
        dispatchComponent(bindingId, emittedValue, authoredArgs) {
          if (typeof record.app.eventDispatchComponent !== "function")
            throw new Error("Citry Events bridge is unavailable");
          return record.app.eventDispatchComponent(record, bindingId, emittedValue, authoredArgs);
        },
        componentRoot(childId) {
          if (typeof record.app.componentRoot !== "function")
            throw new Error("Citry Events component-root bridge is unavailable");
          return record.app.componentRoot(record, childId);
        },
        controls(bindingIds) {
          if (bindingIds === "") return Object.freeze([]);
          if (typeof bindingIds !== "string") throw new TypeError("Citry control binding ids must be a string");
          const bindings = record.live.value?.preparedData?.controlBindings;
          const ids = bindingIds.split(",");
          const specs = ids.map(id => bindings && bindings[id]);
          if (specs.some(spec => !spec)) throw new Error("Citry control binding is missing or stale");
          const prior = record.controlHandles.get(bindingIds);
          if (prior && prior.every((handle, index) => handle.spec === specs[index])) return prior;
          const handles = Object.freeze(specs.map(spec => Object.freeze({record, spec})));
          record.controlHandles.set(bindingIds, handles);
          return handles;
        },
        runtimeEvents(bindingIds) {
          if (bindingIds === "") return Object.freeze([]);
          if (typeof bindingIds !== "string") throw new TypeError("Citry runtime event binding ids must be a string");
          const ids = bindingIds.split(",");
          if (new Set(ids).size !== ids.length) throw new Error("Citry runtime event binding ids are duplicated");
          const eventBindings = record.live.value?.preparedData?.eventBindings;
          const pollBindings = record.live.value?.preparedData?.pollBindings;
          const resolved = ids.map(id => {
            if (/^citryRuntimeEvent[0-9a-f]+$/.test(id)) {
              const spec = eventBindings && eventBindings[id];
              validateRuntimeEventSpec(id, spec, {eventContext:{descriptor:record.events.descriptor}});
              return {kind:"event", spec};
            }
            if (/^citryRuntimePoll[0-9a-f]+$/.test(id)) {
              const spec = pollBindings && pollBindings[id];
              validateRuntimePollSpec(id, spec, {eventContext:{descriptor:record.events.descriptor}});
              return {kind:"poll", spec};
            }
            throw new Error("Citry runtime binding id has an invalid kind");
          });
          return Object.freeze(ids.map((id, index) => Object.freeze({
            kind: resolved[index].kind,
            record,
            id,
            spec: resolved[index].spec,
            args: undefined,
          })));
        },
        timings(bindingIds, pollEntries) {
          if (typeof bindingIds !== "string") throw new TypeError("Citry event timing ids must be a string");
          if (pollEntries !== undefined && !Array.isArray(pollEntries))
            throw new TypeError("Citry poll timing entries must be an array");
          if (bindingIds === "" && (pollEntries === undefined || pollEntries.length === 0))
            throw new TypeError("Citry timing requires an event or poll binding");
          const bindings = record.live.value?.preparedData?.eventBindings;
          const ids = bindingIds === "" ? [] : bindingIds.split(",");
          if (new Set(ids).size !== ids.length) throw new Error("Citry event timing ids are duplicated");
          const specs = ids.map(id => bindings && bindings[id]);
          if (specs.some(spec => !spec || spec.debounce === null && spec.throttle === null))
            throw new Error("Citry event timing binding is missing, stale, or untimed");
          const prior = record.eventTimingHandles?.get(bindingIds);
          const eventHandles = prior && prior.every((handle, index) => handle.spec === specs[index])
            ? prior
            : Object.freeze(ids.map((id, index) => Object.freeze({kind:"event", record, id, spec: specs[index]})));
          if (eventHandles !== prior) (record.eventTimingHandles ||= new Map()).set(bindingIds, eventHandles);
          if (pollEntries === undefined || pollEntries.length === 0) return eventHandles;
          const polls = record.live.value?.preparedData?.pollBindings;
          const seenPolls = new Set();
          const pollHandles = pollEntries.map(entry => {
            plain(entry, "Citry poll timing entry");
            if (Object.keys(entry).sort().join(",") !== "args,id" || typeof entry.id !== "string" ||
                !/^citryPoll[0-9a-f]+$/.test(entry.id) ||
                entry.args !== undefined && typeof entry.args !== "function" || seenPolls.has(entry.id))
              throw new TypeError("Citry poll timing entry is invalid or duplicated");
            seenPolls.add(entry.id);
            const spec = polls && polls[entry.id];
            if (!spec || Object.keys(spec).sort().join(",") !== "args,handler,id,interval" ||
                spec.id !== entry.id || typeof spec.handler !== "string" || spec.handler === "" ||
                spec.args !== null && typeof spec.args !== "string" ||
                !Number.isSafeInteger(spec.interval) || spec.interval <= 0)
              throw new Error("Citry poll timing binding is missing, stale, or invalid");
            return Object.freeze({kind:"poll", record, id:entry.id, spec, args:entry.args});
          });
          return pollHandles.length === 0 ? eventHandles : Object.freeze([...eventHandles, ...pollHandles]);
        },
      })});
      if (userBeforeCreate) userBeforeCreate.call(this);
    };
    options.created = function () {
      const record = instanceRecords.get(this), definition = record.app.definitions.get(record.definition.value.id);
      if (!definition) throw new Error("missing initial render definition: " + record.definition.value.id);
      record.definition.value = {id: record.definition.value.id, render: definition.render, cache: []};
      record.app.mounted.set(record.occurrenceId, {component: this, record});
      if (userCreated) userCreated.call(this);
    };
    options.render = function (...args) {
      const record = instanceRecords.get(this), definition = record.definition.value;
      if (!definition.render) throw new Error("render definition is unavailable");
      args[1] = definition.cache;
      return definition.render.apply(this, args);
    };
    options.mounted = function () {
      const record = instanceRecords.get(this);
      if (userMounted) userMounted.call(this);
      const transaction = record.app.transaction;
      if (transaction) {
        const generations = transaction.newMounts.get(record.occurrenceId) || [];
        generations.push(record.generation);
        transaction.newMounts.set(record.occurrenceId, generations);
      } else {
        const occurrence = record.app.occurrences.get(record.occurrenceId);
        const mounted = {stableId: record.occurrenceId, generation: record.generation, occurrence};
        const task = Promise.resolve(record.app.preparedHost?.onOccurrenceMounted(mounted))
          .then(() => runCallback(this, record, callback, record.app.revision))
          .catch(error => {
            record.app.terminal = true;
            record.app.initialError = error;
          })
          .finally(() => {
            record.app.initialTasks.delete(task);
          });
        record.app.initialTasks.add(task);
      }
    };
    options.beforeUnmount = function () {
      const record = instanceRecords.get(this);
      let error;
      if (record) {
        record.state.retire();
        try { dispose(record); }
        catch (caught) { error = caught; }
        finally {
          try {
            const transaction = record.app.transaction;
            const acceptedTransaction = transaction?.acceptedRetirementIds.has(record.occurrenceId) &&
              transaction.oldAcceptedRecords.get(record.occurrenceId)?.record === record
              ? transaction.acceptedTransaction : undefined;
            record.app.preparedHost?.onOccurrenceUnmounted({
              stableId: record.occurrenceId,
              generation: record.generation,
              acceptedTransaction,
            });
          } catch (caught) {
            if (error === undefined) error = caught;
            else console.error("[Citry] occurrence unmount failed:", caught);
          }
          if (record.app.mounted.get(record.occurrenceId)?.record === record) record.app.mounted.delete(record.occurrenceId);
          instanceRecords.delete(this);
        }
      }
      try { if (userBeforeUnmount) userBeforeUnmount.call(this); }
      catch (caught) { if (error === undefined) error = caught; else console.error("[Citry] beforeUnmount failed:", caught); }
      if (error !== undefined) throw error;
    };
    return options;
  }

  function defineType(appId, typeKey, userOptions) {
    const app = definitionRegistry(appId);
    if (typeof typeKey !== "string" || app.types.has(typeKey)) throw new Error("invalid or duplicate stable type");
    if (userOptions === undefined) userOptions = registeredTypeOptions.get(typeKey)?.options || {};
    const options = V.defineComponent(typeOptions(appId, typeKey, userOptions));
    app.types.set(typeKey, options);
    return options;
  }

  function registerTypeOptions(typeKey, sourceHash, options) {
    if (typeof typeKey !== "string" || typeof sourceHash !== "string" || !/^[0-9a-f]{64}$/.test(sourceHash))
      throw new Error("invalid Vue type options identity");
    if (typeof options === "function") options = {onServerRender: options};
    plain(options, "Vue type options");
    const prior = registeredTypeOptions.get(typeKey);
    if (prior) {
      if (prior.sourceHash !== sourceHash) throw new Error("Vue type options identity collision");
      return;
    }
    registeredTypeOptions.set(typeKey, Object.freeze({options, sourceHash}));
  }

  const loadedDefinitionUrls = new Map();
  const loadedScriptUrls = new Map();
  const loadedStyleUrls = new Map();
  function sriFromHex(value) {
    if (typeof value !== "string" || !/^[0-9a-f]{64}$/.test(value)) throw new Error("invalid definition digest");
    return "sha256-" + btoa(String.fromCharCode(...value.match(/../g).map(part => parseInt(part, 16))));
  }
  function canApplyOwnedIntegrity() {
    // A sandboxed iframe without allow-same-origin has an opaque origin.  Its
    // requests are cross-origin even when the URL points back to the hosting
    // site, so browsers require CORS before they can validate SRI.  Explicit
    // integrity supplied for an external asset is retained below.
    return global.origin !== "null";
  }
  function loadDefinition(asset, nonce) {
    if (global.CitryStableDefinitions?.[asset.id]) return Promise.resolve();
    const prior = loadedDefinitionUrls.get(asset.url);
    if (prior) return prior;
    const promise = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = asset.url;
      if (canApplyOwnedIntegrity()) script.integrity = sriFromHex(asset.sha256);
      if (nonce) script.nonce = nonce;
      const finish = callback => {
        script.onload = null;
        script.onerror = null;
        script.remove();
        callback();
      };
      script.onload = () => finish(() => resolve());
      script.onerror = () => finish(() => {
        loadedDefinitionUrls.delete(asset.url);
        reject(new Error("Citry Vue definition failed to load: " + asset.url));
      });
      document.head.append(script);
    });
    loadedDefinitionUrls.set(asset.url, promise);
    return promise;
  }
  function normalizeStyleAsset(asset, occurrenceTypes) {
    plain(asset, "prepared style asset");
    if (Object.keys(asset).sort().join(",") !== "lazyAllowed,owner,source" ||
        typeof asset.lazyAllowed !== "boolean")
      throw new Error("invalid prepared style asset");
    plain(asset.owner, "prepared style owner"); plain(asset.source, "prepared style source");
    if (asset.owner.kind === "component") {
      if (Object.keys(asset.owner).sort().join(",") !== "kind,occurrenceIds,typeKey" ||
          typeof asset.owner.typeKey !== "string" || !Array.isArray(asset.owner.occurrenceIds) ||
          !asset.owner.occurrenceIds.length || asset.owner.occurrenceIds.some(id => typeof id !== "string" ||
            (occurrenceTypes && occurrenceTypes.get(id) !== asset.owner.typeKey)) ||
          new Set(asset.owner.occurrenceIds).size !== asset.owner.occurrenceIds.length ||
          [...asset.owner.occurrenceIds].sort().some((id, index) => id !== asset.owner.occurrenceIds[index]))
        throw new Error("invalid prepared style asset");
    } else if (asset.owner.kind !== "extension" || Object.keys(asset.owner).sort().join(",") !== "extensionName,kind" ||
        typeof asset.owner.extensionName !== "string") throw new Error("invalid prepared style asset");
    normalizeAssetSource(asset.source, "style");
    return asset;
  }
  function normalizeScriptAsset(asset) {
    plain(asset, "prepared script asset");
    if (Object.keys(asset).sort().join(",") !== "lazyAllowed,owner,registersOptions,source" ||
        typeof asset.lazyAllowed !== "boolean" || typeof asset.registersOptions !== "boolean")
      throw new Error("invalid prepared script asset");
    plain(asset.owner, "prepared script owner");
    if (asset.owner.kind === "component") {
      if (Object.keys(asset.owner).sort().join(",") !== "kind,typeKey" || typeof asset.owner.typeKey !== "string")
        throw new Error("invalid prepared script asset");
    } else if (asset.owner.kind !== "extension" || Object.keys(asset.owner).sort().join(",") !== "extensionName,kind" ||
        typeof asset.owner.extensionName !== "string" || asset.registersOptions)
      throw new Error("invalid prepared script asset");
    normalizeAssetSource(asset.source, "script");
    return asset;
  }
  function normalizeAssetSource(source, elementKind) {
    if (source.kind === "owned") {
      if (typeof source.url !== "string" || typeof source.sha256 !== "string" ||
          !["kind,sha256,url", "attrs,kind,sha256,url"].includes(Object.keys(source).sort().join(",")))
        throw new Error("invalid prepared asset source");
      sriFromHex(source.sha256);
    } else if (source.kind === "external") {
      if (Object.keys(source).sort().join(",") !== "attrs,kind,url" || typeof source.url !== "string" || !plain(source.attrs, "prepared external asset attrs"))
        throw new Error("invalid prepared asset source");
    } else throw new Error("invalid prepared asset source");
    const attrs = source.attrs || {};
    const forbidden = elementKind === "script"
      ? new Set(["src", "nonce", "async", "defer", "nomodule"])
      : new Set(["href", "nonce"]);
    if (Object.entries(attrs).some(([name, value]) => typeof name !== "string" || !name ||
        (typeof value !== "string" && typeof value !== "boolean") || forbidden.has(name.toLowerCase())) ||
        (attrs.integrity !== undefined && (typeof attrs.integrity !== "string" || !validIntegrity(attrs.integrity))))
      throw new Error("invalid prepared asset source attributes");
    const aliases = name => Object.keys(attrs).filter(key => key.toLowerCase() === name);
    if (elementKind === "script") {
      const types = aliases("type");
      const classicTypes = new Set(["text/javascript", "application/javascript", "application/ecmascript",
        "application/x-ecmascript", "application/x-javascript", "text/ecmascript", "text/javascript1.0",
        "text/javascript1.1", "text/javascript1.2", "text/javascript1.3", "text/javascript1.4",
        "text/javascript1.5", "text/jscript", "text/livescript", "text/x-ecmascript", "text/x-javascript"]);
      if (types.length > 1 || types.length === 1 && (typeof attrs[types[0]] !== "string" ||
          !classicTypes.has(attrs[types[0]].trim().toLowerCase().split(";", 1)[0].trimEnd())))
        throw new Error("prepared scripts must use one classic JavaScript MIME type");
    } else {
      const rels = aliases("rel");
      if (rels.length > 1 || rels.length === 1 && (rels[0] !== "rel" || attrs.rel !== "stylesheet"))
        throw new Error("prepared stylesheets must retain canonical rel metadata");
    }
    return source;
  }
  function validIntegrity(value) {
    const tokens = value.trim().split(/\s+/).filter(Boolean), lengths = {sha256: 32, sha384: 48, sha512: 64};
    if (!tokens.length) return false;
    return tokens.every(token => {
      const separator = token.indexOf("-"), algorithm = token.slice(0, separator), encoded = token.slice(separator + 1);
      if (separator < 1 || !(algorithm in lengths) || !encoded || encoded.includes("?")) return false;
      const normalized = encoded.replaceAll("-", "+").replaceAll("_", "/");
      const padded = normalized + "=".repeat((4 - normalized.length % 4) % 4);
      try {
        const decoded = atob(padded);
        if (decoded.length !== lengths[algorithm]) return false;
        const canonical = btoa(decoded), urlsafe = canonical.replaceAll("+", "-").replaceAll("/", "_");
        return [canonical, canonical.replace(/=+$/, ""), urlsafe, urlsafe.replace(/=+$/, "")].includes(encoded);
      } catch { return false; }
    });
  }
  function assetIdentity(asset) {
    const source = asset.source;
    return JSON.stringify([source.kind, source.url, source.sha256 || null, Object.entries(source.attrs || {}).sort()]);
  }
  function assetRefs(asset) {
    return asset.owner.kind === "component" ? new Set(asset.owner.occurrenceIds) : new Set(["extension:" + asset.owner.extensionName]);
  }
  function applyAssetSource(element, source, nonce) {
    const attrs = source.attrs || {};
    for (const [name, value] of Object.entries(attrs)) {
      if (name.toLowerCase() === "nonce") throw new Error("prepared assets cannot replace the bootstrap nonce");
      if (value === true) element.setAttribute(name, ""); else if (value !== false) element.setAttribute(name, value);
    }
    if (source.kind === "owned" && canApplyOwnedIntegrity() &&
        !Object.keys(attrs).some(name => name.toLowerCase() === "integrity"))
      element.integrity = sriFromHex(source.sha256);
    if (nonce) element.nonce = nonce;
  }
  function styleRecordKey(appId, url) {
    return JSON.stringify([appId, url]);
  }
  function scriptRecordKey(appId, asset) {
    return asset.owner.kind === "extension" ? JSON.stringify([appId, asset.source.url]) : asset.source.url;
  }
  function existingStyleElement(appId, url) {
    return [...document.querySelectorAll('[data-citry-vue-style-app][data-citry-css-url]')]
      .find(element => element.getAttribute("data-citry-vue-style-app") === appId &&
        element.getAttribute("data-citry-css-url") === url) || null;
  }
  function retireUnusedStyles() {
    for (const [key, record] of loadedStyleUrls) if (!record.refs.size && !record.stages.size) {
      record.element?.remove();
      loadedStyleUrls.delete(key);
    }
  }
  function abortStyleStage(stage) {
    if (!stage) return;
    for (const record of loadedStyleUrls.values()) record.stages.delete(stage.token);
    retireUnusedStyles();
  }
  function commitStyleStage(appId, stage) {
    for (const record of loadedStyleUrls.values()) {
      const prior = record.refs.get(appId);
      if (prior) {
        for (const id of stage.replacedIds) prior.delete(id);
        if (!prior.size) record.refs.delete(appId);
      }
      record.stages.delete(stage.token);
    }
    for (const [url, ids] of stage.refs) {
      const record = loadedStyleUrls.get(styleRecordKey(appId, url));
      if (!record) throw new Error("prepared stylesheet disappeared before commit");
      const refs = record.refs.get(appId) || new Set();
      for (const id of ids) refs.add(id);
      record.refs.set(appId, refs);
    }
    retireUnusedStyles();
  }
  function releaseAppStyles(appId) {
    for (const record of loadedStyleUrls.values()) record.refs.delete(appId);
    retireUnusedStyles();
  }
  function releaseAppScripts(appId) {
    for (const [key, record] of loadedScriptUrls) {
      if (record.appId === appId) loadedScriptUrls.delete(key);
    }
  }
  function loadStyle(appId, asset, nonce, stage, knownInitial = false) {
    const key = styleRecordKey(appId, asset.source.url);
    const prior = loadedStyleUrls.get(key);
    if (prior) {
      if (prior.identity !== assetIdentity(asset))
        throw new Error("prepared stylesheet URL identity collision");
      if (stage) prior.stages.add(stage.token);
      return prior.promise;
    }
    if (!knownInitial && !asset.lazyAllowed)
      throw new Error("lazy stylesheet loading is unsupported after custom dependency hooks");
    const link = document.createElement("link");
    const record = {element: link, refs: new Map(), stages: new Set(stage ? [stage.token] : []),
      identity: assetIdentity(asset)};
    record.promise = new Promise((resolve, reject) => {
      link.rel = "stylesheet";
      link.href = asset.source.url;
      link.setAttribute("data-citry-vue-style-app", appId);
      link.setAttribute("data-citry-css-url", asset.source.url);
      applyAssetSource(link, asset.source, nonce);
      link.onload = resolve;
      link.onerror = () => {
        reject(new Error("Citry Vue stylesheet failed to load: " + asset.source.url));
        if (loadedStyleUrls.get(key) === record) {
          loadedStyleUrls.delete(key);
          link.remove();
        }
      };
      document.head.append(link);
    });
    loadedStyleUrls.set(key, record);
    return record.promise;
  }
  function loadTypeScript(appId, asset, nonce, knownInitial = false) {
    normalizeScriptAsset(asset);
    const key = scriptRecordKey(appId, asset), prior = loadedScriptUrls.get(key);
    const identity = assetIdentity(asset);
    if (prior) {
      if (prior.identity !== identity) throw new Error("prepared script URL identity collision");
      return prior.promise;
    }
    if (!knownInitial && !asset.lazyAllowed)
      throw new Error("lazy type script loading is unsupported after custom dependency hooks");
    const record = {appId: asset.owner.kind === "extension" ? appId : null, identity, promise: null};
    record.promise = new Promise((resolve, reject) => {
      const script = document.createElement("script");
      script.src = asset.source.url;
      applyAssetSource(script, asset.source, nonce);
      const finish = callback => {
        script.onload = null;
        script.onerror = null;
        script.remove();
        callback();
      };
      script.onload = () => finish(() => {
        if (asset.registersOptions && (asset.owner.kind !== "component" || !registeredTypeOptions.has(asset.owner.typeKey))) {
          if (loadedScriptUrls.get(key) === record) loadedScriptUrls.delete(key);
          reject(new Error("Citry Vue type script did not register its declared Options"));
        } else resolve();
      });
      script.onerror = () => finish(() => {
        if (loadedScriptUrls.get(key) === record) loadedScriptUrls.delete(key);
        reject(new Error("Citry Vue type script failed to load: " + asset.source.url));
      });
      document.head.append(script);
    });
    loadedScriptUrls.set(key, record);
    return record.promise;
  }

  function waitForStartup(value, lifecycle) {
    if (!lifecycle?.signal) return value;
    lifecycle.guard();
    if (lifecycle.signal.aborted)
      return Promise.reject(lifecycle.signal.reason || new Error("Citry Vue startup was cancelled"));
    return new Promise((resolve, reject) => {
      let signal = lifecycle.signal;
      const release = () => {
        signal?.removeEventListener("abort", cancelled);
        signal = null;
      };
      const cancelled = () => {
        const reason = signal?.reason;
        release();
        reject(reason || new Error("Citry Vue startup was cancelled"));
      };
      signal.addEventListener("abort", cancelled, {once: true});
      Promise.resolve(value).then(
        result => { release(); resolve(result); },
        error => { release(); reject(error); },
      );
    });
  }

  function validateCandidateAssets(appId, scripts, styles, occurrenceTypes, extensionNames, configuration,
      enforceLazy) {
    const normalizedScripts = scripts.map(asset => normalizeScriptAsset(asset));
    const normalizedStyles = styles.map(asset => normalizeStyleAsset(asset, occurrenceTypes));
    const candidates = [
      [normalizedScripts, loadedScriptUrls, asset => scriptRecordKey(appId, asset), "script"],
      [normalizedStyles, loadedStyleUrls, asset => styleRecordKey(appId, asset.source.url), "stylesheet"],
    ];
    for (const [assets, live, keyFor, label] of candidates) {
      const seen = new Map();
      for (const asset of assets) {
        if (asset.owner.kind === "extension" && !extensionNames.has(asset.owner.extensionName))
          throw new Error("prepared asset references an uninstalled browser extension");
        const key = keyFor(asset), prior = seen.get(key) || live.get(key);
        if (prior && prior.identity !== assetIdentity(asset))
          throw new Error(`prepared ${label} URL identity collision`);
        seen.set(key, {identity: assetIdentity(asset)});
        if (enforceLazy && !live.has(key)) {
          if (asset.lazyAllowed !== true) throw new Error(`prepared unseen ${label} asset disallows lazy loading`);
          if (asset.owner.kind === "component" && configuration.allowLazyTypeAssets !== true)
            throw new Error("lazy type assets are unsupported by this dependency or JavaScript policy");
        }
      }
    }
    return {scripts: normalizedScripts, styles: normalizedStyles};
  }

  async function primeInitialAssets(manifest, configuration, extensionNames, lifecycle) {
    if (!Array.isArray(manifest.scripts) || !Array.isArray(manifest.styles) || !Array.isArray(manifest.typePolicies))
      throw new Error("prepared manifest dependency assets must be arrays");
    normalizeTypePolicies(manifest.typePolicies);
    const initialTypes = new Map(manifest.occurrences.map(item => [item.id, item.typeKey]));
    const {scripts: normalizedScripts, styles: normalizedStyles} = validateCandidateAssets(
      manifest.appId, manifest.scripts, manifest.styles, initialTypes, extensionNames, configuration, false);
    const initialStyleStage = configuration.loadInitialAssets === true ? {
      token: Symbol("initial-style-stage"),
      refs: new Map(),
      replacedIds: new Set(),
    } : null;
    try {
    if (configuration.loadInitialAssets !== true) {
      for (const asset of normalizedScripts) if (asset.registersOptions &&
          (asset.owner.kind !== "component" || !registeredTypeOptions.has(asset.owner.typeKey)))
        throw new Error("initial Citry Vue type Options were not emitted before bootstrap");
      for (const asset of normalizedStyles) {
        const key = styleRecordKey(manifest.appId, asset.source.url);
        if (!loadedStyleUrls.has(key) && !existingStyleElement(manifest.appId, asset.source.url))
          throw new Error("initial Citry Vue stylesheet was not emitted before bootstrap");
      }
    }
    if (configuration.loadInitialAssets === true) {
      await waitForStartup(
        Promise.all(normalizedStyles.map(asset =>
          loadStyle(manifest.appId, asset, configuration.nonce, initialStyleStage, true))),
        lifecycle,
      );
      lifecycle?.guard();
      for (const asset of normalizedScripts) {
        await waitForStartup(loadTypeScript(manifest.appId, asset, configuration.nonce, true), lifecycle);
        lifecycle?.guard();
      }
    }
    for (const [assets, loaded, name] of [[manifest.scripts, loadedScriptUrls, "script"]]) {
      for (const asset of assets) {
        if (name === "script" && asset.registersOptions &&
            (asset.owner.kind !== "component" || !registeredTypeOptions.has(asset.owner.typeKey)))
          throw new Error("initial Citry Vue type Options were not emitted before bootstrap");
        const key = scriptRecordKey(manifest.appId, asset);
        const prior = loaded.get(key), identity = assetIdentity(asset);
        if (prior && prior.identity !== identity) throw new Error("prepared script URL identity collision");
        if (!prior) loaded.set(key, {
          appId: asset.owner.kind === "extension" ? manifest.appId : null,
          identity,
          promise: Promise.resolve(),
        });
      }
    }
    for (const rawAsset of manifest.styles) {
      const asset = normalizeStyleAsset(rawAsset, initialTypes);
      if (asset.owner.kind === "extension" && !extensionNames.has(asset.owner.extensionName))
        throw new Error("prepared asset references an uninstalled browser extension");
      const key = styleRecordKey(manifest.appId, asset.source.url);
      let record = loadedStyleUrls.get(key);
      if (!record) {
        const element = existingStyleElement(manifest.appId, asset.source.url);
        if (!element) throw new Error("initial Citry Vue stylesheet was not emitted before bootstrap");
        record = {element, refs: new Map(), stages: new Set(), promise: Promise.resolve(),
          identity: assetIdentity(asset)};
        loadedStyleUrls.set(key, record);
      } else if (record.identity !== assetIdentity(asset)) {
        throw new Error("prepared stylesheet URL identity collision");
      }
      const refs = record.refs.get(manifest.appId) || new Set();
      for (const id of assetRefs(asset)) refs.add(id);
      record.refs.set(manifest.appId, refs);
    }
    } finally {
      abortStyleStage(initialStyleStage);
    }
  }

  function normalizeTypePolicies(values) {
    const policies = new Map();
    for (const value of values) {
      plain(value, "prepared type policy");
      if (typeof value.typeKey !== "string" || typeof value.lazyAllowed !== "boolean" ||
          Object.keys(value).sort().join(",") !== "lazyAllowed,typeKey" || policies.has(value.typeKey))
        throw new Error("invalid prepared type policy");
      policies.set(value.typeKey, value.lazyAllowed);
    }
    return policies;
  }

  async function startPreparedOwned(configuration, lifecycle, startAttempt) {
    if (lifecycle) configuration = {...configuration, nonce: lifecycle.nonce};
    plain(configuration, "prepared bootstrap");
    const manifest = plain(configuration.manifest, "prepared manifest");
    const hostElement = typeof configuration.host === "string" ? document.querySelector(configuration.host) : configuration.host;
    if (!(hostElement instanceof Element) || !plain(configuration.tags, "component tags"))
      throw new Error("prepared bootstrap needs one host element and component tags");
    const appId = manifest.appId, registered = new Set(), contexts = new Map(), sources = new Map();
    const pluginEntries = extensionEntries(manifest.extensions || {}), plugins = new Map();
    let staged = null;
    if (!Array.isArray(manifest.definitions) || !Array.isArray(manifest.occurrences))
      throw new Error("prepared manifest lacks definitions or occurrences");
    const declaredDefinitions = preflightDefinitions(
      {definitions: new Map()}, manifest.definitions, manifest.occurrences, manifest.rootId);
    configure(manifest, startAttempt);
    definitionRegistry(appId).hostElement = hostElement;
    const claimedContextNames = new Set();
    for (const [, item] of pluginEntries) for (const name of item.templateContextNames) {
      if (claimedContextNames.has(name)) throw new Error("duplicate browser plugin template context claim: " + name);
      claimedContextNames.add(name);
    }
    definitionRegistry(appId).templateContextNames = Object.freeze([...claimedContextNames].sort());
    await waitForStartup(
      primeInitialAssets(manifest, configuration, new Set(pluginEntries.map(([name]) => name)), lifecycle),
      lifecycle,
    );
    lifecycle?.guard();
    for (const asset of manifest.definitions) {
      await waitForStartup(loadDefinition(asset, configuration.nonce), lifecycle);
      lifecycle?.guard();
    }
    for (const asset of manifest.definitions) {
      registerDefinition(appId, asset.id, global.CitryStableDefinitions?.[asset.id], declaredDefinitions.get(asset.id));
      registered.add(asset.id);
    }
    const componentTypes = {};
    const initialTypeTags = new Map(Object.entries(configuration.tags));
    for (const definition of definitionRegistry(appId).definitions.values()) {
      for (const call of [...definition.localCalls, ...definition.localCallRuns]) {
        const prior = initialTypeTags.get(call.typeKey);
        if (prior && prior !== call.componentTag) throw new Error("prepared stable type has conflicting component tags");
        initialTypeTags.set(call.typeKey, call.componentTag);
      }
    }
    const pluginHost = Object.freeze({
      appId,
      vue: V,
      occurrenceId(component) {
        const record = instanceRecords.get(component);
        return record?.app.id === appId ? record.occurrenceId : null;
      },
      occurrence(id) { return definitionRegistry(appId).occurrences.get(id) || null; },
      revision() { return definitionRegistry(appId).revision; },
    });
    const cleanupPluginStages = (values, method) => {
      for (const item of [...values].reverse()) {
        try { item.plugin[method](item.stage); }
        catch (error) { console.error("[Citry] browser plugin " + method + " failed:", error); }
      }
    };
    const activatedInitialPlugins = [];
    try {
      for (const [name, item] of pluginEntries) {
        const registration = browserPluginFactories.get(name);
        if (!registration || registration.schemaVersion !== item.schemaVersion ||
            JSON.stringify(registration.templateContextNames) !== JSON.stringify(item.templateContextNames))
          throw new Error("missing or incompatible Citry browser plugin: " + name);
        const plugin = registration.factory(pluginHost);
        if (!plugin || typeof plugin.install !== "function" || typeof plugin.prepareRevision !== "function" ||
            typeof plugin.activateRevision !== "function" || typeof plugin.commitRevision !== "function" ||
            typeof plugin.abortRevision !== "function" || typeof plugin.rollbackRevision !== "function" ||
            typeof plugin.dispose !== "function")
          throw new Error("invalid Citry browser plugin factory result: " + name);
        plugins.set(name, {plugin, stage: null});
        const stage = await waitForStartup(plugin.prepareRevision(detached(item.payload), detached(manifest)), lifecycle);
        lifecycle?.guard();
        plugins.set(name, {plugin, stage});
      }
      lifecycle?.guard();
      for (const item of plugins.values()) {
        activatedInitialPlugins.push(item);
        item.plugin.activateRevision(item.stage);
      }
    } catch (error) {
      cleanupPluginStages(activatedInitialPlugins, "rollbackRevision");
      const activated = new Set(activatedInitialPlugins);
      cleanupPluginStages([...plugins.values()].filter(item => item.stage !== null && !activated.has(item)), "abortRevision");
      releaseAppStyles(appId);
      releaseAppScripts(appId);
      apps.delete(appId);
      for (const {plugin} of plugins.values()) {
        try { plugin.dispose(); } catch (disposeError) { console.error("[Citry] browser plugin dispose failed:", disposeError); }
      }
      throw error;
    }
    definitionRegistry(appId).browserPlugins = [...plugins.values()].map(item => item.plugin);
    definitionRegistry(appId).initialPluginStages = [...plugins.values()];
    const ownedApp = definitionRegistry(appId);
    const firstLiveElement = (vnode, seen = new Set()) => {
      if (!vnode || typeof vnode !== "object" || seen.has(vnode)) return null;
      seen.add(vnode);
      const nested = vnode.component?.subTree;
      if (nested) {
        const element = firstLiveElement(nested, seen);
        if (element) return element;
      }
      if (vnode.type === V.Static && vnode.el instanceof Node && vnode.anchor instanceof Node) {
        let node = vnode.el;
        while (node) {
          if (node instanceof Element && node.isConnected) return node;
          if (node === vnode.anchor) break;
          node = node.nextSibling;
        }
      }
      if (vnode.el instanceof Element && vnode.el.isConnected) return vnode.el;
      if (Array.isArray(vnode.children)) for (const child of vnode.children) {
        const element = firstLiveElement(child, seen);
        if (element) return element;
      }
      return null;
    };
    const liveComponentCarrier = component => {
      const element = firstLiveElement(component?.$?.subTree);
      if (element) return element;
      const root = component?.$el;
      if (typeof Node === "function" && root instanceof Node && root.isConnected) return root;
      throw new Error("Citry Events component has no live DOM root");
    };
    const dispatchCarrier = source => {
      if (!source || sources.get(source.stableId)?.generation !== source.generation)
        throw new Error("Citry Events dispatch source is stale or retired");
      const mounted = ownedApp.mounted.get(source.stableId);
      if (!mounted || mounted.record.generation !== source.generation)
        throw new Error("Citry Events dispatch source is stale or retired");
      return liveComponentCarrier(mounted.component);
    };
    const liveRootElements = (component, seen = new Set(), output = []) => {
      const visit = vnode => {
        if (!vnode || typeof vnode !== "object" || seen.has(vnode)) return;
        seen.add(vnode);
        if (vnode.component?.subTree) { visit(vnode.component.subTree); return; }
        if (vnode.type === V.Fragment && Array.isArray(vnode.children)) {
          for (const child of vnode.children) visit(child);
          return;
        }
        if (typeof Element === "function" && vnode.el instanceof Element && vnode.el.isConnected) {
          if (!output.includes(vnode.el)) output.push(vnode.el);
          return;
        }
        if (Array.isArray(vnode.children)) for (const child of vnode.children) visit(child);
      };
      visit(component?.$?.subTree);
      if (!output.length && typeof Element === "function" && component?.$el instanceof Element && component.$el.isConnected)
        output.push(component.$el);
      return output;
    };
    const componentContains = (component, element) =>
      liveRootElements(component).some(root => root === element || root.contains(element));
    ownedApp.componentRoot = (record, childId) => {
      if (record?.app !== ownedApp || ownedApp.mounted.get(record.occurrenceId)?.record !== record)
        throw new Error("Citry component event source is stale or retired");
      if (typeof childId !== "string" || childId.length === 0)
        throw new TypeError("Citry component event child id must be a non-empty string");
      const child = ownedApp.occurrences.get(childId);
      if (!child)
        throw new Error("Citry component event child is not a descendant of its source");
      let cursor = child.parentId;
      while (cursor !== null && cursor !== record.occurrenceId)
        cursor = ownedApp.occurrences.get(cursor)?.parentId ?? null;
      if (cursor !== record.occurrenceId)
        throw new Error("Citry component event child is not a descendant of its source");
      const mounted = ownedApp.mounted.get(childId);
      if (!mounted || mounted.record.app !== ownedApp || mounted.record.occurrenceId !== childId)
        throw new Error("Citry component event child is stale or retired");
      return liveComponentCarrier(mounted.component);
    };
    const sourceForElement = element => {
      if (typeof Element !== "function" || !(element instanceof Element) || !element.isConnected) return null;
      const candidates = [];
      for (const [id, mounted] of ownedApp.mounted) {
        if (!componentContains(mounted.component, element)) continue;
        let depth = 0, cursor = id;
        while (ownedApp.occurrences.get(cursor)?.parentId !== null) {
          depth += 1;
          cursor = ownedApp.occurrences.get(cursor).parentId;
        }
        const source = sources.get(id);
        if (source?.generation === mounted.record.generation) candidates.push({source, depth});
      }
      candidates.sort((left, right) => right.depth - left.depth);
      return candidates[0]?.source || null;
    };
    const sourceForTarget = target => {
      if (typeof target === "string") {
        const renderId = target.startsWith("render:") ? target.slice("render:".length) : target;
        for (const occurrence of ownedApp.occurrences.values()) {
          if (occurrence.renderId !== renderId) continue;
          const mounted = ownedApp.mounted.get(occurrence.id), source = sources.get(occurrence.id);
          if (mounted && source?.generation === mounted.record.generation) return source;
          return null;
        }
        return null;
      }
      return sourceForElement(target);
    };
    for (const typeKey of new Set(manifest.occurrences.map(item => item.typeKey))) {
      let options = registeredTypeOptions.get(typeKey)?.options || {};
      for (const plugin of definitionRegistry(appId).browserPlugins) if (typeof plugin.decorateTypeOptions === "function")
        options = plugin.decorateTypeOptions(typeKey, options);
      componentTypes[typeKey] = defineTypeWithCallback(appId, typeKey, options);
    }
    const cleanupEventAttempt = (attempt, reason = new Error("prepared Events render was cancelled")) => {
      if (!attempt || attempt.cleaned || attempt.published) return;
      attempt.aborted = true;
      attempt.abortReason ||= reason;
      attempt.rejectCancellation?.(attempt.abortReason);
      abortStyleStage(attempt.styleStage);
      for (const item of attempt.pluginStages || []) {
        if (item.cleaned || !item.hasStage) continue;
        item.cleaned = true;
        try { item.plugin[item.attempted ? "rollbackRevision" : "abortRevision"](item.stage); }
        catch (error) { console.error("[Citry] Events plugin stage cleanup failed:", error); }
      }
      attempt.cleaned = true;
      if (staged === attempt) staged = null;
    };
    const validateAddresses = (values, requireAddresses) => {
      const byRender = new Map();
      const addressed = values.filter(item => own(item, "renderId"));
      if ((requireAddresses && addressed.length !== values.length) ||
          (addressed.length !== 0 && addressed.length !== values.length))
        throw new Error("prepared Events occurrence addresses are incomplete");
      for (const occurrence of addressed) {
        if (typeof occurrence.renderId !== "string" || !/^[a-z0-9_-]+$/.test(occurrence.renderId) ||
            byRender.has(occurrence.renderId))
          throw new Error("prepared Events occurrence address is invalid or duplicated");
        if (occurrence.eventContext && occurrence.eventContext.serverRenderId !== occurrence.renderId)
          throw new Error("prepared Events occurrence address disagrees with its event context");
        byRender.set(occurrence.renderId, occurrence);
      }
      return byRender;
    };
    const addressSnapshot = (requireAddresses = false) =>
      validateAddresses([...ownedApp.occurrences.values()], requireAddresses);
    const translateTargetEnvelope = (rawEnvelope, target, allocator) => {
      const envelope = clone(rawEnvelope), incoming = new Map(envelope.occurrences.map(item => [item.id, item]));
      if (incoming.size !== envelope.occurrences.length || !incoming.has(envelope.rootId))
        throw new Error("invalid isolated prepared target snapshot");
      for (const item of incoming.values()) if (typeof item.id !== "string" ||
          !/^citryOccurrence[0-9A-Za-z]+$/.test(item.id))
        throw new Error("prepared Events incoming occurrence ID is invalid");
      validateGraph(incoming, envelope.rootId);
      normalizeMarkers(envelope.markers, incoming);
      const existingChildren = new Map();
      for (const item of ownedApp.occurrences.values()) {
        const key = item.parentId;
        if (!existingChildren.has(key)) existingChildren.set(key, []);
        existingChildren.get(key).push(item);
      }
      const incomingChildren = new Map();
      for (const item of incoming.values()) {
        if (!incomingChildren.has(item.parentId)) incomingChildren.set(item.parentId, []);
        incomingChildren.get(item.parentId).push(item);
      }
      const occupied = allocator.occupied;
      const reserved = allocator.reserved;
      const claimedExisting = allocator.claimedExisting;
      const mapped = new Map([[envelope.rootId, target.id]]);
      claimedExisting.add(target.id);
      const visit = oldParent => {
        const newParent = mapped.get(oldParent);
        const candidates = existingChildren.get(newParent) || [];
        for (const child of incomingChildren.get(oldParent) || []) {
          const match = candidates.find(item => !claimedExisting.has(item.id) &&
            item.placementKey === child.placementKey && item.typeKey === child.typeKey);
          let id;
          if (match) id = match.id;
          else {
            if (!occupied.has(child.id)) id = child.id;
            if (!id) {
              do id = `citryOccurrenceTranslated${envelope.revision}${allocator.ordinal++}`;
              while (reserved.has(id));
            }
            reserved.add(id);
            occupied.add(id);
          }
          claimedExisting.add(id);
          mapped.set(child.id, id); visit(child.id);
        }
      };
      visit(envelope.rootId);
      const resolve = id => {
        if (typeof id !== "string" || !mapped.has(id)) throw new Error("prepared target references an unknown incoming occurrence");
        return mapped.get(id);
      };
      const translatePreparedData = value => {
        const prepared = clone(value);
        for (const call of Object.values(prepared.calls || {})) {
          if (call.key !== call.id) throw new Error("prepared component call key must equal its occurrence id");
          call.id = resolve(call.id); call.key = call.id;
          if (typeof call.parentId === "string") call.parentId = resolve(call.parentId);
        }
        for (const ids of Object.values(prepared.callRuns || {})) for (let index = 0; index < ids.length; index += 1)
          ids[index] = resolve(ids[index]);
        return prepared;
      };
      envelope.rootId = resolve(envelope.rootId);
      envelope.updatedIds = envelope.updatedIds.map(resolve).sort();
      envelope.occurrences = envelope.occurrences.map(item => ({...item, id: resolve(item.id),
        parentId: item.parentId === null ? null : resolve(item.parentId), preparedData: translatePreparedData(item.preparedData)}));
      envelope.markers = envelope.markers.map(item => ({...item,
        ownerId: resolve(item.ownerId), occurrenceId: resolve(item.occurrenceId)})).sort((a,b) => {
        const left = `${a.ownerId}\0${a.name}\0${a.occurrenceId}`;
        const right = `${b.ownerId}\0${b.name}\0${b.occurrenceId}`;
        return left < right ? -1 : left > right ? 1 : 0;
      });
      envelope.replacements = envelope.replacements.map(item => ({...item, ownerId: resolve(item.ownerId),
        expectedRemountIds: item.expectedRemountIds.map(resolve).sort()})).sort((a,b) => {
        const left = `${a.ownerId}\0${a.siteId}`, right = `${b.ownerId}\0${b.siteId}`;
        return left < right ? -1 : left > right ? 1 : 0;
      });
      for (const style of envelope.styles || []) if (style.owner?.kind === "component" && Array.isArray(style.owner.occurrenceIds))
        style.owner.occurrenceIds = style.owner.occurrenceIds.map(resolve).sort();
      for (const [name, extension] of extensionEntries(envelope.extensions || {})) {
        const plugin = plugins.get(name)?.plugin;
        if ([...mapped].some(([before, after]) => before !== after)) {
          if (typeof plugin?.translateRevision !== "function") throw new Error("browser plugin cannot translate occurrence identities: " + name);
          const translated = plugin.translateRevision(detached(extension.payload), resolve);
          if (translated && typeof translated.then === "function") throw new Error("browser plugin occurrence translation must be synchronous: " + name);
          envelope.extensions[name] = {...extension, payload: detached(translated)};
        }
      }
      return envelope;
    };
    const host = {
      appId(source) { return sources.get(source.stableId)?.generation === source.generation ? appId : ""; },
      resolve(source) { return sources.get(source.stableId)?.generation === source.generation ? contexts.get(source.stableId) || null : null; },
      revision(source) { return sources.get(source.stableId)?.generation === source.generation ? definitionRegistry(appId).revision : -1; },
      resolveTarget(target) { return sourceForTarget(target); },
      preflightResult(result, source) {
        const renders = result.ok ? result.actions.filter(action => action.action === "render") : [];
        if (!renders.length) return {result};
        if (renders.length > 1) {
          const indexes = renders.map(action => result.actions.indexOf(action));
          if (indexes.some((index, ordinal) => index !== indexes[0] + ordinal) ||
              renders.some(action => action.wait === false || typeof action.delay === "number" && action.delay > 0))
            throw new Error("multiple prepared Render actions must be one immediate blocking contiguous group");
        }
        const byRender = addressSnapshot();
        const allIncomingIds = new Set();
        for (const action of renders) for (const occurrence of action.prepared?.occurrences || []) {
          if (typeof occurrence.id !== "string") throw new Error("prepared Events incoming occurrence ID is invalid");
          allIncomingIds.add(occurrence.id);
        }
        const allocator = {occupied: new Set(ownedApp.occurrences.keys()),
          reserved: new Set([...ownedApp.occurrences.keys(), ...allIncomingIds]), claimedExisting: new Set(), ordinal: 0};
        const handles = [], entries = [], targetIds = new Set();
        let combined = null;
        const canonical = value => {
          if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
          if (value && typeof value === "object") return `{${Object.keys(value).sort()
            .map(key => `${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
          return JSON.stringify(value);
        };
        const merged = (name, identity) => {
          const values = [], seen = new Map();
          for (const entry of entries) for (const value of entry.envelope[name] || []) {
            const key = identity(value), prior = seen.get(key);
            if (prior && canonical(prior) !== canonical(value))
              throw new Error(`prepared ${name} identity conflicts across Render targets`);
            if (!prior) { seen.set(key, value); values.push(value); }
          }
          return values;
        };
        const mergedStyles = () => {
          const values = [], seen = new Map();
          for (const entry of entries) for (const raw of entry.envelope.styles || []) {
            const value = clone(raw);
            const key = canonical([value.source?.url, value.owner?.kind,
              value.owner?.typeKey || value.owner?.extensionName]);
            const prior = seen.get(key);
            if (!prior) { seen.set(key, value); values.push(value); continue; }
            const priorComparable = clone(prior), valueComparable = clone(value);
            if (priorComparable.owner?.kind === "component") priorComparable.owner.occurrenceIds = [];
            if (valueComparable.owner?.kind === "component") valueComparable.owner.occurrenceIds = [];
            if (canonical(priorComparable) !== canonical(valueComparable))
              throw new Error("prepared styles identity conflicts across Render targets");
            if (prior.owner.kind === "component") prior.owner.occurrenceIds =
              [...new Set([...prior.owner.occurrenceIds, ...value.owner.occurrenceIds])].sort();
          }
          return values;
        };
        for (const action of renders) {
          if (action.renderer !== "vue-prepared/1" || action.swap !== "morph" || typeof action.target !== "string")
            throw new Error("cross-component Vue rendering requires a render target, morph, and vue-prepared/1");
          let target, selectedMarker = null;
          if (action.target.startsWith("render:")) target = byRender.get(action.target.slice(7));
          else {
            const match = /^mark:([a-z0-9_-]+):([A-Za-z][A-Za-z0-9_-]*)$/.exec(action.target);
            if (!match) throw new Error("prepared Events marker target syntax is invalid");
            const caller = byRender.get(match[1]);
            if (!caller || caller.id !== source.stableId)
              throw new Error("prepared Events marker caller is stale or does not match the event source");
            selectedMarker = ownedApp.markers.get(caller.id + "\0" + match[2]);
            target = selectedMarker && ownedApp.occurrences.get(selectedMarker.occurrenceId);
          }
          if (!target) throw new Error("prepared Events Render target is stale or unknown");
          if (targetIds.has(target.id)) throw new Error("multiple prepared Render actions target the same occurrence");
          for (const other of targetIds) {
            let cursor = target.id;
            while (cursor !== null && cursor !== other) cursor = ownedApp.occurrences.get(cursor)?.parentId ?? null;
            let reverse = other;
            while (reverse !== null && reverse !== target.id) reverse = ownedApp.occurrences.get(reverse)?.parentId ?? null;
            if (cursor === other || reverse === target.id) throw new Error("prepared Render targets overlap");
          }
          targetIds.add(target.id);
          const mounted = ownedApp.mounted.get(target.id);
          if (!mounted) throw new Error("prepared Events Render target is not mounted");
          validateIsolatedEnvelope(ownedApp, action.prepared);
          let sourceCursor = source.stableId, strictAncestor = false;
          while (sourceCursor !== null) {
            if (sourceCursor === target.id) { strictAncestor = target.id !== source.stableId; break; }
            sourceCursor = ownedApp.occurrences.get(sourceCursor)?.parentId ?? null;
          }
          if (strictAncestor) {
            const renderIndex = result.actions.indexOf(action);
            const sourceRenderId = ownedApp.occurrences.get(source.stableId)?.renderId;
            result.actions.forEach((candidate, index) => {
              const sourceBound = candidate.action === "state" ||
                (candidate.action === "event" &&
                  (candidate.target === undefined || candidate.target === `render:${sourceRenderId}`));
              if (sourceBound && (index > renderIndex || (index < renderIndex &&
                  (candidate.wait === false || typeof candidate.delay === "number" && candidate.delay > 0))))
                throw new Error("ancestor Render cannot be combined with deferred or later source-bound actions");
            });
          }
          const root = action.prepared?.occurrences?.find(item => item.id === action.prepared.rootId);
          if (!root || root.typeKey !== target.typeKey) throw new Error("prepared Events Render target changed component type");
          const extensions = new Map(extensionEntries(action.prepared.extensions || {}));
          for (const name of plugins.keys()) if (!extensions.has(name)) throw new Error("prepared revision omitted installed browser plugin: " + name);
          for (const [name, incoming] of extensions) {
            const registration = browserPluginFactories.get(name);
            if (!plugins.has(name)) throw new Error("prepared revision introduced an uninstalled browser plugin: " + name);
            if (!registration || incoming.schemaVersion !== registration.schemaVersion ||
                JSON.stringify(incoming.templateContextNames) !== JSON.stringify(registration.templateContextNames))
              throw new Error("prepared revision changed browser plugin schema: " + name);
            if (renders.length > 1 && typeof plugins.get(name).plugin.prepareRevisionBatch !== "function")
              throw new Error("browser plugin does not support multiple prepared Render targets: " + name);
          }
          const translated = translateTargetEnvelope(action.prepared, target, allocator);
          validateIsolatedEnvelope(ownedApp, translated, target.id);
          entries.push({envelope: translated, targetId: target.id,
            extensions: new Map(extensionEntries(translated.extensions || {}))});
          handles.push(Object.freeze({app: ownedApp, id: target.id, generation: mounted.record.generation,
            renderId: target.renderId, typeKey: target.typeKey, revision: ownedApp.revision,
            markerOwnerId: selectedMarker?.ownerId || null, markerName: selectedMarker?.name || null}));
        }
        const removed = new Set();
        for (const id of ownedApp.occurrences.keys()) for (const rootId of targetIds) {
          let cursor = id;
          while (cursor !== null && cursor !== rootId) cursor = ownedApp.occurrences.get(cursor)?.parentId ?? null;
          if (cursor === rootId) { removed.add(id); break; }
        }
        const occurrences = new Map([...ownedApp.occurrences].filter(([id]) => !removed.has(id)));
        for (const entry of entries) {
          const existingTarget = ownedApp.occurrences.get(entry.targetId);
          for (const item of entry.envelope.occurrences) {
            if (occurrences.has(item.id)) throw new Error("subtree occurrence collides outside its target group");
            occurrences.set(item.id, item.id === entry.targetId ? {...item,
              parentId: existingTarget.parentId, placementKey: existingTarget.placementKey} : item);
          }
        }
        const compareMarker = (a, b) => {
          const left = `${a.ownerId}\0${a.name}\0${a.occurrenceId}`;
          const right = `${b.ownerId}\0${b.name}\0${b.occurrenceId}`;
          return left < right ? -1 : left > right ? 1 : 0;
        };
        const markers = [
          ...[...ownedApp.markers.values()].filter(item => targetIds.has(item.occurrenceId) || !removed.has(item.occurrenceId)),
          ...entries.flatMap(entry => entry.envelope.markers.filter(item => item.occurrenceId !== entry.targetId)),
        ].sort(compareMarker);
        normalizeMarkers(markers, occurrences);
        combined = {...entries[0].envelope, rootId: ownedApp.rootId,
          occurrences: [...occurrences.values()], markers};
        combined = {...combined,
          definitions: merged("definitions", value => value.id),
          scripts: merged("scripts", value => canonical([value.owner, value.source?.url])),
          styles: mergedStyles(),
          typePolicies: merged("typePolicies", value => value.typeKey),
          updatedIds: [...new Set(entries.flatMap(entry => entry.envelope.updatedIds))].sort(),
          replacements: entries.flatMap(entry => entry.envelope.replacements).sort((a,b) => {
            const left = `${a.ownerId}\0${a.siteId}`, right = `${b.ownerId}\0${b.siteId}`;
            return left < right ? -1 : left > right ? 1 : 0;
          }),
        };
        const incomingTypes = new Map(combined.occurrences.map(item => [item.id, item.typeKey]));
        const policies = normalizeTypePolicies(combined.typePolicies);
        validateCandidateAssets(appId, combined.scripts, combined.styles, incomingTypes,
          new Set(plugins.keys()), configuration, true);
        for (const typeKey of incomingTypes.values()) if (!ownedApp.types.has(typeKey) &&
            (configuration.allowLazyTypeAssets !== true || policies.get(typeKey) !== true))
          throw new Error("lazy component types are unsupported by this dependency or JavaScript policy");
        const declared = preflightDefinitions(ownedApp, combined.definitions, combined.occurrences, combined.rootId);
        const shadow = {...ownedApp, definitions: new Map(ownedApp.definitions)};
        for (const [id, definition] of declared) shadow.definitions.set(id, definition);
        validateCombinedActions(shadow, clone(combined));
        validateAddresses(combined.occurrences, true);
        const firstIndex = result.actions.indexOf(renders[0]);
        const transformed = renders.length === 1 ? result : {...result, actions: [
          ...result.actions.slice(0, firstIndex), {...renders[0], prepared: combined},
          ...result.actions.slice(firstIndex + renders.length),
        ]};
        return {result: transformed, renderPlan: Object.freeze({handles: Object.freeze(handles), envelope: combined,
          entries: Object.freeze(entries), replacedRootIds: Object.freeze([...targetIds])})};
      },
      async prepareRender(action, source, signal, renderPlan) {
        if (signal?.aborted) throw new Error("prepared Events render was cancelled");
        if (staged) throw new Error("a prepared Events transaction is already staged");
        let rejectCancellation;
        const cancellation = new Promise((_, reject) => { rejectCancellation = reject; });
        cancellation.catch(() => undefined);
        const attempt = {
          preparing: true,
          aborted: false,
          abortReason: null,
          cleaned: false,
          published: false,
          styleStage: null,
          pluginStages: [],
          rejectCancellation,
        };
        const cancel = () => cleanupEventAttempt(attempt);
        signal?.addEventListener("abort", cancel, {once: true});
        const guardHandles = () => {
          if (!source || sources.get(source.stableId)?.generation !== source.generation)
            throw new Error("prepared Events source became stale while rendering");
          for (const handle of renderPlan?.handles || []) if (handle && (handle.app !== ownedApp || ownedApp.revision !== handle.revision ||
              ownedApp.mounted.get(handle.id)?.record.generation !== handle.generation ||
              ownedApp.occurrences.get(handle.id)?.renderId !== handle.renderId ||
              ownedApp.occurrences.get(handle.id)?.typeKey !== handle.typeKey ||
              handle.markerOwnerId !== null && ownedApp.markers.get(handle.markerOwnerId + "\0" + handle.markerName)?.occurrenceId !== handle.id))
            throw new Error("prepared Events Render target became stale while rendering");
        };
        const wait = async promise => {
          const value = await Promise.race([promise, cancellation]);
          if (attempt.aborted || signal?.aborted) throw attempt.abortReason || new Error("prepared Events render was cancelled");
          guardHandles();
          return value;
        };
        staged = attempt;
        try {
        const envelope = renderPlan?.envelope || action.prepared;
        const handles = renderPlan?.handles || [];
        const replacedRootIds = renderPlan?.replacedRootIds || [source.stableId];
        if (!envelope || envelope.appId !== appId || !Array.isArray(envelope.definitions) || !Array.isArray(envelope.scripts) || !Array.isArray(envelope.styles) || !Array.isArray(envelope.typePolicies)) throw new Error("invalid prepared Events envelope");
        const incomingExtensions = new Map(extensionEntries(envelope.extensions || {}));
        for (const name of incomingExtensions.keys()) if (!plugins.has(name))
          throw new Error("prepared revision introduced an uninstalled browser plugin: " + name);
        for (const name of plugins.keys()) if (!incomingExtensions.has(name))
          throw new Error("prepared revision omitted installed browser plugin: " + name);
        normalizeTypePolicies(envelope.typePolicies);
        for (const [name, installed] of plugins) {
          const incoming = incomingExtensions.get(name), registration = browserPluginFactories.get(name);
          if (!registration || incoming.schemaVersion !== registration.schemaVersion ||
              JSON.stringify(incoming.templateContextNames) !== JSON.stringify(registration.templateContextNames))
            throw new Error("prepared revision changed browser plugin schema: " + name);
        }
        const incomingOccurrenceTypes = new Map(envelope.occurrences.map(item => [item.id, item.typeKey]));
        const normalizedAssets = validateCandidateAssets(appId, envelope.scripts, envelope.styles,
          incomingOccurrenceTypes, new Set(incomingExtensions.keys()), configuration, true);
        const replacedStyleIds = new Set();
        for (const id of definitionRegistry(appId).occurrences.keys()) {
          for (const rootId of replacedRootIds) {
            let cursor = id;
            while (cursor !== null && cursor !== rootId)
              cursor = definitionRegistry(appId).occurrences.get(cursor)?.parentId ?? null;
            if (cursor === rootId) { replacedStyleIds.add(id); break; }
          }
        }
        attempt.styleStage = {
          token: Object.freeze({appId, revision: envelope.revision}),
          replacedIds: replacedStyleIds,
          refs: new Map(),
        };
        for (const asset of normalizedAssets.styles) {
          const refs = attempt.styleStage.refs.get(asset.source.url) || new Set();
          for (const id of assetRefs(asset)) refs.add(id);
          attempt.styleStage.refs.set(asset.source.url, refs);
        }
        if (!source || sources.get(source.stableId)?.generation !== source.generation)
          throw new Error("prepared Events source is stale before render preflight");
        guardHandles();
        const declaredDefinitions = preflightDefinitions(
          definitionRegistry(appId), envelope.definitions, envelope.occurrences, envelope.rootId);
        const shadow = {...definitionRegistry(appId), definitions: new Map(definitionRegistry(appId).definitions)};
        for (const [id, definition] of declaredDefinitions) shadow.definitions.set(id, definition);
        validateCombinedActions(shadow, clone(envelope));
        const declaredDefinitionIds = new Set(declaredDefinitions.keys());
        const priorDefinitionKeys = new Set(Object.keys(global.CitryStableDefinitions || {}));
        for (const asset of envelope.definitions) await wait(loadDefinition(asset, configuration.nonce));
        for (const id of Object.keys(global.CitryStableDefinitions || {}))
          if (!priorDefinitionKeys.has(id) && !declaredDefinitionIds.has(id))
            throw new Error("prepared definition asset registered an undeclared definition");
        for (const asset of envelope.definitions) if (!registered.has(asset.id)) {
          registerDefinition(
            appId, asset.id, global.CitryStableDefinitions?.[asset.id], declaredDefinitions.get(asset.id));
          registered.add(asset.id);
        }
        validateCombinedActions(definitionRegistry(appId), clone(envelope));
        const declaredOptionTypes = new Set(normalizedAssets.scripts.filter(asset => asset.registersOptions).map(asset => asset.owner.typeKey));
        const priorOptionTypes = new Set(registeredTypeOptions.keys());
        for (const asset of normalizedAssets.scripts)
          await wait(loadTypeScript(appId, asset, configuration.nonce));
        await wait(Promise.all(normalizedAssets.styles.map(asset =>
          loadStyle(appId, asset, configuration.nonce, attempt.styleStage))));
        for (const typeKey of registeredTypeOptions.keys())
          if (!priorOptionTypes.has(typeKey) && !declaredOptionTypes.has(typeKey))
            throw new Error("prepared type asset registered undeclared Vue Options");
        try {
          for (const [name, installed] of plugins) {
            const incoming = incomingExtensions.get(name);
            const item = {
              name, plugin: installed.plugin, attempted: false, cleaned: false, hasStage: false, stage: undefined,
            };
            attempt.pluginStages.push(item);
            const entries = renderPlan?.entries;
            const pending = Promise.resolve(entries?.length > 1
              ? installed.plugin.prepareRevisionBatch(entries.map(entry => ({
                  payload: detached(entry.extensions.get(name).payload), rootId: entry.targetId,
                })), detached(envelope))
              : entries?.length === 1
                ? installed.plugin.prepareRevision(detached(entries[0].extensions.get(name).payload),
                    detached(entries[0].envelope))
                : installed.plugin.prepareRevision(detached(incoming.payload), detached(envelope)));
            pending.then(stage => {
              item.stage = stage;
              item.hasStage = true;
              if (attempt.aborted && !item.cleaned) {
                item.cleaned = true;
                try { item.plugin.abortRevision(stage); }
                catch (error) { console.error("[Citry] late Events plugin stage cleanup failed:", error); }
              }
            }, () => undefined);
            await wait(pending);
          }
        } catch (error) {
          cleanupEventAttempt(attempt, error);
          throw error;
        }
        if (attempt.aborted || signal?.aborted) throw attempt.abortReason || new Error("prepared Events render was cancelled");
        attempt.preparing = false;
        attempt.envelope = envelope;
        attempt.replacedRootIds = replacedRootIds;
        attempt.targetHandles = handles;
        attempt.callbackOwnerIds = new Set(handles.map(handle => handle.markerOwnerId).filter(Boolean));
        return {transaction: attempt};
        } catch (error) {
          cleanupEventAttempt(attempt, error);
          throw error;
        } finally {
          signal?.removeEventListener("abort", cancel);
        }
      },
      abortRender(prepared) {
        const transaction = prepared?.transaction;
        if (!transaction) {
          if (staged?.preparing) cleanupEventAttempt(staged);
          return;
        }
        if (staged === transaction) cleanupEventAttempt(transaction);
      },
      async commitRender(prepared, source) {
        if (apps.get(appId) !== ownedApp || ownedApp.terminal || !staged || prepared.transaction !== staged)
          throw new Error("prepared Events transaction is stale");
        const transaction = staged;
        try {
          if (!source || sources.get(source.stableId)?.generation !== source.generation)
            throw new Error("prepared Events source became stale before publication");
          for (const handle of transaction.targetHandles || []) if (handle && (handle.app !== ownedApp || ownedApp.revision !== handle.revision ||
              ownedApp.mounted.get(handle.id)?.record.generation !== handle.generation ||
              ownedApp.occurrences.get(handle.id)?.renderId !== handle.renderId ||
              ownedApp.occurrences.get(handle.id)?.typeKey !== handle.typeKey ||
              handle.markerOwnerId !== null && ownedApp.markers.get(handle.markerOwnerId + "\0" + handle.markerName)?.occurrenceId !== handle.id))
            throw new Error("prepared Events Render target became stale before publication");
          await applyEnvelope(appId, transaction.envelope, transaction.replacedRootIds[0] || source.stableId, {
            combined: true,
            acceptedTransaction: transaction,
            callbackOwnerIds: transaction.callbackOwnerIds,
            activate() { for (const item of transaction.pluginStages) {
              if (apps.get(appId) !== ownedApp || ownedApp.terminal || staged !== transaction)
                throw new Error("prepared Events transaction is stale before activation");
              item.attempted = true;
              item.plugin.activateRevision(item.stage);
            } },
            commit() {
              if (apps.get(appId) !== ownedApp || ownedApp.terminal || staged !== transaction)
                throw new Error("prepared Events transaction is stale before publication");
              for (const item of transaction.pluginStages) {
                item.plugin.commitRevision(item.stage);
                if (apps.get(appId) !== ownedApp || ownedApp.terminal || staged !== transaction)
                  throw new Error("prepared Events transaction was disposed during plugin publication");
              }
              if (apps.get(appId) !== ownedApp || ownedApp.terminal || staged !== transaction)
                throw new Error("prepared Events transaction is stale before style publication");
              commitStyleStage(appId, transaction.styleStage);
              transaction.published = true;
            },
          });
          if (apps.get(appId) !== ownedApp || ownedApp.terminal || staged !== transaction)
            throw new Error("prepared Events transaction became stale after publication");
        } catch (error) {
          cleanupEventAttempt(transaction, error);
          throw error;
        } finally {
          if (staged === transaction) staged = null;
        }
      },
      commitState(serverRenderId, stateToken) {
        for (const [id, value] of contexts) if (value.serverRenderId === serverRenderId)
          contexts.set(id, {...value, stateToken});
      },
      dispatchEvent(name, detail, source) {
        const mounted = ownedApp.mounted.get(source.stableId);
        if (!mounted || mounted.record.generation !== source.generation)
          throw new Error("Citry Events dispatch source is stale or retired");
        mounted.record.events.dispatch(name, detail);
        dispatchCarrier(source).dispatchEvent(new CustomEvent(name, {detail, bubbles: true}));
      },
      dispatchEventGlobal(name, detail) {
        document.dispatchEvent(new CustomEvent(name, {detail, bubbles: true}));
      },
      lifecycle(kind, source, event, extra = {}) {
        // A committed self-render may retire the sender and mount its
        // replacement before the bridge emits `swapped`/`after`. Those
        // notifications describe the committed instance, so follow the
        // stable occurrence identity for post-commit hooks while keeping
        // cancellation/error checks bound to the original generation.
        const effectiveSource = kind === "swapped" || kind === "after"
          ? sources.get(source.stableId) || source
          : source;
        const context = contexts.get(effectiveSource.stableId);
        const mounted = ownedApp.mounted.get(effectiveSource.stableId);
        if (!context || !mounted || mounted.record.generation !== effectiveSource.generation) return true;
        const details = {
          instance: context.serverRenderId,
          class: context.componentClassId,
          event,
          ...extra,
        };
        if (kind === "swapped") details.els = liveRootElements(mounted.component);
        const roots = liveRootElements(mounted.component);
        const carrier = roots[0] || document;
        return carrier.dispatchEvent(new CustomEvent(`citry:events:${kind}`, {
          detail: details,
          bubbles: true,
          cancelable: kind === "before",
        }));
      },
      redirect(url) { global.location.assign(url); },
      updateUrl(url, mode) { global.history[mode === "push" ? "pushState" : "replaceState"]({}, "", url); },
      takePendingState(source, handlerName) {
        const mounted = ownedApp.mounted.get(source.stableId);
        if (!mounted || mounted.record.generation !== source.generation) return undefined;
        const descriptor = mounted.record.events.descriptor;
        if (descriptor?.eventHandlers?.[handlerName]?.httpMethod === "GET") return undefined;
        if (!mounted.record.state.pending) return undefined;
        const keys = Object.keys(mounted.record.state.pending);
        if (!keys.length) return undefined;
        const snapshot = cloneStateValue(mounted.record.state.pending);
        mounted.record.state.pending = Object.create(null);
        return snapshot;
      },
      restorePendingState(source, updates) {
        const mounted = ownedApp.mounted.get(source.stableId);
        if (!mounted || mounted.record.generation !== source.generation || !mounted.record.state.current ||
            !mounted.record.state.writable || !mounted.record.state.pending) return;
        for (const [key, value] of Object.entries(updates))
          if (mounted.record.state.writable.has(key) && !own(mounted.record.state.pending, key))
            mounted.record.state.pending[key] = cloneStateValue(value);
      },
    };
    const cookieToken = () => {
      const match = document.cookie.split(";").map(value => value.trim()).find(value => value.startsWith("csrftoken="));
      return match ? decodeURIComponent(match.slice("csrftoken=".length)) : "";
    };
    const hasEvents = manifest.occurrences.some(occurrence => occurrence.eventContext);
    if (manifest.occurrences.some(occurrence => own(occurrence, "renderId"))) addressSnapshot();
    let bridge = null;
    const ensureEventsBridge = () => {
      addressSnapshot(true);
      if (bridge) return bridge;
      if (!global.CitryVueEvents || typeof configuration.endpoint !== "string")
        throw new Error("prepared Events components require the Events bridge and endpoint");
      bridge = global.CitryVueEvents.createVueEventsBridge({
        endpoint: configuration.endpoint,
        eventBaseUrl: configuration.eventBaseUrl,
        host,
        csrf: configuration.csrf || {token: cookieToken},
        runtimeConfig: () => publicEventsConfig,
        transport: () => {
          const name = typeof publicEventsConfig.transport === "string" && publicEventsConfig.transport
            ? publicEventsConfig.transport : "fetch";
          const implementation = publicEventTransports.get(name);
          if (implementation) return implementation;
          if (name === "fetch") return null;
          throw new Error("Citry Events transport is not registered: " + name);
        },
        activity(source, descriptor) {
          const mounted = ownedApp.mounted.get(source.stableId);
          if (!mounted || mounted.record.generation !== source.generation)
            throw new Error("Citry Events activity source is stale or retired");
          mounted.record.events.descriptor = descriptor;
          return mounted.record.events;
        },
      });
      return bridge;
    };
    if (hasEvents) ensureEventsBridge();
    async function sendDeclarativeEvent(record, binding, source, args) {
      const eventsBridge = ensureEventsBridge();
      let result;
      try {
        result = await eventsBridge.send({source, handler: binding.handler, args});
      } catch (error) {
        if (!ownedApp.terminal && eventsBridge.isDeclarativeFailureHandled(error)) return undefined;
        throw error;
      }
      document.dispatchEvent(new CustomEvent("citry:rendered", {detail: {appId, revision: definitionRegistry(appId).revision}}));
      return result;
    }
    const resolveDeclarativeEvent = (record, bindingId) => {
      if (record.app !== definitionRegistry(appId) || record.app.mounted.get(record.occurrenceId)?.record !== record)
        throw new Error("Citry Events source is stale or retired");
      const bindings = record.live.value?.preparedData?.eventBindings;
      const binding = bindings && bindings[bindingId];
      if (!binding) throw new Error("Citry Events binding is missing or stale");
      const source = sources.get(record.occurrenceId);
      if (!source) throw new Error("Citry Events binding has no mounted Vue owner");
      return {binding, source};
    };
    const declarativeEventArgs = (value, authoredArgs) => {
      let args = authoredArgs;
      if (args === undefined) {
        const isEvent = typeof global.Event === "function" && value instanceof global.Event;
        const form = isEvent && value.target instanceof HTMLFormElement
          ? value.target
          : isEvent && value.currentTarget instanceof HTMLFormElement ? value.currentTarget : null;
        args = form
          ? global.CitryVueEvents.collectFormArgs(form, new Set())
          : {};
      }
      plain(args, "Citry Events arguments");
      return args;
    };
    definitionRegistry(appId).eventDispatch = async (record, bindingId, event, authoredArgs) => {
      const {binding, source} = resolveDeclarativeEvent(record, bindingId);
      if (binding.event !== event.type) throw new Error("Citry Events binding is missing or stale");
      const args = declarativeEventArgs(event, authoredArgs);
      if (binding.debounce === null && binding.throttle === null)
        return sendDeclarativeEvent(record, binding, source, args);
      const element = event.currentTarget;
      if (!(element instanceof Element)) throw new Error("timed component-boundary Events bindings are not supported");
      if (!timingDirectiveOwns(element, record, bindingId, binding))
        throw new Error("Citry timed Events binding has no authenticated element lifecycle");
      const capturedArgs = cloneJsonValue(args, "Citry Events arguments");
      const lifetime = eventTimingLifetime(record, element, bindingId, binding);
      if (binding.throttle !== null) {
        const now = performance.now();
        if (now - lifetime.last < binding.throttle) return undefined;
        lifetime.last = now;
      }
      if (binding.debounce !== null) {
        if (lifetime.timer) clearTimeout(lifetime.timer);
        lifetime.resolve?.(undefined);
        return await new Promise((resolve, reject) => {
          lifetime.resolve = resolve;
          scheduleDelay(lifetime, binding.debounce, () => {
            const currentBinding = lifetime.binding;
            lifetime.resolve = undefined;
            if (!timedBindingIsCurrent(record, element, bindingId, currentBinding)) {
              releaseEventTiming(lifetime);
              resolve(undefined);
              return;
            }
            const remainingThrottle = currentBinding.throttle === null
              ? 0 : currentBinding.throttle - (performance.now() - lifetime.last);
            if (remainingThrottle > 0)
              scheduleDelay(lifetime, remainingThrottle, () => releaseEventTiming(lifetime));
            else releaseEventTiming(lifetime);
            void sendDeclarativeEvent(record, currentBinding, source, capturedArgs).then(resolve, reject);
          });
        });
      }
      if (!timedBindingIsCurrent(record, element, bindingId, binding)) {
        finishEventTiming(lifetime, undefined);
        return undefined;
      }
      if (lifetime.timer) {
        clearTimeout(lifetime.timer);
        lifetime.timer = 0;
      }
      scheduleDelay(lifetime, binding.throttle, () => releaseEventTiming(lifetime));
      return sendDeclarativeEvent(record, binding, source, capturedArgs);
    };
    definitionRegistry(appId).eventDispatchComponent = async (record, bindingId, emittedValue, authoredArgs) => {
      const {binding, source} = resolveDeclarativeEvent(record, bindingId);
      const args = declarativeEventArgs(emittedValue, authoredArgs);
      if (binding.debounce !== null || binding.throttle !== null)
        throw new Error("timed component-boundary Events bindings are not supported");
      return sendDeclarativeEvent(record, binding, source, args);
    };
    definitionRegistry(appId).eventPoll = async (record, bindingId, args) => {
      if (record.app !== definitionRegistry(appId) || record.app.mounted.get(record.occurrenceId)?.record !== record)
        throw new Error("Citry polling source is stale or retired");
      const binding = record.live.value?.preparedData?.pollBindings?.[bindingId];
      if (!binding) throw new Error("Citry polling binding is missing or stale");
      const source = sources.get(record.occurrenceId);
      if (!source) throw new Error("Citry polling binding has no mounted Vue owner");
      return sendDeclarativeEvent(record, binding, source, args);
    };
    definitionRegistry(appId).eventSend = async (record, handler, args, opts) => {
      if (record.app !== ownedApp || ownedApp.mounted.get(record.occurrenceId)?.record !== record)
        throw new Error("Citry Events source is stale or retired");
      const checkedArgs = args === undefined ? {} : args;
      plain(checkedArgs, "Citry Events arguments");
      const source = sources.get(record.occurrenceId);
      if (!source) throw new Error("Citry Events call has no mounted Vue owner");
      const options = opts === undefined ? undefined : opts && typeof opts === "object" ? {timeout: opts.timeout} : opts;
      return ensureEventsBridge().send({source, handler, args: checkedArgs, options});
    };
    ownedApp.resolvePublicTarget = sourceForTarget;
    ownedApp.publicSend = (source, handler, args, opts) => {
      const mounted = ownedApp.mounted.get(source.stableId);
      if (!mounted || mounted.record.generation !== source.generation)
        return Promise.reject(new Error("Citry.events.send target is stale or retired."));
      requireEventHandler(mounted.record, handler);
      const checkedArgs = args === undefined ? {} : args;
      plain(checkedArgs, "Citry Events arguments");
      const options = opts === undefined ? undefined : opts && typeof opts === "object" ? {timeout: opts.timeout} : opts;
      return ensureEventsBridge().send({source, handler, args: checkedArgs, options});
    };
    ownedApp.publicApplyActions = (actions, source) => ensureEventsBridge().applyActions(actions, source);
    attachPreparedHost(appId, {
      onOccurrenceMounted({stableId, generation, occurrence}) {
        sources.set(stableId, {stableId, generation});
        const mounted = ownedApp.mounted.get(stableId);
        if (mounted?.record.generation === generation)
          { mounted.record.events.descriptor = occurrence.eventContext?.descriptor || null;
            mounted.record.state.adopt(occurrence.eventContext); }
        if (occurrence.eventContext) contexts.set(stableId, occurrence.eventContext);
      },
      onOccurrenceUnmounted({stableId, generation, acceptedTransaction}) {
        const source = sources.get(stableId);
        if (!source || source.generation !== generation) return;
        bridge?.retire(source, acceptedTransaction);
        sources.delete(stableId);
        contexts.delete(stableId);
      },
      beforeServerCallbacks({mounted}) {
        if ([...ownedApp.occurrences.values()].some(occurrence => occurrence.eventContext)) ensureEventsBridge();
        for (const id of sources.keys()) if (!definitionRegistry(appId).occurrences.has(id)) { sources.delete(id); contexts.delete(id); }
        for (const {stableId, generation, occurrence, adoptContext = true} of mounted) {
          sources.set(stableId, {stableId, generation});
          const current = ownedApp.mounted.get(stableId);
          if (adoptContext && current?.record.generation === generation)
            { current.record.events.descriptor = occurrence.eventContext?.descriptor || null;
              current.record.state.adopt(occurrence.eventContext); }
          if (adoptContext) {
            if (occurrence.eventContext) contexts.set(stableId, occurrence.eventContext);
            else contexts.delete(stableId);
          }
        }
      },
    });
    const root = manifest.occurrences.find(item => item.id === manifest.rootId);
    const vueApp = V.createApp(componentTypes[root.typeKey], {citryId: root.id});
    vueApp.component("citry-opaque-html", opaqueHtmlComponent);
    vueApp.directive("citry-control", {
      mounted(element, binding) {
        if (binding.value.length) installControls(element, binding.value);
      },
      updated(element, binding) {
        if (!binding.value.length) { disposeControl(element); return; }
        const lifetime = controlLifetimes.get(element);
        if (!lifetime || lifetime.handles !== binding.value || lifetime.signature !== controlSignature(element, binding.value))
          installControls(element, binding.value);
        else for (const handle of binding.value) applyControlValue(element, handle.record.state.facade[handle.spec.field]);
      },
      beforeUnmount(element) { disposeControl(element); },
    });
    const runtimeEventLifetimes = new WeakMap();
    const disposeRuntimeEvents = element => {
      const lifetime = runtimeEventLifetimes.get(element);
      if (!lifetime) return;
      for (const item of lifetime.values()) element.removeEventListener(item.event, item.listener);
      const timed = runtimeEventTimingDirectives.get(element);
      disposeElementEventTimings(element, timed);
      runtimeEventTimingDirectives.delete(element);
      runtimeEventLifetimes.delete(element);
    };
    const runtimeEventSignature = eventTimingSignature;
    const runtimeTimingSignature = handle => {
      if (handle.kind === "event") return "event:" + runtimeEventSignature(handle);
      const spec = handle.spec;
      return JSON.stringify([
        "poll",
        handle.record.occurrenceId,
        handle.record.generation,
        handle.id,
        spec.handler,
        spec.args,
        spec.interval,
      ]);
    };
    const reconcileRuntimeEventTimings = (element, handles) => {
      const prior = runtimeEventTimingDirectives.get(element) || [];
      const current = Object.freeze(handles);
      runtimeEventTimingDirectives.set(element, current);
      const currentByKey = new Map(current.map(handle => [handle.kind + ":" + handle.id, handle]));
      const retained = new Set();
      for (const old of prior) {
        const replacement = currentByKey.get(old.kind + ":" + old.id);
        if (replacement && replacement.record === old.record &&
            runtimeTimingSignature(replacement) === runtimeTimingSignature(old)) {
          const lifetime = eventTimingLifetimes.get(element)?.get(old.id);
          if (lifetime?.record === old.record && lifetime.binding === old.spec) {
            lifetime.binding = replacement.spec;
            lifetime.args = replacement.args;
            retained.add(replacement);
          } else if (old.kind === "event") {
            retained.add(replacement);
          }
          continue;
        }
        disposeElementEventTimings(element, [old]);
      }
      for (const handle of current) {
        if (handle.kind === "poll" && !retained.has(handle)) registerPoll(element, handle);
      }
    };
    const installRuntimeEvents = (element, handles) => {
      const prior = runtimeEventLifetimes.get(element) || new Map();
      const current = new Map();
      for (const handle of handles.filter(handle => handle.kind === "event")) {
        const spec = handle.spec;
        const signature = runtimeEventSignature(handle);
        const retained = prior.get(handle.id);
        if (retained?.signature === signature) { current.set(handle.id, retained); continue; }
        if (retained) element.removeEventListener(retained.event, retained.listener);
        let listener = event => {
          let dispatched;
          try { dispatched = handle.record.app.eventDispatch(handle.record, handle.id, event, undefined); }
          catch (error) {
            handle.record.app.vueApp.config.errorHandler(error, handle.record.app.mounted.get(handle.record.occurrenceId)?.component, "Citry runtime event");
            return;
          }
          Promise.resolve(dispatched).catch(error => handle.record.app.vueApp.config.errorHandler(
            error, handle.record.app.mounted.get(handle.record.occurrenceId)?.component, "Citry runtime event"));
        };
        const modifiers = ["prevent", "stop", "self"].filter(name => spec[name] === true);
        if (modifiers.length) listener = V.withModifiers(listener, modifiers);
        if (spec.key !== null) listener = V.withKeys(listener, [spec.key]);
        element.addEventListener(spec.event, listener, spec.once === true ? {once:true} : undefined);
        current.set(handle.id, {event:spec.event, listener, signature});
      }
      for (const [id, item] of prior) if (!current.has(id)) element.removeEventListener(item.event, item.listener);
      const timed = handles.filter(handle => handle.kind === "poll" ||
        handle.spec.debounce !== null || handle.spec.throttle !== null);
      reconcileRuntimeEventTimings(element, timed);
      runtimeEventLifetimes.set(element, current);
    };
    vueApp.directive("citry-runtime-events", {
      mounted(element, binding) { installRuntimeEvents(element, binding.value); },
      updated(element, binding) { installRuntimeEvents(element, binding.value); },
      beforeUnmount(element) { disposeRuntimeEvents(element); },
    });
    vueApp.directive("citry-event-timing", {
      mounted(element, binding) { reconcileEventTimings(element, binding.value); },
      updated(element, binding) { reconcileEventTimings(element, binding.value); },
      beforeUnmount(element) {
        const handles = eventTimingDirectives.get(element);
        disposeElementEventTimings(element, handles);
        eventTimingDirectives.delete(element);
      },
    });
    vueApp.config.globalProperties.$loading = function (name) {
      const current = V.getCurrentInstance?.();
      const record = instanceRecords.get(this) || instanceRecords.get(this?.$?.proxy) ||
        instanceRecords.get(current?.proxy) || instanceRecords.get(current?.ctx);
      if (!record) throw new Error("$loading is unavailable outside a Citry Vue component");
      return record.events.loading(name);
    };
    vueApp.config.globalProperties.$error = function (name) {
      const current = V.getCurrentInstance?.();
      const record = instanceRecords.get(this) || instanceRecords.get(this?.$?.proxy) ||
        instanceRecords.get(current?.proxy) || instanceRecords.get(current?.ctx);
      if (!record) throw new Error("$error is unavailable outside a Citry Vue component");
      return record.events.error(name);
    };
    let initialPublished = false;
    try {
      lifecycle?.guard();
      for (const {plugin} of plugins.values()) vueApp.use(plugin);
      for (const [typeKey, type] of Object.entries(componentTypes)) {
        const tag = initialTypeTags.get(typeKey);
        if (typeof tag !== "string") throw new Error("prepared component type has no registered tag");
        definitionRegistry(appId).typeTags.set(typeKey, tag);
        vueApp.component(tag, type);
      }
      attachVueApp(appId, vueApp);
      lifecycle?.guard();
      vueApp.mount(hostElement);
      await waitForStartup(whenReady(appId), lifecycle);
      initialPublished = true;
      for (const {plugin, stage} of plugins.values()) plugin.commitRevision(stage);
      definitionRegistry(appId).initialPluginStages = [];
    } catch (error) {
      ownedApp.terminal = true;
      cleanupEventAttempt(staged, error);
      bridge?.dispose?.();
      if (!initialPublished) cleanupPluginStages(plugins.values(), "rollbackRevision");
      definitionRegistry(appId).initialPluginStages = [];
      try { vueApp.unmount(); } catch (unmountError) {
        console.error("[Citry] failed to dispose a rejected Vue app:", unmountError);
      }
      for (const {plugin} of plugins.values()) {
        try { plugin.dispose(); } catch (disposeError) { console.error("[Citry] browser plugin dispose failed:", disposeError); }
      }
      releaseAppStyles(appId);
      releaseAppScripts(appId);
      apps.delete(appId);
      throw error;
    }
    document.dispatchEvent(new CustomEvent("citry:ready", {detail: {appId, revision: definitionRegistry(appId).revision}}));
    const nativeUnmount = vueApp.unmount.bind(vueApp);
    let disposed = false;
    vueApp.unmount = () => {
      if (disposed) return;
      disposed = true;
      ownedApp.terminal = true;
      cleanupEventAttempt(staged, new Error("Vue app was disposed"));
      bridge?.dispose?.();
      try { nativeUnmount(); }
      finally {
        const current = apps.get(appId);
        if (current?.vueApp === vueApp) current.mounted.clear();
        for (const {plugin} of plugins.values()) {
          try { plugin.dispose(); } catch (error) { console.error("[Citry] browser plugin dispose failed:", error); }
        }
        if (apps.get(appId) === ownedApp) {
          releaseAppStyles(appId);
          releaseAppScripts(appId);
          apps.delete(appId);
        }
      }
    };
    return Object.freeze({appId, app: vueApp});
  }

  async function startPrepared(configuration, lifecycle) {
    const candidateId = configuration && typeof configuration === "object" && configuration.manifest &&
      typeof configuration.manifest === "object" ? configuration.manifest.appId : null;
    const startAttempt = Object.freeze({});
    try {
      return await startPreparedOwned(configuration, lifecycle, startAttempt);
    } catch (error) {
      const created = typeof candidateId === "string" ? apps.get(candidateId) : undefined;
      if (created?.startAttempt === startAttempt) {
        for (const item of [...(created.initialPluginStages || [])].reverse()) {
          try { item.plugin.rollbackRevision(item.stage); }
          catch (rollbackError) { console.error("[Citry] browser plugin rollbackRevision failed:", rollbackError); }
        }
        created.initialPluginStages = [];
        try { created.vueApp?.unmount(); } catch (unmountError) {
          console.error("[Citry] rejected Vue app disposal failed:", unmountError);
        }
        for (const plugin of created.browserPlugins) {
          try { plugin.dispose(); } catch (disposeError) {
            console.error("[Citry] rejected browser plugin disposal failed:", disposeError);
          }
        }
        if (apps.get(candidateId) === created) apps.delete(candidateId);
        releaseAppStyles(candidateId);
        releaseAppScripts(candidateId);
      }
      throw error;
    }
  }

  function disposeCallbacks(record) {
    const scope = record.callbackScope, cleanup = record.callbackCleanup;
    const subscriptions = record.callbackSubscriptions;
    record.callbackScope = undefined; record.callbackCleanup = undefined; record.callbackSubscriptions = undefined;
    let error;
    try { scope?.stop(); } catch (caught) { error = caught; }
    for (const unsubscribe of subscriptions || []) {
      try { unsubscribe(); }
      catch (caught) { if (error === undefined) error = caught; else console.error("[Citry] callback event cleanup failed:", caught); }
    }
    try { if (cleanup) cleanup(); }
    catch (caught) { if (error === undefined) error = caught; else console.error("[Citry] callback cleanup failed:", caught); }
    if (error !== undefined) throw error;
  }
  function subscribeRecordEvent(record, name, handler) {
    const unsubscribe = record.events.subscribe(name, handler);
    const subscriptions = record.callbackSubscriptions;
    if (!subscriptions) return unsubscribe;
    let active = true;
    const off = () => {
      if (!active) return;
      active = false;
      subscriptions.delete(off);
      unsubscribe();
    };
    subscriptions.add(off);
    return off;
  }
  function dispose(record) {
    disposeEventTimings(record);
    record.events?.dispose?.();
    disposeCallbacks(record);
  }
  async function runCallback(component, record, callback, revision) {
    if (!callback) return;
    const scope = V.effectScope(true);
    const subscriptions = new Set();
    record.callbackScope = scope;
    record.callbackSubscriptions = subscriptions;
    try {
      const cleanup = scope.run(() => callback({
        component,
        revision,
        onEvent: (name, handler) => subscribeRecordEvent(record, name, handler),
      }));
      if (cleanup !== undefined && typeof cleanup !== "function") throw new TypeError("onServerRender must return a function or undefined");
      record.callbackCleanup = cleanup;
    } catch (error) {
      scope.stop();
      for (const unsubscribe of subscriptions) unsubscribe();
      record.callbackScope = undefined;
      record.callbackCleanup = undefined;
      record.callbackSubscriptions = undefined;
      throw error;
    }
  }

  async function whenReady(appId) {
    const app = definitionRegistry(appId);
    await V.nextTick();
    while (app.initialTasks.size) {
      await Promise.all([...app.initialTasks]);
      await V.nextTick();
    }
    if (app.terminal) throw app.initialError || new Error("Citry Vue app failed during initialization");
    validateMountedParents(app);
    return app;
  }

  function validateMountedParents(app) {
    for (const [id, mounted] of app.mounted) {
      let parent = mounted.component.$parent;
      while (parent && !instanceRecords.has(parent)) parent = parent.$parent;
      const actualParentId = parent ? instanceRecords.get(parent).occurrenceId : null;
      if (actualParentId !== app.occurrences.get(id)?.parentId) {
        throw new Error("mounted Vue parent does not match prepared occurrence parent: " + id);
      }
    }
  }

  function validateIsolatedEnvelope(app, envelope, expectedRootId = null) {
    plain(envelope, "envelope");
    if (envelope.protocol !== "citry-vue-prepared/1" || envelope.appId !== app.id ||
        envelope.baseRevision !== app.revision || envelope.revision !== app.revision + 1 ||
        typeof envelope.rootId !== "string" || expectedRootId !== null && envelope.rootId !== expectedRootId ||
        !Array.isArray(envelope.definitions) || !Array.isArray(envelope.scripts) ||
        !Array.isArray(envelope.styles) || !Array.isArray(envelope.typePolicies) ||
        !Array.isArray(envelope.occurrences) || !Array.isArray(envelope.updatedIds) ||
        !Array.isArray(envelope.replacements) || !Array.isArray(envelope.markers) ||
        own(envelope, "topologyChanges")) throw new Error("stale or malformed envelope");
    const subtree = new Map();
    for (const item of envelope.occurrences) {
      plain(item, "subtree occurrence");
      if (typeof item.id !== "string" || subtree.has(item.id)) throw new Error("invalid or duplicate subtree occurrence");
      subtree.set(item.id, item);
    }
    validateGraph(subtree, envelope.rootId);
    const declaredUpdates = new Set(envelope.updatedIds);
    if (envelope.updatedIds.some(id => typeof id !== "string") ||
        declaredUpdates.size !== envelope.updatedIds.length || declaredUpdates.size !== subtree.size ||
        [...subtree.keys()].some(id => !declaredUpdates.has(id)))
      throw new Error("subtree update ids must exactly cover its snapshot");
    if (envelope.replacements.some(item => !item || !subtree.has(item.ownerId)))
      throw new Error("subtree replacement owner lies outside its snapshot");
    normalizeMarkers(envelope.markers, subtree);
    return subtree;
  }

  function expandSubtreeEnvelope(app, envelope, targetId) {
    const subtree = validateIsolatedEnvelope(app, envelope, targetId);
    if (!app.occurrences.has(targetId)) throw new Error("stale or malformed envelope");
    const removed = new Set();
    for (const id of app.occurrences.keys()) {
      let cursor = id;
      while (cursor !== null && cursor !== targetId) cursor = app.occurrences.get(cursor)?.parentId ?? null;
      if (cursor === targetId) removed.add(id);
    }
    const combined = new Map([...app.occurrences].filter(([id]) => !removed.has(id)));
    for (const id of subtree.keys()) if (combined.has(id)) throw new Error("subtree occurrence collides outside its target");
    const existingTarget = app.occurrences.get(targetId);
    for (const [id, item] of subtree) combined.set(id, id === targetId ? {
      ...item, parentId: existingTarget.parentId, placementKey: existingTarget.placementKey,
    } : item);
    const markers = [
      ...[...app.markers.values()].filter(item => item.occurrenceId === targetId || !removed.has(item.occurrenceId)),
      ...envelope.markers.filter(item => item.occurrenceId !== targetId),
    ].sort((a,b) => {
      const left = `${a.ownerId}\0${a.name}\0${a.occurrenceId}`;
      const right = `${b.ownerId}\0${b.name}\0${b.occurrenceId}`;
      return left < right ? -1 : left > right ? 1 : 0;
    });
    normalizeMarkers(markers, combined);
    return {...envelope, rootId: app.rootId, occurrences: [...combined.values()], markers};
  }

  function validateActions(app, envelope, targetId) {
    return validateCombinedActions(app, expandSubtreeEnvelope(app, envelope, targetId));
  }

  function validateCombinedActions(app, envelope) {
    plain(envelope, "combined envelope");
    if (envelope.protocol !== "citry-vue-prepared/1" || envelope.appId !== app.id ||
        envelope.baseRevision !== app.revision || envelope.revision !== app.revision + 1 ||
        envelope.rootId !== app.rootId || !Array.isArray(envelope.definitions) ||
        !Array.isArray(envelope.scripts) || !Array.isArray(envelope.styles) ||
        !Array.isArray(envelope.typePolicies) || !Array.isArray(envelope.occurrences) ||
        !Array.isArray(envelope.updatedIds) || !Array.isArray(envelope.replacements) ||
        !Array.isArray(envelope.markers) || own(envelope, "topologyChanges"))
      throw new Error("stale or malformed combined envelope");
    const incoming = new Map(envelope.occurrences.map(item => [item.id, item]));
    normalizeMarkers(envelope.markers, incoming);
    const staged = [], ids = new Set(), updatedIds = new Set(), nextDefinitionTypes = new Map(app.definitionTypes);
    for (const id of envelope.updatedIds) { if (typeof id !== "string" || updatedIds.has(id)) throw new Error("invalid updated occurrence ids"); updatedIds.add(id); }
    for (const action of envelope.occurrences) {
      plain(action, "occurrence action");
      if (typeof action.id !== "string" || typeof action.typeKey !== "string" || typeof action.definitionId !== "string" || (action.parentId !== null && typeof action.parentId !== "string") || (action.placementKey !== null && typeof action.placementKey !== "string") || !own(action, "serverData")) throw new TypeError("invalid occurrence action");
      plain(action.serverData, "serverData");
      plain(action.preparedData, "preparedData");
      if (ids.has(action.id)) throw new Error("duplicate occurrence action"); ids.add(action.id);
      const mounted = app.mounted.get(action.id), prepared = app.occurrences.get(action.id), nextDefinition = app.definitions.get(action.definitionId);
      const added = !prepared;
      if ((prepared && (prepared.typeKey !== action.typeKey || prepared.parentId !== action.parentId || prepared.placementKey !== action.placementKey)) || !nextDefinition) throw new Error("unknown occurrence or definition");
      const boundType = nextDefinitionTypes.get(action.definitionId);
      if (boundType && boundType !== action.typeKey) throw new Error("render definition stable-type mismatch");
      nextDefinitionTypes.set(action.definitionId, action.typeKey);
      const definitionChanged = !prepared || prepared.definitionId !== action.definitionId;
      validateOccurrenceCallRuns(incoming, action, nextDefinition);
      if (definitionChanged) {
        const priorDefinition = prepared && app.definitions.get(prepared.definitionId);
        if (!updatedIds.has(action.id) || nextDefinition.target !== ORDINARY_TARGET ||
            (prepared && (!priorDefinition || priorDefinition.target !== ORDINARY_TARGET)))
          throw new Error("incompatible retained render definition");
      }
      const nextKeys = new Set(Object.keys(action.serverData));
      const serverShapeChanged = mounted ? signatureKey([...nextKeys].sort()) !==
        signatureKey([...mounted.record.serverKeys].sort()) : false;
      if (mounted) for (const key of nextKeys) if (!mounted.record.serverKeys.has(key) && (key in mounted.component || key.startsWith("$") || key.startsWith("_"))) throw new Error("later js_data/public collision: " + key);
      const payloadChanged = added || JSON.stringify(prepared.serverData) !== JSON.stringify(action.serverData) || JSON.stringify(prepared.preparedData) !== JSON.stringify(action.preparedData);
      if (payloadChanged && !updatedIds.has(action.id)) throw new Error("changed occurrence missing from updatedIds");
      if (updatedIds.has(action.id)) staged.push({action: clone(action), ...(mounted || {}), nextKeys,
        serverShapeChanged, definitionChanged, nextDefinition, added});
    }
    validateGraph(incoming, app.rootId);
    for (const id of updatedIds) if (!ids.has(id)) throw new Error("unknown explicitly updated occurrence");
    const removed = [];
    for (const id of app.occurrences.keys()) if (!incoming.has(id)) {
      removed.push(id);
    }
    const addedIds = new Set([...incoming.keys()].filter(id => !app.occurrences.has(id)));
    const expectedRemountIds = new Set(), replacementSites = new Set();
    let priorReplacementOwner, priorReplacementSite;
    for (const replacement of envelope.replacements) {
      plain(replacement, "replacement");
      if (typeof replacement.ownerId !== "string" || typeof replacement.siteId !== "string" || !Array.isArray(replacement.expectedRemountIds)) throw new Error("invalid replacement metadata");
      const siteKey = JSON.stringify([replacement.ownerId, replacement.siteId]);
      if (replacementSites.has(siteKey)) throw new Error("duplicate replacement site");
      replacementSites.add(siteKey);
      if (priorReplacementOwner !== undefined && (replacement.ownerId < priorReplacementOwner ||
          (replacement.ownerId === priorReplacementOwner && replacement.siteId <= priorReplacementSite)))
        throw new Error("replacement sites must be sorted");
      priorReplacementOwner = replacement.ownerId;
      priorReplacementSite = replacement.siteId;
      const ownerStage = staged.find(item => item.action.id === replacement.ownerId);
      if (!ownerStage?.definitionChanged) throw new Error("replacement owner must have a changed definition");
      const declaredSite = ownerStage.nextDefinition.replacementSites.find(item => item.siteId === replacement.siteId);
      const priorSite = app.definitions.get(app.occurrences.get(replacement.ownerId).definitionId)
        .replacementSites.find(item => item.siteId === replacement.siteId);
      if (!declaredSite && !priorSite) throw new Error("replacement site is absent from both definitions");
      const expectedForSite = new Set();
      for (const [site, occurrence] of [[priorSite, app.occurrences.get(replacement.ownerId)], [declaredSite, incoming.get(replacement.ownerId)]]) {
        if (!site) continue;
        for (const localId of site.localDescendants) {
          const call = occurrence.preparedData.calls[localId];
          if (!call) throw new Error("replacement site references an absent ordinary local call");
          if (incoming.has(call.id) && app.mounted.has(call.id)) expectedForSite.add(call.id);
        }
        for (const runId of site.localDescendantRuns) {
          for (const id of occurrence.preparedData.callRuns[runId]) {
            if (incoming.has(id) && app.mounted.has(id)) expectedForSite.add(id);
          }
        }
      }
      if (signatureKey(replacement.expectedRemountIds) !== signatureKey([...expectedForSite].sort()))
        throw new Error("expected remount ids do not match replacement descendant runs");
      let priorRemountId = "";
      for (const id of replacement.expectedRemountIds) {
        if (typeof id !== "string" || expectedRemountIds.has(id) || !incoming.has(id) || id === replacement.ownerId)
          throw new Error("invalid expected remount id");
        if (priorRemountId && id < priorRemountId) throw new Error("expected remount ids must be sorted");
        priorRemountId = id;
        let cursor = incoming.get(id).parentId, descendant = false;
        while (cursor !== null) {
          if (cursor === replacement.ownerId) { descendant = true; break; }
          cursor = incoming.get(cursor).parentId;
        }
        if (!descendant || !app.mounted.has(id)) throw new Error("expected remount is not a mounted descendant");
        expectedRemountIds.add(id);
      }
    }
    for (const item of staged.filter(item => item.definitionChanged && !item.added)) {
      const prior = app.definitions.get(app.occurrences.get(item.action.id).definitionId);
      const before = new Map(prior.replacementSites.map(site => [site.siteId, site.key]));
      const after = new Map(item.nextDefinition.replacementSites.map(site => [site.siteId, site.key]));
      const changed = [...new Set([...before.keys(), ...after.keys()])].filter(id => before.get(id) !== after.get(id)).sort();
      const declared = envelope.replacements.filter(entry => entry.ownerId === item.action.id).map(entry => entry.siteId).sort();
      if (signatureKey(changed) !== signatureKey(declared))
        throw new Error("replacement metadata does not match changed definition sites: " + item.action.id);
      const beforeDirectives = new Map(prior.directiveSignature.map(value => [value.siteId, signatureKey(value)]));
      const afterDirectives = new Map(item.nextDefinition.directiveSignature.map(value => [value.siteId, signatureKey(value)]));
      const changedDirectives = [...new Set([...beforeDirectives.keys(), ...afterDirectives.keys()])]
        .filter(id => beforeDirectives.get(id) !== afterDirectives.get(id));
      if (changedDirectives.some(id => !declared.some(site => id.startsWith(site + "D"))))
        throw new Error("runtime directive change is outside a declared keyed replacement site");
    }
    const expectedNewIds = addedIds;
    return {snapshot: envelope, staged, removed, nextDefinitionTypes, expectedRemountIds, expectedNewIds};
  }

  function registerIncomingTypes(app, snapshot) {
    const incomingTypes = new Set(snapshot.occurrences.map(item => item.typeKey));
    const pending = [];
    for (const typeKey of incomingTypes) {
      if (app.types.has(typeKey)) continue;
      if (!app.vueApp) throw new Error("new prepared component type requires an attached Vue app");
      const tags = new Set();
      for (const definition of app.definitions.values()) {
        for (const call of [...definition.localCalls, ...definition.localCallRuns])
          if (call.typeKey === typeKey) tags.add(call.componentTag);
      }
      if (tags.size !== 1) throw new Error("new prepared component type has no unique component tag");
      const tag = [...tags][0];
      const priorType = [...app.typeTags].find(([, value]) => value === tag)?.[0];
      if (priorType && priorType !== typeKey) throw new Error("prepared component tag is already registered to another type");
      pending.push({typeKey, tag});
    }
    const prepared = [];
    for (const {typeKey, tag} of pending) {
      let options = registeredTypeOptions.get(typeKey)?.options || {};
      for (const plugin of app.browserPlugins) if (typeof plugin.decorateTypeOptions === "function")
        options = plugin.decorateTypeOptions(typeKey, options);
      const callback = options.onServerRender;
      const type = V.defineComponent(typeOptions(app.id, typeKey, options));
      type.__citryCallback = callback;
      prepared.push({typeKey, tag, type});
    }
    for (const {typeKey, tag, type} of prepared) {
      app.types.set(typeKey, type);
      app.typeTags.set(typeKey, tag);
      app.vueApp.component(tag, type);
    }
  }

  function nativeControlElements(root) {
    if (!(root instanceof Element)) return [];
    const elements = [];
    const isNativeControl = value => value instanceof HTMLInputElement || value instanceof HTMLTextAreaElement ||
      value instanceof HTMLSelectElement;
    if (isNativeControl(root)) elements.push(root);
    elements.push(...root.querySelectorAll("input,textarea,select"));
    return elements;
  }

  function captureNativeControlState(root) {
    const snapshots = [];
    for (const element of nativeControlElements(root)) {
      if (controlLifetimes.has(element)) continue;
      if (element instanceof HTMLInputElement) {
        const type = element.type.toLowerCase();
        if (type === "file") continue;
        if (type === "checkbox" || type === "radio") {
          if (element.checked === element.defaultChecked) continue;
          snapshots.push({root, element, kind: "checked", value: element.checked});
          continue;
        }
        if (element.value !== element.defaultValue) snapshots.push({root, element, kind: "value", value: element.value});
        continue;
      }
      if (element instanceof HTMLTextAreaElement) {
        if (element.value !== element.defaultValue) snapshots.push({root, element, kind: "value", value: element.value});
        continue;
      }
      const options = [...element.options];
      const values = options.map(option => option.value);
      const selected = options.map(option => option.selected);
      const defaults = options.map(option => option.defaultSelected);
      if (selected.some((value, index) => value !== defaults[index]))
        snapshots.push({root, element, kind: "selected", values, selected});
    }
    return snapshots;
  }

  function restoreNativeControlState(snapshots) {
    for (const snapshot of snapshots || []) {
      const {root, element} = snapshot;
      if (!(root instanceof Element) || !root.isConnected || !element.isConnected || !root.contains(element)) continue;
      if (snapshot.kind === "value" && "value" in element) element.value = snapshot.value;
      else if (snapshot.kind === "checked" && "checked" in element) element.checked = snapshot.value;
      else if (snapshot.kind === "selected" && element instanceof HTMLSelectElement) {
        const options = [...element.options];
        if (options.length !== snapshot.values.length || options.some((option, index) => option.value !== snapshot.values[index]))
          continue;
        options.forEach((option, index) => { option.selected = snapshot.selected[index]; });
      }
    }
  }

  function captureFocusForPublication() {
    const element = document.activeElement;
    // Body/document focus is the browser's unfocused sentinel, so only retain a user control.
    if (typeof HTMLElement !== "function" || !(element instanceof HTMLElement) ||
        element === document.body || element === document.documentElement)
      return null;
    const isTextControl = (typeof HTMLInputElement === "function" && element instanceof HTMLInputElement) ||
      (typeof HTMLTextAreaElement === "function" && element instanceof HTMLTextAreaElement);
    if (!isTextControl) return null;
    const snapshot = {element, selection: null};
    if (isTextControl) {
      // Keyed moves can clear an active control's range while Vue temporarily detaches it.
      const start = element.selectionStart, end = element.selectionEnd;
      if (Number.isInteger(start) && Number.isInteger(end)) {
        snapshot.selection = {
          start,
          end,
          direction: typeof element.selectionDirection === "string" ? element.selectionDirection : null,
        };
      }
    }
    return snapshot;
  }

  function restoreFocusAfterPublication(snapshot) {
    const element = snapshot?.element;
    if (!element?.isConnected) return;
    const current = document.activeElement;
    const focusWasLost = current === null || current === document || current === document.body ||
      current === document.documentElement;
    // A move to another connected element wins over the focus captured for this render.
    if (!focusWasLost && current !== element) return;
    if (current !== element) {
      try { element.focus({preventScroll: true}); }
      catch (_) { return; }
    }
    const selection = snapshot.selection;
    if (!selection || typeof element.setSelectionRange !== "function") return;
    // Server data may shorten the value, so keep the old range inside its new bounds.
    const length = typeof element.value === "string" ? element.value.length : 0;
    const start = Math.min(selection.start, length), end = Math.min(selection.end, length);
    try {
      if (selection.direction === null) element.setSelectionRange(start, end);
      else element.setSelectionRange(start, end, selection.direction);
    } catch (_) {
      // A control whose type changed during the render no longer accepts text ranges.
    }
  }

  async function applyEnvelope(appId, envelope, targetId = envelope.rootId, pluginTransaction = null) {
    const app = definitionRegistry(appId);
    if (app.busy) throw new Error("concurrent server render rejected");
    if (app.terminal) throw new Error("Citry Vue app lifecycle is terminal");
    const incoming = clone(envelope);
    if (!Array.isArray(incoming.definitions) || !Array.isArray(incoming.occurrences))
      throw new Error("prepared envelope lacks definitions or occurrences");
    preflightDefinitions(app, incoming.definitions, incoming.occurrences, incoming.rootId);
    const {snapshot, staged, removed, nextDefinitionTypes, expectedRemountIds, expectedNewIds} =
      pluginTransaction?.combined ? validateCombinedActions(app, incoming) : validateActions(app, incoming, targetId);
    app.busy = true;
    const priorMounted = new Map(app.mounted);
    const acceptedRetirementIds = new Set([...expectedRemountIds, ...removed]);
    const oldAcceptedRecords = new Map([...acceptedRetirementIds].map(id => [id, app.mounted.get(id)]));
    app.transaction = {
      expectedRemountIds,
      expectedNewIds,
      acceptedRetirementIds,
      oldAcceptedRecords,
      acceptedTransaction: pluginTransaction?.acceptedTransaction,
      newMounts: new Map(),
    };
    try {
      pluginTransaction?.activate();
      registerIncomingTypes(app, snapshot);
    } catch (error) {
      app.transaction = null;
      app.busy = false;
      throw error;
    }
    try {
      const callbackCleanupRecords = new Set();
      for (const item of staged) if (item.record && !item.added && !expectedRemountIds.has(item.action.id))
        callbackCleanupRecords.add(item.record);
      for (const callbackOwnerId of pluginTransaction?.callbackOwnerIds || []) {
        if (acceptedRetirementIds.has(callbackOwnerId)) continue;
        const owner = app.mounted.get(callbackOwnerId)?.record;
        if (owner) callbackCleanupRecords.add(owner);
      }
      for (const record of callbackCleanupRecords) disposeCallbacks(record);
      for (const id of removed) { const mounted = app.mounted.get(id); if (mounted) dispose(mounted.record); }
      for (const {action, component, record, nextKeys, added} of staged) {
        if (!record || added || expectedRemountIds.has(action.id)) continue;
        for (const key of record.serverKeys) if (!nextKeys.has(key)) delete component[key];
        for (const key of nextKeys) if (!record.serverKeys.has(key)) installServerKey(component, record, key);
        record.serverKeys = nextKeys;
      }
      for (const item of staged) if (item.record && item.definitionChanged && !item.added && !expectedRemountIds.has(item.action.id)) item.record.definition.value = {id: item.action.definitionId, render: item.nextDefinition.render, cache: []};
      app.occurrences = new Map(snapshot.occurrences.map(item => [item.id, Object.freeze({...clone(item), serverData: clone(item.serverData)})]));
      app.markers = normalizeMarkers(snapshot.markers, app.occurrences);
      app.definitionTypes = nextDefinitionTypes;
      const changedIds = new Set(staged.map(item => item.action.id)), priorLive = app.snapshot.value;
      const nextLive = new Map([...app.occurrences].map(([id,item]) => [id, changedIds.has(id) || expectedRemountIds.has(id) ? {...item, serverData: V.reactive(clone(item.serverData))} : priorLive.get(id)]));
      // Removed instances keep their prior server data until Vue runs beforeUnmount in this flush.
      for (const id of removed) if (priorLive.has(id)) nextLive.set(id, priorLive.get(id));
      const focusSnapshot = captureFocusForPublication();
      const nativeControlSnapshot = captureNativeControlState(app.hostElement);
      app.snapshot.value = nextLive;
      for (const item of staged) if (item.record && !item.added && !expectedRemountIds.has(item.action.id)) item.record.live.value = nextLive.get(item.action.id);
      for (const item of staged) if (item.record && item.serverShapeChanged && !item.added &&
          !expectedRemountIds.has(item.action.id)) item.component.$forceUpdate();
      await V.nextTick();
      restoreNativeControlState(nativeControlSnapshot);
      restoreFocusAfterPublication(focusSnapshot);
      if (app.terminal) throw new Error("render failed after prepared revision publication");
      if (!app.mounted.has(app.rootId) || [...app.mounted.keys()].some(id => !app.occurrences.has(id)) ||
          removed.some(id => app.mounted.has(id))) throw new Error("rendered occurrence set does not match prepared snapshot");
      validateMountedParents(app);
      for (const id of app.mounted.keys())
        if (!expectedRemountIds.has(id) && !expectedNewIds.has(id) && app.mounted.get(id)?.record !== priorMounted.get(id)?.record)
          throw new Error("unexpected descendant remount");
      for (const id of expectedRemountIds) {
        const mounted = app.mounted.get(id), old = oldAcceptedRecords.get(id);
        const observed = app.transaction.newMounts.get(id);
        if (mounted && (mounted.record === old.record || mounted.record.generation <= old.record.generation ||
            !observed || observed.length !== 1 || observed[0] !== mounted.record.generation))
          throw new Error("expected descendant remount did not occur");
      }
      for (const id of expectedNewIds) {
        const mounted = app.mounted.get(id), observed = app.transaction.newMounts.get(id);
        if (mounted && (!observed || observed.length !== 1 || observed[0] !== mounted.record.generation))
          throw new Error("new occurrence mount generation is invalid");
      }
      const expectedMounted = new Set([...expectedRemountIds, ...expectedNewIds]);
      if ([...app.transaction.newMounts.keys()].some(id => !expectedMounted.has(id)))
        throw new Error("unexpected descendant remount occurred");
      if (removed.length) app.snapshot.value = new Map([...app.snapshot.value].filter(([id]) => app.occurrences.has(id)));
      const callbackIds = new Set([...staged.map(item => item.action.id), ...expectedRemountIds,
        ...(pluginTransaction?.callbackOwnerIds || [])]
        .filter(id => app.mounted.has(id)));
      app.revision = snapshot.revision;
      pluginTransaction?.commit();
      if (app.preparedHost) {
        const stagedCallbackIds = new Set([...staged.map(item => item.action.id), ...expectedRemountIds]);
        const mounted = [...callbackIds].map(id => {
          const current = app.mounted.get(id);
          if (!current) throw new Error("prepared callback target is not mounted");
          return {
            stableId: id,
            generation: current.record.generation,
            occurrence: app.occurrences.get(id),
            adoptContext: stagedCallbackIds.has(id),
          };
        });
        await app.preparedHost.beforeServerCallbacks({revision: app.revision, mounted});
      }
      for (const id of callbackIds) {
        const mounted = app.mounted.get(id);
        await runCallback(mounted.component, mounted.record, mounted.component.$options.__citryCallback, app.revision);
      }
      await V.nextTick();
      if (app.terminal) throw new Error("render failed during onServerRender flush");
    } catch (error) {
      app.terminal = true;
      try { app.vueApp?.unmount(); } catch (unmountError) { console.error("[Citry] terminal Vue disposal failed:", unmountError); }
      throw error;
    }
    finally { app.transaction = null; app.busy = false; }
  }

  // Kept private on the stable options so the coordinator invokes the exact type callback.
  const originalDefineType = defineType;
  function defineTypeWithCallback(appId, typeKey, userOptions) {
    const resolvedOptions = userOptions === undefined ? registeredTypeOptions.get(typeKey)?.options || {} : userOptions;
    const callback = resolvedOptions.onServerRender;
    const result = originalDefineType(appId, typeKey, resolvedOptions);
    result.__citryCallback = callback;
    return result;
  }

  global.CitryStable = {configure, registerDefinition, registerTypeOptions, registerBrowserPlugin, defineType: defineTypeWithCallback, startPrepared, attachVueApp, attachPreparedHost, whenReady, applyEnvelope, compilerRuntime, _apps: apps};
  if (!global.CitryVueFragments?.installFragmentManager)
    throw new Error("Citry Vue fragment support is unavailable");
  const fragmentDocumentNonce = document.currentScript?.nonce || document.currentScript?.getAttribute("nonce") || "";
  global.CitryVueFragments.installFragmentManager(
    global.Citry ||= {},
    (node, exceptAppId) => [...apps.values()].some(app => app.id !== exceptAppId &&
      app.hostElement instanceof Element && app.hostElement.contains(node)),
    startPrepared,
    fragmentDocumentNonce,
  );
})(window);
