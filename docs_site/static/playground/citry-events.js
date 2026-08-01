/* Citry events client runtime. GENERATED FILE, do not edit: built from packages/js/citry-client/src/citry-events.ts (pnpm run build there). Bundles AlpineJS 3.15.12 + @alpinejs/morph 3.15.12 (MIT). */
(() => {
  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/scheduler.js
  var flushPending = false;
  var flushing = false;
  var queue = [];
  var lastFlushedIndex = -1;
  var transactionActive = false;
  function scheduler(callback) {
    queueJob(callback);
  }
  function startTransaction() {
    transactionActive = true;
  }
  function commitTransaction() {
    transactionActive = false;
    queueFlush();
  }
  function queueJob(job) {
    if (!queue.includes(job)) queue.push(job);
    queueFlush();
  }
  function dequeueJob(job) {
    let index = queue.indexOf(job);
    if (index !== -1 && index > lastFlushedIndex) queue.splice(index, 1);
  }
  function queueFlush() {
    if (!flushing && !flushPending) {
      if (transactionActive) return;
      flushPending = true;
      queueMicrotask(flushJobs);
    }
  }
  function flushJobs() {
    flushPending = false;
    flushing = true;
    for (let i = 0; i < queue.length; i++) {
      queue[i]();
      lastFlushedIndex = i;
    }
    queue.length = 0;
    lastFlushedIndex = -1;
    flushing = false;
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/reactivity.js
  var reactive;
  var effect;
  var release;
  var raw;
  var shouldSchedule = true;
  function disableEffectScheduling(callback) {
    shouldSchedule = false;
    callback();
    shouldSchedule = true;
  }
  function setReactivityEngine(engine) {
    reactive = engine.reactive;
    release = engine.release;
    effect = (callback) => engine.effect(callback, { scheduler: (task) => {
      if (shouldSchedule) {
        scheduler(task);
      } else {
        task();
      }
    } });
    raw = engine.raw;
  }
  function overrideEffect(override) {
    effect = override;
  }
  function elementBoundEffect(el) {
    let cleanup2 = () => {
    };
    let wrappedEffect = (callback) => {
      let effectReference = effect(callback);
      if (!el._x_effects) {
        el._x_effects = /* @__PURE__ */ new Set();
        el._x_runEffects = () => {
          el._x_effects.forEach((i) => i());
        };
      }
      el._x_effects.add(effectReference);
      cleanup2 = () => {
        if (effectReference === void 0) return;
        el._x_effects.delete(effectReference);
        release(effectReference);
      };
      return effectReference;
    };
    return [wrappedEffect, () => {
      cleanup2();
    }];
  }
  function watch(getter, callback) {
    let firstTime = true;
    let oldValue;
    let oldValueJSON;
    let effectReference = effect(() => {
      let value = getter();
      let newJSON = JSON.stringify(value);
      if (!firstTime) {
        if (typeof value === "object" || value !== oldValue) {
          let previousValue = typeof oldValue === "object" ? JSON.parse(oldValueJSON) : oldValue;
          queueMicrotask(() => {
            callback(value, previousValue);
          });
        }
      }
      oldValue = value;
      oldValueJSON = newJSON;
      firstTime = false;
    });
    return () => release(effectReference);
  }
  async function transaction(callback) {
    startTransaction();
    try {
      await callback();
      await Promise.resolve();
    } finally {
      commitTransaction();
    }
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/mutation.js
  var onAttributeAddeds = [];
  var onElRemoveds = [];
  var onElAddeds = [];
  function onElAdded(callback) {
    onElAddeds.push(callback);
  }
  function onElRemoved(el, callback) {
    if (typeof callback === "function") {
      if (!el._x_cleanups) el._x_cleanups = [];
      el._x_cleanups.push(callback);
    } else {
      callback = el;
      onElRemoveds.push(callback);
    }
  }
  function onAttributesAdded(callback) {
    onAttributeAddeds.push(callback);
  }
  function onAttributeRemoved(el, name, callback) {
    if (!el._x_attributeCleanups) el._x_attributeCleanups = {};
    if (!el._x_attributeCleanups[name]) el._x_attributeCleanups[name] = [];
    el._x_attributeCleanups[name].push(callback);
  }
  function cleanupAttributes(el, names) {
    if (!el._x_attributeCleanups) return;
    Object.entries(el._x_attributeCleanups).forEach(([name, value]) => {
      if (names === void 0 || names.includes(name)) {
        value.forEach((i) => i());
        delete el._x_attributeCleanups[name];
      }
    });
  }
  function cleanupElement(el) {
    el._x_effects?.forEach(dequeueJob);
    while (el._x_cleanups?.length) el._x_cleanups.pop()();
  }
  var observer = new MutationObserver(onMutate);
  var currentlyObserving = false;
  function startObservingMutations() {
    observer.observe(document, { subtree: true, childList: true, attributes: true, attributeOldValue: true });
    currentlyObserving = true;
  }
  function stopObservingMutations() {
    flushObserver();
    observer.disconnect();
    currentlyObserving = false;
  }
  var queuedMutations = [];
  function flushObserver() {
    let records = observer.takeRecords();
    queuedMutations.push(() => records.length > 0 && onMutate(records));
    let queueLengthWhenTriggered = queuedMutations.length;
    queueMicrotask(() => {
      if (queuedMutations.length === queueLengthWhenTriggered) {
        while (queuedMutations.length > 0) queuedMutations.shift()();
      }
    });
  }
  function mutateDom(callback) {
    if (!currentlyObserving) return callback();
    stopObservingMutations();
    let result = callback();
    startObservingMutations();
    return result;
  }
  var isCollecting = false;
  var deferredMutations = [];
  function deferMutations() {
    isCollecting = true;
  }
  function flushAndStopDeferringMutations() {
    isCollecting = false;
    onMutate(deferredMutations);
    deferredMutations = [];
  }
  function onMutate(mutations) {
    if (isCollecting) {
      deferredMutations = deferredMutations.concat(mutations);
      return;
    }
    let addedNodes = [];
    let removedNodes = /* @__PURE__ */ new Set();
    let addedAttributes = /* @__PURE__ */ new Map();
    let removedAttributes = /* @__PURE__ */ new Map();
    for (let i = 0; i < mutations.length; i++) {
      if (mutations[i].target._x_ignoreMutationObserver) continue;
      if (mutations[i].type === "childList") {
        mutations[i].removedNodes.forEach((node) => {
          if (node.nodeType !== 1) return;
          if (!node._x_marker) return;
          removedNodes.add(node);
        });
        mutations[i].addedNodes.forEach((node) => {
          if (node.nodeType !== 1) return;
          if (removedNodes.has(node)) {
            removedNodes.delete(node);
            return;
          }
          if (node._x_marker) return;
          addedNodes.push(node);
        });
      }
      if (mutations[i].type === "attributes") {
        let el = mutations[i].target;
        let name = mutations[i].attributeName;
        let oldValue = mutations[i].oldValue;
        let add2 = () => {
          if (!addedAttributes.has(el)) addedAttributes.set(el, []);
          addedAttributes.get(el).push({ name, value: el.getAttribute(name) });
        };
        let remove = () => {
          if (!removedAttributes.has(el)) removedAttributes.set(el, []);
          removedAttributes.get(el).push(name);
        };
        if (el.hasAttribute(name) && oldValue === null) {
          add2();
        } else if (el.hasAttribute(name)) {
          remove();
          add2();
        } else {
          remove();
        }
      }
    }
    removedAttributes.forEach((attrs, el) => {
      cleanupAttributes(el, attrs);
    });
    addedAttributes.forEach((attrs, el) => {
      onAttributeAddeds.forEach((i) => i(el, attrs));
    });
    for (let node of removedNodes) {
      if (addedNodes.some((i) => i.contains(node))) continue;
      onElRemoveds.forEach((i) => i(node));
    }
    for (let node of addedNodes) {
      if (!node.isConnected) continue;
      onElAddeds.forEach((i) => i(node));
    }
    addedNodes = null;
    removedNodes = null;
    addedAttributes = null;
    removedAttributes = null;
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/scope.js
  function scope(node) {
    return mergeProxies(closestDataStack(node));
  }
  function addScopeToNode(node, data2, referenceNode) {
    node._x_dataStack = [data2, ...closestDataStack(referenceNode || node)];
    return () => {
      node._x_dataStack = node._x_dataStack.filter((i) => i !== data2);
    };
  }
  function closestDataStack(node) {
    if (node._x_dataStack) return node._x_dataStack;
    if (typeof ShadowRoot === "function" && node instanceof ShadowRoot) {
      return closestDataStack(node.host);
    }
    if (!node.parentNode) {
      return [];
    }
    return closestDataStack(node.parentNode);
  }
  function mergeProxies(objects) {
    return new Proxy({ objects }, mergeProxyTrap);
  }
  function keyInPrototypeChain(obj, key) {
    if (obj === null || obj === Object.prototype) return null;
    if (Object.prototype.hasOwnProperty.call(obj, key)) return obj;
    return keyInPrototypeChain(Object.getPrototypeOf(obj), key);
  }
  var mergeProxyTrap = {
    ownKeys({ objects }) {
      return Array.from(
        new Set(objects.flatMap((i) => Object.keys(i)))
      );
    },
    has({ objects }, name) {
      if (name == Symbol.unscopables) return false;
      return objects.some(
        (obj) => Object.prototype.hasOwnProperty.call(obj, name) || Reflect.has(obj, name)
      );
    },
    get({ objects }, name, thisProxy) {
      if (name == "toJSON") return collapseProxies;
      return Reflect.get(
        objects.find(
          (obj) => Reflect.has(obj, name)
        ) || {},
        name,
        thisProxy
      );
    },
    set({ objects }, name, value, thisProxy) {
      let target;
      for (const obj of objects) {
        target = keyInPrototypeChain(obj, name);
        if (target) break;
      }
      if (!target) target = objects[objects.length - 1];
      const descriptor = Object.getOwnPropertyDescriptor(target, name);
      if (descriptor?.set && descriptor?.get)
        return descriptor.set.call(thisProxy, value) || true;
      return Reflect.set(target, name, value);
    }
  };
  function collapseProxies() {
    let keys = Reflect.ownKeys(this);
    return keys.reduce((acc, key) => {
      acc[key] = Reflect.get(this, key);
      return acc;
    }, {});
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/interceptor.js
  function initInterceptors(data2) {
    let isObject3 = (val) => typeof val === "object" && !Array.isArray(val) && val !== null;
    let recurse = (obj, basePath = "") => {
      Object.entries(Object.getOwnPropertyDescriptors(obj)).forEach(([key, { value, enumerable }]) => {
        if (enumerable === false || value === void 0) return;
        if (typeof value === "object" && value !== null && value.__v_skip) return;
        let path = basePath === "" ? key : `${basePath}.${key}`;
        if (typeof value === "object" && value !== null && value._x_interceptor) {
          obj[key] = value.initialize(data2, path, key);
        } else {
          if (isObject3(value) && value !== obj && !(value instanceof Element)) {
            recurse(value, path);
          }
        }
      });
    };
    return recurse(data2);
  }
  function interceptor(callback, mutateObj = () => {
  }) {
    let obj = {
      initialValue: void 0,
      _x_interceptor: true,
      initialize(data2, path, key) {
        return callback(this.initialValue, () => get(data2, path), (value) => set(data2, path, value), path, key);
      }
    };
    mutateObj(obj);
    return (initialValue) => {
      if (typeof initialValue === "object" && initialValue !== null && initialValue._x_interceptor) {
        let initialize = obj.initialize.bind(obj);
        obj.initialize = (data2, path, key) => {
          let innerValue = initialValue.initialize(data2, path, key);
          obj.initialValue = innerValue;
          return initialize(data2, path, key);
        };
      } else {
        obj.initialValue = initialValue;
      }
      return obj;
    };
  }
  function get(obj, path) {
    return path.split(".").reduce((carry, segment) => carry[segment], obj);
  }
  function set(obj, path, value) {
    if (typeof path === "string") path = path.split(".");
    if (path.length === 1) obj[path[0]] = value;
    else if (path.length === 0) throw error;
    else {
      if (obj[path[0]])
        return set(obj[path[0]], path.slice(1), value);
      else {
        obj[path[0]] = {};
        return set(obj[path[0]], path.slice(1), value);
      }
    }
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/magics.js
  var magics = {};
  function magic(name, callback) {
    magics[name] = callback;
  }
  function injectMagics(obj, el) {
    let memoizedUtilities = getUtilities(el);
    Object.entries(magics).forEach(([name, callback]) => {
      Object.defineProperty(obj, `$${name}`, {
        get() {
          return callback(el, memoizedUtilities);
        },
        enumerable: false
      });
    });
    return obj;
  }
  function getUtilities(el) {
    let [utilities, cleanup2] = getElementBoundUtilities(el);
    let utils = { interceptor, ...utilities };
    onElRemoved(el, cleanup2);
    return utils;
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/utils/error.js
  function tryCatch(el, expression, callback, ...args) {
    try {
      return callback(...args);
    } catch (e) {
      handleError(e, el, expression);
    }
  }
  function handleError(...args) {
    return errorHandler(...args);
  }
  var errorHandler = normalErrorHandler;
  function setErrorHandler(handler4) {
    errorHandler = handler4;
  }
  function normalErrorHandler(error2, el, expression = void 0) {
    error2 = Object.assign(
      error2 ?? { message: "No error message given." },
      { el, expression }
    );
    console.warn(`Alpine Expression Error: ${error2.message}

${expression ? 'Expression: "' + expression + '"\n\n' : ""}`, el);
    setTimeout(() => {
      throw error2;
    }, 0);
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/evaluator.js
  var shouldAutoEvaluateFunctions = true;
  function dontAutoEvaluateFunctions(callback) {
    let cache = shouldAutoEvaluateFunctions;
    shouldAutoEvaluateFunctions = false;
    let result = callback();
    shouldAutoEvaluateFunctions = cache;
    return result;
  }
  function evaluate(el, expression, extras = {}) {
    let result;
    evaluateLater(el, expression)((value) => result = value, extras);
    return result;
  }
  function evaluateLater(...args) {
    return theEvaluatorFunction(...args);
  }
  var theEvaluatorFunction = () => {
  };
  function setEvaluator(newEvaluator) {
    theEvaluatorFunction = newEvaluator;
  }
  var theRawEvaluatorFunction;
  function setRawEvaluator(newEvaluator) {
    theRawEvaluatorFunction = newEvaluator;
  }
  function normalEvaluator(el, expression) {
    let overriddenMagics = {};
    injectMagics(overriddenMagics, el);
    let dataStack = [overriddenMagics, ...closestDataStack(el)];
    let evaluator = typeof expression === "function" ? generateEvaluatorFromFunction(dataStack, expression) : generateEvaluatorFromString(dataStack, expression, el);
    return tryCatch.bind(null, el, expression, evaluator);
  }
  function generateEvaluatorFromFunction(dataStack, func) {
    return (receiver = () => {
    }, { scope: scope2 = {}, params = [], context } = {}) => {
      if (!shouldAutoEvaluateFunctions) {
        runIfTypeOfFunction(receiver, func, mergeProxies([scope2, ...dataStack]), params);
        return;
      }
      let result = func.apply(mergeProxies([scope2, ...dataStack]), params);
      runIfTypeOfFunction(receiver, result);
    };
  }
  var evaluatorMemo = {};
  function generateFunctionFromString(expression, el) {
    if (evaluatorMemo[expression]) {
      return evaluatorMemo[expression];
    }
    let AsyncFunction = Object.getPrototypeOf(async function() {
    }).constructor;
    let rightSideSafeExpression = /^[\n\s]*if.*\(.*\)/.test(expression.trim()) || /^(let|const)\s/.test(expression.trim()) ? `(async()=>{ ${expression} })()` : expression;
    const safeAsyncFunction = () => {
      try {
        let func2 = new AsyncFunction(
          ["__self", "scope"],
          `with (scope) { __self.result = ${rightSideSafeExpression} }; __self.finished = true; return __self.result;`
        );
        Object.defineProperty(func2, "name", {
          value: `[Alpine] ${expression}`
        });
        return func2;
      } catch (error2) {
        handleError(error2, el, expression);
        return Promise.resolve();
      }
    };
    let func = safeAsyncFunction();
    evaluatorMemo[expression] = func;
    return func;
  }
  function generateEvaluatorFromString(dataStack, expression, el) {
    let func = generateFunctionFromString(expression, el);
    return (receiver = () => {
    }, { scope: scope2 = {}, params = [], context } = {}) => {
      func.result = void 0;
      func.finished = false;
      let completeScope = mergeProxies([scope2, ...dataStack]);
      if (typeof func === "function") {
        let promise = func.call(context, func, completeScope).catch((error2) => handleError(error2, el, expression));
        if (func.finished) {
          runIfTypeOfFunction(receiver, func.result, completeScope, params, el);
          func.result = void 0;
        } else {
          promise.then((result) => {
            runIfTypeOfFunction(receiver, result, completeScope, params, el);
          }).catch((error2) => handleError(error2, el, expression)).finally(() => func.result = void 0);
        }
      }
    };
  }
  function runIfTypeOfFunction(receiver, value, scope2, params, el) {
    if (shouldAutoEvaluateFunctions && typeof value === "function") {
      let result = value.apply(scope2, params);
      if (result instanceof Promise) {
        result.then((i) => runIfTypeOfFunction(receiver, i, scope2, params)).catch((error2) => handleError(error2, el, value));
      } else {
        receiver(result);
      }
    } else if (typeof value === "object" && value instanceof Promise) {
      value.then((i) => receiver(i));
    } else {
      receiver(value);
    }
  }
  function evaluateRaw(...args) {
    return theRawEvaluatorFunction(...args);
  }
  function normalRawEvaluator(el, expression, extras = {}) {
    let overriddenMagics = {};
    injectMagics(overriddenMagics, el);
    let dataStack = [overriddenMagics, ...closestDataStack(el)];
    let scope2 = mergeProxies([extras.scope ?? {}, ...dataStack]);
    let params = extras.params ?? [];
    if (expression.includes("await")) {
      let AsyncFunction = Object.getPrototypeOf(async function() {
      }).constructor;
      let rightSideSafeExpression = /^[\n\s]*if.*\(.*\)/.test(expression.trim()) || /^(let|const)\s/.test(expression.trim()) ? `(async()=>{ ${expression} })()` : expression;
      let func = new AsyncFunction(
        ["scope"],
        `with (scope) { let __result = ${rightSideSafeExpression}; return __result }`
      );
      let result = func.call(extras.context, scope2);
      return result;
    } else {
      let rightSideSafeExpression = /^[\n\s]*if.*\(.*\)/.test(expression.trim()) || /^(let|const)\s/.test(expression.trim()) ? `(()=>{ ${expression} })()` : expression;
      let func = new Function(
        ["scope"],
        `with (scope) { let __result = ${rightSideSafeExpression}; return __result }`
      );
      let result = func.call(extras.context, scope2);
      if (typeof result === "function" && shouldAutoEvaluateFunctions) {
        return result.apply(scope2, params);
      }
      return result;
    }
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/directives.js
  function runCitryAmbientDirective(el, attributeName, registerCleanup, callback) {
    let run = globalThis.Citry && globalThis.Citry.alpine && globalThis.Citry.alpine._runDirective;
    return typeof run === "function" ? run(el, attributeName, registerCleanup, callback) : callback();
  }
  var prefixAsString = "x-";
  function prefix(subject = "") {
    return prefixAsString + subject;
  }
  function setPrefix(newPrefix) {
    prefixAsString = newPrefix;
  }
  var directiveHandlers = {};
  function directive(name, callback) {
    directiveHandlers[name] = callback;
    return {
      before(directive2) {
        if (!directiveHandlers[directive2]) {
          console.warn(String.raw`Cannot find directive \`${directive2}\`. \`${name}\` will use the default order of execution`);
          return;
        }
        const pos = directiveOrder.indexOf(directive2);
        directiveOrder.splice(pos >= 0 ? pos : directiveOrder.indexOf("DEFAULT"), 0, name);
      }
    };
  }
  function directiveExists(name) {
    return Object.keys(directiveHandlers).includes(name);
  }
  function directives(el, attributes, originalAttributeOverride) {
    attributes = Array.from(attributes);
    if (el._x_virtualDirectives) {
      let vAttributes = Object.entries(el._x_virtualDirectives).map(([name, value]) => ({ name, value }));
      let staticAttributes = attributesOnly(vAttributes);
      vAttributes = vAttributes.map((attribute) => {
        if (staticAttributes.find((attr) => attr.name === attribute.name)) {
          return {
            name: `x-bind:${attribute.name}`,
            value: `"${attribute.value}"`
          };
        }
        return attribute;
      });
      attributes = attributes.concat(vAttributes);
    }
    let transformedAttributeMap = {};
    let directives2 = attributes.map(toTransformedAttributes((newName, oldName) => transformedAttributeMap[newName] = oldName)).filter(outNonAlpineAttributes).map(toParsedDirectives(transformedAttributeMap, originalAttributeOverride)).sort(byPriority);
    return directives2.map((directive2) => {
      return getDirectiveHandler(el, directive2);
    });
  }
  function attributesOnly(attributes) {
    return Array.from(attributes).map(toTransformedAttributes()).filter((attr) => !outNonAlpineAttributes(attr));
  }
  var isDeferringHandlers = false;
  var directiveHandlerStacks = /* @__PURE__ */ new Map();
  var currentHandlerStackKey = /* @__PURE__ */ Symbol();
  function deferHandlingDirectives(callback) {
    isDeferringHandlers = true;
    let key = /* @__PURE__ */ Symbol();
    currentHandlerStackKey = key;
    directiveHandlerStacks.set(key, []);
    let flushHandlers = () => {
      while (directiveHandlerStacks.get(key).length) directiveHandlerStacks.get(key).shift()();
      directiveHandlerStacks.delete(key);
    };
    let stopDeferring = () => {
      isDeferringHandlers = false;
      flushHandlers();
    };
    callback(flushHandlers);
    stopDeferring();
  }
  function getElementBoundUtilities(el) {
    let cleanups = [];
    let cleanup2 = (callback) => cleanups.push(callback);
    let [effect3, cleanupEffect] = elementBoundEffect(el);
    cleanups.push(cleanupEffect);
    let utilities = {
      Alpine: alpine_default,
      effect: effect3,
      cleanup: cleanup2,
      evaluateLater: evaluateLater.bind(evaluateLater, el),
      evaluate: evaluate.bind(evaluate, el)
    };
    let doCleanup = () => cleanups.forEach((i) => i());
    return [utilities, doCleanup];
  }
  function getDirectiveHandler(el, directive2) {
    let noop = () => {
    };
    let handler4 = directiveHandlers[directive2.type] || noop;
    let [utilities, cleanup2] = getElementBoundUtilities(el);
    onAttributeRemoved(el, directive2.original, cleanup2);
    let fullHandler = () => {
      if (el._x_ignore || el._x_ignoreSelf) return;
      handler4.inline && runCitryAmbientDirective(
        el,
        directive2.original,
        utilities.cleanup,
        () => handler4.inline(el, directive2, utilities)
      );
      handler4 = handler4.bind(handler4, el, directive2, utilities);
      let runHandler = () => runCitryAmbientDirective(el, directive2.original, utilities.cleanup, handler4);
      isDeferringHandlers ? directiveHandlerStacks.get(currentHandlerStackKey).push(runHandler) : runHandler();
    };
    fullHandler.runCleanups = cleanup2;
    return fullHandler;
  }
  var startingWith = (subject, replacement) => ({ name, value }) => {
    if (name.startsWith(subject)) name = name.replace(subject, replacement);
    return { name, value };
  };
  var into = (i) => i;
  function toTransformedAttributes(callback = () => {
  }) {
    return ({ name, value }) => {
      let { name: newName, value: newValue } = attributeTransformers.reduce((carry, transform) => {
        return transform(carry);
      }, { name, value });
      if (newName !== name) callback(newName, name);
      return { name: newName, value: newValue };
    };
  }
  var attributeTransformers = [];
  function mapAttributes(callback) {
    attributeTransformers.push(callback);
  }
  function outNonAlpineAttributes({ name }) {
    return alpineAttributeRegex().test(name);
  }
  var alpineAttributeRegex = () => new RegExp(`^${prefixAsString}([^:^.]+)\\b`);
  function toParsedDirectives(transformedAttributeMap, originalAttributeOverride) {
    return ({ name, value }) => {
      if (name === value) value = "";
      let typeMatch = name.match(alpineAttributeRegex());
      let valueMatch = name.match(/:([a-zA-Z0-9\-_:]+)/);
      let modifiers = name.match(/\.[^.\]]+(?=[^\]]*$)/g) || [];
      let original = originalAttributeOverride || transformedAttributeMap[name] || name;
      return {
        type: typeMatch ? typeMatch[1] : null,
        value: valueMatch ? valueMatch[1] : null,
        modifiers: modifiers.map((i) => i.replace(".", "")),
        expression: value,
        original
      };
    };
  }
  var DEFAULT = "DEFAULT";
  var directiveOrder = [
    "ignore",
    "ref",
    "id",
    "data",
    "anchor",
    "bind",
    "init",
    "for",
    "model",
    "modelable",
    "transition",
    "show",
    "if",
    DEFAULT,
    "teleport"
  ];
  function byPriority(a, b) {
    let typeA = directiveOrder.indexOf(a.type) === -1 ? DEFAULT : a.type;
    let typeB = directiveOrder.indexOf(b.type) === -1 ? DEFAULT : b.type;
    return directiveOrder.indexOf(typeA) - directiveOrder.indexOf(typeB);
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/utils/dispatch.js
  function dispatch(el, name, detail = {}, options = {}) {
    return el.dispatchEvent(
      new CustomEvent(name, {
        detail,
        bubbles: true,
        // Allows events to pass the shadow DOM barrier.
        composed: true,
        cancelable: true,
        // Allows overriding the default event options.
        ...options
      })
    );
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/utils/walk.js
  function walk(el, callback) {
    if (typeof ShadowRoot === "function" && el instanceof ShadowRoot) {
      Array.from(el.children).forEach((el2) => walk(el2, callback));
      return;
    }
    let skip = false;
    callback(el, () => skip = true);
    if (skip) return;
    let node = el.firstElementChild;
    while (node) {
      walk(node, callback, false);
      node = node.nextElementSibling;
    }
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/utils/warn.js
  function warn(message, ...args) {
    console.warn(`Alpine Warning: ${message}`, ...args);
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/lifecycle.js
  var started = false;
  function start() {
    if (started) warn("Alpine has already been initialized on this page. Calling Alpine.start() more than once can cause problems.");
    started = true;
    if (!document.body) warn("Unable to initialize. Trying to load Alpine before `<body>` is available. Did you forget to add `defer` in Alpine's `<script>` tag?");
    dispatch(document, "alpine:init");
    dispatch(document, "alpine:initializing");
    startObservingMutations();
    onElAdded((el) => initTree(el, walk));
    onElRemoved((el) => destroyTree(el));
    onAttributesAdded((el, attrs) => {
      directives(el, attrs).forEach((handle) => handle());
    });
    let outNestedComponents = (el) => !closestRoot(el.parentElement, true);
    Array.from(document.querySelectorAll(allSelectors().join(","))).filter(outNestedComponents).forEach((el) => {
      initTree(el);
    });
    dispatch(document, "alpine:initialized");
    setTimeout(() => {
      warnAboutMissingPlugins();
    });
  }
  var rootSelectorCallbacks = [];
  var initSelectorCallbacks = [];
  function rootSelectors() {
    return rootSelectorCallbacks.map((fn) => fn());
  }
  function allSelectors() {
    return rootSelectorCallbacks.concat(initSelectorCallbacks).map((fn) => fn());
  }
  function addRootSelector(selectorCallback) {
    rootSelectorCallbacks.push(selectorCallback);
  }
  function addInitSelector(selectorCallback) {
    initSelectorCallbacks.push(selectorCallback);
  }
  function closestRoot(el, includeInitSelectors = false) {
    return findClosest(el, (element) => {
      const selectors = includeInitSelectors ? allSelectors() : rootSelectors();
      if (selectors.some((selector) => element.matches(selector))) return true;
    });
  }
  function findClosest(el, callback) {
    if (!el) return;
    if (callback(el)) return el;
    if (el._x_teleportBack) return findClosest(el._x_teleportBack, callback);
    if (el.parentNode instanceof ShadowRoot) {
      return findClosest(el.parentNode.host, callback);
    }
    if (!el.parentElement) return;
    return findClosest(el.parentElement, callback);
  }
  function isRoot(el) {
    return rootSelectors().some((selector) => el.matches(selector));
  }
  var initInterceptors2 = [];
  function interceptInit(callback) {
    initInterceptors2.push(callback);
  }
  var markerDispenser = 1;
  function initTree(el, walker = walk, intercept = () => {
  }) {
    if (findClosest(el, (i) => i._x_ignore)) return;
    deferHandlingDirectives(() => {
      walker(el, (el2, skip) => {
        if (el2._x_marker) return;
        intercept(el2, skip);
        initInterceptors2.forEach((i) => i(el2, skip));
        directives(el2, el2.attributes).forEach((handle) => handle());
        if (!el2._x_ignore) el2._x_marker = markerDispenser++;
        el2._x_ignore && skip();
      });
    });
  }
  function destroyTree(root, walker = walk) {
    walker(root, (el) => {
      cleanupElement(el);
      cleanupAttributes(el);
      delete el._x_marker;
    });
  }
  function warnAboutMissingPlugins() {
    let pluginDirectives = [
      ["ui", "dialog", ["[x-dialog], [x-popover]"]],
      ["anchor", "anchor", ["[x-anchor]"]],
      ["sort", "sort", ["[x-sort]"]]
    ];
    pluginDirectives.forEach(([plugin2, directive2, selectors]) => {
      if (directiveExists(directive2)) return;
      selectors.some((selector) => {
        if (document.querySelector(selector)) {
          warn(`found "${selector}", but missing ${plugin2} plugin`);
          return true;
        }
      });
    });
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/nextTick.js
  var tickStack = [];
  var isHolding = false;
  function nextTick(callback = () => {
  }) {
    queueMicrotask(() => {
      isHolding || setTimeout(() => {
        releaseNextTicks();
      });
    });
    return new Promise((res) => {
      tickStack.push(() => {
        callback();
        res();
      });
    });
  }
  function releaseNextTicks() {
    isHolding = false;
    while (tickStack.length) tickStack.shift()();
  }
  function holdNextTicks() {
    isHolding = true;
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/utils/classes.js
  function setClasses(el, value) {
    if (Array.isArray(value)) {
      return setClassesFromString(el, value.join(" "));
    } else if (typeof value === "object" && value !== null) {
      return setClassesFromObject(el, value);
    } else if (typeof value === "function") {
      return setClasses(el, value());
    }
    return setClassesFromString(el, value);
  }
  function splitClasses(classString) {
    return classString.split(/\s/).filter(Boolean);
  }
  function setClassesFromString(el, classString) {
    let missingClasses = (classString2) => splitClasses(classString2).filter((i) => !el.classList.contains(i)).filter(Boolean);
    let addClassesAndReturnUndo = (classes) => {
      el.classList.add(...classes);
      return () => {
        el.classList.remove(...classes);
      };
    };
    classString = classString === true ? classString = "" : classString || "";
    return addClassesAndReturnUndo(missingClasses(classString));
  }
  function setClassesFromObject(el, classObject) {
    let forAdd = Object.entries(classObject).flatMap(([classString, bool]) => bool ? splitClasses(classString) : false).filter(Boolean);
    let forRemove = Object.entries(classObject).flatMap(([classString, bool]) => !bool ? splitClasses(classString) : false).filter(Boolean);
    let added = [];
    let removed = [];
    forRemove.forEach((i) => {
      if (el.classList.contains(i)) {
        el.classList.remove(i);
        removed.push(i);
      }
    });
    forAdd.forEach((i) => {
      if (!el.classList.contains(i)) {
        el.classList.add(i);
        added.push(i);
      }
    });
    return () => {
      removed.forEach((i) => el.classList.add(i));
      added.forEach((i) => el.classList.remove(i));
    };
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/utils/styles.js
  function setStyles(el, value) {
    if (typeof value === "object" && value !== null) {
      return setStylesFromObject(el, value);
    }
    return setStylesFromString(el, value);
  }
  function setStylesFromObject(el, value) {
    let previousStyles = {};
    Object.entries(value).forEach(([key, value2]) => {
      previousStyles[key] = el.style[key];
      if (!key.startsWith("--")) {
        key = kebabCase(key);
      }
      el.style.setProperty(key, value2);
    });
    setTimeout(() => {
      if (el.style.length === 0) {
        el.removeAttribute("style");
      }
    });
    return () => {
      setStyles(el, previousStyles);
    };
  }
  function setStylesFromString(el, value) {
    let cache = el.getAttribute("style", value);
    el.setAttribute("style", value);
    return () => {
      el.setAttribute("style", cache || "");
    };
  }
  function kebabCase(subject) {
    return subject.replace(/([a-z])([A-Z])/g, "$1-$2").toLowerCase();
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/utils/once.js
  function once(callback, fallback = () => {
  }) {
    let called = false;
    return function() {
      if (!called) {
        called = true;
        callback.apply(this, arguments);
      } else {
        fallback.apply(this, arguments);
      }
    };
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/directives/x-transition.js
  directive("transition", (el, { value, modifiers, expression }, { evaluate: evaluate2 }) => {
    if (typeof expression === "function") expression = evaluate2(expression);
    if (expression === false) return;
    if (!expression || typeof expression === "boolean") {
      registerTransitionsFromHelper(el, modifiers, value);
    } else {
      registerTransitionsFromClassString(el, expression, value);
    }
  });
  function registerTransitionsFromClassString(el, classString, stage) {
    registerTransitionObject(el, setClasses, "");
    let directiveStorageMap = {
      "enter": (classes) => {
        el._x_transition.enter.during = classes;
      },
      "enter-start": (classes) => {
        el._x_transition.enter.start = classes;
      },
      "enter-end": (classes) => {
        el._x_transition.enter.end = classes;
      },
      "leave": (classes) => {
        el._x_transition.leave.during = classes;
      },
      "leave-start": (classes) => {
        el._x_transition.leave.start = classes;
      },
      "leave-end": (classes) => {
        el._x_transition.leave.end = classes;
      }
    };
    directiveStorageMap[stage](classString);
  }
  function registerTransitionsFromHelper(el, modifiers, stage) {
    registerTransitionObject(el, setStyles);
    let doesntSpecify = !modifiers.includes("in") && !modifiers.includes("out") && !stage;
    let transitioningIn = doesntSpecify || modifiers.includes("in") || ["enter"].includes(stage);
    let transitioningOut = doesntSpecify || modifiers.includes("out") || ["leave"].includes(stage);
    if (modifiers.includes("in") && !doesntSpecify) {
      modifiers = modifiers.filter((i, index) => index < modifiers.indexOf("out"));
    }
    if (modifiers.includes("out") && !doesntSpecify) {
      modifiers = modifiers.filter((i, index) => index > modifiers.indexOf("out"));
    }
    let wantsAll = !modifiers.includes("opacity") && !modifiers.includes("scale");
    let wantsOpacity = wantsAll || modifiers.includes("opacity");
    let wantsScale = wantsAll || modifiers.includes("scale");
    let opacityValue = wantsOpacity ? 0 : 1;
    let scaleValue = wantsScale ? modifierValue(modifiers, "scale", 95) / 100 : 1;
    let delay = modifierValue(modifiers, "delay", 0) / 1e3;
    let origin = modifierValue(modifiers, "origin", "center");
    let property = "opacity, transform";
    let durationIn = modifierValue(modifiers, "duration", 150) / 1e3;
    let durationOut = modifierValue(modifiers, "duration", 75) / 1e3;
    let easing = `cubic-bezier(0.4, 0.0, 0.2, 1)`;
    if (transitioningIn) {
      el._x_transition.enter.during = {
        transformOrigin: origin,
        transitionDelay: `${delay}s`,
        transitionProperty: property,
        transitionDuration: `${durationIn}s`,
        transitionTimingFunction: easing
      };
      el._x_transition.enter.start = {
        opacity: opacityValue,
        transform: `scale(${scaleValue})`
      };
      el._x_transition.enter.end = {
        opacity: 1,
        transform: `scale(1)`
      };
    }
    if (transitioningOut) {
      el._x_transition.leave.during = {
        transformOrigin: origin,
        transitionDelay: `${delay}s`,
        transitionProperty: property,
        transitionDuration: `${durationOut}s`,
        transitionTimingFunction: easing
      };
      el._x_transition.leave.start = {
        opacity: 1,
        transform: `scale(1)`
      };
      el._x_transition.leave.end = {
        opacity: opacityValue,
        transform: `scale(${scaleValue})`
      };
    }
  }
  function registerTransitionObject(el, setFunction, defaultValue = {}) {
    if (!el._x_transition) el._x_transition = {
      enter: { during: defaultValue, start: defaultValue, end: defaultValue },
      leave: { during: defaultValue, start: defaultValue, end: defaultValue },
      in(before = () => {
      }, after = () => {
      }) {
        transition(el, setFunction, {
          during: this.enter.during,
          start: this.enter.start,
          end: this.enter.end
        }, before, after);
      },
      out(before = () => {
      }, after = () => {
      }) {
        transition(el, setFunction, {
          during: this.leave.during,
          start: this.leave.start,
          end: this.leave.end
        }, before, after);
      }
    };
  }
  window.Element.prototype._x_toggleAndCascadeWithTransitions = function(el, value, show, hide) {
    const nextTick2 = document.visibilityState === "visible" ? requestAnimationFrame : setTimeout;
    let clickAwayCompatibleShow = () => nextTick2(show);
    if (value) {
      if (el._x_transition && (el._x_transition.enter || el._x_transition.leave)) {
        el._x_transition.enter && (Object.entries(el._x_transition.enter.during).length || Object.entries(el._x_transition.enter.start).length || Object.entries(el._x_transition.enter.end).length) ? el._x_transition.in(show) : clickAwayCompatibleShow();
      } else {
        el._x_transition ? el._x_transition.in(show) : clickAwayCompatibleShow();
      }
      return;
    }
    el._x_hidePromise = el._x_transition ? new Promise((resolve, reject) => {
      el._x_transition.out(() => {
      }, () => resolve(hide));
      el._x_transitioning && el._x_transitioning.beforeCancel(() => reject({ isFromCancelledTransition: true }));
    }) : Promise.resolve(hide);
    queueMicrotask(() => {
      let closest = closestHide(el);
      if (closest) {
        if (!closest._x_hideChildren) closest._x_hideChildren = [];
        closest._x_hideChildren.push(el);
      } else {
        nextTick2(() => {
          let hideAfterChildren = (el2) => {
            let carry = Promise.all([
              el2._x_hidePromise,
              ...(el2._x_hideChildren || []).map(hideAfterChildren)
            ]).then(([i]) => i?.());
            delete el2._x_hidePromise;
            delete el2._x_hideChildren;
            return carry;
          };
          hideAfterChildren(el).catch((e) => {
            if (!e.isFromCancelledTransition) throw e;
          });
        });
      }
    });
  };
  function closestHide(el) {
    let parent = el.parentNode;
    if (!parent) return;
    return parent._x_hidePromise ? parent : closestHide(parent);
  }
  function transition(el, setFunction, { during, start: start2, end } = {}, before = () => {
  }, after = () => {
  }) {
    if (el._x_transitioning) el._x_transitioning.cancel();
    if (Object.keys(during).length === 0 && Object.keys(start2).length === 0 && Object.keys(end).length === 0) {
      before();
      after();
      return;
    }
    let undoStart, undoDuring, undoEnd;
    performTransition(el, {
      start() {
        undoStart = setFunction(el, start2);
      },
      during() {
        undoDuring = setFunction(el, during);
      },
      before,
      end() {
        undoStart();
        undoEnd = setFunction(el, end);
      },
      after,
      cleanup() {
        undoDuring();
        undoEnd();
      }
    });
  }
  function performTransition(el, stages) {
    let interrupted, reachedBefore, reachedEnd;
    let finish = once(() => {
      mutateDom(() => {
        interrupted = true;
        if (!reachedBefore) stages.before();
        if (!reachedEnd) {
          stages.end();
          releaseNextTicks();
        }
        stages.after();
        if (el.isConnected) stages.cleanup();
        delete el._x_transitioning;
      });
    });
    el._x_transitioning = {
      beforeCancels: [],
      beforeCancel(callback) {
        this.beforeCancels.push(callback);
      },
      cancel: once(function() {
        while (this.beforeCancels.length) {
          this.beforeCancels.shift()();
        }
        ;
        finish();
      }),
      finish
    };
    mutateDom(() => {
      stages.start();
      stages.during();
    });
    holdNextTicks();
    requestAnimationFrame(() => {
      if (interrupted) return;
      let duration = Number(getComputedStyle(el).transitionDuration.replace(/,.*/, "").replace("s", "")) * 1e3;
      let delay = Number(getComputedStyle(el).transitionDelay.replace(/,.*/, "").replace("s", "")) * 1e3;
      if (duration === 0) duration = Number(getComputedStyle(el).animationDuration.replace("s", "")) * 1e3;
      mutateDom(() => {
        stages.before();
      });
      reachedBefore = true;
      requestAnimationFrame(() => {
        if (interrupted) return;
        mutateDom(() => {
          stages.end();
        });
        releaseNextTicks();
        setTimeout(el._x_transitioning.finish, duration + delay);
        reachedEnd = true;
      });
    });
  }
  function modifierValue(modifiers, key, fallback) {
    if (modifiers.indexOf(key) === -1) return fallback;
    const rawValue = modifiers[modifiers.indexOf(key) + 1];
    if (!rawValue) return fallback;
    if (key === "scale") {
      if (isNaN(rawValue)) return fallback;
    }
    if (key === "duration" || key === "delay") {
      let match = rawValue.match(/([0-9]+)ms/);
      if (match) return match[1];
    }
    if (key === "origin") {
      if (["top", "right", "left", "center", "bottom"].includes(modifiers[modifiers.indexOf(key) + 2])) {
        return [rawValue, modifiers[modifiers.indexOf(key) + 2]].join(" ");
      }
    }
    return rawValue;
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/clone.js
  var isCloning = false;
  function skipDuringClone(callback, fallback = () => {
  }) {
    return (...args) => isCloning ? fallback(...args) : callback(...args);
  }
  function onlyDuringClone(callback) {
    return (...args) => isCloning && callback(...args);
  }
  var interceptors = [];
  function interceptClone(callback) {
    interceptors.push(callback);
  }
  function cloneNode(from, to) {
    interceptors.forEach((i) => i(from, to));
    isCloning = true;
    dontRegisterReactiveSideEffects(() => {
      initTree(to, (el, callback) => {
        callback(el, () => {
        });
      });
    });
    isCloning = false;
  }
  var isCloningLegacy = false;
  function clone(oldEl, newEl) {
    if (!newEl._x_dataStack) newEl._x_dataStack = oldEl._x_dataStack;
    isCloning = true;
    isCloningLegacy = true;
    dontRegisterReactiveSideEffects(() => {
      cloneTree(newEl);
    });
    isCloning = false;
    isCloningLegacy = false;
  }
  function cloneTree(el) {
    let hasRunThroughFirstEl = false;
    let shallowWalker = (el2, callback) => {
      walk(el2, (el3, skip) => {
        if (hasRunThroughFirstEl && isRoot(el3)) return skip();
        hasRunThroughFirstEl = true;
        callback(el3, skip);
      });
    };
    initTree(el, shallowWalker);
  }
  function dontRegisterReactiveSideEffects(callback) {
    let cache = effect;
    overrideEffect((callback2, el) => {
      let storedEffect = cache(callback2);
      release(storedEffect);
      return () => {
      };
    });
    callback();
    overrideEffect(cache);
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/utils/bind.js
  function bind(el, name, value, modifiers = []) {
    if (!el._x_bindings) el._x_bindings = reactive({});
    el._x_bindings[name] = value;
    name = modifiers.includes("camel") ? camelCase(name) : name;
    switch (name) {
      case "value":
        bindInputValue(el, value);
        break;
      case "style":
        bindStyles(el, value);
        break;
      case "class":
        bindClasses(el, value);
        break;
      // 'selected' and 'checked' are special attributes that aren't necessarily
      // synced with their corresponding properties when updated, so both the
      // attribute and property need to be updated when bound.
      case "selected":
      case "checked":
        bindAttributeAndProperty(el, name, value);
        break;
      default:
        bindAttribute(el, name, value);
        break;
    }
  }
  function bindInputValue(el, value) {
    if (isRadio(el)) {
      if (el.attributes.value === void 0) {
        el.value = value;
      }
    } else if (isCheckbox(el)) {
      if (Number.isInteger(value)) {
        el.value = value;
      } else if (!Array.isArray(value) && typeof value !== "boolean" && ![null, void 0].includes(value)) {
        el.value = String(value);
      } else {
        if (Array.isArray(value)) {
          el.checked = value.some((val) => checkedAttrLooseCompare(val, el.value));
        } else {
          el.checked = !!value;
        }
      }
    } else if (el.tagName === "SELECT") {
      updateSelect(el, value);
    } else {
      if (el.value === value) return;
      el.value = value === void 0 ? "" : value;
    }
  }
  function bindClasses(el, value) {
    if (el._x_undoAddedClasses) el._x_undoAddedClasses();
    el._x_undoAddedClasses = setClasses(el, value);
  }
  function bindStyles(el, value) {
    if (el._x_undoAddedStyles) el._x_undoAddedStyles();
    el._x_undoAddedStyles = setStyles(el, value);
  }
  function bindAttributeAndProperty(el, name, value) {
    bindAttribute(el, name, value);
    setPropertyIfChanged(el, name, value);
  }
  function bindAttribute(el, name, value) {
    if ([null, void 0, false].includes(value) && attributeShouldntBePreservedIfFalsy(name)) {
      el.removeAttribute(name);
    } else {
      if (isBooleanAttr(name)) value = name;
      setIfChanged(el, name, value);
    }
  }
  function setIfChanged(el, attrName, value) {
    if (el.getAttribute(attrName) != value) {
      el.setAttribute(attrName, value);
    }
  }
  function setPropertyIfChanged(el, propName, value) {
    if (el[propName] !== value) {
      el[propName] = value;
    }
  }
  function updateSelect(el, value) {
    const arrayWrappedValue = [].concat(value).map((value2) => {
      return value2 + "";
    });
    Array.from(el.options).forEach((option) => {
      option.selected = arrayWrappedValue.includes(option.value);
    });
  }
  function camelCase(subject) {
    return subject.toLowerCase().replace(/-(\w)/g, (match, char) => char.toUpperCase());
  }
  function checkedAttrLooseCompare(valueA, valueB) {
    return valueA == valueB;
  }
  function safeParseBoolean(rawValue) {
    if ([1, "1", "true", "on", "yes", true].includes(rawValue)) {
      return true;
    }
    if ([0, "0", "false", "off", "no", false].includes(rawValue)) {
      return false;
    }
    return rawValue ? Boolean(rawValue) : null;
  }
  var booleanAttributes = /* @__PURE__ */ new Set([
    "allowfullscreen",
    "async",
    "autofocus",
    "autoplay",
    "checked",
    "controls",
    "default",
    "defer",
    "disabled",
    "formnovalidate",
    "inert",
    "ismap",
    "itemscope",
    "loop",
    "multiple",
    "muted",
    "nomodule",
    "novalidate",
    "open",
    "playsinline",
    "readonly",
    "required",
    "reversed",
    "selected",
    "shadowrootclonable",
    "shadowrootdelegatesfocus",
    "shadowrootserializable"
  ]);
  function isBooleanAttr(attrName) {
    return booleanAttributes.has(attrName);
  }
  function attributeShouldntBePreservedIfFalsy(name) {
    return !["aria-pressed", "aria-checked", "aria-expanded", "aria-selected"].includes(name);
  }
  function getBinding(el, name, fallback) {
    if (el._x_bindings && el._x_bindings[name] !== void 0) return el._x_bindings[name];
    return getAttributeBinding(el, name, fallback);
  }
  function extractProp(el, name, fallback, extract = true) {
    if (el._x_bindings && el._x_bindings[name] !== void 0) return el._x_bindings[name];
    if (el._x_inlineBindings && el._x_inlineBindings[name] !== void 0) {
      let binding = el._x_inlineBindings[name];
      binding.extract = extract;
      return dontAutoEvaluateFunctions(() => {
        return evaluate(el, binding.expression);
      });
    }
    return getAttributeBinding(el, name, fallback);
  }
  function getAttributeBinding(el, name, fallback) {
    let attr = el.getAttribute(name);
    if (attr === null) return typeof fallback === "function" ? fallback() : fallback;
    if (attr === "") return true;
    if (isBooleanAttr(name)) {
      return !![name, "true"].includes(attr);
    }
    return attr;
  }
  function isCheckbox(el) {
    return el.type === "checkbox" || el.localName === "ui-checkbox" || el.localName === "ui-switch";
  }
  function isRadio(el) {
    return el.type === "radio" || el.localName === "ui-radio";
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/utils/debounce.js
  function debounce(func, wait) {
    let timeout;
    return function() {
      const context = this, args = arguments;
      const later = function() {
        timeout = null;
        func.apply(context, args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/utils/throttle.js
  function throttle(func, limit) {
    let inThrottle;
    return function() {
      let context = this, args = arguments;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/entangle.js
  function entangle({ get: outerGet, set: outerSet }, { get: innerGet, set: innerSet }) {
    let firstRun = true;
    let outerHash;
    let innerHash;
    let reference = effect(() => {
      let outer = outerGet();
      let inner = innerGet();
      if (firstRun) {
        innerSet(cloneIfObject(outer));
        firstRun = false;
      } else {
        let outerHashLatest = JSON.stringify(outer);
        let innerHashLatest = JSON.stringify(inner);
        if (outerHashLatest !== outerHash) {
          innerSet(cloneIfObject(outer));
        } else if (outerHashLatest !== innerHashLatest) {
          outerSet(cloneIfObject(inner));
        } else {
        }
      }
      outerHash = JSON.stringify(outerGet());
      innerHash = JSON.stringify(innerGet());
    });
    return () => {
      release(reference);
    };
  }
  function cloneIfObject(value) {
    return typeof value === "object" ? JSON.parse(JSON.stringify(value)) : value;
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/plugin.js
  function plugin(callback) {
    let callbacks = Array.isArray(callback) ? callback : [callback];
    callbacks.forEach((i) => i(alpine_default));
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/store.js
  var stores = {};
  var isReactive = false;
  function store(name, value) {
    if (!isReactive) {
      stores = reactive(stores);
      isReactive = true;
    }
    if (value === void 0) {
      return stores[name];
    }
    stores[name] = value;
    initInterceptors(stores[name]);
    if (typeof value === "object" && value !== null && value.hasOwnProperty("init") && typeof value.init === "function") {
      stores[name].init();
    }
  }
  function getStores() {
    return stores;
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/binds.js
  var binds = {};
  function bind2(name, bindings) {
    let getBindings = typeof bindings !== "function" ? () => bindings : bindings;
    if (name instanceof Element) {
      return applyBindingsObject(name, getBindings());
    } else {
      binds[name] = getBindings;
    }
    return () => {
    };
  }
  function injectBindingProviders(obj) {
    Object.entries(binds).forEach(([name, callback]) => {
      Object.defineProperty(obj, name, {
        get() {
          return (...args) => {
            return callback(...args);
          };
        }
      });
    });
    return obj;
  }
  function applyBindingsObject(el, obj, original) {
    let cleanupRunners = [];
    while (cleanupRunners.length) cleanupRunners.pop()();
    let attributes = Object.entries(obj).map(([name, value]) => ({ name, value }));
    let staticAttributes = attributesOnly(attributes);
    attributes = attributes.map((attribute) => {
      if (staticAttributes.find((attr) => attr.name === attribute.name)) {
        return {
          name: `x-bind:${attribute.name}`,
          value: `"${attribute.value}"`
        };
      }
      return attribute;
    });
    directives(el, attributes, original).map((handle) => {
      cleanupRunners.push(handle.runCleanups);
      handle();
    });
    return () => {
      while (cleanupRunners.length) cleanupRunners.pop()();
    };
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/datas.js
  var datas = {};
  function data(name, callback) {
    datas[name] = callback;
  }
  function injectDataProviders(obj, context) {
    Object.entries(datas).forEach(([name, callback]) => {
      Object.defineProperty(obj, name, {
        get() {
          return (...args) => {
            return callback.bind(context)(...args);
          };
        },
        enumerable: false
      });
    });
    return obj;
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/alpine.js
  var Alpine = {
    get reactive() {
      return reactive;
    },
    get release() {
      return release;
    },
    get effect() {
      return effect;
    },
    get raw() {
      return raw;
    },
    get transaction() {
      return transaction;
    },
    version: "3.15.12",
    flushAndStopDeferringMutations,
    dontAutoEvaluateFunctions,
    disableEffectScheduling,
    startObservingMutations,
    stopObservingMutations,
    setReactivityEngine,
    onAttributeRemoved,
    onAttributesAdded,
    closestDataStack,
    skipDuringClone,
    onlyDuringClone,
    addRootSelector,
    addInitSelector,
    setErrorHandler,
    interceptClone,
    addScopeToNode,
    deferMutations,
    mapAttributes,
    evaluateLater,
    interceptInit,
    initInterceptors,
    injectMagics,
    setEvaluator,
    setRawEvaluator,
    mergeProxies,
    extractProp,
    findClosest,
    onElRemoved,
    closestRoot,
    destroyTree,
    interceptor,
    // INTERNAL: not public API and is subject to change without major release.
    transition,
    // INTERNAL
    setStyles,
    // INTERNAL
    mutateDom,
    directive,
    entangle,
    throttle,
    debounce,
    evaluate,
    evaluateRaw,
    initTree,
    nextTick,
    prefixed: prefix,
    prefix: setPrefix,
    plugin,
    magic,
    store,
    start,
    clone,
    // INTERNAL
    cloneNode,
    // INTERNAL
    bound: getBinding,
    $data: scope,
    watch,
    walk,
    data,
    bind: bind2
  };
  var alpine_default = Alpine;

  // ../../../node_modules/.pnpm/@vue+shared@3.1.5/node_modules/@vue/shared/dist/shared.esm-bundler.js
  function makeMap(str, expectsLowerCase) {
    const map = /* @__PURE__ */ Object.create(null);
    const list = str.split(",");
    for (let i = 0; i < list.length; i++) {
      map[list[i]] = true;
    }
    return expectsLowerCase ? (val) => !!map[val.toLowerCase()] : (val) => !!map[val];
  }
  var specialBooleanAttrs = `itemscope,allowfullscreen,formnovalidate,ismap,nomodule,novalidate,readonly`;
  var isBooleanAttr2 = /* @__PURE__ */ makeMap(specialBooleanAttrs + `,async,autofocus,autoplay,controls,default,defer,disabled,hidden,loop,open,required,reversed,scoped,seamless,checked,muted,multiple,selected`);
  var EMPTY_OBJ = true ? Object.freeze({}) : {};
  var EMPTY_ARR = true ? Object.freeze([]) : [];
  var hasOwnProperty = Object.prototype.hasOwnProperty;
  var hasOwn = (val, key) => hasOwnProperty.call(val, key);
  var isArray = Array.isArray;
  var isMap = (val) => toTypeString(val) === "[object Map]";
  var isString = (val) => typeof val === "string";
  var isSymbol = (val) => typeof val === "symbol";
  var isObject = (val) => val !== null && typeof val === "object";
  var objectToString = Object.prototype.toString;
  var toTypeString = (value) => objectToString.call(value);
  var toRawType = (value) => {
    return toTypeString(value).slice(8, -1);
  };
  var isIntegerKey = (key) => isString(key) && key !== "NaN" && key[0] !== "-" && "" + parseInt(key, 10) === key;
  var cacheStringFunction = (fn) => {
    const cache = /* @__PURE__ */ Object.create(null);
    return ((str) => {
      const hit = cache[str];
      return hit || (cache[str] = fn(str));
    });
  };
  var camelizeRE = /-(\w)/g;
  var camelize = cacheStringFunction((str) => {
    return str.replace(camelizeRE, (_, c) => c ? c.toUpperCase() : "");
  });
  var hyphenateRE = /\B([A-Z])/g;
  var hyphenate = cacheStringFunction((str) => str.replace(hyphenateRE, "-$1").toLowerCase());
  var capitalize = cacheStringFunction((str) => str.charAt(0).toUpperCase() + str.slice(1));
  var toHandlerKey = cacheStringFunction((str) => str ? `on${capitalize(str)}` : ``);
  var hasChanged = (value, oldValue) => value !== oldValue && (value === value || oldValue === oldValue);

  // ../../../node_modules/.pnpm/@vue+reactivity@3.1.5/node_modules/@vue/reactivity/dist/reactivity.esm-bundler.js
  var targetMap = /* @__PURE__ */ new WeakMap();
  var effectStack = [];
  var activeEffect;
  var ITERATE_KEY = /* @__PURE__ */ Symbol(true ? "iterate" : "");
  var MAP_KEY_ITERATE_KEY = /* @__PURE__ */ Symbol(true ? "Map key iterate" : "");
  function isEffect(fn) {
    return fn && fn._isEffect === true;
  }
  function effect2(fn, options = EMPTY_OBJ) {
    if (isEffect(fn)) {
      fn = fn.raw;
    }
    const effect3 = createReactiveEffect(fn, options);
    if (!options.lazy) {
      effect3();
    }
    return effect3;
  }
  function stop(effect3) {
    if (effect3.active) {
      cleanup(effect3);
      if (effect3.options.onStop) {
        effect3.options.onStop();
      }
      effect3.active = false;
    }
  }
  var uid = 0;
  function createReactiveEffect(fn, options) {
    const effect3 = function reactiveEffect() {
      if (!effect3.active) {
        return fn();
      }
      if (!effectStack.includes(effect3)) {
        cleanup(effect3);
        try {
          enableTracking();
          effectStack.push(effect3);
          activeEffect = effect3;
          return fn();
        } finally {
          effectStack.pop();
          resetTracking();
          activeEffect = effectStack[effectStack.length - 1];
        }
      }
    };
    effect3.id = uid++;
    effect3.allowRecurse = !!options.allowRecurse;
    effect3._isEffect = true;
    effect3.active = true;
    effect3.raw = fn;
    effect3.deps = [];
    effect3.options = options;
    return effect3;
  }
  function cleanup(effect3) {
    const { deps } = effect3;
    if (deps.length) {
      for (let i = 0; i < deps.length; i++) {
        deps[i].delete(effect3);
      }
      deps.length = 0;
    }
  }
  var shouldTrack = true;
  var trackStack = [];
  function pauseTracking() {
    trackStack.push(shouldTrack);
    shouldTrack = false;
  }
  function enableTracking() {
    trackStack.push(shouldTrack);
    shouldTrack = true;
  }
  function resetTracking() {
    const last = trackStack.pop();
    shouldTrack = last === void 0 ? true : last;
  }
  function track(target, type, key) {
    if (!shouldTrack || activeEffect === void 0) {
      return;
    }
    let depsMap = targetMap.get(target);
    if (!depsMap) {
      targetMap.set(target, depsMap = /* @__PURE__ */ new Map());
    }
    let dep = depsMap.get(key);
    if (!dep) {
      depsMap.set(key, dep = /* @__PURE__ */ new Set());
    }
    if (!dep.has(activeEffect)) {
      dep.add(activeEffect);
      activeEffect.deps.push(dep);
      if (activeEffect.options.onTrack) {
        activeEffect.options.onTrack({
          effect: activeEffect,
          target,
          type,
          key
        });
      }
    }
  }
  function trigger(target, type, key, newValue, oldValue, oldTarget) {
    const depsMap = targetMap.get(target);
    if (!depsMap) {
      return;
    }
    const effects = /* @__PURE__ */ new Set();
    const add2 = (effectsToAdd) => {
      if (effectsToAdd) {
        effectsToAdd.forEach((effect3) => {
          if (effect3 !== activeEffect || effect3.allowRecurse) {
            effects.add(effect3);
          }
        });
      }
    };
    if (type === "clear") {
      depsMap.forEach(add2);
    } else if (key === "length" && isArray(target)) {
      depsMap.forEach((dep, key2) => {
        if (key2 === "length" || key2 >= newValue) {
          add2(dep);
        }
      });
    } else {
      if (key !== void 0) {
        add2(depsMap.get(key));
      }
      switch (type) {
        case "add":
          if (!isArray(target)) {
            add2(depsMap.get(ITERATE_KEY));
            if (isMap(target)) {
              add2(depsMap.get(MAP_KEY_ITERATE_KEY));
            }
          } else if (isIntegerKey(key)) {
            add2(depsMap.get("length"));
          }
          break;
        case "delete":
          if (!isArray(target)) {
            add2(depsMap.get(ITERATE_KEY));
            if (isMap(target)) {
              add2(depsMap.get(MAP_KEY_ITERATE_KEY));
            }
          }
          break;
        case "set":
          if (isMap(target)) {
            add2(depsMap.get(ITERATE_KEY));
          }
          break;
      }
    }
    const run = (effect3) => {
      if (effect3.options.onTrigger) {
        effect3.options.onTrigger({
          effect: effect3,
          target,
          key,
          type,
          newValue,
          oldValue,
          oldTarget
        });
      }
      if (effect3.options.scheduler) {
        effect3.options.scheduler(effect3);
      } else {
        effect3();
      }
    };
    effects.forEach(run);
  }
  var isNonTrackableKeys = /* @__PURE__ */ makeMap(`__proto__,__v_isRef,__isVue`);
  var builtInSymbols = new Set(Object.getOwnPropertyNames(Symbol).map((key) => Symbol[key]).filter(isSymbol));
  var get2 = /* @__PURE__ */ createGetter();
  var readonlyGet = /* @__PURE__ */ createGetter(true);
  var arrayInstrumentations = /* @__PURE__ */ createArrayInstrumentations();
  function createArrayInstrumentations() {
    const instrumentations = {};
    ["includes", "indexOf", "lastIndexOf"].forEach((key) => {
      instrumentations[key] = function(...args) {
        const arr = toRaw(this);
        for (let i = 0, l = this.length; i < l; i++) {
          track(arr, "get", i + "");
        }
        const res = arr[key](...args);
        if (res === -1 || res === false) {
          return arr[key](...args.map(toRaw));
        } else {
          return res;
        }
      };
    });
    ["push", "pop", "shift", "unshift", "splice"].forEach((key) => {
      instrumentations[key] = function(...args) {
        pauseTracking();
        const res = toRaw(this)[key].apply(this, args);
        resetTracking();
        return res;
      };
    });
    return instrumentations;
  }
  function createGetter(isReadonly = false, shallow = false) {
    return function get3(target, key, receiver) {
      if (key === "__v_isReactive") {
        return !isReadonly;
      } else if (key === "__v_isReadonly") {
        return isReadonly;
      } else if (key === "__v_raw" && receiver === (isReadonly ? shallow ? shallowReadonlyMap : readonlyMap : shallow ? shallowReactiveMap : reactiveMap).get(target)) {
        return target;
      }
      const targetIsArray = isArray(target);
      if (!isReadonly && targetIsArray && hasOwn(arrayInstrumentations, key)) {
        return Reflect.get(arrayInstrumentations, key, receiver);
      }
      const res = Reflect.get(target, key, receiver);
      if (isSymbol(key) ? builtInSymbols.has(key) : isNonTrackableKeys(key)) {
        return res;
      }
      if (!isReadonly) {
        track(target, "get", key);
      }
      if (shallow) {
        return res;
      }
      if (isRef(res)) {
        const shouldUnwrap = !targetIsArray || !isIntegerKey(key);
        return shouldUnwrap ? res.value : res;
      }
      if (isObject(res)) {
        return isReadonly ? readonly(res) : reactive2(res);
      }
      return res;
    };
  }
  var set2 = /* @__PURE__ */ createSetter();
  function createSetter(shallow = false) {
    return function set3(target, key, value, receiver) {
      let oldValue = target[key];
      if (!shallow) {
        value = toRaw(value);
        oldValue = toRaw(oldValue);
        if (!isArray(target) && isRef(oldValue) && !isRef(value)) {
          oldValue.value = value;
          return true;
        }
      }
      const hadKey = isArray(target) && isIntegerKey(key) ? Number(key) < target.length : hasOwn(target, key);
      const result = Reflect.set(target, key, value, receiver);
      if (target === toRaw(receiver)) {
        if (!hadKey) {
          trigger(target, "add", key, value);
        } else if (hasChanged(value, oldValue)) {
          trigger(target, "set", key, value, oldValue);
        }
      }
      return result;
    };
  }
  function deleteProperty(target, key) {
    const hadKey = hasOwn(target, key);
    const oldValue = target[key];
    const result = Reflect.deleteProperty(target, key);
    if (result && hadKey) {
      trigger(target, "delete", key, void 0, oldValue);
    }
    return result;
  }
  function has(target, key) {
    const result = Reflect.has(target, key);
    if (!isSymbol(key) || !builtInSymbols.has(key)) {
      track(target, "has", key);
    }
    return result;
  }
  function ownKeys(target) {
    track(target, "iterate", isArray(target) ? "length" : ITERATE_KEY);
    return Reflect.ownKeys(target);
  }
  var mutableHandlers = {
    get: get2,
    set: set2,
    deleteProperty,
    has,
    ownKeys
  };
  var readonlyHandlers = {
    get: readonlyGet,
    set(target, key) {
      if (true) {
        console.warn(`Set operation on key "${String(key)}" failed: target is readonly.`, target);
      }
      return true;
    },
    deleteProperty(target, key) {
      if (true) {
        console.warn(`Delete operation on key "${String(key)}" failed: target is readonly.`, target);
      }
      return true;
    }
  };
  var toReactive = (value) => isObject(value) ? reactive2(value) : value;
  var toReadonly = (value) => isObject(value) ? readonly(value) : value;
  var toShallow = (value) => value;
  var getProto = (v) => Reflect.getPrototypeOf(v);
  function get$1(target, key, isReadonly = false, isShallow = false) {
    target = target[
      "__v_raw"
      /* RAW */
    ];
    const rawTarget = toRaw(target);
    const rawKey = toRaw(key);
    if (key !== rawKey) {
      !isReadonly && track(rawTarget, "get", key);
    }
    !isReadonly && track(rawTarget, "get", rawKey);
    const { has: has2 } = getProto(rawTarget);
    const wrap = isShallow ? toShallow : isReadonly ? toReadonly : toReactive;
    if (has2.call(rawTarget, key)) {
      return wrap(target.get(key));
    } else if (has2.call(rawTarget, rawKey)) {
      return wrap(target.get(rawKey));
    } else if (target !== rawTarget) {
      target.get(key);
    }
  }
  function has$1(key, isReadonly = false) {
    const target = this[
      "__v_raw"
      /* RAW */
    ];
    const rawTarget = toRaw(target);
    const rawKey = toRaw(key);
    if (key !== rawKey) {
      !isReadonly && track(rawTarget, "has", key);
    }
    !isReadonly && track(rawTarget, "has", rawKey);
    return key === rawKey ? target.has(key) : target.has(key) || target.has(rawKey);
  }
  function size(target, isReadonly = false) {
    target = target[
      "__v_raw"
      /* RAW */
    ];
    !isReadonly && track(toRaw(target), "iterate", ITERATE_KEY);
    return Reflect.get(target, "size", target);
  }
  function add(value) {
    value = toRaw(value);
    const target = toRaw(this);
    const proto = getProto(target);
    const hadKey = proto.has.call(target, value);
    if (!hadKey) {
      target.add(value);
      trigger(target, "add", value, value);
    }
    return this;
  }
  function set$1(key, value) {
    value = toRaw(value);
    const target = toRaw(this);
    const { has: has2, get: get3 } = getProto(target);
    let hadKey = has2.call(target, key);
    if (!hadKey) {
      key = toRaw(key);
      hadKey = has2.call(target, key);
    } else if (true) {
      checkIdentityKeys(target, has2, key);
    }
    const oldValue = get3.call(target, key);
    target.set(key, value);
    if (!hadKey) {
      trigger(target, "add", key, value);
    } else if (hasChanged(value, oldValue)) {
      trigger(target, "set", key, value, oldValue);
    }
    return this;
  }
  function deleteEntry(key) {
    const target = toRaw(this);
    const { has: has2, get: get3 } = getProto(target);
    let hadKey = has2.call(target, key);
    if (!hadKey) {
      key = toRaw(key);
      hadKey = has2.call(target, key);
    } else if (true) {
      checkIdentityKeys(target, has2, key);
    }
    const oldValue = get3 ? get3.call(target, key) : void 0;
    const result = target.delete(key);
    if (hadKey) {
      trigger(target, "delete", key, void 0, oldValue);
    }
    return result;
  }
  function clear() {
    const target = toRaw(this);
    const hadItems = target.size !== 0;
    const oldTarget = true ? isMap(target) ? new Map(target) : new Set(target) : void 0;
    const result = target.clear();
    if (hadItems) {
      trigger(target, "clear", void 0, void 0, oldTarget);
    }
    return result;
  }
  function createForEach(isReadonly, isShallow) {
    return function forEach(callback, thisArg) {
      const observed = this;
      const target = observed[
        "__v_raw"
        /* RAW */
      ];
      const rawTarget = toRaw(target);
      const wrap = isShallow ? toShallow : isReadonly ? toReadonly : toReactive;
      !isReadonly && track(rawTarget, "iterate", ITERATE_KEY);
      return target.forEach((value, key) => {
        return callback.call(thisArg, wrap(value), wrap(key), observed);
      });
    };
  }
  function createIterableMethod(method, isReadonly, isShallow) {
    return function(...args) {
      const target = this[
        "__v_raw"
        /* RAW */
      ];
      const rawTarget = toRaw(target);
      const targetIsMap = isMap(rawTarget);
      const isPair = method === "entries" || method === Symbol.iterator && targetIsMap;
      const isKeyOnly = method === "keys" && targetIsMap;
      const innerIterator = target[method](...args);
      const wrap = isShallow ? toShallow : isReadonly ? toReadonly : toReactive;
      !isReadonly && track(rawTarget, "iterate", isKeyOnly ? MAP_KEY_ITERATE_KEY : ITERATE_KEY);
      return {
        // iterator protocol
        next() {
          const { value, done } = innerIterator.next();
          return done ? { value, done } : {
            value: isPair ? [wrap(value[0]), wrap(value[1])] : wrap(value),
            done
          };
        },
        // iterable protocol
        [Symbol.iterator]() {
          return this;
        }
      };
    };
  }
  function createReadonlyMethod(type) {
    return function(...args) {
      if (true) {
        const key = args[0] ? `on key "${args[0]}" ` : ``;
        console.warn(`${capitalize(type)} operation ${key}failed: target is readonly.`, toRaw(this));
      }
      return type === "delete" ? false : this;
    };
  }
  function createInstrumentations() {
    const mutableInstrumentations2 = {
      get(key) {
        return get$1(this, key);
      },
      get size() {
        return size(this);
      },
      has: has$1,
      add,
      set: set$1,
      delete: deleteEntry,
      clear,
      forEach: createForEach(false, false)
    };
    const shallowInstrumentations2 = {
      get(key) {
        return get$1(this, key, false, true);
      },
      get size() {
        return size(this);
      },
      has: has$1,
      add,
      set: set$1,
      delete: deleteEntry,
      clear,
      forEach: createForEach(false, true)
    };
    const readonlyInstrumentations2 = {
      get(key) {
        return get$1(this, key, true);
      },
      get size() {
        return size(this, true);
      },
      has(key) {
        return has$1.call(this, key, true);
      },
      add: createReadonlyMethod(
        "add"
        /* ADD */
      ),
      set: createReadonlyMethod(
        "set"
        /* SET */
      ),
      delete: createReadonlyMethod(
        "delete"
        /* DELETE */
      ),
      clear: createReadonlyMethod(
        "clear"
        /* CLEAR */
      ),
      forEach: createForEach(true, false)
    };
    const shallowReadonlyInstrumentations2 = {
      get(key) {
        return get$1(this, key, true, true);
      },
      get size() {
        return size(this, true);
      },
      has(key) {
        return has$1.call(this, key, true);
      },
      add: createReadonlyMethod(
        "add"
        /* ADD */
      ),
      set: createReadonlyMethod(
        "set"
        /* SET */
      ),
      delete: createReadonlyMethod(
        "delete"
        /* DELETE */
      ),
      clear: createReadonlyMethod(
        "clear"
        /* CLEAR */
      ),
      forEach: createForEach(true, true)
    };
    const iteratorMethods = ["keys", "values", "entries", Symbol.iterator];
    iteratorMethods.forEach((method) => {
      mutableInstrumentations2[method] = createIterableMethod(method, false, false);
      readonlyInstrumentations2[method] = createIterableMethod(method, true, false);
      shallowInstrumentations2[method] = createIterableMethod(method, false, true);
      shallowReadonlyInstrumentations2[method] = createIterableMethod(method, true, true);
    });
    return [
      mutableInstrumentations2,
      readonlyInstrumentations2,
      shallowInstrumentations2,
      shallowReadonlyInstrumentations2
    ];
  }
  var [mutableInstrumentations, readonlyInstrumentations, shallowInstrumentations, shallowReadonlyInstrumentations] = /* @__PURE__ */ createInstrumentations();
  function createInstrumentationGetter(isReadonly, shallow) {
    const instrumentations = shallow ? isReadonly ? shallowReadonlyInstrumentations : shallowInstrumentations : isReadonly ? readonlyInstrumentations : mutableInstrumentations;
    return (target, key, receiver) => {
      if (key === "__v_isReactive") {
        return !isReadonly;
      } else if (key === "__v_isReadonly") {
        return isReadonly;
      } else if (key === "__v_raw") {
        return target;
      }
      return Reflect.get(hasOwn(instrumentations, key) && key in target ? instrumentations : target, key, receiver);
    };
  }
  var mutableCollectionHandlers = {
    get: /* @__PURE__ */ createInstrumentationGetter(false, false)
  };
  var readonlyCollectionHandlers = {
    get: /* @__PURE__ */ createInstrumentationGetter(true, false)
  };
  function checkIdentityKeys(target, has2, key) {
    const rawKey = toRaw(key);
    if (rawKey !== key && has2.call(target, rawKey)) {
      const type = toRawType(target);
      console.warn(`Reactive ${type} contains both the raw and reactive versions of the same object${type === `Map` ? ` as keys` : ``}, which can lead to inconsistencies. Avoid differentiating between the raw and reactive versions of an object and only use the reactive version if possible.`);
    }
  }
  var reactiveMap = /* @__PURE__ */ new WeakMap();
  var shallowReactiveMap = /* @__PURE__ */ new WeakMap();
  var readonlyMap = /* @__PURE__ */ new WeakMap();
  var shallowReadonlyMap = /* @__PURE__ */ new WeakMap();
  function targetTypeMap(rawType) {
    switch (rawType) {
      case "Object":
      case "Array":
        return 1;
      case "Map":
      case "Set":
      case "WeakMap":
      case "WeakSet":
        return 2;
      default:
        return 0;
    }
  }
  function getTargetType(value) {
    return value[
      "__v_skip"
      /* SKIP */
    ] || !Object.isExtensible(value) ? 0 : targetTypeMap(toRawType(value));
  }
  function reactive2(target) {
    if (target && target[
      "__v_isReadonly"
      /* IS_READONLY */
    ]) {
      return target;
    }
    return createReactiveObject(target, false, mutableHandlers, mutableCollectionHandlers, reactiveMap);
  }
  function readonly(target) {
    return createReactiveObject(target, true, readonlyHandlers, readonlyCollectionHandlers, readonlyMap);
  }
  function createReactiveObject(target, isReadonly, baseHandlers, collectionHandlers, proxyMap) {
    if (!isObject(target)) {
      if (true) {
        console.warn(`value cannot be made reactive: ${String(target)}`);
      }
      return target;
    }
    if (target[
      "__v_raw"
      /* RAW */
    ] && !(isReadonly && target[
      "__v_isReactive"
      /* IS_REACTIVE */
    ])) {
      return target;
    }
    const existingProxy = proxyMap.get(target);
    if (existingProxy) {
      return existingProxy;
    }
    const targetType = getTargetType(target);
    if (targetType === 0) {
      return target;
    }
    const proxy = new Proxy(target, targetType === 2 ? collectionHandlers : baseHandlers);
    proxyMap.set(target, proxy);
    return proxy;
  }
  function toRaw(observed) {
    return observed && toRaw(observed[
      "__v_raw"
      /* RAW */
    ]) || observed;
  }
  function isRef(r) {
    return Boolean(r && r.__v_isRef === true);
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/magics/$nextTick.js
  magic("nextTick", () => nextTick);

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/magics/$dispatch.js
  magic("dispatch", (el) => dispatch.bind(dispatch, el));

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/magics/$watch.js
  magic("watch", (el, { evaluateLater: evaluateLater2, cleanup: cleanup2 }) => (key, callback) => {
    let evaluate2 = evaluateLater2(key);
    let getter = () => {
      let value;
      evaluate2((i) => value = i);
      return value;
    };
    let unwatch = watch(getter, callback);
    cleanup2(unwatch);
  });

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/magics/$store.js
  magic("store", getStores);

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/magics/$data.js
  magic("data", (el) => scope(el));

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/magics/$root.js
  magic("root", (el) => closestRoot(el));

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/magics/$refs.js
  magic("refs", (el) => {
    if (el._x_refs_proxy) return el._x_refs_proxy;
    el._x_refs_proxy = mergeProxies(getArrayOfRefObject(el));
    return el._x_refs_proxy;
  });
  function getArrayOfRefObject(el) {
    let refObjects = [];
    findClosest(el, (i) => {
      if (i._x_refs) refObjects.push(i._x_refs);
    });
    return refObjects;
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/ids.js
  var globalIdMemo = {};
  function findAndIncrementId(name) {
    if (!globalIdMemo[name]) globalIdMemo[name] = 0;
    return ++globalIdMemo[name];
  }
  function closestIdRoot(el, name) {
    return findClosest(el, (element) => {
      if (element._x_ids && element._x_ids[name]) return true;
    });
  }
  function setIdRoot(el, name) {
    if (!el._x_ids) el._x_ids = {};
    if (!el._x_ids[name]) el._x_ids[name] = findAndIncrementId(name);
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/magics/$id.js
  magic("id", (el, { cleanup: cleanup2 }) => (name, key = null) => {
    let cacheKey = `${name}${key ? `-${key}` : ""}`;
    return cacheIdByNameOnElement(el, cacheKey, cleanup2, () => {
      let root = closestIdRoot(el, name);
      let id = root ? root._x_ids[name] : findAndIncrementId(name);
      return key ? `${name}-${id}-${key}` : `${name}-${id}`;
    });
  });
  interceptClone((from, to) => {
    if (from._x_id) {
      to._x_id = from._x_id;
    }
  });
  function cacheIdByNameOnElement(el, cacheKey, cleanup2, callback) {
    if (!el._x_id) el._x_id = {};
    if (el._x_id[cacheKey]) return el._x_id[cacheKey];
    let output = callback();
    el._x_id[cacheKey] = output;
    cleanup2(() => {
      delete el._x_id[cacheKey];
    });
    return output;
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/magics/$el.js
  magic("el", (el) => el);

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/magics/index.js
  warnMissingPluginMagic("Focus", "focus", "focus");
  warnMissingPluginMagic("Persist", "persist", "persist");
  function warnMissingPluginMagic(name, magicName, slug) {
    magic(magicName, (el) => warn(`You can't use [$${magicName}] without first installing the "${name}" plugin here: https://alpinejs.dev/plugins/${slug}`, el));
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/directives/x-modelable.js
  directive("modelable", (el, { expression }, { effect: effect3, evaluateLater: evaluateLater2, cleanup: cleanup2 }) => {
    let func = evaluateLater2(expression);
    let innerGet = () => {
      let result;
      func((i) => result = i);
      return result;
    };
    let evaluateInnerSet = evaluateLater2(`${expression} = __placeholder`);
    let innerSet = (val) => evaluateInnerSet(() => {
    }, { scope: { "__placeholder": val } });
    let initialValue = innerGet();
    innerSet(initialValue);
    queueMicrotask(() => {
      if (!el._x_model) return;
      el._x_removeModelListeners["default"]();
      let outerGet = el._x_model.get;
      let outerSet = el._x_model.setWithModifiers;
      let releaseEntanglement = entangle(
        {
          get() {
            return outerGet();
          },
          set(value) {
            outerSet(value);
          }
        },
        {
          get() {
            return innerGet();
          },
          set(value) {
            innerSet(value);
          }
        }
      );
      cleanup2(releaseEntanglement);
    });
  });

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/directives/x-teleport.js
  directive("teleport", (el, { modifiers, expression }, { cleanup: cleanup2 }) => {
    if (el.tagName.toLowerCase() !== "template") warn("x-teleport can only be used on a <template> tag", el);
    let target = getTarget(expression);
    let clone2 = el.content.cloneNode(true).firstElementChild;
    el._x_teleport = clone2;
    clone2._x_teleportBack = el;
    el.setAttribute("data-teleport-template", true);
    clone2.setAttribute("data-teleport-target", true);
    if (el._x_forwardEvents) {
      el._x_forwardEvents.forEach((eventName) => {
        clone2.addEventListener(eventName, (e) => {
          e.stopPropagation();
          el.dispatchEvent(new e.constructor(e.type, e));
        });
      });
    }
    addScopeToNode(clone2, {}, el);
    let placeInDom = (clone3, target2, modifiers2) => {
      if (modifiers2.includes("prepend")) {
        target2.parentNode.insertBefore(clone3, target2);
      } else if (modifiers2.includes("append")) {
        target2.parentNode.insertBefore(clone3, target2.nextSibling);
      } else {
        target2.appendChild(clone3);
      }
    };
    mutateDom(() => {
      skipDuringClone(() => {
        placeInDom(clone2, target, modifiers);
        initTree(clone2);
      })();
    });
    el._x_teleportPutBack = () => {
      let target2 = getTarget(expression);
      mutateDom(() => {
        placeInDom(el._x_teleport, target2, modifiers);
      });
    };
    cleanup2(
      () => mutateDom(() => {
        clone2.remove();
        destroyTree(clone2);
      })
    );
  });
  var teleportContainerDuringClone = document.createElement("div");
  function getTarget(expression) {
    let target = skipDuringClone(() => {
      return document.querySelector(expression);
    }, () => {
      return teleportContainerDuringClone;
    })();
    if (!target) warn(`Cannot find x-teleport element for selector: "${expression}"`);
    return target;
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/directives/x-ignore.js
  var handler = () => {
  };
  handler.inline = (el, { modifiers }, { cleanup: cleanup2 }) => {
    modifiers.includes("self") ? el._x_ignoreSelf = true : el._x_ignore = true;
    cleanup2(() => {
      modifiers.includes("self") ? delete el._x_ignoreSelf : delete el._x_ignore;
    });
  };
  directive("ignore", handler);

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/directives/x-effect.js
  directive("effect", skipDuringClone((el, { expression }, { effect: effect3 }) => {
    effect3(evaluateLater(el, expression));
  }));

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/utils/on.js
  function on(el, event, modifiers, callback) {
    let listenerTarget = el;
    let handler4 = (e) => callback(e);
    let options = {};
    let wrapHandler = (callback2, wrapper) => (e) => wrapper(callback2, e);
    if (modifiers.includes("dot")) event = dotSyntax(event);
    if (modifiers.includes("camel")) event = camelCase2(event);
    if (modifiers.includes("capture")) options.capture = true;
    if (modifiers.includes("window")) listenerTarget = window;
    if (modifiers.includes("document")) listenerTarget = document;
    if (modifiers.includes("passive")) {
      options.passive = modifiers[modifiers.indexOf("passive") + 1] !== "false";
    }
    handler4 = addDebounceOrThrottle(modifiers, handler4);
    if (modifiers.includes("prevent")) handler4 = wrapHandler(handler4, (next, e) => {
      e.preventDefault();
      next(e);
    });
    if (modifiers.includes("stop")) handler4 = wrapHandler(handler4, (next, e) => {
      e.stopPropagation();
      next(e);
    });
    if (modifiers.includes("once")) {
      handler4 = wrapHandler(handler4, (next, e) => {
        next(e);
        listenerTarget.removeEventListener(event, handler4, options);
      });
    }
    if (modifiers.includes("away") || modifiers.includes("outside")) {
      listenerTarget = document;
      handler4 = wrapHandler(handler4, (next, e) => {
        if (el.contains(e.target)) return;
        if (e.target.isConnected === false) return;
        if (el.offsetWidth < 1 && el.offsetHeight < 1) return;
        if (el._x_isShown === false) return;
        next(e);
      });
    }
    if (modifiers.includes("self")) handler4 = wrapHandler(handler4, (next, e) => {
      e.target === el && next(e);
    });
    if (event === "submit") {
      handler4 = wrapHandler(handler4, (next, e) => {
        if (e.target._x_pendingModelUpdates) {
          e.target._x_pendingModelUpdates.forEach((fn) => fn());
        }
        next(e);
      });
    }
    if (isKeyEvent(event) || isClickEvent(event)) {
      handler4 = wrapHandler(handler4, (next, e) => {
        if (isListeningForASpecificKeyThatHasntBeenPressed(e, modifiers)) {
          return;
        }
        next(e);
      });
    }
    listenerTarget.addEventListener(event, handler4, options);
    return () => {
      listenerTarget.removeEventListener(event, handler4, options);
    };
  }
  function addDebounceOrThrottle(modifiers, handler4) {
    if (modifiers.includes("debounce")) {
      let nextModifier = modifiers[modifiers.indexOf("debounce") + 1] || "invalid-wait";
      let wait = isNumeric(nextModifier.split("ms")[0]) ? Number(nextModifier.split("ms")[0]) : 250;
      handler4 = debounce(handler4, wait);
    }
    if (modifiers.includes("throttle")) {
      let nextModifier = modifiers[modifiers.indexOf("throttle") + 1] || "invalid-wait";
      let wait = isNumeric(nextModifier.split("ms")[0]) ? Number(nextModifier.split("ms")[0]) : 250;
      handler4 = throttle(handler4, wait);
    }
    return handler4;
  }
  function dotSyntax(subject) {
    return subject.replace(/-/g, ".");
  }
  function camelCase2(subject) {
    return subject.toLowerCase().replace(/-(\w)/g, (match, char) => char.toUpperCase());
  }
  function isNumeric(subject) {
    return !Array.isArray(subject) && !isNaN(subject);
  }
  function kebabCase2(subject) {
    if ([" ", "_"].includes(
      subject
    )) return subject;
    return subject.replace(/([a-z])([A-Z])/g, "$1-$2").replace(/[_\s]/, "-").toLowerCase();
  }
  function isKeyEvent(event) {
    return ["keydown", "keyup"].includes(event);
  }
  function isClickEvent(event) {
    return ["contextmenu", "click", "mouse"].some((i) => event.includes(i));
  }
  function isListeningForASpecificKeyThatHasntBeenPressed(e, modifiers) {
    let keyModifiers = modifiers.filter((i) => {
      return !["window", "document", "prevent", "stop", "once", "capture", "self", "away", "outside", "passive", "preserve-scroll", "blur", "change", "lazy"].includes(i);
    });
    if (keyModifiers.includes("debounce")) {
      let debounceIndex = keyModifiers.indexOf("debounce");
      keyModifiers.splice(debounceIndex, isNumeric((keyModifiers[debounceIndex + 1] || "invalid-wait").split("ms")[0]) ? 2 : 1);
    }
    if (keyModifiers.includes("throttle")) {
      let debounceIndex = keyModifiers.indexOf("throttle");
      keyModifiers.splice(debounceIndex, isNumeric((keyModifiers[debounceIndex + 1] || "invalid-wait").split("ms")[0]) ? 2 : 1);
    }
    if (keyModifiers.length === 0) return false;
    if (keyModifiers.length === 1 && keyToModifiers(e.key).includes(keyModifiers[0])) return false;
    const systemKeyModifiers = ["ctrl", "shift", "alt", "meta", "cmd", "super"];
    const selectedSystemKeyModifiers = systemKeyModifiers.filter((modifier) => keyModifiers.includes(modifier));
    keyModifiers = keyModifiers.filter((i) => !selectedSystemKeyModifiers.includes(i));
    if (selectedSystemKeyModifiers.length > 0) {
      const activelyPressedKeyModifiers = selectedSystemKeyModifiers.filter((modifier) => {
        if (modifier === "cmd" || modifier === "super") modifier = "meta";
        return e[`${modifier}Key`];
      });
      if (activelyPressedKeyModifiers.length === selectedSystemKeyModifiers.length) {
        if (isClickEvent(e.type)) return false;
        if (keyToModifiers(e.key).includes(keyModifiers[0])) return false;
      }
    }
    return true;
  }
  function keyToModifiers(key) {
    if (!key) return [];
    key = kebabCase2(key);
    let modifierToKeyMap = {
      "ctrl": "control",
      "slash": "/",
      "space": " ",
      "spacebar": " ",
      "cmd": "meta",
      "esc": "escape",
      "up": "arrow-up",
      "down": "arrow-down",
      "left": "arrow-left",
      "right": "arrow-right",
      "period": ".",
      "comma": ",",
      "equal": "=",
      "minus": "-",
      "underscore": "_"
    };
    modifierToKeyMap[key] = key;
    return Object.keys(modifierToKeyMap).map((modifier) => {
      if (modifierToKeyMap[modifier] === key) return modifier;
    }).filter((modifier) => modifier);
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/directives/x-model.js
  directive("model", (el, { modifiers, expression }, { effect: effect3, cleanup: cleanup2 }) => {
    let scopeTarget = el;
    if (modifiers.includes("parent")) {
      scopeTarget = findClosest(el, (element) => element !== el);
    }
    let evaluateGet = evaluateLater(scopeTarget, expression);
    let evaluateSet;
    if (typeof expression === "string") {
      evaluateSet = evaluateLater(scopeTarget, `${expression} = __placeholder`);
    } else if (typeof expression === "function" && typeof expression() === "string") {
      evaluateSet = evaluateLater(scopeTarget, `${expression()} = __placeholder`);
    } else {
      evaluateSet = () => {
      };
    }
    let getValue = () => {
      let result;
      evaluateGet((value) => result = value);
      return isGetterSetter(result) ? result.get() : result;
    };
    let setValue = (value) => {
      let result;
      evaluateGet((value2) => result = value2);
      if (isGetterSetter(result)) {
        result.set(value);
      } else {
        evaluateSet(() => {
        }, {
          scope: { "__placeholder": value }
        });
      }
    };
    if (typeof expression === "string" && el.type === "radio") {
      mutateDom(() => {
        if (!el.hasAttribute("name")) el.setAttribute("name", expression);
      });
    }
    let hasChangeModifier = modifiers.includes("change") || modifiers.includes("lazy");
    let hasBlurModifier = modifiers.includes("blur");
    let hasEnterModifier = modifiers.includes("enter");
    let hasExplicitEventModifiers = hasChangeModifier || hasBlurModifier || hasEnterModifier;
    let removeListener;
    if (isCloning) {
      removeListener = () => {
      };
    } else if (hasExplicitEventModifiers) {
      let listeners = [];
      let syncValue = (e) => setValue(getInputValue(el, modifiers, e, getValue()));
      if (hasChangeModifier) {
        listeners.push(on(el, "change", modifiers, syncValue));
      }
      if (hasBlurModifier) {
        listeners.push(on(el, "blur", modifiers, syncValue));
        if (el.form) {
          let form = el.form;
          let syncCallback = () => syncValue({ target: el });
          if (!form._x_pendingModelUpdates) form._x_pendingModelUpdates = [];
          form._x_pendingModelUpdates.push(syncCallback);
          cleanup2(() => {
            if (form._x_pendingModelUpdates) {
              form._x_pendingModelUpdates.splice(form._x_pendingModelUpdates.indexOf(syncCallback), 1);
            }
          });
        }
      }
      if (hasEnterModifier) {
        listeners.push(on(el, "keydown", modifiers, (e) => {
          if (e.key === "Enter") syncValue(e);
        }));
      }
      removeListener = () => listeners.forEach((remove) => remove());
    } else {
      let event = el.tagName.toLowerCase() === "select" || ["checkbox", "radio"].includes(el.type) ? "change" : "input";
      removeListener = on(el, event, modifiers, (e) => {
        setValue(getInputValue(el, modifiers, e, getValue()));
      });
    }
    if (modifiers.includes("fill")) {
      if ([void 0, null, ""].includes(getValue()) || isCheckbox(el) && Array.isArray(getValue()) || el.tagName.toLowerCase() === "select" && el.multiple) {
        setValue(
          getInputValue(el, modifiers, { target: el }, getValue())
        );
      }
    }
    if (!el._x_removeModelListeners) el._x_removeModelListeners = {};
    el._x_removeModelListeners["default"] = removeListener;
    cleanup2(() => el._x_removeModelListeners["default"]());
    if (el.form) {
      let removeResetListener = on(el.form, "reset", [], (e) => {
        nextTick(() => el._x_model && el._x_model.set(getInputValue(el, modifiers, { target: el }, getValue())));
      });
      cleanup2(() => removeResetListener());
    }
    el._x_model = {
      get() {
        return getValue();
      },
      set(value) {
        setValue(value);
      },
      setWithModifiers: addDebounceOrThrottle(modifiers, setValue)
    };
    el._x_forceModelUpdate = (value) => {
      if (value === void 0 && typeof expression === "string" && expression.match(/\./)) value = "";
      mutateDom(() => {
        if (isCheckbox(el)) {
          if (Array.isArray(value)) {
            el.checked = value.some((val) => val == el.value);
          } else {
            el.checked = !!value;
          }
        } else if (isRadio(el)) {
          if (typeof value === "boolean") {
            el.checked = safeParseBoolean(el.value) === value;
          } else {
            el.checked = el.value == value;
          }
        } else {
          bind(el, "value", value);
        }
      });
    };
    effect3(() => {
      let value = getValue();
      if (modifiers.includes("unintrusive") && document.activeElement.isSameNode(el)) return;
      el._x_forceModelUpdate(value);
    });
  });
  function getInputValue(el, modifiers, event, currentValue) {
    return mutateDom(() => {
      if (event instanceof CustomEvent && event.detail !== void 0)
        return event.detail !== null && event.detail !== void 0 ? event.detail : event.target.value;
      else if (isCheckbox(el)) {
        if (Array.isArray(currentValue)) {
          let newValue = null;
          if (modifiers.includes("number")) {
            newValue = safeParseNumber(event.target.value);
          } else if (modifiers.includes("boolean")) {
            newValue = safeParseBoolean(event.target.value);
          } else {
            newValue = event.target.value;
          }
          return event.target.checked ? currentValue.includes(newValue) ? currentValue : currentValue.concat([newValue]) : currentValue.filter((el2) => !checkedAttrLooseCompare2(el2, newValue));
        } else {
          return event.target.checked;
        }
      } else if (el.tagName.toLowerCase() === "select" && el.multiple) {
        if (modifiers.includes("number")) {
          return Array.from(event.target.selectedOptions).map((option) => {
            let rawValue = option.value || option.text;
            return safeParseNumber(rawValue);
          });
        } else if (modifiers.includes("boolean")) {
          return Array.from(event.target.selectedOptions).map((option) => {
            let rawValue = option.value || option.text;
            return safeParseBoolean(rawValue);
          });
        }
        return Array.from(event.target.selectedOptions).map((option) => {
          return option.value || option.text;
        });
      } else {
        let newValue;
        if (isRadio(el)) {
          if (event.target.checked) {
            newValue = event.target.value;
          } else {
            newValue = currentValue;
          }
        } else {
          newValue = event.target.value;
        }
        if (modifiers.includes("number")) {
          return safeParseNumber(newValue);
        } else if (modifiers.includes("boolean")) {
          return safeParseBoolean(newValue);
        } else if (modifiers.includes("trim")) {
          return newValue.trim();
        } else {
          return newValue;
        }
      }
    });
  }
  function safeParseNumber(rawValue) {
    let number = rawValue ? parseFloat(rawValue) : null;
    return isNumeric2(number) ? number : rawValue;
  }
  function checkedAttrLooseCompare2(valueA, valueB) {
    return valueA == valueB;
  }
  function isNumeric2(subject) {
    return !Array.isArray(subject) && !isNaN(subject);
  }
  function isGetterSetter(value) {
    return value !== null && typeof value === "object" && typeof value.get === "function" && typeof value.set === "function";
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/directives/x-cloak.js
  directive("cloak", (el) => queueMicrotask(() => mutateDom(() => el.removeAttribute(prefix("cloak")))));

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/directives/x-init.js
  addInitSelector(() => `[${prefix("init")}]`);
  directive("init", skipDuringClone((el, { expression }, { evaluate: evaluate2 }) => {
    if (typeof expression === "string") {
      return !!expression.trim() && evaluate2(expression, {}, false);
    }
    return evaluate2(expression, {}, false);
  }));

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/directives/x-text.js
  directive("text", (el, { expression }, { effect: effect3, evaluateLater: evaluateLater2 }) => {
    let evaluate2 = evaluateLater2(expression);
    effect3(() => {
      evaluate2((value) => {
        mutateDom(() => {
          el.textContent = value;
        });
      });
    });
  });

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/directives/x-html.js
  directive("html", (el, { expression }, { effect: effect3, evaluateLater: evaluateLater2 }) => {
    let evaluate2 = evaluateLater2(expression);
    effect3(() => {
      evaluate2((value) => {
        mutateDom(() => {
          el.innerHTML = value ?? "";
          el._x_ignoreSelf = true;
          initTree(el);
          delete el._x_ignoreSelf;
        });
      });
    });
  });

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/directives/x-bind.js
  mapAttributes(startingWith(":", into(prefix("bind:"))));
  var handler2 = (el, { value, modifiers, expression, original }, { effect: effect3, cleanup: cleanup2 }) => {
    if (!value) {
      let bindingProviders = {};
      injectBindingProviders(bindingProviders);
      let getBindings = evaluateLater(el, expression);
      getBindings((bindings) => {
        applyBindingsObject(el, bindings, original);
      }, { scope: bindingProviders });
      return;
    }
    if (value === "key") return storeKeyForXFor(el, expression);
    if (el._x_inlineBindings && el._x_inlineBindings[value] && el._x_inlineBindings[value].extract) {
      return;
    }
    let evaluate2 = evaluateLater(el, expression);
    effect3(() => evaluate2((result) => {
      if (result === void 0 && typeof expression === "string" && expression.match(/\./)) {
        result = "";
      }
      mutateDom(() => bind(el, value, result, modifiers));
    }));
    cleanup2(() => {
      el._x_undoAddedClasses && el._x_undoAddedClasses();
      el._x_undoAddedStyles && el._x_undoAddedStyles();
    });
  };
  handler2.inline = (el, { value, modifiers, expression }) => {
    if (!value) return;
    if (!el._x_inlineBindings) el._x_inlineBindings = {};
    el._x_inlineBindings[value] = { expression, extract: false };
  };
  directive("bind", handler2);
  function storeKeyForXFor(el, expression) {
    el._x_keyExpression = expression;
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/directives/x-data.js
  addRootSelector(() => `[${prefix("data")}]`);
  directive("data", ((el, { expression }, { cleanup: cleanup2 }) => {
    if (shouldSkipRegisteringDataDuringClone(el)) return;
    expression = expression === "" ? "{}" : expression;
    let magicContext = {};
    injectMagics(magicContext, el);
    let dataProviderContext = {};
    injectDataProviders(dataProviderContext, magicContext);
    let data2 = evaluate(el, expression, { scope: dataProviderContext });
    if (data2 === void 0 || data2 === true) data2 = {};
    injectMagics(data2, el);
    let reactiveData = reactive(data2);
    initInterceptors(reactiveData);
    let undo = addScopeToNode(el, reactiveData);
    reactiveData["init"] && evaluate(el, reactiveData["init"]);
    cleanup2(() => {
      reactiveData["destroy"] && evaluate(el, reactiveData["destroy"]);
      undo();
    });
  }));
  interceptClone((from, to) => {
    if (from._x_dataStack) {
      to._x_dataStack = from._x_dataStack;
      to.setAttribute("data-has-alpine-state", true);
    }
  });
  function shouldSkipRegisteringDataDuringClone(el) {
    if (!isCloning) return false;
    if (isCloningLegacy) return true;
    return el.hasAttribute("data-has-alpine-state");
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/directives/x-show.js
  directive("show", (el, { modifiers, expression }, { effect: effect3 }) => {
    let evaluate2 = evaluateLater(el, expression);
    if (!el._x_doHide) el._x_doHide = () => {
      mutateDom(() => {
        el.style.setProperty("display", "none", modifiers.includes("important") ? "important" : void 0);
      });
    };
    if (!el._x_doShow) el._x_doShow = () => {
      mutateDom(() => {
        if (el.style.length === 1 && el.style.display === "none") {
          el.removeAttribute("style");
        } else {
          el.style.removeProperty("display");
        }
      });
    };
    let hide = () => {
      el._x_doHide();
      el._x_isShown = false;
    };
    let show = () => {
      el._x_doShow();
      el._x_isShown = true;
    };
    let clickAwayCompatibleShow = () => setTimeout(show);
    let toggle = once(
      (value) => value ? show() : hide(),
      (value) => {
        if (typeof el._x_toggleAndCascadeWithTransitions === "function") {
          el._x_toggleAndCascadeWithTransitions(el, value, show, hide);
        } else {
          value ? clickAwayCompatibleShow() : hide();
        }
      }
    );
    let oldValue;
    let firstTime = true;
    effect3(() => evaluate2((value) => {
      if (!firstTime && value === oldValue) return;
      if (modifiers.includes("immediate")) value ? clickAwayCompatibleShow() : hide();
      toggle(value);
      oldValue = value;
      firstTime = false;
    }));
  });

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/directives/x-for.js
  directive("for", (el, { expression }, { effect: effect3, cleanup: cleanup2 }) => {
    let iteratorNames = parseForExpression(expression);
    let evaluateItems = evaluateLater(el, iteratorNames.items);
    let evaluateKey = evaluateLater(
      el,
      // the x-bind:key expression is stored for our use instead of evaluated.
      el._x_keyExpression || "index"
    );
    el._x_lookup = /* @__PURE__ */ new Map();
    effect3(() => loop(el, iteratorNames, evaluateItems, evaluateKey));
    cleanup2(() => {
      el._x_lookup.forEach(
        (el2) => mutateDom(() => {
          destroyTree(el2);
          el2.remove();
        })
      );
      delete el._x_lookup;
    });
  });
  function refreshScope(scope2) {
    return (newScope) => {
      Object.entries(newScope).forEach(([key, value]) => {
        scope2[key] = value;
      });
    };
  }
  function loop(templateEl, iteratorNames, evaluateItems, evaluateKey) {
    evaluateItems((items) => {
      if (isNumeric3(items))
        items = Array.from({ length: items }, (_, i) => i + 1);
      if (items === void 0 || items === null) items = [];
      if (items instanceof Set) items = Array.from(items);
      if (items instanceof Map) items = Array.from(items);
      let oldLookup = templateEl._x_lookup;
      let lookup = /* @__PURE__ */ new Map();
      templateEl._x_lookup = lookup;
      let hasStringKeys = isObject2(items);
      let scopeEntries = Object.entries(items).map(([index, item]) => {
        if (!hasStringKeys) index = parseInt(index);
        let scope2 = getIterationScopeVariables(iteratorNames, item, index, items);
        let key;
        evaluateKey((innerKey) => {
          if (typeof innerKey === "object")
            warn("x-for key cannot be an object, it must be a string or an integer", templateEl);
          if (oldLookup.has(innerKey)) {
            lookup.set(innerKey, oldLookup.get(innerKey));
            oldLookup.delete(innerKey);
          }
          key = innerKey;
        }, { scope: { index, ...scope2 } });
        return [key, scope2];
      });
      mutateDom(() => {
        oldLookup.forEach((el) => {
          destroyTree(el);
          el.remove();
        });
        let added = /* @__PURE__ */ new Set();
        let prev = templateEl;
        scopeEntries.forEach(([key, scope2]) => {
          if (lookup.has(key)) {
            let el = lookup.get(key);
            el._x_refreshXForScope(scope2);
            if (prev.nextElementSibling !== el) {
              if (prev.nextElementSibling)
                el.replaceWith(prev.nextElementSibling);
              prev.after(el);
            }
            prev = el;
            if (el._x_currentIfEl) {
              if (el.nextElementSibling !== el._x_currentIfEl)
                prev.after(el._x_currentIfEl);
              prev = el._x_currentIfEl;
            }
            return;
          }
          if (templateEl.content.children.length > 1)
            warn("x-for templates require a single root element, additional elements will be ignored.", templateEl);
          let clone2 = document.importNode(templateEl.content, true).firstElementChild;
          let reactiveScope = reactive(scope2);
          addScopeToNode(clone2, reactiveScope, templateEl);
          clone2._x_refreshXForScope = refreshScope(reactiveScope);
          lookup.set(key, clone2);
          added.add(clone2);
          prev.after(clone2);
          prev = clone2;
        });
        skipDuringClone(() => added.forEach((clone2) => initTree(clone2)))();
      });
    });
  }
  function parseForExpression(expression) {
    let forIteratorRE = /,([^,\}\]]*)(?:,([^,\}\]]*))?$/;
    let stripParensRE = /^\s*\(|\)\s*$/g;
    let forAliasRE = /([\s\S]*?)\s+(?:in|of)\s+([\s\S]*)/;
    let inMatch = expression.match(forAliasRE);
    if (!inMatch) return;
    let res = {};
    res.items = inMatch[2].trim();
    let item = inMatch[1].replace(stripParensRE, "").trim();
    let iteratorMatch = item.match(forIteratorRE);
    if (iteratorMatch) {
      res.item = item.replace(forIteratorRE, "").trim();
      res.index = iteratorMatch[1].trim();
      if (iteratorMatch[2]) {
        res.collection = iteratorMatch[2].trim();
      }
    } else {
      res.item = item;
    }
    return res;
  }
  function getIterationScopeVariables(iteratorNames, item, index, items) {
    let scopeVariables = {};
    if (/^\[.*\]$/.test(iteratorNames.item) && Array.isArray(item)) {
      let names = iteratorNames.item.replace("[", "").replace("]", "").split(",").map((i) => i.trim());
      names.forEach((name, i) => {
        scopeVariables[name] = item[i];
      });
    } else if (/^\{.*\}$/.test(iteratorNames.item) && !Array.isArray(item) && typeof item === "object") {
      let names = iteratorNames.item.replace("{", "").replace("}", "").split(",").map((i) => i.trim());
      names.forEach((name) => {
        scopeVariables[name] = item[name];
      });
    } else {
      scopeVariables[iteratorNames.item] = item;
    }
    if (iteratorNames.index) scopeVariables[iteratorNames.index] = index;
    if (iteratorNames.collection) scopeVariables[iteratorNames.collection] = items;
    return scopeVariables;
  }
  function isNumeric3(subject) {
    return typeof subject !== "object" && !isNaN(subject);
  }
  function isObject2(subject) {
    return typeof subject === "object" && !Array.isArray(subject);
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/directives/x-ref.js
  function handler3() {
  }
  handler3.inline = (el, { expression }, { cleanup: cleanup2 }) => {
    let root = closestRoot(el);
    if (!root) return;
    if (!root._x_refs) root._x_refs = {};
    root._x_refs[expression] = el;
    cleanup2(() => delete root._x_refs[expression]);
  };
  directive("ref", handler3);

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/directives/x-if.js
  directive("if", (el, { expression }, { effect: effect3, cleanup: cleanup2 }) => {
    if (el.tagName.toLowerCase() !== "template") warn("x-if can only be used on a <template> tag", el);
    let evaluate2 = evaluateLater(el, expression);
    let show = () => {
      if (el._x_currentIfEl) return el._x_currentIfEl;
      let clone2 = el.content.cloneNode(true).firstElementChild;
      addScopeToNode(clone2, {}, el);
      mutateDom(() => {
        el.after(clone2);
        skipDuringClone(() => initTree(clone2))();
      });
      el._x_currentIfEl = clone2;
      el._x_undoIf = () => {
        mutateDom(() => {
          destroyTree(clone2);
          clone2.remove();
        });
        delete el._x_currentIfEl;
      };
      return clone2;
    };
    let hide = () => {
      if (!el._x_undoIf) return;
      el._x_undoIf();
      delete el._x_undoIf;
    };
    effect3(() => evaluate2((value) => {
      value ? show() : hide();
    }));
    cleanup2(() => el._x_undoIf && el._x_undoIf());
  });

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/directives/x-id.js
  directive("id", (el, { expression }, { evaluate: evaluate2 }) => {
    let names = evaluate2(expression);
    names.forEach((name) => setIdRoot(el, name));
  });
  interceptClone((from, to) => {
    if (from._x_ids) {
      to._x_ids = from._x_ids;
    }
  });

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/directives/x-on.js
  mapAttributes(startingWith("@", into(prefix("on:"))));
  directive("on", skipDuringClone((el, { value, modifiers, expression }, { cleanup: cleanup2 }) => {
    let evaluate2 = expression ? evaluateLater(el, expression) : () => {
    };
    if (el.tagName.toLowerCase() === "template") {
      if (!el._x_forwardEvents) el._x_forwardEvents = [];
      if (!el._x_forwardEvents.includes(value)) el._x_forwardEvents.push(value);
    }
    let removeListener = on(el, value, modifiers, (e) => {
      evaluate2(() => {
      }, { scope: { "$event": e }, params: [e] });
    });
    cleanup2(() => removeListener());
  }));

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/directives/index.js
  warnMissingPluginDirective("Collapse", "collapse", "collapse");
  warnMissingPluginDirective("Intersect", "intersect", "intersect");
  warnMissingPluginDirective("Focus", "trap", "focus");
  warnMissingPluginDirective("Mask", "mask", "mask");
  function warnMissingPluginDirective(name, directiveName, slug) {
    directive(directiveName, (el) => warn(`You can't use [x-${directiveName}] without first installing the "${name}" plugin here: https://alpinejs.dev/plugins/${slug}`, el));
  }

  // ../../../node_modules/.pnpm/alpinejs@3.15.12/node_modules/alpinejs/src/index.js
  alpine_default.setEvaluator(normalEvaluator);
  alpine_default.setRawEvaluator(normalRawEvaluator);
  alpine_default.setReactivityEngine({ reactive: reactive2, effect: effect2, release: stop, raw: toRaw });
  var src_default = alpine_default;

  // ../../../node_modules/.pnpm/@alpinejs+morph@3.15.12/node_modules/@alpinejs/morph/dist/module.esm.js
  function morph(from, toHtml, options) {
    monkeyPatchDomSetAttributeToAllowAtSymbols();
    let context = createMorphContext(options);
    let toEl = typeof toHtml === "string" ? createElement(toHtml) : toHtml;
    if (window.Alpine && window.Alpine.closestDataStack && !from._x_dataStack) {
      toEl._x_dataStack = window.Alpine.closestDataStack(from);
      toEl._x_dataStack && window.Alpine.cloneNode(from, toEl);
    }
    context.patch(from, toEl);
    return from;
  }
  function morphBetween(startMarker, endMarker, toHtml, options = {}) {
    monkeyPatchDomSetAttributeToAllowAtSymbols();
    let context = createMorphContext(options);
    let fromContainer = startMarker.parentNode;
    let fromBlock = new Block(startMarker, endMarker);
    let toContainer = typeof toHtml === "string" ? (() => {
      let container = document.createElement("div");
      container.insertAdjacentHTML("beforeend", toHtml);
      return container;
    })() : toHtml;
    let toStartMarker = document.createComment("[morph-start]");
    let toEndMarker = document.createComment("[morph-end]");
    toContainer.insertBefore(toStartMarker, toContainer.firstChild);
    toContainer.appendChild(toEndMarker);
    let toBlock = new Block(toStartMarker, toEndMarker);
    if (window.Alpine && window.Alpine.closestDataStack) {
      toContainer._x_dataStack = window.Alpine.closestDataStack(fromContainer);
      toContainer._x_dataStack && window.Alpine.cloneNode(fromContainer, toContainer);
    }
    context.patchChildren(fromBlock, toBlock);
  }
  function createMorphContext(options = {}) {
    let defaultGetKey = (el) => el.getAttribute("key");
    let noop = () => {
    };
    let context = {
      key: options.key || defaultGetKey,
      lookahead: options.lookahead || false,
      updating: options.updating || noop,
      updated: options.updated || noop,
      removing: options.removing || noop,
      removed: options.removed || noop,
      adding: options.adding || noop,
      added: options.added || noop
    };
    context.patch = function(from, to) {
      if (context.differentElementNamesTypesOrKeys(from, to)) {
        return context.swapElements(from, to);
      }
      let updateChildrenOnly = false;
      let skipChildren = false;
      let skipUntil = (predicate) => context.skipUntilCondition = predicate;
      if (shouldSkipChildren(context.updating, () => skipChildren = true, skipUntil, from, to, () => updateChildrenOnly = true))
        return;
      if (from.nodeType === 1 && window.Alpine) {
        window.Alpine.cloneNode(from, to);
        if (from._x_teleport && to._x_teleport) {
          context.patch(from._x_teleport, to._x_teleport);
        }
      }
      if (textOrComment(to)) {
        context.patchNodeValue(from, to);
        context.updated(from, to);
        return;
      }
      if (!updateChildrenOnly) {
        context.patchAttributes(from, to);
      }
      context.updated(from, to);
      if (!skipChildren) {
        context.patchChildren(from, to);
      }
    };
    context.differentElementNamesTypesOrKeys = function(from, to) {
      return from.nodeType != to.nodeType || from.nodeName != to.nodeName || context.getKey(from) != context.getKey(to);
    };
    context.swapElements = function(from, to) {
      if (shouldSkip(context.removing, from))
        return;
      let toCloned = to.cloneNode(true);
      if (shouldSkip(context.adding, toCloned))
        return;
      from.replaceWith(toCloned);
      context.removed(from);
      context.added(toCloned);
    };
    context.patchNodeValue = function(from, to) {
      let value = to.nodeValue;
      if (from.nodeValue !== value) {
        from.nodeValue = value;
      }
    };
    context.patchAttributes = function(from, to) {
      if (from._x_transitioning)
        return;
      if (from._x_isShown && !to._x_isShown) {
        return;
      }
      if (!from._x_isShown && to._x_isShown) {
        return;
      }
      let domAttributes = Array.from(from.attributes);
      let toAttributes = Array.from(to.attributes);
      for (let i = domAttributes.length - 1; i >= 0; i--) {
        let name = domAttributes[i].name;
        if (!to.hasAttribute(name)) {
          if (name === "open" && from.nodeName === "DIALOG" && from.open) {
            from.close();
          } else {
            from.removeAttribute(name);
          }
        }
      }
      for (let i = toAttributes.length - 1; i >= 0; i--) {
        let name = toAttributes[i].name;
        let value = toAttributes[i].value;
        if (from.getAttribute(name) !== value) {
          from.setAttribute(name, value);
        }
      }
    };
    context.patchChildren = function(from, to) {
      let fromKeys = context.keyToMap(from.children);
      let fromKeyHoldovers = {};
      let currentTo = getFirstNode(to);
      let currentFrom = getFirstNode(from);
      while (currentTo) {
        seedingMatchingId(currentTo, currentFrom);
        let toKey = context.getKey(currentTo);
        let fromKey = context.getKey(currentFrom);
        if (context.skipUntilCondition) {
          let fromDone = !currentFrom || context.skipUntilCondition(currentFrom);
          let toDone = !currentTo || context.skipUntilCondition(currentTo);
          if (fromDone && toDone) {
            context.skipUntilCondition = null;
          } else {
            if (!fromDone)
              currentFrom = currentFrom && getNextSibling(from, currentFrom);
            if (!toDone)
              currentTo = currentTo && getNextSibling(to, currentTo);
            continue;
          }
        }
        if (!currentFrom) {
          if (toKey && fromKeyHoldovers[toKey]) {
            let holdover = fromKeyHoldovers[toKey];
            from.appendChild(holdover);
            currentFrom = holdover;
            fromKey = context.getKey(currentFrom);
          } else {
            if (!shouldSkip(context.adding, currentTo)) {
              let clone2 = currentTo.cloneNode(true);
              from.appendChild(clone2);
              context.added(clone2);
            }
            currentTo = getNextSibling(to, currentTo);
            continue;
          }
        }
        let isIf = (node) => node && node.nodeType === 8 && node.textContent === "[if BLOCK]><![endif]";
        let isEnd = (node) => node && node.nodeType === 8 && node.textContent === "[if ENDBLOCK]><![endif]";
        if (isIf(currentTo) && isIf(currentFrom)) {
          let nestedIfCount = 0;
          let fromBlockStart = currentFrom;
          while (currentFrom) {
            let next = getNextSibling(from, currentFrom);
            if (isIf(next)) {
              nestedIfCount++;
            } else if (isEnd(next) && nestedIfCount > 0) {
              nestedIfCount--;
            } else if (isEnd(next) && nestedIfCount === 0) {
              currentFrom = next;
              break;
            }
            currentFrom = next;
          }
          let fromBlockEnd = currentFrom;
          nestedIfCount = 0;
          let toBlockStart = currentTo;
          while (currentTo) {
            let next = getNextSibling(to, currentTo);
            if (isIf(next)) {
              nestedIfCount++;
            } else if (isEnd(next) && nestedIfCount > 0) {
              nestedIfCount--;
            } else if (isEnd(next) && nestedIfCount === 0) {
              currentTo = next;
              break;
            }
            currentTo = next;
          }
          let toBlockEnd = currentTo;
          let fromBlock = new Block(fromBlockStart, fromBlockEnd);
          let toBlock = new Block(toBlockStart, toBlockEnd);
          context.patchChildren(fromBlock, toBlock);
          continue;
        }
        if (currentFrom.nodeType === 1 && context.lookahead && !currentFrom.isEqualNode(currentTo)) {
          let nextToElementSibling = getNextSibling(to, currentTo);
          let found = false;
          while (!found && nextToElementSibling) {
            if (nextToElementSibling.nodeType === 1 && currentFrom.isEqualNode(nextToElementSibling)) {
              found = true;
              currentFrom = context.addNodeBefore(from, currentTo, currentFrom);
              fromKey = context.getKey(currentFrom);
            }
            nextToElementSibling = getNextSibling(to, nextToElementSibling);
          }
        }
        if (toKey !== fromKey) {
          if (!toKey && fromKey) {
            fromKeyHoldovers[fromKey] = currentFrom;
            currentFrom = context.addNodeBefore(from, currentTo, currentFrom);
            fromKeyHoldovers[fromKey].remove();
            currentFrom = getNextSibling(from, currentFrom);
            currentTo = getNextSibling(to, currentTo);
            continue;
          }
          if (toKey && !fromKey) {
            if (fromKeys[toKey]) {
              currentFrom.replaceWith(fromKeys[toKey]);
              currentFrom = fromKeys[toKey];
              fromKey = context.getKey(currentFrom);
            }
          }
          if (toKey && fromKey) {
            let fromKeyNode = fromKeys[toKey];
            if (fromKeyNode) {
              fromKeyHoldovers[fromKey] = currentFrom;
              currentFrom.replaceWith(fromKeyNode);
              currentFrom = fromKeyNode;
              fromKey = context.getKey(currentFrom);
            } else {
              fromKeyHoldovers[fromKey] = currentFrom;
              currentFrom = context.addNodeBefore(from, currentTo, currentFrom);
              fromKeyHoldovers[fromKey].remove();
              currentFrom = getNextSibling(from, currentFrom);
              currentTo = getNextSibling(to, currentTo);
              continue;
            }
          }
        }
        let currentFromNext = currentFrom && getNextSibling(from, currentFrom);
        context.patch(currentFrom, currentTo);
        currentTo = currentTo && getNextSibling(to, currentTo);
        currentFrom = currentFromNext;
      }
      let removals = [];
      while (currentFrom) {
        if (!shouldSkip(context.removing, currentFrom))
          removals.push(currentFrom);
        currentFrom = getNextSibling(from, currentFrom);
      }
      while (removals.length) {
        let domForRemoval = removals.shift();
        domForRemoval.remove();
        context.removed(domForRemoval);
      }
    };
    context.getKey = function(el) {
      return el && el.nodeType === 1 && context.key(el);
    };
    context.keyToMap = function(els) {
      let map = {};
      for (let el of els) {
        let theKey = context.getKey(el);
        if (theKey) {
          map[theKey] = el;
        }
      }
      return map;
    };
    context.addNodeBefore = function(parent, node, beforeMe) {
      if (!shouldSkip(context.adding, node)) {
        let clone2 = node.cloneNode(true);
        parent.insertBefore(clone2, beforeMe);
        context.added(clone2);
        return clone2;
      }
      return node;
    };
    return context;
  }
  morph.step = () => {
  };
  morph.log = () => {
  };
  function shouldSkip(hook, ...args) {
    let skip = false;
    hook(...args, () => skip = true);
    return skip;
  }
  function shouldSkipChildren(hook, skipChildren, skipUntil, ...args) {
    let skip = false;
    hook(...args, () => skip = true, skipChildren, skipUntil);
    return skip;
  }
  var patched = false;
  function createElement(html) {
    const template = document.createElement("template");
    template.innerHTML = html;
    return template.content.firstElementChild;
  }
  function textOrComment(el) {
    return el.nodeType === 3 || el.nodeType === 8;
  }
  var Block = class {
    constructor(start2, end) {
      this.startComment = start2;
      this.endComment = end;
    }
    get children() {
      let children = [];
      let currentNode = this.startComment.nextSibling;
      while (currentNode && currentNode !== this.endComment) {
        children.push(currentNode);
        currentNode = currentNode.nextSibling;
      }
      return children;
    }
    appendChild(child) {
      this.endComment.before(child);
    }
    get firstChild() {
      let first = this.startComment.nextSibling;
      if (first === this.endComment)
        return;
      return first;
    }
    nextNode(reference) {
      let next = reference.nextSibling;
      if (next === this.endComment)
        return;
      return next;
    }
    insertBefore(newNode, reference) {
      reference.before(newNode);
      return newNode;
    }
  };
  function getFirstNode(parent) {
    return parent.firstChild;
  }
  function getNextSibling(parent, reference) {
    let next;
    if (parent instanceof Block) {
      next = parent.nextNode(reference);
    } else {
      next = reference.nextSibling;
    }
    return next;
  }
  function monkeyPatchDomSetAttributeToAllowAtSymbols() {
    if (patched)
      return;
    patched = true;
    let original = Element.prototype.setAttribute;
    let hostDiv = document.createElement("div");
    Element.prototype.setAttribute = function newSetAttribute(name, value) {
      if (!name.includes("@")) {
        return original.call(this, name, value);
      }
      let escapedValue = value.replace(/&/g, "&amp;").replace(/"/g, "&quot;");
      hostDiv.innerHTML = `<span ${name}="${escapedValue}"></span>`;
      let attr = hostDiv.firstElementChild.getAttributeNode(name);
      hostDiv.firstElementChild.removeAttributeNode(attr);
      this.setAttributeNode(attr);
    };
  }
  function seedingMatchingId(to, from) {
    let fromId = from && from._x_bindings && from._x_bindings.id;
    if (!fromId)
      return;
    if (!to.setAttribute)
      return;
    to.setAttribute("id", fromId);
    to.id = fromId;
  }
  function src_default2(Alpine2) {
    Alpine2.morph = morph;
    Alpine2.morphBetween = morphBetween;
  }
  var module_default = src_default2;

  // src/citry-events.ts
  var isSafeRenderId = function(value) {
    return /^[a-z0-9_-]+$/.test(value);
  };
  (function() {
    "use strict";
    var C = globalThis.Citry = globalThis.Citry || {};
    if (!C.alpine) throw new Error("[Citry] Alpine: the core hook broker is not loaded.");
    var alpineRuntime = C.alpine;
    if (!alpineRuntime._install(src_default, module_default)) return;
    if (C.events && !C.events._stubQueue) return;
    var bootstrapStub = C.events || null;
    var pointedError = function(message) {
      return new Error("[Citry] " + message);
    };
    var classes = /* @__PURE__ */ new Map();
    var anchors = /* @__PURE__ */ new Map();
    var idToAnchor = /* @__PURE__ */ new Map();
    var anchorCounter = 0;
    var callIntentCounter = 0;
    var nextCallIntent = function() {
      callIntentCounter += 1;
      return callIntentCounter;
    };
    var boundaryAttached = /* @__PURE__ */ new WeakSet();
    var processedEventsManifestTags = /* @__PURE__ */ new WeakSet();
    var config = {};
    var transportImpl = null;
    var fromBase64 = function(value) {
      return decodeURIComponent(
        Array.prototype.map.call(atob(value), function(ch) {
          return "%" + ("00" + ch.charCodeAt(0).toString(16)).slice(-2);
        }).join("")
      );
    };
    var declaredEvents = function(classId) {
      var descriptor = classes.get(classId);
      return descriptor && descriptor.eventHandlers ? Object.keys(descriptor.eventHandlers) : [];
    };
    var eventHttpMethod = function(classId, name) {
      var descriptor = classes.get(classId);
      var options = descriptor && descriptor.eventHandlers ? descriptor.eventHandlers[name] : null;
      return options && typeof options.httpMethod === "string" ? options.httpMethod : "POST";
    };
    var eventDeclaresState = function(classId, name) {
      var descriptor = classes.get(classId);
      var options = descriptor && descriptor.eventHandlers ? descriptor.eventHandlers[name] : null;
      return Boolean(options && options.usesState === true);
    };
    var requireDeclaredEvent = function(anchor, name, caller) {
      if (anchor.classId == null) {
        throw pointedError(
          "this component instance was removed or replaced, so '" + name + "' cannot be sent (" + caller + "). Keep an instance across parent re-renders with #c-key (design 5.5)."
        );
      }
      var declared = declaredEvents(anchor.classId);
      if (declared.indexOf(name) === -1) {
        throw pointedError(
          "component " + anchor.classId + " has no event '" + name + "' (" + caller + "); declared events: " + (declared.join(", ") || "(none)") + "."
        );
      }
    };
    var newErrorSlot = function() {
      return { current: null, latestStartedIntent: 0, failureOrder: 0 };
    };
    var refreshAggregateError = function(anchor) {
      var selected = null;
      var selectedOrder = 0;
      Object.keys(anchor.errorBox.handlers).forEach(function(name) {
        var slot = anchor.errorBox.handlers[name];
        if (slot.current && slot.failureOrder > selectedOrder) {
          selected = slot.current;
          selectedOrder = slot.failureOrder;
        }
      });
      anchor.errorBox.current = selected;
    };
    var refreshErrorHandlers = function(anchor, reset) {
      var declared = new Set(declaredEvents(anchor.classId));
      var handlers = anchor.errorBox.handlers;
      if (reset) {
        handlers = /* @__PURE__ */ Object.create(null);
        anchor.errorBox.handlers = handlers;
        anchor.errorBox.failureClock = 0;
      }
      Object.keys(handlers).forEach(function(name) {
        if (!declared.has(name)) delete handlers[name];
      });
      declared.forEach(function(name) {
        if (!handlers[name]) handlers[name] = newErrorSlot();
      });
      refreshAggregateError(anchor);
    };
    var readLoading = function(anchor, name, caller) {
      if (name === void 0) return anchor.loading.any > 0;
      requireDeclaredEvent(anchor, name, caller);
      return (anchor.loading.handlers[name] || 0) > 0;
    };
    var readError = function(anchor, name, caller) {
      if (name === void 0) return anchor.errorBox.current;
      requireDeclaredEvent(anchor, name, caller);
      var slot = anchor.errorBox.handlers[name];
      return slot ? slot.current : null;
    };
    var readPayloadLoading = function(componentId, name) {
      var anchor = idToAnchor.get(componentId) || null;
      if (anchor) return readLoading(anchor, name, "loading");
      if (name !== void 0) {
        throw pointedError(
          "component instance '" + componentId + "' declares no events, so loading('" + name + "') cannot inspect a handler; add a `class Events` to the component."
        );
      }
      return false;
    };
    var readPayloadError = function(componentId, name) {
      var anchor = idToAnchor.get(componentId) || null;
      if (anchor) return readError(anchor, name, "error");
      if (name !== void 0) {
        throw pointedError(
          "component instance '" + componentId + "' declares no events, so error('" + name + "') cannot inspect a handler; add a `class Events` to the component."
        );
      }
      return null;
    };
    var writableFields = function(classId, values) {
      var descriptor = classes.get(classId);
      if (descriptor && Array.isArray(descriptor.writableStateFields)) {
        return new Set(descriptor.writableStateFields);
      }
      return new Set(Object.keys(values));
    };
    var dropInvalidPendingFields = function(anchor, phase) {
      if (!anchor.writable) return;
      const droppedPending = Object.keys(anchor.pending).filter(function(field) {
        return !anchor.writable.has(field);
      });
      droppedPending.forEach(function(field) {
        delete anchor.pending[field];
      });
      if (droppedPending.length) {
        console.warn(
          "[Citry] events: component " + anchor.classId + " no longer permits pending $state fields " + phase + "; dropped: " + droppedPending.sort().join(", ") + "."
        );
      }
    };
    var refreshWritableFields = function(anchor, dropInvalidPending) {
      if (!anchor.values || !anchor.classId) return;
      var next = writableFields(anchor.classId, anchor.values);
      if (!anchor.writable) {
        anchor.writable = next;
        return;
      }
      anchor.writable.clear();
      next.forEach(function(field) {
        anchor.writable.add(field);
      });
      if (dropInvalidPending) {
        dropInvalidPendingFields(anchor, "after a descriptor update");
      }
    };
    var refreshAnchorsForClasses = function(classIds, dropInvalidPending) {
      anchors.forEach(function(anchor) {
        if (anchor.classId && classIds.has(anchor.classId)) {
          refreshWritableFields(anchor, dropInvalidPending);
          refreshErrorHandlers(anchor);
        }
      });
    };
    var snapshotErrorBoxesForClasses = function(classIds) {
      var snapshots = [];
      anchors.forEach(function(anchor) {
        if (!anchor.classId || !classIds.has(anchor.classId)) return;
        var handlers = /* @__PURE__ */ Object.create(null);
        Object.keys(anchor.errorBox.handlers).forEach(function(name) {
          handlers[name] = Object.assign({}, anchor.errorBox.handlers[name]);
        });
        snapshots.push({
          anchor,
          current: anchor.errorBox.current,
          handlers,
          failureClock: anchor.errorBox.failureClock
        });
      });
      return snapshots;
    };
    var restoreErrorBoxes = function(snapshots) {
      snapshots.forEach(function(snapshot) {
        var handlers = snapshot.anchor.errorBox.handlers;
        Object.keys(handlers).forEach(function(name) {
          delete handlers[name];
        });
        Object.keys(snapshot.handlers).forEach(function(name) {
          handlers[name] = Object.assign({}, snapshot.handlers[name]);
        });
        snapshot.anchor.errorBox.failureClock = snapshot.failureClock;
        snapshot.anchor.errorBox.current = snapshot.current;
      });
    };
    var installClassDescriptors = function(entries, dropInvalidPending) {
      var classIds = /* @__PURE__ */ new Set();
      entries.forEach(function(entry) {
        classes.set(entry[0], entry[1]);
        classIds.add(entry[0]);
      });
      refreshAnchorsForClasses(classIds, dropInvalidPending);
    };
    var makeStateProxy = function(anchor) {
      var values = anchor.values;
      var writable = anchor.writable;
      return new Proxy(values, {
        get: function(target, key) {
          return target[key];
        },
        set: function(target, key, value) {
          if (typeof key !== "string") {
            target[key] = value;
            return true;
          }
          if (!writable.has(key)) {
            throw pointedError(
              "$state field '" + key + "' of component " + anchor.classId + " is not client-writable; writable fields: " + (Array.from(writable).sort().join(", ") || "(none)") + ". Keep client-only UI state in your own x-data (design 7.2: _public/_model)."
            );
          }
          target[key] = value;
          anchor.pending[key] = value;
          return true;
        },
        deleteProperty: function(target, key) {
          throw pointedError(
            "State fields cannot be deleted through $state (tried to delete '" + String(key) + "'); State is the declared server contract."
          );
        }
      });
    };
    var adoptStateContract = function(anchor, classId, values) {
      anchor.classId = classId;
      anchor.values = src_default.reactive(Object.assign({}, values));
      anchor.writable = writableFields(classId, values);
      anchor.stateProxy = makeStateProxy(anchor);
      var handlers = /* @__PURE__ */ Object.create(null);
      declaredEvents(classId).forEach(function(name) {
        handlers[name] = 0;
      });
      anchor.loading.handlers = handlers;
      refreshErrorHandlers(anchor, true);
    };
    var createAnchor = function(componentId, classId, token, values) {
      anchorCounter += 1;
      var anchor = {
        anchorId: "a" + anchorCounter,
        componentId,
        classId,
        token: token || "",
        // The out-of-order guard's bookkeeping (design 4.2): the counter and the
        // highest applied epoch live on the anchor, never on the component id,
        // because the id changes on every render. The transport work package
        // does the send-side increment and the receive-side compare.
        epoch: 0,
        highestApplied: 0,
        epochOwner: null,
        seenInDom: false,
        // field -> value queued by a `$state` write and not yet sent. These
        // fields win over incoming server values in the reconcile rule.
        pending: {},
        values: null,
        stateProxy: null,
        writable: null,
        loading: src_default.reactive({
          any: 0,
          handlers: /* @__PURE__ */ Object.create(null)
        }),
        errorBox: src_default.reactive({
          current: null,
          handlers: /* @__PURE__ */ Object.create(null),
          failureClock: 0
        }),
        errorGeneration: 0,
        timers: /* @__PURE__ */ new Set(),
        busyTriggers: /* @__PURE__ */ new Set()
      };
      adoptStateContract(anchor, classId, values);
      anchors.set(anchor.anchorId, anchor);
      idToAnchor.set(componentId, anchor);
      return anchor;
    };
    var reconcileValues = function(anchor, serverValues) {
      Object.keys(serverValues).forEach(function(key) {
        if (Object.prototype.hasOwnProperty.call(anchor.pending, key)) return;
        anchor.values[key] = serverValues[key];
      });
    };
    var retireAnchor = function(anchor, preserveGeneral) {
      var pendingKeys = Object.keys(anchor.pending);
      var dropped = [];
      if (pendingKeys.length || anchor.loading.any > 0) {
        if (pendingKeys.length) dropped.push("pending unsent writes (" + pendingKeys.sort().join(", ") + ")");
        if (anchor.loading.any > 0) dropped.push("a nonzero loading count (" + anchor.loading.any + " in flight)");
        console.warn(
          "[Citry] events: an instance of " + anchor.classId + " was reset or removed while holding " + dropped.join(" and ") + "; that client state is discarded. Keep it across parent re-renders with #c-key (design 5.5)."
        );
      }
      anchor.timers.forEach(function(intervalId) {
        clearInterval(intervalId);
      });
      anchor.timers.clear();
      anchor.busyTriggers.clear();
      if (anchor.clientAnchor) {
        if (!preserveGeneral) globalThis.Citry?.manager?.ownership?._retireEvents(anchor.clientAnchor);
        globalThis.Citry?.manager?.ownership?._detachEvents(anchor.clientAnchor, anchor);
        anchor.clientAnchor = null;
      }
      if (anchor.componentId != null) idToAnchor.delete(anchor.componentId);
      anchors.delete(anchor.anchorId);
      anchor.componentId = null;
      anchor.classId = null;
      anchor.token = "";
      anchor.pending = {};
      anchor.values = null;
      anchor.stateProxy = null;
      anchor.writable = /* @__PURE__ */ new Set();
      anchor.errorGeneration += 1;
      refreshErrorHandlers(anchor, true);
    };
    var linkRenderedInstance = function(anchor, meta) {
      var oldComponentId = anchor.componentId;
      if (meta == null) {
        retireAnchor(anchor);
        return { branch: "plain-html", oldComponentId };
      }
      if (anchor.clientAnchor) {
        globalThis.Citry?.manager?.ownership?._transitionEvents(anchor.clientAnchor, meta.componentId, meta.classId);
      }
      var branch;
      if (meta.classId === anchor.classId) {
        branch = "reconcile";
        reconcileValues(anchor, meta.values || {});
      } else {
        branch = "adopt";
        anchor.pending = {};
        anchor.errorGeneration += 1;
        adoptStateContract(anchor, meta.classId, meta.values || {});
      }
      anchor.token = meta.token || "";
      anchor.componentId = meta.componentId;
      idToAnchor.set(meta.componentId, anchor);
      return { branch, oldComponentId };
    };
    var finishRender = function(anchor, oldComponentId) {
      if (oldComponentId == null || oldComponentId === anchor.componentId) return;
      if (idToAnchor.get(oldComponentId) === anchor) idToAnchor.delete(oldComponentId);
    };
    var attachBoundaryScope = function(root) {
      boundaryAttached.add(root);
      var ids = (root.getAttribute("data-cid") || "").trim().split(/\s+/).filter(Boolean);
      var graphOwned = ids.some(function(id) {
        return Boolean(idToAnchor.get(id)?.clientAnchor);
      });
      if (!graphOwned) alpineRuntime._isolateScope(root, {});
    };
    var attachBoundaryScopes = function(componentId) {
      var roots = document.querySelectorAll("[data-cid-" + componentId + "]");
      var anchor = roots.length ? idToAnchor.get(componentId) : null;
      if (anchor) anchor.seenInDom = true;
      roots.forEach(function(root) {
        if (boundaryAttached.has(root)) return;
        attachBoundaryScope(root);
      });
    };
    var isPlainObject = function(value) {
      return value !== null && typeof value === "object" && !Array.isArray(value);
    };
    var isJsonValue = function(value, ancestors) {
      if (value === null || typeof value === "string" || typeof value === "boolean") return true;
      if (typeof value === "number") return Number.isFinite(value);
      if (typeof value !== "object") return false;
      var seen = ancestors || /* @__PURE__ */ new Set();
      if (seen.has(value)) return false;
      seen.add(value);
      var valid;
      if (Array.isArray(value)) {
        const keys = Object.keys(value);
        valid = Object.getOwnPropertySymbols(value).length === 0 && keys.length === value.length && keys.every(function(key, index) {
          return key === String(index);
        }) && value.every(function(item) {
          return isJsonValue(item, seen);
        });
      } else {
        valid = (Object.getPrototypeOf(value) === Object.prototype || Object.getPrototypeOf(value) === null) && Object.getOwnPropertySymbols(value).length === 0 && Object.getOwnPropertyNames(value).every(function(key) {
          return Object.prototype.propertyIsEnumerable.call(value, key) && isJsonValue(value[key], seen);
        });
      }
      seen.delete(value);
      return valid;
    };
    var hasExactKeys = function(value, required, optional) {
      var allowed = new Set(required.concat(optional || []));
      return required.every(function(key) {
        return Object.prototype.hasOwnProperty.call(value, key);
      }) && Object.keys(value).every(function(key) {
        return allowed.has(key);
      });
    };
    var stageEventsManifest = function(manifest) {
      if (!isPlainObject(manifest)) throw new TypeError("events manifest must be an object");
      if (!hasExactKeys(manifest, ["protocol", "clientGraphRevision", "componentClasses", "componentInstances"])) {
        throw new TypeError("events manifest must contain exactly the citry-events/1 fields");
      }
      if (manifest.protocol !== "citry-events/1") throw new TypeError("events manifest protocol must be citry-events/1");
      if (manifest.clientGraphRevision !== null && (typeof manifest.clientGraphRevision !== "string" || !/^[0-9a-f]{64}$/.test(manifest.clientGraphRevision))) {
        throw new TypeError("events manifest clientGraphRevision must be a lowercase 64-character digest or null");
      }
      if (!Array.isArray(manifest.componentClasses)) {
        throw new TypeError("events manifest componentClasses must be an array");
      }
      if (!Array.isArray(manifest.componentInstances)) {
        throw new TypeError("events manifest componentInstances must be an array");
      }
      var stagedClasses = [];
      var classIds = /* @__PURE__ */ new Set();
      manifest.componentClasses.forEach(function(candidate) {
        if (!isPlainObject(candidate) || !hasExactKeys(candidate, ["componentClassId", "eventHandlers"], ["writableStateFields"])) {
          throw new TypeError("events component class must contain exactly its protocol fields");
        }
        if (typeof candidate.componentClassId !== "string" || !candidate.componentClassId) {
          throw new TypeError("events componentClassId must be non-empty text");
        }
        if (classIds.has(candidate.componentClassId)) throw new TypeError("events manifest repeats a componentClassId");
        if (!isPlainObject(candidate.eventHandlers)) {
          throw new TypeError("events component class eventHandlers must be an object");
        }
        Object.keys(candidate.eventHandlers).forEach(function(eventName) {
          if (!eventName) throw new TypeError("events handler names must be non-empty text");
          const options = candidate.eventHandlers[eventName];
          if (!isPlainObject(options)) {
            throw new TypeError("events handler options must be an object");
          }
          if (!hasExactKeys(
            options,
            ["httpMethod"],
            ["usesState", "debounceMilliseconds", "throttleMilliseconds", "latestCallWins", "allowBatching"]
          )) {
            throw new TypeError("events handler options contain missing or unknown fields");
          }
          if (typeof options.httpMethod !== "string" || !/^[!#$%&'*+.^_`|~0-9A-Z-]+$/.test(options.httpMethod)) {
            throw new TypeError("events handler httpMethod must be uppercase HTTP-token text");
          }
          ["debounceMilliseconds", "throttleMilliseconds"].forEach(function(field) {
            if (Object.prototype.hasOwnProperty.call(options, field) && (!Number.isInteger(options[field]) || options[field] < 0)) {
              throw new TypeError("events handler " + field + " must be a non-negative integer");
            }
          });
          if (options.usesState !== void 0 && options.usesState !== true) {
            throw new TypeError("events handler usesState may only be true");
          }
          if (options.latestCallWins !== void 0 && options.latestCallWins !== true) {
            throw new TypeError("events handler latestCallWins may only be true");
          }
          if (options.allowBatching !== void 0 && options.allowBatching !== false) {
            throw new TypeError("events handler allowBatching may only be false");
          }
        });
        if (candidate.writableStateFields !== void 0 && (!Array.isArray(candidate.writableStateFields) || candidate.writableStateFields.some(function(field) {
          return typeof field !== "string" || !field;
        }) || new Set(candidate.writableStateFields).size !== candidate.writableStateFields.length)) {
          throw new TypeError("events writableStateFields must contain unique, non-empty strings");
        }
        var descriptor = candidate;
        classIds.add(descriptor.componentClassId);
        stagedClasses.push([descriptor.componentClassId, descriptor]);
      });
      var componentIds = /* @__PURE__ */ new Set();
      var stagedInstances = manifest.componentInstances.map(function(candidate) {
        if (!isPlainObject(candidate) || !hasExactKeys(candidate, ["renderId", "componentClassId", "stateToken", "publicState"])) {
          throw new TypeError("events component instance must contain exactly its protocol fields");
        }
        var componentId = candidate.renderId;
        if (typeof componentId !== "string" || !componentId)
          throw new TypeError("events renderId must be non-empty text");
        if (!isSafeRenderId(componentId)) {
          throw new TypeError("events renderId must be safe for an HTML attribute name");
        }
        if (componentIds.has(componentId)) throw new TypeError("events manifest repeats a renderId");
        componentIds.add(componentId);
        if (typeof candidate.componentClassId !== "string" || !candidate.componentClassId) {
          throw new TypeError("events instance componentClassId must be non-empty text");
        }
        if (!classIds.has(candidate.componentClassId)) {
          throw new TypeError("events instance refers to an unknown componentClassId");
        }
        if (candidate.stateToken !== null && (typeof candidate.stateToken !== "string" || !candidate.stateToken)) {
          throw new TypeError("events stateToken must be non-empty text or null");
        }
        if (!isPlainObject(candidate.publicState) || !isJsonValue(candidate.publicState)) {
          throw new TypeError("events publicState must be a strict JSON object");
        }
        if (candidate.stateToken === null && Object.keys(candidate.publicState).length) {
          throw new TypeError("a stateless events instance cannot carry publicState");
        }
        return {
          componentId,
          classId: candidate.componentClassId,
          token: candidate.stateToken,
          values: candidate.publicState
        };
      });
      return { classes: stagedClasses, instances: stagedInstances };
    };
    var applyEventsManifest = function(manifest) {
      var staged = stageEventsManifest(manifest);
      var graphRevision = manifest.clientGraphRevision;
      var ownership = graphRevision ? globalThis.Citry?.manager?.ownership : null;
      if (graphRevision) {
        if (!ownership) throw new Error("the ownership graph registry is unavailable");
        ownership._preflightEvents(graphRevision, staged.instances);
      }
      installClassDescriptors(staged.classes, true);
      staged.instances.forEach(function(meta) {
        var existing = idToAnchor.get(meta.componentId);
        var eventsAnchor;
        if (existing) {
          if (meta.token) existing.token = meta.token;
          eventsAnchor = existing;
        } else {
          eventsAnchor = createAnchor(meta.componentId, meta.classId, meta.token || "", meta.values);
        }
        if (graphRevision && ownership) {
          eventsAnchor.clientAnchor = ownership._attachEvents(
            graphRevision,
            meta.componentId,
            meta.classId,
            eventsAnchor
          );
        }
        attachBoundaryScopes(meta.componentId);
      });
    };
    var EVENTS_MANIFEST_SELECTOR = 'script[type="application/json"][data-citry-events]';
    var consumedOwnershipRevisions = /* @__PURE__ */ new Set();
    var applyEventsManifestTransaction = function(manifest) {
      var graphRevision = manifest.clientGraphRevision;
      var ownership = graphRevision ? globalThis.Citry?.manager?.ownership : null;
      try {
        applyEventsManifest(manifest);
        if (graphRevision) {
          consumedOwnershipRevisions.add(graphRevision);
          ownership._finishEvents(graphRevision, null);
        }
      } catch (err) {
        if (graphRevision && ownership) ownership._finishEvents(graphRevision, err);
        throw err;
      }
    };
    var processEventsManifestTag = function(el) {
      if (processedEventsManifestTags.has(el)) return;
      processedEventsManifestTags.add(el);
      el.dataset.citryEventsProcessed = "";
      try {
        const manifest = JSON.parse(el.textContent);
        const candidateRevision = isPlainObject(manifest) ? manifest.clientGraphRevision : null;
        const preceding = el.previousElementSibling;
        let pairedRevision = null;
        if (preceding?.matches('script[type="application/json"][data-citry-graph]')) {
          const graphManifest = JSON.parse(preceding.textContent);
          if (isPlainObject(graphManifest) && typeof graphManifest.revision === "string" && /^[0-9a-f]{64}$/.test(graphManifest.revision)) {
            pairedRevision = graphManifest.revision;
          }
        }
        const reservationRevision = pairedRevision || (typeof candidateRevision === "string" && /^[0-9a-f]{64}$/.test(candidateRevision) ? candidateRevision : null);
        let ownership = null;
        let reservedRevision = null;
        let handedOff = false;
        if (reservationRevision) {
          ownership = globalThis.Citry?.manager?.ownership || null;
          if (!ownership) throw new Error("the ownership graph registry is unavailable");
          if (consumedOwnershipRevisions.has(reservationRevision)) {
            throw new Error(`ownership graph ${reservationRevision} already supplied an Events manifest`);
          }
          ownership._beginEvents(reservationRevision);
          reservedRevision = reservationRevision;
        }
        try {
          stageEventsManifest(manifest);
          const graphRevision = manifest.clientGraphRevision;
          if (reservedRevision && graphRevision !== reservedRevision) {
            throw new TypeError("a graph-backed Events manifest must link to its paired ownership revision");
          }
          if (graphRevision) {
            if (!ownership || reservedRevision !== graphRevision) {
              throw new Error("the ownership graph registry is unavailable");
            }
            if (!ownership.has(graphRevision)) {
              ownership.whenReady(graphRevision).then(
                function() {
                  try {
                    applyEventsManifestTransaction(manifest);
                  } catch (err) {
                    console.error("[Citry] failed to process events manifest:", err);
                  }
                },
                function(err) {
                  ownership._finishEvents(graphRevision, err);
                  console.error("[Citry] failed to wait for an events manifest ownership graph:", err);
                }
              );
              handedOff = true;
              return;
            }
          }
          handedOff = true;
          applyEventsManifestTransaction(manifest);
        } catch (err) {
          if (reservedRevision && ownership && !handedOff) ownership._finishEvents(reservedRevision, err);
          throw err;
        }
      } catch (err) {
        console.error("[Citry] failed to process events manifest:", err);
      }
    };
    var processExistingEventsManifests = function() {
      document.querySelectorAll(EVENTS_MANIFEST_SELECTOR).forEach(processEventsManifestTag);
    };
    var innermostPhysicalComponentId = function(el) {
      var root = el && el.closest ? el.closest("[data-cid]") : null;
      if (!root) return null;
      var ids = (root.getAttribute("data-cid") || "").trim().split(/\s+/).filter(Boolean);
      return ids.length ? ids[ids.length - 1] : "";
    };
    var projectedComponentId = function(el) {
      var ownership = C.manager && C.manager.ownership;
      if (el && el.nodeType === 1 && ownership && typeof ownership._ownerForElement === "function") {
        return ownership._ownerForElement(el);
      }
      return void 0;
    };
    var innermostComponentId = function(el) {
      var owner = projectedComponentId(el);
      if (owner !== void 0) return owner;
      return innermostPhysicalComponentId(el);
    };
    var resolveAnchor = function(el, magicName) {
      var id = innermostComponentId(el);
      if (id === null) {
        throw pointedError(
          "$" + magicName + " was used outside any interactive component instance (no element with a data-cid marker encloses this one). The magics only work inside a component that declares events."
        );
      }
      return id && idToAnchor.get(id) || null;
    };
    var INERT_STATE = new Proxy(
      {},
      {
        get: function(target, key) {
          if (key === Symbol.toPrimitive || key === "toString" || key === "valueOf") {
            return function() {
              return "";
            };
          }
          return void 0;
        },
        set: function() {
          return true;
        },
        has: function() {
          return false;
        }
      }
    );
    var toErrorEnvelope = function(err) {
      var structured;
      if (err && typeof err === "object" && (typeof err.status === "number" || typeof err.code === "string")) {
        structured = {
          status: typeof err.status === "number" ? err.status : 0,
          code: typeof err.code === "string" ? err.code : "transport_error",
          message: typeof err.message === "string" ? err.message : String(err)
        };
        if (err.fieldErrors && typeof err.fieldErrors === "object") {
          structured.fieldErrors = err.fieldErrors;
        }
        return structured;
      }
      return {
        status: 0,
        code: "transport_error",
        message: err && err.message ? String(err.message) : String(err)
      };
    };
    var beginLoading = function(anchor, name) {
      anchor.loading.any += 1;
      var handlers = anchor.loading.handlers;
      handlers[name] = (handlers[name] || 0) + 1;
    };
    var endLoading = function(anchor, name) {
      if (anchor.loading.any > 0) anchor.loading.any -= 1;
      var handlers = anchor.loading.handlers;
      if (typeof handlers[name] === "number" && handlers[name] > 0) handlers[name] -= 1;
    };
    var PROTOCOL = "citry-events/1";
    var CLIENT_SWAPS = ["morph", "replace", "inner", "append", "prepend", "remove", "none"];
    var CLIENT_ACTIONS = ["render", "data", "state", "event", "redirect", "url"];
    var MAX_CALLS_PER_ENVELOPE = 16;
    var DEFAULT_TIMEOUT_MS = 3e4;
    var CSRF_COOKIE_DEFAULT = "csrftoken";
    var CSRF_HEADER_DEFAULT = "X-CSRFToken";
    var detectEventsBase = function() {
      var current = document.currentScript;
      var tag;
      var src = current && typeof current.src === "string" ? current.src : "";
      if (!/\/runtime\.js([?#]|$)/.test(src)) {
        tag = document.querySelector('script[src$="ext/events/runtime.js"]');
        src = tag ? tag.src : "";
      }
      var match = /^(.*\/)runtime\.js([?#].*)?$/.exec(src);
      return match ? match[1] : null;
    };
    var detectedEventsBase = detectEventsBase();
    var eventsBaseUrl = function() {
      var configured = config.url;
      if (typeof configured === "string" && configured) {
        return configured.charAt(configured.length - 1) === "/" ? configured : configured + "/";
      }
      if (detectedEventsBase) return detectedEventsBase;
      throw pointedError(
        `the events routes' base URL is unknown (no events runtime script tag with a src to read it from); set it explicitly with Citry.events.configure({url: "/<prefix>/ext/events/"}).`
      );
    };
    var envelopeCounter = 0;
    var mintCorrelationId = function() {
      envelopeCounter += 1;
      return "r_" + envelopeCounter.toString(36) + Math.random().toString(36).slice(2, 6);
    };
    var readCookie = function(name) {
      var entries = document.cookie ? document.cookie.split("; ") : [];
      var found = null;
      entries.forEach(function(entry) {
        if (entry.indexOf(name + "=") === 0) found = decodeURIComponent(entry.slice(name.length + 1));
      });
      return found;
    };
    var resolveCsrfHeader = function() {
      var csrf = config.csrf && typeof config.csrf === "object" ? config.csrf : {};
      var header = typeof csrf.header === "string" && csrf.header ? csrf.header : CSRF_HEADER_DEFAULT;
      var token = null;
      if (typeof csrf.token === "function") token = String(csrf.token());
      else if (typeof csrf.token === "string") token = csrf.token;
      else token = readCookie(typeof csrf.cookie === "string" && csrf.cookie ? csrf.cookie : CSRF_COOKIE_DEFAULT);
      return token ? { header, token } : null;
    };
    var clientError = function(code, message) {
      return { status: 0, code, message };
    };
    var encodeGetCallQuery = function(envelope, call) {
      var query = new URLSearchParams();
      var appendValue = function(name, value) {
        if (typeof value === "string" || typeof value === "boolean") {
          query.append(name, String(value));
          return;
        }
        if (typeof value === "number" && Number.isFinite(value)) {
          query.append(name, String(value));
          return;
        }
        throw clientError(
          "transport_error",
          "GET event '" + call.handlerName + "' can carry only string, boolean, finite-number, or non-empty arrays of those query values; field '" + name + "' is not representable."
        );
      };
      Object.keys(call.args || {}).forEach(function(name) {
        var value = call.args[name];
        if (value === void 0) return;
        if (Array.isArray(value)) {
          if (!value.length) {
            throw clientError(
              "transport_error",
              "GET event '" + call.handlerName + "' cannot represent an empty array in query field '" + name + "'."
            );
          }
          value.forEach(function(item) {
            appendValue(name, item);
          });
          return;
        }
        appendValue(name, value);
      });
      if (call.callerRenderId) query.set("_citry_caller_render_id", call.callerRenderId);
      if (call.stateToken) query.set("_citry_state_token", call.stateToken);
      if (typeof call.sendSequence === "number") query.set("_citry_send_sequence", String(call.sendSequence));
      query.set("_citry_protocol", envelope.protocol);
      query.set("_citry_request_id", envelope.requestId);
      if (envelope.capabilities) query.set("_citry_capabilities", JSON.stringify(envelope.capabilities));
      return query.toString();
    };
    var resolveTimeoutMs = function(opts) {
      var optsTimeout = opts && typeof opts === "object" ? opts.timeout : void 0;
      var chosen = DEFAULT_TIMEOUT_MS;
      [optsTimeout, config.timeout].some(function(value) {
        if (typeof value === "number" && Number.isFinite(value) && value > 0) {
          chosen = value;
          return true;
        }
        return false;
      });
      return chosen;
    };
    var versionSkewPrompted = false;
    var surfaceVersionSkew = function(anchor, eventName) {
      var unprevented = fireLifecycle("citry:events:stale", anchor, eventName, { reason: "version" }, true);
      if (!unprevented || versionSkewPrompted) return;
      versionSkewPrompted = true;
      if (window.confirm("This page and the server are running different versions of the app. Reload to get back in sync?")) {
        window.location.reload();
      }
    };
    var stagedDownloads = /* @__PURE__ */ new WeakMap();
    var makeSendRecord = function(anchor, eventName, call, timeoutMs) {
      var resolveFn = function() {
      };
      var rejectFn = function() {
      };
      var promise = new Promise(function(resolve, reject) {
        resolveFn = resolve;
        rejectFn = reject;
      });
      var record = {
        anchor,
        event: eventName,
        call,
        timeoutMs,
        promise,
        resolve: resolveFn,
        reject: rejectFn,
        timedOut: false,
        timerId: 0,
        superseded: false,
        onSettled: null
      };
      return record;
    };
    var isObj = isPlainObject;
    var ERROR_STATUSES = {
      invalid_args: 422,
      invalid_state: 403,
      stale_state: 409,
      unknown_event: 404,
      unknown_component: 404,
      forbidden: 403,
      not_found: 404,
      conflict: 409,
      error: null,
      csrf_failed: 403,
      payload_too_large: 413,
      protocol_mismatch: 400,
      handler_error: 500
    };
    var isWireError = function(e) {
      if (!isObj(e) || !hasExactKeys(e, ["status", "code", "message"], ["fieldErrors"])) return false;
      if (!Number.isInteger(e.status) || e.status < 400 || e.status > 599) return false;
      if (typeof e.code !== "string" || !Object.prototype.hasOwnProperty.call(ERROR_STATUSES, e.code)) return false;
      if (ERROR_STATUSES[e.code] !== null && ERROR_STATUSES[e.code] !== e.status) return false;
      if (typeof e.message !== "string" || !e.message) return false;
      return e.fieldErrors === void 0 || isObj(e.fieldErrors) && Object.values(e.fieldErrors).every((value) => typeof value === "string");
    };
    var badReply = (reason) => clientError("transport_error", "invalid event response (" + reason + ").");
    var isActionTarget = function(value) {
      if (typeof value !== "string" || !value) return false;
      if (value.indexOf("render:") !== 0) return true;
      return isSafeRenderId(value.slice(7));
    };
    var validateWireAction = function(candidate) {
      if (!isObj(candidate) || typeof candidate.action !== "string") return false;
      if (candidate.delay !== void 0 && (typeof candidate.delay !== "number" || !Number.isFinite(candidate.delay) || candidate.delay < 0) || candidate.wait !== void 0 && candidate.wait !== false) {
        return false;
      }
      var timing = ["delay", "wait"];
      if (candidate.action === "render") {
        return hasExactKeys(candidate, ["action", "target", "swap", "html"], timing) && isActionTarget(candidate.target) && typeof candidate.swap === "string" && CLIENT_SWAPS.indexOf(candidate.swap) !== -1 && typeof candidate.html === "string";
      }
      if (candidate.action === "data") {
        return hasExactKeys(candidate, ["action", "value"], ["delay"]) && isJsonValue(candidate.value);
      }
      if (candidate.action === "state") {
        return hasExactKeys(candidate, ["action", "targetRenderId", "stateToken"], timing) && typeof candidate.targetRenderId === "string" && isSafeRenderId(candidate.targetRenderId) && typeof candidate.stateToken === "string" && !!candidate.stateToken;
      }
      if (candidate.action === "event") {
        return hasExactKeys(candidate, ["action", "eventName"], ["detail", "target"].concat(timing)) && typeof candidate.eventName === "string" && !!candidate.eventName && candidate.eventName.indexOf("citry:") !== 0 && (candidate.detail === void 0 || isJsonValue(candidate.detail)) && (candidate.target === void 0 || isActionTarget(candidate.target));
      }
      if (candidate.action === "redirect") {
        return hasExactKeys(candidate, ["action", "url"], timing) && typeof candidate.url === "string" && !!candidate.url;
      }
      if (candidate.action === "url") {
        return hasExactKeys(candidate, ["action", "url", "mode"], timing) && typeof candidate.url === "string" && !!candidate.url && (candidate.mode === "push" || candidate.mode === "replace");
      }
      return false;
    };
    var validateOkResult = function(candidate, expectedSequence) {
      if (!hasExactKeys(candidate, ["ok", "actions"], ["sendSequence"]) || candidate.ok !== true) return false;
      if (!Array.isArray(candidate.actions) || !candidate.actions.every(validateWireAction)) return false;
      if (candidate.actions.filter(function(action) {
        return action.action === "data";
      }).length > 1)
        return false;
      return candidate.sendSequence === expectedSequence;
    };
    var validateErrorResult = function(candidate, expectedSequence, checkSequence = true) {
      if (!hasExactKeys(candidate, ["ok", "error"], ["sendSequence"]) || candidate.ok !== false) return false;
      if (!isWireError(candidate.error)) return false;
      if (candidate.sendSequence !== void 0 && (!Number.isInteger(candidate.sendSequence) || candidate.sendSequence < 0)) {
        return false;
      }
      return !checkSequence || candidate.sendSequence === expectedSequence;
    };
    var preflight = function(reply, sent) {
      if (!isObj(reply) || !hasExactKeys(reply, ["protocol", "requestId", "results"]) || reply.protocol !== PROTOCOL || !Array.isArray(reply.results) || !reply.results.length) {
        throw badReply("header");
      }
      var results = reply.results;
      if (reply.requestId === null) {
        const edge = results[0];
        if (results.length !== 1 || !isObj(edge) || edge.sendSequence !== void 0 || !validateErrorResult(edge, void 0, false) || !isObj(edge.error) || edge.error.fieldErrors !== void 0 || edge.error.code !== "protocol_mismatch" && edge.error.code !== "payload_too_large") {
          throw badReply("edge");
        }
        return sent.calls.map(() => edge);
      }
      if (reply.requestId !== sent.requestId || results.length !== sent.calls.length) throw badReply("correlation");
      results.forEach((item, slot) => {
        if (!isObj(item)) throw badReply("result " + slot);
        var expectedSequence = sent.calls[slot].sendSequence;
        if (!validateOkResult(item, expectedSequence) && !validateErrorResult(item, expectedSequence)) {
          throw badReply("result " + slot);
        }
      });
      return results;
    };
    var fireRecordSettled = function(record) {
      var hook = record.onSettled;
      record.onSettled = null;
      if (hook) hook();
    };
    var settleRecordFromResult = function(record, result, slot) {
      var error2;
      var dataFired = false;
      var ctx;
      var download;
      if (record.timedOut) {
        fireStale(record.anchor, record.event, "timeout");
        console.debug(
          "[Citry] events: dropped the response of '" + record.event + "': it arrived after the call timed out."
        );
        if (result) stagedDownloads.delete(result);
        return Promise.resolve();
      }
      if (record.superseded) {
        fireStale(record.anchor, record.event, "superseded");
        console.debug(
          "[Citry] events: dropped the response of '" + record.event + "': a newer call superseded it (latest_wins)."
        );
        if (result) stagedDownloads.delete(result);
        return Promise.resolve();
      }
      if (result == null || typeof result !== "object") {
        record.reject(
          clientError(
            "transport_error",
            "the result envelope carried no result for '" + record.event + "' (results[" + slot + "] is missing)."
          )
        );
        return Promise.resolve();
      }
      if (result.ok !== true) {
        error2 = result.error && typeof result.error === "object" ? result.error : toErrorEnvelope(result.error);
        if (error2.code === "stale_state") surfaceVersionSkew(record.anchor, record.event);
        record.reject(error2);
        return Promise.resolve();
      }
      download = stagedDownloads.get(result);
      if (download) {
        stagedDownloads.delete(result);
        try {
          saveDownload(download);
          record.resolve(void 0);
        } catch (err) {
          console.error("[Citry] events: saving the download from '" + record.event + "' failed:", err);
          record.reject(toErrorEnvelope(err));
        }
        return Promise.resolve();
      }
      ctx = {
        anchor: record.anchor,
        instance: record.call.callerRenderId,
        event: record.event,
        onData: function(value) {
          dataFired = true;
          record.resolve(value);
        }
      };
      return applyResult(result, ctx).then(
        function() {
          if (!dataFired) record.resolve(void 0);
        },
        function(err) {
          console.error("[Citry] events: applying the result of '" + record.event + "' failed:", err);
          if (!dataFired) record.reject(toErrorEnvelope(err));
        }
      );
    };
    var sendRecordsOverWire = function(records) {
      var impl;
      var dispatched;
      var envelope = {
        protocol: PROTOCOL,
        requestId: mintCorrelationId(),
        capabilities: { swaps: CLIENT_SWAPS.slice(), actions: CLIENT_ACTIONS.slice() },
        calls: records.map(function(record) {
          return record.call;
        })
      };
      try {
        impl = activeTransport();
      } catch (err) {
        records.forEach(function(record) {
          record.reject(err);
          fireRecordSettled(record);
        });
        return;
      }
      try {
        dispatched = Promise.resolve(impl.send(envelope));
      } catch (err) {
        dispatched = Promise.reject(err);
      }
      var rejectRecords = function(err) {
        var error2 = toErrorEnvelope(err);
        records.forEach(function(record) {
          window.clearTimeout(record.timerId);
          if (!record.timedOut && !record.superseded) record.reject(error2);
          fireRecordSettled(record);
        });
      };
      records.forEach(function(record) {
        record.timerId = window.setTimeout(function() {
          record.timedOut = true;
          record.reject(
            clientError(
              "timeout",
              "'" + record.event + "' timed out after " + record.timeoutMs + " ms; raise it per call (sendEvent opts) or page-wide (Citry.events.configure({timeout}))."
            )
          );
          fireRecordSettled(record);
        }, record.timeoutMs);
      });
      dispatched.then(
        function(resultEnvelope) {
          var results;
          var chain = Promise.resolve();
          try {
            results = preflight(resultEnvelope, envelope);
          } catch (err) {
            rejectRecords(err);
            return;
          }
          records.forEach(function(record) {
            window.clearTimeout(record.timerId);
          });
          records.forEach(function(record, slot) {
            chain = chain.then(function() {
              return settleRecordFromResult(record, results[slot], slot).then(function() {
                fireRecordSettled(record);
              });
            });
          });
        },
        function(err) {
          rejectRecords(err);
        }
      );
    };
    var splitDisposition = function(disposition) {
      var parts = [];
      var current = "";
      var quoted = false;
      var escaped = false;
      for (let index = 0; index < disposition.length; index += 1) {
        const char = disposition[index];
        if (escaped) {
          current += char;
          escaped = false;
        } else if (quoted && char === "\\") {
          current += char;
          escaped = true;
        } else if (char === '"') {
          current += char;
          quoted = !quoted;
        } else if (char === ";" && !quoted) {
          parts.push(current.trim());
          current = "";
        } else {
          current += char;
        }
      }
      parts.push(current.trim());
      return parts;
    };
    var unquoteDispositionValue = function(raw2) {
      var value = raw2.trim();
      if (value.length < 2 || value[0] !== '"' || value[value.length - 1] !== '"') return value;
      var decoded = "";
      var escaped = false;
      for (let index = 1; index < value.length - 1; index += 1) {
        const char = value[index];
        if (escaped) {
          decoded += char;
          escaped = false;
        } else if (char === "\\") {
          escaped = true;
        } else {
          decoded += char;
        }
      }
      if (escaped) decoded += "\\";
      return decoded;
    };
    var safeDownloadFilename = function(filename) {
      var safe = Array.from(filename).filter(function(char) {
        const code = char.charCodeAt(0);
        return !(code >= 0 && code <= 31 || code >= 127 && code <= 159);
      }).join("").replace(/[\\/]/g, "_").replace(/[\u061c\u200e\u200f\u202a-\u202e\u2066-\u2069]/g, "").trim();
      return !safe || safe === "." || safe === ".." ? "download" : safe;
    };
    var downloadFilename = function(disposition) {
      var parts = splitDisposition(disposition);
      if (!parts.length || parts[0].toLowerCase() !== "attachment") return null;
      var parameters = /* @__PURE__ */ new Map();
      parts.slice(1).forEach(function(part) {
        var equals = part.indexOf("=");
        if (equals <= 0) return;
        var name = part.slice(0, equals).trim().toLowerCase();
        if (!parameters.has(name)) parameters.set(name, unquoteDispositionValue(part.slice(equals + 1)));
      });
      var filename = parameters.get("filename") || "download";
      var extended = parameters.get("filename*");
      if (extended) {
        const match = /^([^']*)'[^']*'(.*)$/.exec(extended);
        if (match && match[1].toLowerCase() === "utf-8") {
          try {
            filename = decodeURIComponent(match[2]);
          } catch (err) {
            console.warn("[Citry] events: could not decode the download filename:", err);
          }
        }
      }
      return safeDownloadFilename(filename);
    };
    var saveDownload = function(download) {
      var objectUrl = URL.createObjectURL(download.blob);
      var link = document.createElement("a");
      try {
        link.href = objectUrl;
        link.download = download.filename;
        document.body.appendChild(link);
        link.click();
      } finally {
        link.remove();
        window.setTimeout(function() {
          URL.revokeObjectURL(objectUrl);
        }, 1e4);
      }
    };
    var downloadResponse = function(response, filename, envelope) {
      if (!response.ok) {
        return Promise.reject({
          status: response.status,
          code: "transport_error",
          message: "the download endpoint answered " + response.status + "."
        });
      }
      if (envelope.calls.length !== 1) {
        return Promise.reject({
          status: 0,
          code: "transport_error",
          message: "a download response can answer exactly one event call."
        });
      }
      return response.blob().then(function(blob) {
        var call = envelope.calls[0];
        var result = { ok: true, actions: [] };
        if (typeof call.sendSequence === "number") result.sendSequence = call.sendSequence;
        stagedDownloads.set(result, { blob, filename });
        return {
          protocol: PROTOCOL,
          requestId: envelope.requestId,
          results: [result]
        };
      });
    };
    var fetchTransport = {
      send: function(envelope) {
        var base = eventsBaseUrl();
        var single = envelope.calls.length === 1 ? envelope.calls[0] : null;
        var url = single ? base + "e/" + encodeURIComponent(single.componentClassId) + "/" + encodeURIComponent(single.handlerName) : base + "call";
        var method = single && eventHttpMethod(single.componentClassId, single.handlerName) === "GET" ? "GET" : "POST";
        var request = { method, credentials: "same-origin" };
        if (method === "GET" && single) {
          const encodedQuery = encodeGetCallQuery(envelope, single);
          if (encodedQuery) url += "?" + encodedQuery;
        } else {
          const headers = {
            "Content-Type": "application/citry-events+json",
            "X-Citry-Events": "1"
          };
          const csrf = resolveCsrfHeader();
          if (csrf) headers[csrf.header] = csrf.token;
          request.headers = headers;
          request.body = JSON.stringify(envelope);
        }
        return fetch(url, request).then(function(response) {
          var disposition = response.headers.get("Content-Disposition");
          var filename = disposition ? downloadFilename(disposition) : null;
          if (filename !== null) return downloadResponse(response, filename, envelope);
          return response.text().then(function(text) {
            var parsed = null;
            try {
              parsed = JSON.parse(text);
            } catch {
              parsed = null;
            }
            if (!parsed || typeof parsed !== "object" || !Array.isArray(parsed.results)) {
              return Promise.reject({
                status: response.status,
                code: "transport_error",
                message: "the events endpoint answered " + response.status + " without a result envelope."
              });
            }
            return parsed;
          });
        });
      }
    };
    var transports = {};
    var registerTransportImpl = function(name, impl) {
      if (typeof name !== "string" || !name) {
        throw pointedError('registerTransport needs a non-empty name string (e.g. "fetch").');
      }
      if (!impl || typeof impl.send !== "function") {
        throw pointedError(
          "registerTransport('" + name + "') needs an impl object with a send(envelope) function returning (a promise of) the result envelope (design 6.1)."
        );
      }
      transports[name] = impl;
    };
    registerTransportImpl("fetch", fetchTransport);
    var activeTransport = function() {
      var name = typeof config.transport === "string" && config.transport ? config.transport : "fetch";
      var impl = transports[name];
      if (!impl) {
        throw pointedError(
          "no events transport is registered under '" + name + "'; registered: " + Object.keys(transports).sort().join(", ") + ". Register one with Citry.events.registerTransport(name, {send})."
        );
      }
      return impl;
    };
    var sendAll = function(entries) {
      entries.forEach(function(entry) {
        requireDeclaredEvent(entry.anchor, entry.name, "sendEvent");
        const args = entry.args == null ? {} : entry.args;
        if (!isPlainObject(args) || !isJsonValue(args)) {
          throw pointedError("the args for event '" + entry.name + "' must be a strict JSON object.");
        }
        if (eventHttpMethod(entry.anchor.classId, entry.name) !== "GET" && !isJsonValue(entry.anchor.pending)) {
          throw pointedError("the pending State updates for event '" + entry.name + "' must be strict JSON values.");
        }
      });
      var wireRecords = [];
      var promises = entries.map(function(entry) {
        var anchor = entry.anchor;
        var name = entry.name;
        var outcomeGeneration;
        var record;
        var dispatched;
        if (!fireLifecycle("citry:events:before", anchor, name, {}, true)) {
          fireLifecycle("citry:events:after", anchor, name, { ok: false });
          if (entry.onSettled) entry.onSettled();
          return Promise.reject(
            clientError("cancelled", "a citry:events:before listener stopped the send of '" + name + "'.")
          );
        }
        outcomeGeneration = anchor.errorGeneration;
        var errorSlot = anchor.errorBox.handlers[name];
        if (errorSlot) {
          errorSlot.latestStartedIntent = Math.max(errorSlot.latestStartedIntent, entry.intentSequence);
        }
        anchor.epoch += 1;
        var call = {
          componentClassId: anchor.classId,
          handlerName: name,
          callerRenderId: anchor.componentId,
          args: entry.args || {},
          sendSequence: anchor.epoch
        };
        if (anchor.token && (eventHttpMethod(anchor.classId, name) !== "GET" || eventDeclaresState(anchor.classId, name))) {
          call.stateToken = anchor.token;
        }
        if (eventHttpMethod(anchor.classId, name) !== "GET") {
          collectPendingTwoWayDrafts(anchor);
          dropInvalidPendingFields(anchor, "before send");
          const pendingKeys = Object.keys(anchor.pending);
          if (pendingKeys.length) {
            call.stateUpdates = anchor.pending;
            anchor.pending = {};
          }
        }
        var viaStub = Boolean(transportImpl);
        if (transportImpl) {
          try {
            dispatched = Promise.resolve(transportImpl(call, entry.opts || null));
          } catch (err) {
            dispatched = Promise.reject(err);
          }
        } else {
          record = makeSendRecord(anchor, name, call, resolveTimeoutMs(entry.opts));
          record.onSettled = entry.onSettled || null;
          if (entry.onRecord) entry.onRecord(record);
          wireRecords.push(record);
          dispatched = record.promise;
        }
        if (!entry.queueManaged) beginLoading(anchor, name);
        return dispatched.then(
          function(result) {
            if (!entry.queueManaged) endLoading(anchor, name);
            var successSlot = anchor.errorBox.handlers[name];
            if (outcomeGeneration === anchor.errorGeneration && successSlot && successSlot.latestStartedIntent === entry.intentSequence) {
              successSlot.current = null;
              successSlot.failureOrder = 0;
              refreshAggregateError(anchor);
            }
            fireLifecycle("citry:events:after", anchor, name, { ok: true });
            if (viaStub && entry.onSettled) entry.onSettled();
            return result;
          },
          function(err) {
            var failureSlot;
            if (!entry.queueManaged) endLoading(anchor, name);
            if (call.stateUpdates) {
              const droppedUpdates = [];
              Object.keys(call.stateUpdates).forEach(function(key) {
                if (!anchor.writable || !anchor.writable.has(key)) {
                  droppedUpdates.push(key);
                } else if (!Object.prototype.hasOwnProperty.call(anchor.pending, key)) {
                  anchor.pending[key] = call.stateUpdates[key];
                }
              });
              if (droppedUpdates.length) {
                console.warn(
                  "[Citry] events: a rejected call carried $state fields that are no longer client-writable; they were not restored to the pending queue: " + droppedUpdates.sort().join(", ") + "."
                );
              }
            }
            var structured = toErrorEnvelope(err);
            if (structured.code !== "cancelled" && structured.code !== "superseded") {
              failureSlot = anchor.errorBox.handlers[name];
              if (outcomeGeneration === anchor.errorGeneration && failureSlot && failureSlot.latestStartedIntent === entry.intentSequence) {
                failureSlot.current = structured;
                anchor.errorBox.failureClock += 1;
                failureSlot.failureOrder = anchor.errorBox.failureClock;
                refreshAggregateError(anchor);
              }
              fireLifecycle("citry:events:error", anchor, name, { error: structured });
            }
            fireLifecycle("citry:events:after", anchor, name, { ok: false });
            if (viaStub && entry.onSettled) entry.onSettled();
            throw err;
          }
        );
      });
      if (wireRecords.length) sendRecordsOverWire(wireRecords);
      return promises;
    };
    var queueSeq = 0;
    var queueNodes = [];
    var recurringOutstanding = /* @__PURE__ */ new Map();
    var bumpRecurring = function(key, delta) {
      var next = (recurringOutstanding.get(key) || 0) + delta;
      if (next > 0) recurringOutstanding.set(key, next);
      else recurringOutstanding.delete(key);
    };
    var readQueueOpts = function(opts) {
      var wait = true;
      if (opts && typeof opts === "object") {
        if (opts.wait === false) wait = false;
      }
      return { wait };
    };
    var eventKnobs = function(anchor, name) {
      var descriptor = classes.get(anchor.classId);
      var options = descriptor && descriptor.eventHandlers ? descriptor.eventHandlers[name] : null;
      return {
        bundle: !options || options.allowBatching !== false,
        latestWins: Boolean(options && options.latestCallWins === true)
      };
    };
    var relatedAnchorsOf = function(anchor, element, physicalOnly) {
      var related = /* @__PURE__ */ new Set([anchor]);
      var ownership = globalThis.Citry?.manager?.ownership;
      if (!physicalOnly && anchor.clientAnchor && ownership) {
        ownership._relatedEvents(anchor.clientAnchor).forEach(function(candidate) {
          related.add(candidate);
        });
        return related;
      }
      var addIdsOf = function(el) {
        (el.getAttribute("data-cid") || "").trim().split(/\s+/).filter(Boolean).forEach(function(id) {
          var found = idToAnchor.get(id);
          if (found) related.add(found);
        });
      };
      var walkUp = function(from) {
        var el = from.closest("[data-cid]");
        while (el) {
          addIdsOf(el);
          el = el.parentElement ? el.parentElement.closest("[data-cid]") : null;
        }
      };
      if (element && element.isConnected) walkUp(element);
      if (anchor.componentId != null) {
        document.querySelectorAll("[data-cid-" + anchor.componentId + "]").forEach(function(root) {
          walkUp(root);
          root.querySelectorAll("[data-cid]").forEach(addIdsOf);
        });
      }
      return related;
    };
    var addContainmentEdges = function(node) {
      var related = relatedAnchorsOf(node.anchor, node.element, node.physicalOwner);
      queueNodes.forEach(function(other) {
        if (other === node || other.settled || other.seq >= node.seq) return;
        if (related.has(other.anchor)) node.deps.add(other);
      });
    };
    var busyTriggerCounts = /* @__PURE__ */ new WeakMap();
    var retainBusyTrigger = function(anchor, element) {
      var counts = busyTriggerCounts.get(element);
      if (!counts) {
        counts = /* @__PURE__ */ new Map();
        busyTriggerCounts.set(element, counts);
      }
      counts.set(anchor, (counts.get(anchor) || 0) + 1);
      anchor.busyTriggers.add(element);
      element.setAttribute("data-citry-busy", "");
    };
    var releaseBusyTrigger = function(anchor, element) {
      var counts = busyTriggerCounts.get(element);
      if (!counts) return;
      var next = (counts.get(anchor) || 0) - 1;
      if (next > 0) counts.set(anchor, next);
      else {
        counts.delete(anchor);
        anchor.busyTriggers.delete(element);
      }
      if (counts.size === 0) {
        busyTriggerCounts.delete(element);
        element.removeAttribute("data-citry-busy");
      }
    };
    var stampGestureBusy = function(anchor, element, physicalOnly) {
      if (!physicalOnly && anchor.componentId != null) {
        document.querySelectorAll("[data-cid-" + anchor.componentId + "]").forEach(function(el) {
          el.setAttribute("data-citry-busy", "");
        });
      }
      if (element) {
        retainBusyTrigger(anchor, element);
      }
    };
    var clearGestureBusy = function(anchor, element, physicalOnly) {
      if (element) releaseBusyTrigger(anchor, element);
      if (!physicalOnly && anchor.loading.any <= 0 && anchor.componentId != null) {
        document.querySelectorAll("[data-cid-" + anchor.componentId + "]").forEach(function(el) {
          el.removeAttribute("data-citry-busy");
        });
      }
    };
    var settleQueueNode = function(node) {
      if (node.settled) return;
      node.settled = true;
      var index = queueNodes.indexOf(node);
      if (index !== -1) queueNodes.splice(index, 1);
      queueNodes.forEach(function(other) {
        other.deps.delete(node);
      });
      if (node.recurringKey) bumpRecurring(node.recurringKey, -1);
      endLoading(node.loadingAnchor, node.name);
      clearGestureBusy(node.loadingAnchor, node.element, node.ownerLocked);
      processQueue();
    };
    var supersedeOlderCalls = function(node) {
      var older = queueNodes.filter(function(other) {
        return !other.settled && other.anchor === node.anchor && other.name === node.name;
      });
      older.forEach(function(other) {
        var rejection = clientError(
          "superseded",
          "'" + node.name + "' was superseded by a newer call to the same handler (@event(latest_wins=True), design 3.5)."
        );
        if (other.dispatched) {
          if (other.record) {
            other.record.superseded = true;
            window.clearTimeout(other.record.timerId);
            other.record.reject(rejection);
          } else {
            other.reject(rejection);
          }
          console.debug(
            "[Citry] events: abandoned the in-flight '" + other.name + "': a newer call superseded it (latest_wins)."
          );
        } else {
          other.reject(rejection);
          fireStale(other.anchor, other.name, "superseded");
          console.debug(
            "[Citry] events: dropped queued '" + other.name + "': a newer call superseded it (latest_wins); never sent."
          );
        }
        settleQueueNode(other);
      });
    };
    var cancelAtDequeue = function(node) {
      node.reject(
        clientError(
          "cancelled",
          "'" + node.name + "' was cancelled: its dispatching element or component instance left the DOM while the call was queued (design 5.6)."
        )
      );
      fireStale(node.anchor, node.name, "cancelled");
      console.debug(
        "[Citry] events: cancelled queued '" + node.name + "': its dispatching element or instance is gone; never sent."
      );
      settleQueueNode(node);
    };
    var transferGesture = function(node, fresh) {
      var old = node.loadingAnchor;
      endLoading(old, node.name);
      if (node.element) releaseBusyTrigger(old, node.element);
      if (old.loading.any <= 0 && old.componentId != null) {
        document.querySelectorAll("[data-cid-" + old.componentId + "]").forEach(function(el) {
          el.removeAttribute("data-citry-busy");
        });
      }
      node.anchor = fresh;
      node.loadingAnchor = fresh;
      beginLoading(fresh, node.name);
      stampGestureBusy(fresh, node.element);
    };
    var verifyAtDequeue = function(node) {
      var anchor = node.anchor;
      var physicalId;
      if (node.carrierLive && !node.carrierLive()) return "dead";
      if (node.element) {
        if (!node.element.isConnected) return "dead";
        if (!node.ownerLocked) {
          if (node.physicalOwner) {
            physicalId = innermostPhysicalComponentId(node.element);
            anchor = physicalId && idToAnchor.get(physicalId) || null;
          } else {
            anchor = anchorForElement(node.element);
          }
          if (!anchor) return "dead";
        }
      }
      if (node.ownerLocked) {
        if (anchor.componentId == null) return "dead";
        if (anchor.clientAnchor && globalThis.Citry?.manager?.ownership && !globalThis.Citry.manager.ownership._isLive(anchor.clientAnchor)) {
          return "dead";
        }
        if (!anchor.clientAnchor && anchor.seenInDom && !document.querySelector("[data-cid-" + anchor.componentId + "]")) {
          return "dead";
        }
      } else {
        if (!node.element) {
          if (anchor.componentId == null) return "dead";
          if (anchor.clientAnchor && globalThis.Citry?.manager?.ownership && !globalThis.Citry.manager.ownership._isLive(anchor.clientAnchor)) {
            return "dead";
          }
          if (anchor.seenInDom && !document.querySelector("[data-cid-" + anchor.componentId + "]")) return "dead";
        }
      }
      if (anchor.classId == null || declaredEvents(anchor.classId).indexOf(node.name) === -1) return "dead";
      if (anchor !== node.anchor) transferGesture(node, anchor);
      addContainmentEdges(node);
      return node.deps.size ? "hold" : "dispatch";
    };
    var dispatchReadyNodes = function(ready) {
      var chunks = [];
      var bundled = [];
      ready.forEach(function(node) {
        if (!node.bundle) return;
        bundled.push(node);
        if (bundled.length === MAX_CALLS_PER_ENVELOPE) {
          chunks.push(bundled);
          bundled = [];
        }
      });
      if (bundled.length) chunks.push(bundled);
      ready.forEach(function(node) {
        if (!node.bundle) chunks.push([node]);
      });
      chunks.forEach(function(chunk) {
        chunk.forEach(function(node) {
          node.dispatched = true;
        });
        var entries = chunk.map(function(node) {
          return {
            anchor: node.anchor,
            name: node.name,
            intentSequence: node.intentSequence,
            args: node.args,
            opts: node.opts,
            queueManaged: true,
            onSettled: function() {
              settleQueueNode(node);
            },
            onRecord: function(record) {
              node.record = record;
            }
          };
        });
        var promises;
        try {
          promises = sendAll(entries);
        } catch (err) {
          chunk.forEach(function(node) {
            node.reject(err);
            settleQueueNode(node);
          });
          return;
        }
        promises.forEach(function(promise, index) {
          var node = chunk[index];
          promise.then(
            function(value) {
              node.resolve(value);
            },
            function(err) {
              node.reject(err);
              settleQueueNode(node);
            }
          );
        });
      });
    };
    var queueProcessing = false;
    var queueReprocess = false;
    var processQueue = function() {
      var ready;
      if (queueProcessing) {
        queueReprocess = true;
        return;
      }
      queueProcessing = true;
      do {
        queueReprocess = false;
        ready = [];
        queueNodes.slice().forEach(function(node) {
          if (node.settled || node.dispatched || node.deps.size !== 0) return;
          var verdict = verifyAtDequeue(node);
          if (verdict === "dead") cancelAtDequeue(node);
          else if (verdict === "dispatch") ready.push(node);
        });
        if (ready.length) dispatchReadyNodes(ready);
      } while (queueReprocess);
      queueProcessing = false;
    };
    var dispatchBypass = function(anchor, name, args, opts, element, recurringKey, ownerLocked) {
      beginLoading(anchor, name);
      stampGestureBusy(anchor, element, ownerLocked);
      if (recurringKey) bumpRecurring(recurringKey, 1);
      var settled = false;
      var finish = function() {
        if (settled) return;
        settled = true;
        if (recurringKey) bumpRecurring(recurringKey, -1);
        endLoading(anchor, name);
        clearGestureBusy(anchor, element, ownerLocked);
      };
      try {
        return sendAll([
          {
            anchor,
            name,
            intentSequence: nextCallIntent(),
            args,
            opts,
            queueManaged: true,
            onSettled: finish
          }
        ])[0];
      } catch (err) {
        finish();
        return Promise.reject(err);
      }
    };
    var enqueueSend = function(anchor, name, args, opts, element, ownerLocked, carrierLive, physicalOwner, recurringKey) {
      requireDeclaredEvent(anchor, name, "sendEvent");
      var queueOpts = readQueueOpts(opts);
      if (recurringKey && (recurringOutstanding.get(recurringKey) || 0) > 0) {
        console.debug(
          "[Citry] events: skipped a recurring '" + name + "' tick: its previous call is still queued or in flight."
        );
        return null;
      }
      if (!queueOpts.wait) return dispatchBypass(anchor, name, args, opts, element, recurringKey || null, ownerLocked);
      var knobs = eventKnobs(anchor, name);
      queueSeq += 1;
      var resolveFn = function() {
      };
      var rejectFn = function() {
      };
      var promise = new Promise(function(resolve, reject) {
        resolveFn = resolve;
        rejectFn = reject;
      });
      var node = {
        seq: queueSeq,
        intentSequence: nextCallIntent(),
        anchor,
        loadingAnchor: anchor,
        element,
        ownerLocked: ownerLocked === true,
        physicalOwner: physicalOwner === true,
        carrierLive: carrierLive || null,
        name,
        args,
        opts,
        bundle: knobs.bundle,
        latestWins: knobs.latestWins,
        recurringKey: recurringKey || null,
        dispatched: false,
        settled: false,
        deps: /* @__PURE__ */ new Set(),
        record: null,
        promise,
        resolve: resolveFn,
        reject: rejectFn
      };
      if (node.latestWins) supersedeOlderCalls(node);
      beginLoading(anchor, name);
      stampGestureBusy(anchor, element, node.ownerLocked);
      if (node.recurringKey) bumpRecurring(node.recurringKey, 1);
      addContainmentEdges(node);
      queueNodes.push(node);
      if (node.deps.size === 0) dispatchReadyNodes([node]);
      return node.promise;
    };
    var sendFromAnchor = function(anchor, name, args, opts, element, physicalOwner) {
      return enqueueSend(
        anchor,
        name,
        args || null,
        opts,
        element || null,
        false,
        null,
        physicalOwner
      );
    };
    var sendFromElement = function(el, name, args, opts, recurringKey) {
      var projectedOwner = projectedComponentId(el);
      if (projectedOwner !== void 0) {
        if (projectedOwner === null) {
          fireStale(null, name, "cancelled");
          console.debug("[Citry] events: dropped a source-owned '" + name + "' send: its fill source is retired.");
          return null;
        }
        return sendSourceOwned(projectedOwner, name, args || null, opts, el, function() {
          return projectedComponentId(el) === projectedOwner;
        });
      }
      var anchor = el && el.nodeType === 1 ? anchorForElement(el) : null;
      if (!anchor || anchor.classId == null || declaredEvents(anchor.classId).indexOf(name) === -1) {
        fireStale(anchor, name, "cancelled");
        console.debug(
          "[Citry] events: dropped a '" + name + "' send: its element resolves to no instance declaring the event."
        );
        return null;
      }
      return enqueueSend(anchor, name, args || null, opts, el, false, null, false, recurringKey);
    };
    var sendSourceOwned = function(componentId, name, args, opts, element, carrierLive) {
      var anchor = idToAnchor.get(componentId) || null;
      if (carrierLive && !carrierLive()) {
        fireStale(anchor, name, "cancelled");
        console.debug("[Citry] events: dropped a source-owned '" + name + "' send: its exact source carrier is retired.");
        return null;
      }
      if (!anchor || anchor.classId == null || declaredEvents(anchor.classId).indexOf(name) === -1) {
        fireStale(anchor, name, "cancelled");
        console.debug(
          "[Citry] events: dropped a source-owned '" + name + "' send: its authored component instance is no longer live or does not declare the event."
        );
        return null;
      }
      return enqueueSend(anchor, name, args || null, opts, element, true, carrierLive || null);
    };
    var sendBoundary = function(componentId, name, args, opts, element, carrierLive, event) {
      args = mergeSubmitFormArgs(element, event, args);
      return sendSourceOwned(componentId, name, args || null, opts, element, carrierLive || null);
    };
    var boundaryScope = function(componentId, element, carrierLive) {
      var anchor = idToAnchor.get(componentId) || null;
      var scope2 = {};
      Object.defineProperties(scope2, {
        $state: {
          enumerable: true,
          get: function() {
            return anchor ? anchor.stateProxy : INERT_STATE;
          }
        },
        $loading: {
          enumerable: true,
          value: function(name) {
            if (!anchor) return false;
            return readLoading(anchor, name, "$loading");
          }
        },
        $error: {
          enumerable: true,
          value: function(name) {
            return anchor ? readError(anchor, name, "$error") : null;
          }
        },
        $sendEvent: {
          enumerable: true,
          value: function(name, args, opts) {
            if (!anchor) {
              return Promise.reject(
                pointedError(
                  "the source component instance '" + componentId + "' is no longer registered; $sendEvent was not sent."
                )
              );
            }
            return sendBoundary(componentId, name, args || null, opts, element, carrierLive || null);
          }
        },
        $onEvent: {
          enumerable: true,
          value: function(name, fn) {
            return anchor ? subscribeForAnchor(anchor, name, fn) : function() {
            };
          }
        }
      });
      return scope2;
    };
    var sendCalls = function(intents) {
      if (!Array.isArray(intents) || !intents.length) return [];
      if (intents.length > MAX_CALLS_PER_ENVELOPE) {
        throw pointedError(
          "one envelope carries at most " + MAX_CALLS_PER_ENVELOPE + " calls (the protocol cap, design 4.2); split the batch before sending (" + intents.length + " given)."
        );
      }
      var entries = intents.map(function(intent) {
        var anchor = resolveSendTarget(intent.target);
        if (!anchor) {
          throw pointedError(
            "sendCalls found no interactive component instance for target " + (typeof intent.target === "string" ? "'" + intent.target + "'" : String(intent.target)) + "; pass an instance id from the events manifest or an element inside one."
          );
        }
        return {
          anchor,
          name: intent.name,
          intentSequence: nextCallIntent(),
          args: intent.args,
          opts: intent.opts
        };
      });
      return sendAll(entries);
    };
    var eventTargetsInstance = function(target, componentId) {
      var el = target && target.nodeType === 1 ? target : null;
      var root = el && el.closest ? el.closest("[data-cid]") : null;
      return Boolean(root && root.hasAttribute("data-cid-" + componentId));
    };
    var subscribeForAnchor = function(anchor, name, fn) {
      var handler4 = function(e) {
        if (anchor.componentId == null) return;
        if (eventTargetsInstance(e.target, anchor.componentId)) fn(e.detail);
      };
      document.addEventListener(name, handler4);
      return function() {
        document.removeEventListener(name, handler4);
      };
    };
    var subscribeForId = function(componentId, name, fn) {
      var anchor = idToAnchor.get(componentId);
      if (anchor) return subscribeForAnchor(anchor, name, fn);
      var handler4 = function(e) {
        if (eventTargetsInstance(e.target, componentId)) fn(e.detail);
      };
      document.addEventListener(name, handler4);
      return function() {
        document.removeEventListener(name, handler4);
      };
    };
    var fireLifecycle = function(type, anchor, eventName, extra, cancelable) {
      var detail = {
        instance: anchor ? anchor.componentId : null,
        class: anchor ? anchor.classId : null,
        event: eventName
      };
      Object.keys(extra).forEach(function(key) {
        detail[key] = extra[key];
      });
      var target = null;
      if (anchor && anchor.componentId != null) {
        target = document.querySelector("[data-cid-" + anchor.componentId + "]");
      }
      return (target || document).dispatchEvent(
        new CustomEvent(type, { detail, bubbles: true, cancelable: cancelable === true })
      );
    };
    var fireStale = function(anchor, eventName, reason) {
      fireLifecycle("citry:events:stale", anchor, eventName, { reason });
    };
    var sweepRetiredAnchors = function() {
      anchorSweepScheduled = false;
      var entries = [];
      idToAnchor.forEach(function(anchor, componentId) {
        entries.push([componentId, anchor]);
      });
      entries.forEach(function(entry) {
        var componentId = entry[0];
        var anchor = entry[1];
        if (anchor.clientAnchor && globalThis.Citry?.manager?.ownership) {
          if (globalThis.Citry.manager.ownership._isLive(anchor.clientAnchor)) return;
          if (anchor.componentId === componentId) retireAnchor(anchor);
          else idToAnchor.delete(componentId);
          return;
        }
        if (!anchor.seenInDom) return;
        if (document.querySelector("[data-cid-" + componentId + "]")) return;
        if (anchor.componentId === componentId) retireAnchor(anchor);
        else idToAnchor.delete(componentId);
      });
    };
    var anchorSweepScheduled = false;
    var scheduleAnchorSweep = function() {
      if (anchorSweepScheduled) return;
      anchorSweepScheduled = true;
      Promise.resolve().then(sweepRetiredAnchors);
    };
    var retireDepartedIds = function(departed) {
      departed.forEach(function(componentId) {
        if (document.querySelector("[data-cid-" + componentId + "]")) return;
        var anchor = idToAnchor.get(componentId);
        if (!anchor) return;
        if (anchor.clientAnchor && globalThis.Citry?.manager?.ownership?._isLive(anchor.clientAnchor)) {
          return;
        }
        if (anchor.componentId === componentId) retireAnchor(anchor);
        else idToAnchor.delete(componentId);
      });
    };
    var elementIntervals = /* @__PURE__ */ new WeakMap();
    var registerAnchorInterval = function(anchor, intervalId) {
      anchor.timers.add(intervalId);
    };
    var registerElementInterval = function(el, key, intervalId) {
      var slots = elementIntervals.get(el);
      if (!slots) {
        slots = /* @__PURE__ */ new Map();
        elementIntervals.set(el, slots);
      }
      var existing = slots.get(key);
      if (existing != null && existing !== intervalId) clearInterval(existing);
      slots.set(key, intervalId);
    };
    var unsentDrafts = /* @__PURE__ */ new WeakSet();
    var decodeBindSpecs = function(el) {
      return decodeCevSpecs(el, DATA_CEV_BIND);
    };
    var isTwoWayBound = function(el) {
      return decodeBindSpecs(el).some(function(spec) {
        return spec != null && spec.mode === "two";
      });
    };
    var anchorForElement = function(el) {
      var id = innermostComponentId(el);
      return id && idToAnchor.get(id) || null;
    };
    var hasUnsentDraft = function(el) {
      if (unsentDrafts.has(el)) return true;
      var anchor = anchorForElement(el);
      if (!anchor) return false;
      return decodeBindSpecs(el).some(function(spec) {
        return spec != null && spec.mode === "two" && typeof spec.field === "string" && Object.prototype.hasOwnProperty.call(anchor.pending, spec.field);
      });
    };
    var keepLiveValue = function(el, toEl, guardKept) {
      var live = el;
      var incoming = toEl;
      if (live.type === "checkbox" || live.type === "radio") {
        incoming.checked = live.checked;
        if (live.checked) incoming.setAttribute("checked", "");
        else incoming.removeAttribute("checked");
      } else if (typeof live.value === "string") {
        incoming.value = live.value;
        incoming.setAttribute("value", live.value);
      }
      guardKept.add(el);
    };
    var morphKeyCallback = function(el) {
      return el.getAttribute && el.getAttribute("data-citry-key");
    };
    var makeUpdatingHook = function(guardKept) {
      return function(el, toEl, childrenOnly, skip) {
        if (el.nodeType !== 1) return;
        var element = el;
        if (element.getAttribute("data-citry-morph") === "ignore") {
          if (element.hasAttribute("data-cid")) {
            console.warn(
              '[Citry] events: #c-ignore (data-citry-morph="ignore") on a component instance root is unsupported and was not applied; move it onto an element below the root, or onto a wrapper.'
            );
          } else {
            return skip();
          }
        }
        if (element === document.activeElement && isTwoWayBound(element) && hasUnsentDraft(element)) {
          keepLiveValue(element, toEl, guardKept);
        }
      };
    };
    var captureFocus = function(targets) {
      var active = document.activeElement;
      if (!(active instanceof HTMLElement)) return null;
      if (!targets.some((target) => target === active || target.contains(active))) return null;
      if (active instanceof HTMLInputElement || active instanceof HTMLTextAreaElement) {
        return [active, active.selectionStart, active.selectionEnd];
      }
      return [active];
    };
    var restoreFocus = function(snapshot) {
      if (!snapshot || !snapshot[0].isConnected || document.activeElement === snapshot[0]) return;
      if (document.activeElement !== document.body && document.activeElement !== document.documentElement) return;
      var element = snapshot[0];
      element.focus({ preventScroll: true });
      if (document.activeElement === element && snapshot[1] != null && snapshot[2] != null && (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement)) {
        element.setSelectionRange(snapshot[1], snapshot[2]);
      }
    };
    var applyValueToControl = function(el, value) {
      var control = el;
      var nextChecked;
      var next;
      if (control.type === "checkbox" || control.type === "radio") {
        nextChecked = Boolean(value);
        if (control.checked !== nextChecked) control.checked = nextChecked;
      } else if (typeof control.value === "string") {
        next = value == null ? "" : String(value);
        if (control.value !== next) control.value = next;
      }
    };
    var reapplyBoundControls = function(roots, guardKept) {
      var seen = /* @__PURE__ */ new Set();
      roots.forEach(function(root) {
        var els = [];
        if (root.hasAttribute("data-cev-bind")) els.push(root);
        root.querySelectorAll("[data-cev-bind]").forEach(function(el) {
          els.push(el);
        });
        els.forEach(function(el) {
          if (seen.has(el) || guardKept.has(el)) return;
          seen.add(el);
          var anchor = anchorForElement(el);
          if (!anchor || !anchor.values) return;
          decodeBindSpecs(el).forEach(function(spec) {
            if (spec == null || typeof spec.field !== "string") return;
            if (!Object.prototype.hasOwnProperty.call(anchor.values, spec.field)) return;
            applyValueToControl(el, anchor.values[spec.field]);
          });
        });
      });
    };
    var restampBusy = function(linkedAnchors) {
      linkedAnchors.forEach(function(anchor) {
        if (anchor.loading.any <= 0 || anchor.componentId == null) return;
        document.querySelectorAll("[data-cid-" + anchor.componentId + "]").forEach(function(el) {
          el.setAttribute("data-citry-busy", "");
        });
        anchor.busyTriggers.forEach(function(el) {
          if (el.isConnected) el.setAttribute("data-citry-busy", "");
        });
      });
    };
    var GRAPH_MANIFEST_SELECTOR = 'script[type="application/json"][data-citry-graph]';
    var DEPENDENCY_MANIFEST_SELECTOR = 'script[type="application/json"][data-citry]';
    var parseFragment = function(html) {
      var template = document.createElement("template");
      template.innerHTML = html;
      var content = [];
      var roots = [];
      var tags = [];
      var graphTag = null;
      var eventsTag = null;
      var dependencyTag = null;
      var graphRevision = null;
      Array.prototype.slice.call(template.content.childNodes).forEach(function(node) {
        var el = node.nodeType === 1 ? node : null;
        if (el && el.tagName === "SCRIPT") {
          if (el.matches(GRAPH_MANIFEST_SELECTOR)) {
            if (graphTag) throw new TypeError("a render fragment carries more than one ownership graph manifest");
            graphTag = el;
            const graph = JSON.parse(el.textContent);
            if (typeof graph.revision !== "string") throw new TypeError("an ownership graph manifest has no revision");
            graphRevision = graph.revision;
          } else if (el.matches(EVENTS_MANIFEST_SELECTOR)) {
            if (eventsTag) throw new TypeError("a render fragment carries more than one Events manifest");
            eventsTag = el;
          } else if (el.matches(DEPENDENCY_MANIFEST_SELECTOR)) {
            if (dependencyTag) throw new TypeError("a render fragment carries more than one dependency manifest");
            dependencyTag = el;
          }
          tags.push(el);
          return;
        }
        if (el) roots.push(el);
        content.push(node);
      });
      return {
        fragment: template.content,
        content,
        roots,
        tags,
        graphTag,
        eventsTag,
        dependencyTag,
        graphRevision
      };
    };
    var readFragmentMetas = function(parsed) {
      var metas = /* @__PURE__ */ new Map();
      if (!parsed.eventsTag) return { manifest: null, staged: null, metas };
      var manifest = JSON.parse(parsed.eventsTag.textContent);
      var staged = stageEventsManifest(manifest);
      staged.instances.forEach(function(meta) {
        metas.set(meta.componentId, {
          componentId: meta.componentId,
          classId: meta.classId,
          token: meta.token || void 0,
          values: meta.values
        });
      });
      return { manifest, staged, metas };
    };
    var fragmentRootMeta = function(parsed, metas) {
      var root = parsed.roots.length ? parsed.roots[0] : null;
      if (!root) return metas.size ? Array.from(metas.values())[0] : null;
      var ids = (root.getAttribute("data-cid") || "").trim().split(/\s+/).filter(Boolean);
      var found = null;
      ids.some(function(id) {
        var meta = metas.get(id);
        if (meta) found = meta;
        return Boolean(meta);
      });
      return found;
    };
    var collectKeyedRoots = function(containers, classOf, exclude) {
      var keyedEls = /* @__PURE__ */ new Map();
      var entries = [];
      var seenInstances = /* @__PURE__ */ new Set();
      var consider = function(el) {
        if (keyedEls.has(el)) return;
        var composite = el.getAttribute("data-citry-key") || "";
        var sep = composite.indexOf(":");
        if (sep <= 0) return;
        var classId = composite.slice(0, sep);
        var ids = (el.getAttribute("data-cid") || "").trim().split(/\s+/).filter(Boolean);
        var instanceId = null;
        ids.some(function(id) {
          if (classOf(id) === classId) instanceId = id;
          return instanceId != null;
        });
        if (instanceId == null || exclude.has(instanceId)) return;
        keyedEls.set(el, instanceId);
        if (seenInstances.has(instanceId)) return;
        seenInstances.add(instanceId);
        entries.push({ el, composite, instanceId });
      };
      containers.forEach(function(container) {
        if (container.hasAttribute("data-citry-key")) consider(container);
        container.querySelectorAll("[data-citry-key]").forEach(consider);
      });
      return entries.filter(function(entry) {
        var p = entry.el.parentElement;
        while (p) {
          if (keyedEls.has(p)) return false;
          p = p.parentElement;
        }
        return true;
      });
    };
    var linkKeyedPair = function(old, fresh, metas, state, newContainers) {
      var anchor = idToAnchor.get(old.instanceId);
      var meta = metas.get(fresh.instanceId);
      var oldEls = Array.prototype.slice.call(document.querySelectorAll("[data-cid-" + old.instanceId + "]"));
      var freshEls = [];
      newContainers.forEach(function(container) {
        if (container.hasAttribute("data-cid-" + fresh.instanceId)) freshEls.push(container);
        container.querySelectorAll("[data-cid-" + fresh.instanceId + "]").forEach(function(el) {
          freshEls.push(el);
        });
      });
      if (!anchor || anchor.componentId !== old.instanceId || !meta) {
        const ownership = globalThis.Citry?.manager?.ownership;
        if (!ownership || !ownership._correspond(old.instanceId, fresh.instanceId)) return;
        state.linkedOldIds.add(old.instanceId);
        state.appliedIds.add(fresh.instanceId);
        matchKeyedRegion(oldEls, freshEls, metas, state);
        return;
      }
      var link = linkRenderedInstance(anchor, meta);
      anchor.highestApplied = anchor.epoch;
      anchor.epochOwner = null;
      state.linkedOldIds.add(old.instanceId);
      state.appliedIds.add(fresh.instanceId);
      state.pendingFinish.push({ anchor, oldComponentId: link.oldComponentId });
      state.linkedAnchors.push(anchor);
      matchKeyedRegion(oldEls, freshEls, metas, state);
    };
    var matchKeyedRegion = function(oldContainers, newContainers, metas, state) {
      var oldRoots = collectKeyedRoots(
        oldContainers,
        function(id) {
          var anchor = idToAnchor.get(id);
          return anchor ? anchor.classId : globalThis.Citry?.manager?.ownership?._classForRender(id) || null;
        },
        state.linkedOldIds
      );
      var newRoots = collectKeyedRoots(
        newContainers,
        function(id) {
          var meta = metas.get(id);
          return meta ? meta.classId : globalThis.Citry?.manager?.ownership?._classForRender(id) || null;
        },
        state.appliedIds
      );
      if (!oldRoots.length || !newRoots.length) return;
      var oldByKey = /* @__PURE__ */ new Map();
      oldRoots.forEach(function(root) {
        var queue2 = oldByKey.get(root.composite);
        if (!queue2) {
          queue2 = [];
          oldByKey.set(root.composite, queue2);
        }
        queue2.push(root);
      });
      var newCounts = /* @__PURE__ */ new Map();
      newRoots.forEach(function(root) {
        newCounts.set(root.composite, (newCounts.get(root.composite) || 0) + 1);
      });
      var dupWarned = /* @__PURE__ */ new Set();
      newRoots.forEach(function(fresh) {
        var queue2 = oldByKey.get(fresh.composite);
        if (!queue2 || !queue2.length) return;
        if ((queue2.length > 1 || (newCounts.get(fresh.composite) || 0) > 1) && !dupWarned.has(fresh.composite)) {
          dupWarned.add(fresh.composite);
          console.warn(
            "[Citry] events: duplicate key '" + fresh.composite + "' within one applied region; matched in document order. Component keys must be unique per class within a region (design 5.3)."
          );
        }
        var old = queue2.shift();
        linkKeyedPair(old, fresh, metas, state, newContainers);
      });
    };
    var preserveCallerKey = function(oldEls, caller, freshId, parsed) {
      var oldKey = null;
      oldEls.some(function(el) {
        var value = el.getAttribute("data-citry-key");
        if (value && caller.classId != null && value.indexOf(caller.classId + ":") === 0) oldKey = value;
        return oldKey != null;
      });
      if (oldKey == null) return;
      parsed.roots.forEach(function(root) {
        if (root.hasAttribute("data-cid-" + freshId) && !root.hasAttribute("data-citry-key")) {
          root.setAttribute("data-citry-key", oldKey);
        }
      });
    };
    var childElementsOf = function(els) {
      var children = [];
      els.forEach(function(el) {
        Array.prototype.slice.call(el.children).forEach(function(child) {
          children.push(child);
        });
      });
      return children;
    };
    var groupAdjacentRuns = function(els) {
      var runs = [];
      els.forEach(function(el) {
        var last = runs.length ? runs[runs.length - 1] : null;
        if (last && last[last.length - 1].nextElementSibling === el) last.push(el);
        else runs.push([el]);
      });
      return runs;
    };
    var collectInstanceIds = function(els, includeSelf, out) {
      var record = function(el) {
        (el.getAttribute("data-cid") || "").trim().split(/\s+/).filter(Boolean).forEach(function(id) {
          out.add(id);
        });
      };
      els.forEach(function(el) {
        if (includeSelf && el.hasAttribute("data-cid")) record(el);
        el.querySelectorAll("[data-cid]").forEach(record);
      });
    };
    var OWNERSHIP_COMMENT_PREFIX = "citry:g1";
    var OWNERSHIP_COMMENT_RE = new RegExp(
      "^" + OWNERSHIP_COMMENT_PREFIX + ":([0-9a-f]{64}):(\\d+):([ir]):(\\d+):([se])$"
    );
    var OWNERSHIP_INSTANCE_START_RE = new RegExp("^(" + OWNERSHIP_COMMENT_PREFIX + ":[0-9a-f]{64}:\\d+:i:\\d+):s$");
    var OWNERSHIP_INSTANCE_CAP_RE = new RegExp("^" + OWNERSHIP_COMMENT_PREFIX + ":[0-9a-f]{64}:\\d+:i:\\d+:[se]$");
    var rewritePlacementComment = function(comment, placementId) {
      var match = OWNERSHIP_COMMENT_RE.exec(comment.data.trim());
      if (!match) return;
      comment.data = "citry:p1:" + match[1] + ":" + placementId + ":" + match[2] + ":" + match[3] + ":" + match[4] + ":" + match[5];
    };
    var cloneForPlacement = function(node, placementId) {
      var clone2 = node.cloneNode(true);
      if (placementId == null) return clone2;
      if (clone2 instanceof Comment) rewritePlacementComment(clone2, placementId);
      var walker = document.createTreeWalker(clone2, NodeFilter.SHOW_COMMENT);
      var comment = walker.nextNode();
      while (comment) {
        rewritePlacementComment(comment, placementId);
        comment = walker.nextNode();
      }
      return clone2;
    };
    var graphRangeInnerHtml = function(parsed, placementId) {
      var outerStart = -1;
      var outerEnd = -1;
      var outerKey = "";
      parsed.content.some(function(node, index) {
        if (!(node instanceof Comment)) return false;
        var match = OWNERSHIP_INSTANCE_START_RE.exec(node.data.trim());
        if (!match) return false;
        outerStart = index;
        outerKey = match[1];
        return true;
      });
      if (outerStart >= 0) {
        for (let index = parsed.content.length - 1; index > outerStart; index -= 1) {
          const node = parsed.content[index];
          if (node instanceof Comment && node.data.trim() === outerKey + ":e") {
            outerEnd = index;
            break;
          }
        }
      }
      var holder = document.createElement("template");
      parsed.content.forEach(function(node, index) {
        if (index === outerStart || index === outerEnd) return;
        holder.content.append(cloneForPlacement(node, placementId));
      });
      return holder.innerHTML;
    };
    var replaceRange = function(regionEls, parsed, placementId, stripOuterCaps) {
      var first = regionEls[0];
      var parent = first.parentNode;
      if (!parent) return { roots: [], lastNode: null };
      var liveParent = parent;
      var inserted = [];
      var lastNode = null;
      parsed.content.forEach(function(node) {
        if (stripOuterCaps && node instanceof Comment && OWNERSHIP_INSTANCE_CAP_RE.test(node.data.trim())) {
          return;
        }
        var clone2 = cloneForPlacement(node, placementId);
        liveParent.insertBefore(clone2, first);
        lastNode = clone2;
        if (clone2.nodeType === 1) inserted.push(clone2);
      });
      regionEls.forEach(function(el) {
        el.remove();
      });
      return { roots: inserted, lastNode };
    };
    var insertManifestTags = function(parsed, afterNode) {
      if (!afterNode || !afterNode.parentNode) return;
      var anchorNode = afterNode;
      parsed.tags.forEach(function(tag) {
        if (tag === parsed.graphTag) globalThis.Citry?.manager?.ownership?._claimTag(tag);
        if (tag === parsed.eventsTag) processedEventsManifestTags.add(tag);
        anchorNode.parentNode.insertBefore(tag, anchorNode.nextSibling);
        anchorNode = tag;
      });
    };
    var applyFragmentToRegion = function(regionEls, parsed, swap, state, firstInsertion, placementId, stripOuterCaps) {
      var updating = makeUpdatingHook(state.guardKept);
      var insertedRoots = [];
      var lastNode = null;
      var rangeInsert;
      if (swap === "morph") {
        if (parsed.graphRevision != null && !stripOuterCaps) {
          rangeInsert = replaceRange(regionEls, parsed, placementId, false);
          insertedRoots = rangeInsert.roots;
          lastNode = rangeInsert.lastNode;
        } else if (regionEls.length === parsed.roots.length && parsed.roots.length > 0) {
          regionEls.forEach(function(oldRoot, index) {
            var parent = oldRoot.parentNode;
            var prev = oldRoot.previousSibling;
            alpineRuntime._morph(oldRoot, cloneForPlacement(parsed.roots[index], placementId), {
              key: morphKeyCallback,
              updating
            });
            var landed = prev ? prev.nextSibling : parent ? parent.firstChild : null;
            if (landed && landed.nodeType === 1) insertedRoots.push(landed);
          });
          lastNode = insertedRoots.length ? insertedRoots[insertedRoots.length - 1] : null;
        } else {
          rangeInsert = replaceRange(regionEls, parsed, placementId, stripOuterCaps);
          insertedRoots = rangeInsert.roots;
          lastNode = rangeInsert.lastNode;
        }
      } else if (swap === "replace") {
        rangeInsert = replaceRange(regionEls, parsed, placementId, stripOuterCaps);
        insertedRoots = rangeInsert.roots;
        lastNode = rangeInsert.lastNode;
      } else if (swap === "inner") {
        regionEls.forEach(function(el) {
          while (el.firstChild) el.removeChild(el.firstChild);
          parsed.content.forEach(function(node) {
            var clone2 = cloneForPlacement(node, placementId);
            el.appendChild(clone2);
            if (clone2.nodeType === 1) insertedRoots.push(clone2);
          });
          if (lastNode == null) lastNode = el.lastChild;
        });
      } else if (swap === "append" || swap === "prepend") {
        regionEls.forEach(function(el) {
          var before = swap === "prepend" ? el.firstChild : null;
          var lastClone = null;
          parsed.content.forEach(function(node) {
            var clone2 = cloneForPlacement(node, placementId);
            el.insertBefore(clone2, before);
            lastClone = clone2;
            if (clone2.nodeType === 1) insertedRoots.push(clone2);
          });
          if (lastNode == null) lastNode = lastClone;
        });
      } else {
        console.warn("[Citry] events: unknown swap strategy '" + swap + "'; the render was skipped.");
        return;
      }
      if (firstInsertion) insertManifestTags(parsed, lastNode);
      insertedRoots.forEach(function(el) {
        state.swappedEls.push(el);
      });
    };
    var epochAllowsApply = function(run, targetAnchor) {
      if (run.anchor !== targetAnchor || typeof run.epoch !== "number") return true;
      if (run.epoch > targetAnchor.highestApplied) return true;
      return run.epoch === targetAnchor.highestApplied && targetAnchor.epochOwner === run.token;
    };
    var markEpochApplied = function(run, targetAnchor) {
      if (run.anchor !== targetAnchor || typeof run.epoch !== "number") return;
      targetAnchor.highestApplied = run.epoch;
      targetAnchor.epochOwner = run.token;
    };
    var dropStaleEpoch = function(run, what) {
      if (!run.staleEventFired) {
        run.staleEventFired = true;
        fireStale(run.anchor, run.event, "epoch");
      }
      console.debug(
        "[Citry] events: dropped " + what + " of a stale response (epoch " + run.epoch + ", highest applied " + (run.anchor ? run.anchor.highestApplied : "?") + ")."
      );
    };
    var dropRetired = function(run, what) {
      fireStale(run.anchor, run.event, "retired");
      console.debug("[Citry] events: dropped " + what + " (the instance retired, design 5.5 machinery item 4).");
    };
    var applyStateAction = function(action, run) {
      var instanceId = typeof action.targetRenderId === "string" ? action.targetRenderId : "";
      if (instanceId && !isSafeRenderId(instanceId)) {
        console.warn("[Citry] events: state action carried an unsafe render ID '" + instanceId + "'; skipped.");
        return;
      }
      var anchor;
      if (instanceId && run.anchor != null && (run.instance === instanceId || run.anchor.componentId === instanceId)) {
        anchor = run.anchor;
      } else {
        anchor = instanceId ? idToAnchor.get(instanceId) || null : null;
      }
      if (!anchor || anchor.componentId == null) {
        dropRetired(run, "a state token refresh for instance '" + instanceId + "'");
        return;
      }
      if (!epochAllowsApply(run, anchor)) {
        dropStaleEpoch(run, "a state token refresh");
        return;
      }
      if (typeof action.stateToken === "string" && action.stateToken) anchor.token = action.stateToken;
      markEpochApplied(run, anchor);
    };
    var applyEventAction = function(action, run) {
      var name = typeof action.eventName === "string" ? action.eventName : "";
      if (!name) {
        console.warn("[Citry] events: an event action carried no name; skipped.");
        return;
      }
      var makeEvent = function() {
        return new CustomEvent(name, { detail: action.detail, bubbles: true });
      };
      var targetSpec = typeof action.target === "string" ? action.target : "";
      var id;
      var root;
      if (!targetSpec) {
        document.dispatchEvent(makeEvent());
        return;
      }
      if (targetSpec.indexOf("render:") === 0) {
        id = targetSpec.slice(7);
        if (!isSafeRenderId(id)) {
          console.warn("[Citry] events: event action carried an unsafe render ID '" + id + "'; skipped.");
          return;
        }
        if (run.anchor != null && (run.instance === id || run.anchor.componentId === id)) {
          if (run.anchor.componentId == null) {
            dropRetired(run, "an event dispatch ('" + name + "') for instance '" + id + "'");
            return;
          }
          id = run.anchor.componentId;
        }
        root = document.querySelector("[data-cid-" + id + "]");
        if (!root) {
          dropRetired(run, "an event dispatch ('" + name + "') for instance '" + id + "'");
          return;
        }
        root.dispatchEvent(makeEvent());
        return;
      }
      var els = queryTargets(targetSpec);
      if (els == null) return;
      if (!els.length) {
        console.warn("[Citry] events: event target '" + targetSpec + "' matched nothing; the dispatch was skipped.");
        return;
      }
      els.forEach(function(el) {
        el.dispatchEvent(makeEvent());
      });
    };
    var queryTargets = function(selector) {
      try {
        return Array.prototype.slice.call(document.querySelectorAll(selector));
      } catch (err) {
        console.warn("[Citry] events: invalid target selector '" + selector + "':", err);
        return null;
      }
    };
    var applyRenderAction = function(action, run) {
      var targetSpec = typeof action.target === "string" ? action.target : "";
      var swap = typeof action.swap === "string" && action.swap ? action.swap : "morph";
      if (!targetSpec) {
        console.warn("[Citry] events: a render action carried no target; skipped.");
        return;
      }
      var isInstanceTarget = targetSpec.indexOf("render:") === 0;
      var targetEls;
      var targetAnchor = null;
      var rootlessInstanceTarget = false;
      var targetId;
      var liveTargetId;
      var matched;
      var removed;
      var caller;
      var callerMeta;
      var callerLink;
      if (isInstanceTarget) {
        targetId = targetSpec.slice(7);
        if (!isSafeRenderId(targetId)) {
          console.warn("[Citry] events: render action carried an unsafe cid render ID '" + targetId + "'; skipped.");
          return;
        }
        if (run.anchor != null && (run.instance === targetId || run.anchor.componentId === targetId)) {
          targetAnchor = run.anchor;
        } else {
          targetAnchor = idToAnchor.get(targetId) || null;
        }
        liveTargetId = targetAnchor != null ? targetAnchor.componentId : targetId;
        targetEls = liveTargetId == null ? [] : Array.prototype.slice.call(document.querySelectorAll("[data-cid-" + liveTargetId + "]"));
        if (!targetEls.length) {
          const targetOwnership = globalThis.Citry?.manager?.ownership;
          if (targetAnchor?.clientAnchor && targetOwnership?._hasPlacements(targetAnchor.clientAnchor)) {
            rootlessInstanceTarget = true;
          } else {
            dropRetired(run, "a render for instance '" + targetId + "'");
            return;
          }
        }
      } else {
        matched = queryTargets(targetSpec);
        if (matched == null) return;
        if (!matched.length) {
          console.warn("[Citry] events: render target '" + targetSpec + "' matched nothing; the action was skipped.");
          return;
        }
        targetEls = matched;
      }
      var selfRender = run.anchor != null && targetAnchor === run.anchor;
      if (swap === "none") {
        if (selfRender) {
          if (!epochAllowsApply(run, run.anchor)) {
            dropStaleEpoch(run, "a self-render");
            return;
          }
          markEpochApplied(run, run.anchor);
        }
        return;
      }
      if (swap === "remove") {
        if (selfRender) {
          if (!epochAllowsApply(run, run.anchor)) {
            dropStaleEpoch(run, "a self-render");
            return;
          }
          markEpochApplied(run, run.anchor);
        }
        removed = /* @__PURE__ */ new Set();
        collectInstanceIds(targetEls, true, removed);
        targetEls.forEach(function(el) {
          el.remove();
        });
        retireDepartedIds(removed);
        fireLifecycle("citry:events:swapped", run.anchor, run.event, { els: [] });
        scheduleAnchorSweep();
        return;
      }
      if (selfRender && !epochAllowsApply(run, run.anchor)) {
        dropStaleEpoch(run, "a self-render");
        return;
      }
      var parsed = parseFragment(typeof action.html === "string" ? action.html : "");
      var ownership = globalThis.Citry?.manager?.ownership;
      var ownershipTransaction = null;
      var adoptionRoot = null;
      var dependencyManifest = null;
      var priorClasses = [];
      var priorErrorBoxes = [];
      var fragmentEvents;
      try {
        if (parsed.graphTag) {
          if (!ownership) throw new Error("the ownership graph registry is unavailable");
          ownershipTransaction = ownership._prepareAdoption(
            JSON.parse(parsed.graphTag.textContent),
            parsed.fragment
          );
          adoptionRoot = ownership._adoptionRoot(ownershipTransaction);
        }
        fragmentEvents = readFragmentMetas(parsed);
        if (parsed.graphRevision != null) {
          if (fragmentEvents.manifest && fragmentEvents.manifest.clientGraphRevision !== parsed.graphRevision) {
            throw new TypeError("a graph-backed Events manifest must link to the same ownership revision");
          }
          if (fragmentEvents.staged) {
            ownership._preflightEvents(parsed.graphRevision, fragmentEvents.staged.instances);
          }
        } else if (fragmentEvents.manifest?.clientGraphRevision) {
          throw new TypeError("an Events manifest refers to an ownership graph absent from the render fragment");
        }
        if (parsed.dependencyTag) {
          const dependency = JSON.parse(parsed.dependencyTag.textContent);
          dependencyManifest = dependency;
          if (parsed.graphRevision != null && dependency.graph !== parsed.graphRevision) {
            throw new TypeError("a dependency manifest is not linked to the render fragment's ownership revision");
          }
          if (parsed.graphRevision == null && dependency.graph != null) {
            throw new TypeError("a dependency manifest refers to an ownership graph absent from the render fragment");
          }
          if (parsed.graphRevision != null) {
            dependencyManifest = ownership._preflightDependency(dependency, parsed.graphRevision);
          }
        }
      } catch (err) {
        if (ownershipTransaction && ownership) ownership._abortAdoption(ownershipTransaction, err);
        else if (parsed.graphRevision && ownership) ownership._rejectAdoption(parsed.graphRevision, err);
        throw err;
      }
      try {
        if (selfRender) {
          if (!epochAllowsApply(run, run.anchor)) {
            if (ownershipTransaction && ownership) {
              ownership._abortAdoption(
                ownershipTransaction,
                new Error("the incoming render became stale before adoption")
              );
            }
            dropStaleEpoch(run, "a self-render");
            return;
          }
          markEpochApplied(run, run.anchor);
        }
        const metas = fragmentEvents.metas;
        if (fragmentEvents.staged) {
          const stagedClassIds = /* @__PURE__ */ new Set();
          fragmentEvents.staged.classes.forEach(function(entry) {
            priorClasses.push({ classId: entry[0], had: classes.has(entry[0]), descriptor: classes.get(entry[0]) });
            stagedClassIds.add(entry[0]);
          });
          priorErrorBoxes = snapshotErrorBoxesForClasses(stagedClassIds);
          installClassDescriptors(fragmentEvents.staged.classes);
        }
        const state = {
          appliedIds: /* @__PURE__ */ new Set(),
          linkedOldIds: /* @__PURE__ */ new Set(),
          pendingFinish: [],
          linkedAnchors: [],
          guardKept: /* @__PURE__ */ new Set(),
          departedIds: /* @__PURE__ */ new Set(),
          swappedEls: []
        };
        const focusSnapshot = captureFocus(targetEls);
        const graphTargetRegions = isInstanceTarget && !rootlessInstanceTarget && ownership && targetAnchor?.clientAnchor ? ownership._placementRoots(targetAnchor.clientAnchor) : null;
        if (selfRender && (swap === "morph" || swap === "replace")) {
          caller = run.anchor;
          callerMeta = fragmentRootMeta(parsed, metas);
          if (caller.componentId != null) state.linkedOldIds.add(caller.componentId);
          if (callerMeta) state.appliedIds.add(callerMeta.componentId);
          if (!callerMeta && adoptionRoot && caller.clientAnchor && ownership) {
            if (adoptionRoot.classId === caller.classId) {
              preserveCallerKey(targetEls, caller, adoptionRoot.componentId, parsed);
            }
            const oldComponentId = caller.componentId;
            ownership._transitionEvents(caller.clientAnchor, adoptionRoot.componentId, adoptionRoot.classId);
            retireAnchor(caller, true);
            callerLink = { branch: "general-only", oldComponentId };
          } else {
            callerLink = linkRenderedInstance(caller, callerMeta);
          }
          if (callerLink.branch === "reconcile" || callerLink.branch === "adopt") {
            state.pendingFinish.push({ anchor: caller, oldComponentId: callerLink.oldComponentId });
            state.linkedAnchors.push(caller);
          }
          if (callerLink.branch === "reconcile" && callerMeta != null) {
            preserveCallerKey(targetEls, caller, callerMeta.componentId, parsed);
          }
        }
        const regions = rootlessInstanceTarget ? ownership && targetAnchor?.clientAnchor ? ownership._placementIds(targetAnchor.clientAnchor).map(function() {
          return [];
        }) : [] : isInstanceTarget ? graphTargetRegions ? graphTargetRegions : groupAdjacentRuns(targetEls) : targetEls.map(function(el) {
          return [el];
        });
        regions.forEach(function(regionEls) {
          if (swap === "inner") collectInstanceIds(regionEls, false, state.departedIds);
          else if (swap === "morph" || swap === "replace") collectInstanceIds(regionEls, true, state.departedIds);
          if (rootlessInstanceTarget && liveTargetId != null && (swap === "morph" || swap === "replace")) {
            state.departedIds.add(liveTargetId);
          }
          if (swap === "morph" || swap === "replace" || swap === "inner") {
            matchKeyedRegion(swap === "inner" ? childElementsOf(regionEls) : regionEls, parsed.roots, metas, state);
          }
        });
        if (ownershipTransaction && ownership) {
          ownership._expectRetirement(Array.from(state.departedIds));
        }
        metas.forEach(function(meta, componentId) {
          if (state.appliedIds.has(componentId) || idToAnchor.has(componentId)) return;
          createAnchor(componentId, meta.classId, meta.token || "", meta.values || {});
          state.appliedIds.add(componentId);
        });
        if (parsed.graphRevision != null && fragmentEvents.staged && ownership) {
          const liveOwnership = ownership;
          fragmentEvents.staged.instances.forEach(function(meta) {
            var eventsAnchor = idToAnchor.get(meta.componentId);
            if (!eventsAnchor) throw new TypeError("a staged Events instance has no prepared anchor");
            eventsAnchor.clientAnchor = liveOwnership._attachEvents(
              parsed.graphRevision,
              meta.componentId,
              meta.classId,
              eventsAnchor
            );
          });
        }
        if (ownershipTransaction && ownership) ownership._activateAdoption(ownershipTransaction);
        const placementIds = [];
        if (parsed.graphRevision != null && ownership) {
          const placementOwnership = ownership;
          const existingPlacements = isInstanceTarget && targetAnchor?.clientAnchor ? placementOwnership._placementIds(targetAnchor.clientAnchor) : [];
          regions.forEach(function(_region, index) {
            placementIds.push(existingPlacements[index] ?? (index === 0 ? null : placementOwnership._mintPlacement()));
          });
        } else {
          regions.forEach(function() {
            placementIds.push(null);
          });
        }
        regions.forEach(function(regionEls, index) {
          var stripOuterCaps = parsed.graphRevision != null && isInstanceTarget && (swap === "morph" || swap === "replace");
          if (rootlessInstanceTarget && ownership && targetAnchor?.clientAnchor) {
            const physical = ownership._morphPlacement(
              targetAnchor.clientAnchor,
              index,
              graphRangeInnerHtml(parsed, placementIds[index])
            );
            if (index === 0) insertManifestTags(parsed, physical.end);
            return;
          }
          applyFragmentToRegion(regionEls, parsed, swap, state, index === 0, placementIds[index], stripOuterCaps);
        });
        let adoptionReady = Promise.resolve();
        if (ownershipTransaction && ownership) {
          ownership._commitAdoption(ownershipTransaction);
          consumedOwnershipRevisions.add(parsed.graphRevision);
          if (parsed.dependencyTag && dependencyManifest) {
            adoptionReady = ownership._applyDependency(ownershipTransaction, dependencyManifest, parsed.dependencyTag);
          }
        }
        state.pendingFinish.forEach(function(pending) {
          finishRender(pending.anchor, pending.oldComponentId);
        });
        retireDepartedIds(state.departedIds);
        reapplyBoundControls(state.swappedEls, state.guardKept);
        restampBusy(state.linkedAnchors);
        restoreFocus(focusSnapshot);
        if (fragmentEvents.staged) {
          const committedClassIds = /* @__PURE__ */ new Set();
          fragmentEvents.staged.classes.forEach(function(entry) {
            committedClassIds.add(entry[0]);
          });
          refreshAnchorsForClasses(committedClassIds, true);
        }
        fireLifecycle("citry:events:swapped", run.anchor, run.event, { els: state.swappedEls.slice() });
        scheduleAnchorSweep();
        return adoptionReady;
      } catch (err) {
        const restoredClassIds = /* @__PURE__ */ new Set();
        priorClasses.forEach(function(entry) {
          if (entry.had) classes.set(entry.classId, entry.descriptor);
          else classes.delete(entry.classId);
          restoredClassIds.add(entry.classId);
        });
        refreshAnchorsForClasses(restoredClassIds);
        restoreErrorBoxes(priorErrorBoxes);
        if (ownershipTransaction && ownership) ownership._abortAdoption(ownershipTransaction, err);
        parsed.tags.forEach(function(tag) {
          ownership?._claimTag(tag);
          if (tag.isConnected) tag.remove();
        });
        if (fragmentEvents?.staged) {
          fragmentEvents.staged.instances.forEach(function(meta) {
            var failedAnchor = idToAnchor.get(meta.componentId);
            if (failedAnchor && failedAnchor !== run.anchor) retireAnchor(failedAnchor);
          });
        }
        if (selfRender && run.anchor && run.anchor.componentId != null) retireAnchor(run.anchor);
        targetEls.forEach(function(element) {
          if (element.isConnected) element.remove();
        });
        scheduleAnchorSweep();
        throw err;
      }
    };
    var applyUrlAction = function(action) {
      var url = typeof action.url === "string" ? action.url : "";
      if (!url || action.mode !== "push" && action.mode !== "replace") {
        console.warn(
          "[Citry] events: invalid url action skipped; expected a non-empty url and mode 'push' or 'replace'."
        );
        return;
      }
      try {
        if (action.mode === "replace") history.replaceState(history.state, "", url);
        else history.pushState(history.state, "", url);
      } catch (err) {
        console.warn("[Citry] events: could not apply a url action for '" + url + "':", err);
      }
    };
    var applyOneAction = function(action, run) {
      var kind = action.action;
      if (kind === "render") return applyRenderAction(action, run);
      else if (kind === "data") {
        if (run.onData) run.onData(action.value);
      } else if (kind === "state") applyStateAction(action, run);
      else if (kind === "event") applyEventAction(action, run);
      else if (kind === "redirect") {
        if (typeof action.url === "string" && action.url) window.location.assign(action.url);
      } else if (kind === "url") applyUrlAction(action);
      else {
        throw new TypeError("events action reached application without citry-events/1 validation");
      }
    };
    var applyActionsList = function(actions, run) {
      var hoisted = /* @__PURE__ */ new Set();
      actions.forEach(function(action, index) {
        if (action != null && action.action === "state" && !(typeof action.delay === "number" && action.delay > 0) && action.wait !== false) {
          applyStateAction(action, run);
          hoisted.add(index);
        }
      });
      var chain = Promise.resolve();
      actions.forEach(function(action, index) {
        if (action == null || typeof action !== "object" || hoisted.has(index)) return;
        var delayMs = typeof action.delay === "number" && action.delay > 0 ? action.delay * 1e3 : 0;
        if (action.wait === false) {
          setTimeout(function() {
            try {
              Promise.resolve(applyOneAction(action, run)).catch(function(err) {
                console.error("[Citry] events: applying a scheduled action failed:", err);
              });
            } catch (err) {
              console.error("[Citry] events: applying a scheduled action failed:", err);
            }
          }, delayMs);
          return;
        }
        chain = chain.then(function() {
          if (!delayMs) {
            return applyOneAction(action, run);
          }
          return new Promise(function(resolve) {
            setTimeout(resolve, delayMs);
          }).then(function() {
            return applyOneAction(action, run);
          });
        });
      });
      return chain;
    };
    var applyResult = function(result, ctx) {
      if (!result || result.ok !== true || !Array.isArray(result.actions)) return Promise.resolve();
      var run = {
        anchor: ctx && ctx.anchor || null,
        instance: ctx && ctx.instance || null,
        event: ctx && ctx.event || null,
        onData: ctx && ctx.onData || null,
        epoch: result && typeof result.sendSequence === "number" ? result.sendSequence : null,
        token: {},
        staleEventFired: false
      };
      return applyActionsList(result.actions, run);
    };
    var applyEnvelope = function(results, ctxs) {
      var chain = Promise.resolve();
      (Array.isArray(results) ? results : []).forEach(function(result, index) {
        chain = chain.then(function() {
          return applyResult(result, ctxs ? ctxs[index] : null);
        });
      });
      return chain;
    };
    alpineRuntime._magic("state", function(el) {
      var anchor = resolveAnchor(el, "state");
      return anchor ? anchor.stateProxy : INERT_STATE;
    });
    alpineRuntime._magic("loading", function(el) {
      var anchor = resolveAnchor(el, "loading");
      if (!anchor)
        return function() {
          return false;
        };
      return function(name) {
        return readLoading(anchor, name, "$loading");
      };
    });
    alpineRuntime._magic("error", function(el) {
      var anchor = resolveAnchor(el, "error");
      if (!anchor)
        return function() {
          return null;
        };
      return function(name) {
        return readError(anchor, name, "$error");
      };
    });
    alpineRuntime._magic("sendEvent", function(el) {
      var anchor = resolveAnchor(el, "sendEvent");
      if (!anchor) {
        return function(name) {
          return Promise.reject(
            pointedError(
              "this element's component instance is not registered (a re-render may be mid-flight); $sendEvent('" + name + "') was not sent."
            )
          );
        };
      }
      var dispatchingEl = el && el.nodeType === 1 ? el : null;
      var projectedOwner = projectedComponentId(dispatchingEl);
      return function(name, args, opts) {
        var promise;
        if (projectedOwner !== void 0) {
          if (projectedOwner === null) {
            return Promise.reject(pointedError("$sendEvent cannot send because its fill has no live lexical source."));
          }
          promise = sendSourceOwned(projectedOwner, name, args || null, opts, dispatchingEl, function() {
            return projectedComponentId(dispatchingEl) === projectedOwner;
          });
          return promise || Promise.reject(pointedError("$sendEvent source retired before the call could be queued."));
        }
        return sendFromAnchor(anchor, name, args, opts, dispatchingEl);
      };
    });
    alpineRuntime._magic("onEvent", function(el) {
      var anchor = resolveAnchor(el, "onEvent");
      if (!anchor)
        return function() {
          return function() {
          };
        };
      return function(name, fn) {
        return subscribeForAnchor(anchor, name, fn);
      };
    });
    var DATA_CEV_ON = "data-cev-on";
    var DATA_CEV_POLL = "data-cev-poll";
    var DATA_CEV_BIND = "data-cev-bind";
    var cevSpecCache = /* @__PURE__ */ new WeakMap();
    var decodeCevSpecs = function(el, attrName) {
      var raw2 = el.getAttribute(attrName);
      var parsed;
      if (!raw2) return [];
      var perAttr = cevSpecCache.get(el);
      if (!perAttr) {
        perAttr = /* @__PURE__ */ new Map();
        cevSpecCache.set(el, perAttr);
      }
      var cached = perAttr.get(attrName);
      if (cached && cached.raw === raw2) return cached.specs;
      var specs = [];
      try {
        parsed = JSON.parse(fromBase64(raw2));
        if (Array.isArray(parsed)) specs = parsed;
      } catch (err) {
        console.error("[Citry] events: failed to decode a " + attrName + " spec:", err);
      }
      perAttr.set(attrName, { raw: raw2, specs });
      return specs;
    };
    var evaluateBindingArgs = function(el, bindingName, handler4, expression, event) {
      var scope2 = {};
      var got;
      if (event) scope2.$event = event;
      var result = src_default.evaluate(el, "(" + expression + ")", { scope: scope2 });
      if (result == null || typeof result !== "object" || Array.isArray(result)) {
        got = result === null ? "null" : result === void 0 ? "undefined" : Array.isArray(result) ? "an array" : "a " + typeof result;
        throw pointedError(
          "the argument expression of the '" + bindingName + "' binding for handler '" + handler4 + "' must evaluate to an object (its keys become the event's args); got " + got + ": (" + expression + ")"
        );
      }
      return result;
    };
    var bindingTimingMs = function(spec, field) {
      var own = spec[field];
      if (typeof own === "number" && Number.isFinite(own) && own > 0) return own;
      var descriptor = typeof spec.cid === "string" ? classes.get(spec.cid) : void 0;
      var options = descriptor && descriptor.eventHandlers && typeof spec.handler === "string" ? descriptor.eventHandlers[spec.handler] : void 0;
      var fallback = options ? field === "debounce" ? options.debounceMilliseconds : options.throttleMilliseconds : void 0;
      if (typeof fallback === "number" && Number.isFinite(fallback) && fallback > 0) return fallback;
      return null;
    };
    var bindingTiming = /* @__PURE__ */ new WeakMap();
    var onceExhausted = /* @__PURE__ */ new WeakMap();
    var timingStateFor = function(el, key) {
      var perEl = bindingTiming.get(el);
      if (!perEl) {
        perEl = /* @__PURE__ */ new Map();
        bindingTiming.set(el, perEl);
      }
      var state = perEl.get(key);
      if (!state) {
        state = { debounceTimer: 0, throttleUntil: 0 };
        perEl.set(key, state);
      }
      return state;
    };
    var fireEventBinding = function(el, spec, event) {
      var handler4 = typeof spec.handler === "string" ? spec.handler : "";
      if (!handler4) return;
      var args = null;
      if (el.isConnected && typeof spec.args === "string" && spec.args) {
        args = evaluateBindingArgs(el, "@c-" + (spec.event || ""), handler4, spec.args, event);
      }
      args = mergeSubmitFormArgs(el, event, args);
      var promise = sendFromElement(el, handler4, args, void 0);
      if (promise) promise.then(null, function() {
      });
    };
    var scheduleEventBinding = function(el, spec, key, event) {
      var debounceMs = bindingTimingMs(spec, "debounce");
      var throttleMs = bindingTimingMs(spec, "throttle");
      if (debounceMs == null && throttleMs == null) {
        fireEventBinding(el, spec, event);
        return;
      }
      var state = timingStateFor(el, key);
      var now = Date.now();
      if (throttleMs != null) {
        if (state.throttleUntil > now) return;
        state.throttleUntil = now + throttleMs;
      }
      if (debounceMs == null) {
        fireEventBinding(el, spec, event);
        return;
      }
      if (state.debounceTimer) window.clearTimeout(state.debounceTimer);
      state.debounceTimer = window.setTimeout(function() {
        state.debounceTimer = 0;
        fireEventBinding(el, spec, event);
      }, debounceMs);
    };
    var NON_BUBBLING_EVENTS = {
      focus: true,
      blur: true,
      mouseenter: true,
      mouseleave: true,
      pointerenter: true,
      pointerleave: true,
      scroll: true
    };
    var KEY_FILTER_VALUES = { enter: "Enter", escape: "Escape" };
    var keyFilterMatches = function(event, filter) {
      var expected = KEY_FILTER_VALUES[filter];
      if (!expected) return false;
      return event.key === expected;
    };
    var runElementEventBindings = function(el, event, type) {
      var stopped = false;
      decodeCevSpecs(el, DATA_CEV_ON).forEach(function(spec, index) {
        var fired;
        if (spec == null || typeof spec !== "object" || spec.event !== type) return;
        if (typeof spec.key === "string" && spec.key && !keyFilterMatches(event, spec.key)) return;
        if (spec.self === true && event.target !== el) return;
        var key = type + ":" + index;
        if (spec.once === true) {
          fired = onceExhausted.get(el);
          if (fired && fired.has(key)) return;
          if (!fired) {
            fired = /* @__PURE__ */ new Set();
            onceExhausted.set(el, fired);
          }
          fired.add(key);
        }
        if (spec.prevent === true) event.preventDefault();
        if (spec.stop === true) {
          event.stopPropagation();
          stopped = true;
        }
        scheduleEventBinding(el, spec, key, event);
      });
      return stopped;
    };
    var DELEGATED_SELECTOR = "[" + DATA_CEV_ON + "],[" + DATA_CEV_BIND + "]";
    var runElementBindings = function(el, event, type) {
      var stopped = false;
      if (el.hasAttribute(DATA_CEV_ON)) stopped = runElementEventBindings(el, event, type);
      if (el.hasAttribute(DATA_CEV_BIND)) runElementStateBindings(el, event, type);
      return stopped;
    };
    var handleDelegatedEvent = function(event) {
      var type = event.type;
      var start2 = event.target && event.target.nodeType === 1 ? event.target : null;
      if (!start2 || !start2.closest) return;
      var el = start2.closest(DELEGATED_SELECTOR);
      if (NON_BUBBLING_EVENTS[type] === true) {
        if (el === start2) runElementBindings(el, event, type);
        return;
      }
      while (el) {
        if (runElementBindings(el, event, type)) return;
        el = el.parentElement ? el.parentElement.closest(DELEGATED_SELECTOR) : null;
      }
    };
    var installedListenerTypes = /* @__PURE__ */ new Set();
    var installDelegatedListener = function(type) {
      if (installedListenerTypes.has(type)) return;
      installedListenerTypes.add(type);
      document.addEventListener(type, handleDelegatedEvent, NON_BUBBLING_EVENTS[type] === true);
    };
    var polledElements = /* @__PURE__ */ new Set();
    var pollElementSeq = /* @__PURE__ */ new WeakMap();
    var pollSeqCounter = 0;
    var POLL_KEY_PREFIX = "poll:";
    var pollKeySeq = function(el) {
      var seq = pollElementSeq.get(el);
      if (seq == null) {
        pollSeqCounter += 1;
        seq = pollSeqCounter;
        pollElementSeq.set(el, seq);
      }
      return seq;
    };
    var clearPollTimers = function(el, keep) {
      var slots = elementIntervals.get(el);
      var stale = [];
      if (slots) {
        slots.forEach(function(intervalId, key) {
          if (key.indexOf(POLL_KEY_PREFIX) !== 0) return;
          if (keep && keep.has(key)) return;
          window.clearInterval(intervalId);
          stale.push(key);
        });
        stale.forEach(function(key) {
          slots.delete(key);
        });
      }
      if (!keep) polledElements.delete(el);
    };
    var pollTick = function(el, spec, recurringKey) {
      if (!el.isConnected || !el.hasAttribute(DATA_CEV_POLL)) {
        clearPollTimers(el);
        console.debug("[Citry] events: a @c-poll region left the DOM; its timer stopped.");
        return;
      }
      if (document.hidden) return;
      var handler4 = typeof spec.handler === "string" ? spec.handler : "";
      if (!handler4) return;
      var args = null;
      if (typeof spec.args === "string" && spec.args) {
        args = evaluateBindingArgs(el, "@c-poll", handler4, spec.args, null);
      }
      var promise = sendFromElement(el, handler4, args, void 0, recurringKey);
      if (promise) promise.then(null, function() {
      });
    };
    var syncElementPollTimers = function(el) {
      var expected = /* @__PURE__ */ new Map();
      decodeCevSpecs(el, DATA_CEV_POLL).forEach(function(spec, index) {
        if (spec == null || typeof spec !== "object") return;
        if (typeof spec.handler !== "string" || !spec.handler) return;
        if (typeof spec.interval !== "number" || !Number.isFinite(spec.interval) || spec.interval <= 0) return;
        expected.set(POLL_KEY_PREFIX + index + ":" + spec.handler + ":" + spec.interval, spec);
      });
      clearPollTimers(el, expected);
      var slots = elementIntervals.get(el);
      expected.forEach(function(spec, key) {
        if (slots && slots.get(key) != null) return;
        var recurringKey = "cev-" + POLL_KEY_PREFIX + pollKeySeq(el) + ":" + key;
        var intervalId = window.setInterval(function() {
          pollTick(el, spec, recurringKey);
        }, spec.interval);
        registerElementInterval(el, key, intervalId);
      });
      if (expected.size) polledElements.add(el);
      else polledElements.delete(el);
    };
    var resolveUpdateEventType = function(el, spec) {
      var inputType;
      if (typeof spec.on === "string" && spec.on) return spec.on;
      var tag = el.tagName;
      if (tag === "SELECT") return "change";
      if (tag === "TEXTAREA") return spec.lazy === true ? "change" : "input";
      if (tag === "INPUT") {
        inputType = el.type;
        if (inputType === "file") return null;
        if (inputType === "checkbox" || inputType === "radio") return "change";
        return spec.lazy === true ? "change" : "input";
      }
      return null;
    };
    var resolveNaturalDraftEventType = function(el) {
      var tag = el.tagName;
      if (tag === "SELECT") return "change";
      if (tag === "TEXTAREA") return "input";
      if (tag !== "INPUT") return null;
      var inputType = el.type;
      if (inputType === "file") return null;
      if (inputType === "checkbox" || inputType === "radio") return "change";
      return "input";
    };
    var readControlValue = function(el) {
      var control = el;
      var numeric;
      if (control.type === "checkbox" || control.type === "radio") return control.checked;
      if (control.type === "number" || control.type === "range") {
        numeric = control.valueAsNumber;
        return Number.isFinite(numeric) ? numeric : control.value;
      }
      return control.value;
    };
    var twoWayFlushStates = /* @__PURE__ */ new WeakMap();
    var pendingTwoWayFlushes = /* @__PURE__ */ new Set();
    var twoWayStateFor = function(el, key, spec) {
      var perEl = twoWayFlushStates.get(el);
      if (!perEl) {
        perEl = /* @__PURE__ */ new Map();
        twoWayFlushStates.set(el, perEl);
      }
      var state = perEl.get(key);
      if (!state) {
        state = { el, spec, flushTimer: 0, throttleUntil: 0 };
        perEl.set(key, state);
      }
      state.spec = spec;
      return state;
    };
    var flushTwoWayBinding = function(state) {
      if (state.flushTimer) {
        window.clearTimeout(state.flushTimer);
        state.flushTimer = 0;
      }
      pendingTwoWayFlushes.delete(state);
      var el = state.el;
      var spec = state.spec;
      unsentDrafts.delete(el);
      var anchor = el.isConnected ? anchorForElement(el) : null;
      if (anchor && anchor.stateProxy != null && typeof spec.field === "string") {
        try {
          anchor.stateProxy[spec.field] = readControlValue(el);
        } catch (err) {
          console.error("[Citry] events: a two-way binding could not write $state." + spec.field + ":", err);
        }
      }
      var handler4 = typeof spec.handler === "string" ? spec.handler : "";
      if (!handler4) return;
      var promise = sendFromElement(el, handler4, null, void 0);
      if (promise) promise.then(null, function() {
      });
    };
    var armTwoWayFlush = function(state, delayMs, throttleMs) {
      pendingTwoWayFlushes.add(state);
      state.flushTimer = window.setTimeout(function() {
        state.flushTimer = 0;
        if (throttleMs != null) state.throttleUntil = Date.now() + throttleMs;
        flushTwoWayBinding(state);
      }, delayMs);
    };
    var scheduleTwoWayUpdate = function(el, spec, key, event) {
      if (typeof spec.key === "string" && spec.key && !keyFilterMatches(event, spec.key)) return;
      var state = twoWayStateFor(el, key, spec);
      unsentDrafts.add(el);
      var debounceMs = bindingTimingMs(spec, "debounce");
      var throttleMs = bindingTimingMs(spec, "throttle");
      var now = Date.now();
      if (throttleMs != null) {
        if (state.throttleUntil > now) {
          if (!state.flushTimer) armTwoWayFlush(state, state.throttleUntil - now, throttleMs);
          return;
        }
        state.throttleUntil = now + throttleMs;
      }
      if (debounceMs == null) {
        flushTwoWayBinding(state);
        return;
      }
      if (state.flushTimer) window.clearTimeout(state.flushTimer);
      armTwoWayFlush(state, debounceMs, throttleMs);
    };
    var runElementStateBindings = function(el, event, type) {
      decodeBindSpecs(el).forEach(function(spec, index) {
        if (spec == null || typeof spec !== "object" || spec.mode !== "two") return;
        var updateType = resolveUpdateEventType(el, spec);
        if (updateType !== type) {
          if (resolveNaturalDraftEventType(el) === type) unsentDrafts.add(el);
          return;
        }
        scheduleTwoWayUpdate(el, spec, "bind:" + index, event);
      });
    };
    var collectPendingTwoWayDrafts = function(anchor) {
      pendingTwoWayFlushes.forEach(function(state) {
        var el = state.el;
        if (!el.isConnected || anchorForElement(el) !== anchor) return;
        if (anchor.stateProxy == null || typeof state.spec.field !== "string") return;
        unsentDrafts.delete(el);
        try {
          anchor.stateProxy[state.spec.field] = readControlValue(el);
        } catch (err) {
          console.error("[Citry] events: could not piggyback the two-way draft of $state." + state.spec.field + ":", err);
        }
      });
    };
    var controlBindings = /* @__PURE__ */ new WeakMap();
    var boundControls = /* @__PURE__ */ new Set();
    var warnedUnresolvedUpdate = /* @__PURE__ */ new WeakSet();
    var releaseControlBindings = function(el) {
      var record = controlBindings.get(el);
      if (record) {
        record.effects.forEach(function(effectRef) {
          src_default.release(effectRef);
        });
        controlBindings.delete(el);
      }
      boundControls.delete(el);
    };
    var makeApplicationEffect = function(el, anchor, field) {
      return src_default.effect(function() {
        var values = anchor.values;
        if (values == null) return;
        if (!Object.prototype.hasOwnProperty.call(values, field)) return;
        var value = values[field];
        if (unsentDrafts.has(el)) return;
        applyValueToControl(el, value);
      });
    };
    var syncControlBindings = function(el) {
      var raw2 = el.getAttribute(DATA_CEV_BIND) || "";
      var anchor = el.isConnected ? anchorForElement(el) : null;
      var record = controlBindings.get(el);
      if (!raw2 || !anchor || anchor.values == null) {
        if (record) releaseControlBindings(el);
        return;
      }
      if (record && record.anchor === anchor && record.values === anchor.values && record.raw === raw2) return;
      if (record) releaseControlBindings(el);
      var effects = [];
      var liveAnchor = anchor;
      decodeBindSpecs(el).forEach(function(spec) {
        if (spec == null || typeof spec !== "object" || typeof spec.field !== "string") return;
        effects.push(makeApplicationEffect(el, liveAnchor, spec.field));
      });
      controlBindings.set(el, {
        anchor: liveAnchor,
        values: liveAnchor.values,
        raw: raw2,
        effects
      });
      boundControls.add(el);
    };
    var syncStateBindings = function(el) {
      decodeBindSpecs(el).forEach(function(spec) {
        var draftType;
        if (spec == null || typeof spec !== "object" || spec.mode !== "two") return;
        var type = resolveUpdateEventType(el, spec);
        if (type) {
          installDelegatedListener(type);
          draftType = resolveNaturalDraftEventType(el);
          if (draftType && draftType !== type) installDelegatedListener(draftType);
        } else if (!warnedUnresolvedUpdate.has(el)) {
          warnedUnresolvedUpdate.add(el);
          console.warn(
            "[Citry] events: the two-way :c-" + (typeof spec.field === "string" ? spec.field : "?") + " binding has no update event for this control; name one with '.on:<event>' (design 5.1)."
          );
        }
      });
      syncControlBindings(el);
    };
    var RESERVED_FORM_FIELDS = {
      _citry_state_token: true,
      _citry_caller_render_id: true
    };
    var coerceFormValue = function(form, name, value) {
      var control = form.elements.namedItem(name);
      var input = control && control.nodeType === 1 ? control : null;
      var numeric;
      if (input && input.tagName === "INPUT" && (input.type === "number" || input.type === "range")) {
        numeric = input.valueAsNumber;
        if (Number.isFinite(numeric)) return numeric;
      }
      return value;
    };
    var collectFormArgs = function(form) {
      var entries = /* @__PURE__ */ new Map();
      new FormData(form).forEach(function(value, name) {
        if (RESERVED_FORM_FIELDS[name] === true) return;
        if (typeof value !== "string") return;
        var bucket = entries.get(name);
        if (!bucket) {
          bucket = [];
          entries.set(name, bucket);
        }
        bucket.push(value);
      });
      var out = {};
      entries.forEach(function(values, name) {
        out[name] = values.length === 1 ? coerceFormValue(form, name, values[0]) : values.slice();
      });
      return out;
    };
    var mergeSubmitFormArgs = function(element, event, args) {
      if (!event || event.type !== "submit") return args;
      var target = event.target;
      var form = target && target.nodeType === 1 && target.tagName === "FORM" ? target : element && element.tagName === "FORM" ? element : null;
      if (!form || !form.isConnected) return args;
      var collected = collectFormArgs(form);
      return args ? Object.assign(collected, args) : collected;
    };
    var scanBindings = function() {
      bindingScanScheduled = false;
      document.querySelectorAll("[" + DATA_CEV_ON + "]").forEach(function(el) {
        decodeCevSpecs(el, DATA_CEV_ON).forEach(function(spec) {
          if (spec != null && typeof spec === "object" && typeof spec.event === "string" && spec.event) {
            installDelegatedListener(spec.event);
          }
        });
      });
      document.querySelectorAll("[" + DATA_CEV_POLL + "]").forEach(syncElementPollTimers);
      polledElements.forEach(function(el) {
        if (!el.isConnected || !el.hasAttribute(DATA_CEV_POLL)) clearPollTimers(el);
      });
      document.querySelectorAll("[" + DATA_CEV_BIND + "]").forEach(syncStateBindings);
      boundControls.forEach(function(el) {
        if (!el.isConnected || !el.hasAttribute(DATA_CEV_BIND)) releaseControlBindings(el);
      });
    };
    var bindingScanScheduled = false;
    var scheduleBindingScan = function() {
      if (bindingScanScheduled) return;
      bindingScanScheduled = true;
      Promise.resolve().then(scanBindings);
    };
    var propTypeName = function(ctor) {
      if (typeof ctor === "function" && ctor.name) return ctor.name;
      return String(ctor);
    };
    var matchesPropType = function(value, ctor) {
      if (ctor === String) return typeof value === "string";
      if (ctor === Number) return typeof value === "number";
      if (ctor === Boolean) return typeof value === "boolean";
      if (ctor === Function) return typeof value === "function";
      if (ctor === Symbol) return typeof value === "symbol";
      if (ctor === BigInt) return typeof value === "bigint";
      if (ctor === Array) return Array.isArray(value);
      if (ctor === Object) return typeof value === "object" && value !== null;
      if (typeof ctor === "function") return value instanceof ctor;
      return false;
    };
    var declaredTypeList = function(classId, name, type) {
      var list = Array.isArray(type) ? type : [type];
      list.forEach(function(entry) {
        if (typeof entry !== "function") {
          throw pointedError(
            "component " + classId + " prop '" + name + "': `type` must be a constructor (String, Number, ...) or an array of constructors (design 5.5)."
          );
        }
      });
      return list;
    };
    var resolveDeclaredProps = function(classId, declarations) {
      var resolved = {};
      Object.keys(declarations || {}).forEach(function(name) {
        var def2 = declarations[name];
        var accepted;
        var matched;
        if (def2 == null || typeof def2 !== "object") {
          throw pointedError(
            "component " + classId + " prop '" + name + "': the definition must be an object with `type`, `required`, and/or `default` (design 5.5)."
          );
        }
        var value;
        if (Object.prototype.hasOwnProperty.call(def2, "default")) {
          value = typeof def2.default === "function" ? def2.default() : def2.default;
        }
        if (value === void 0) {
          if (def2.required === true) {
            throw pointedError(
              "component " + classId + " prop '" + name + "' is required, but no value was supplied and it declares no default."
            );
          }
          resolved[name] = void 0;
          return;
        }
        if (value !== null && def2.type != null) {
          accepted = declaredTypeList(classId, name, def2.type);
          matched = accepted.some(function(ctor) {
            return matchesPropType(value, ctor);
          });
          if (!matched) {
            throw pointedError(
              "component " + classId + " prop '" + name + "': the value does not match the declared type; expected " + accepted.map(propTypeName).join(" or ") + ", got " + (Array.isArray(value) ? "an array" : "a " + typeof value) + "."
            );
          }
        }
        resolved[name] = value;
      });
      return src_default.reactive(resolved);
    };
    var decorateComponentContext = function(ctx, control) {
      processExistingEventsManifests();
      ctx.props = {};
      var anchor = idToAnchor.get(ctx.id) || null;
      if (anchor) {
        ctx.state = anchor.stateProxy;
        ctx.loading = function(name) {
          return readLoading(anchor, name, "loading");
        };
        ctx.error = function(name) {
          return readError(anchor, name, "error");
        };
        ctx.sendEvent = function(name, args, opts) {
          try {
            return sendFromAnchor(anchor, name, args, opts);
          } catch (err) {
            return Promise.reject(err);
          }
        };
        ctx.onEvent = function(name, fn) {
          var off = subscribeForAnchor(anchor, name, fn);
          return control ? control.registerCleanup(off) : off;
        };
      } else {
        ctx.state = null;
        ctx.loading = function(name) {
          return readPayloadLoading(ctx.id, name);
        };
        ctx.error = function(name) {
          return readPayloadError(ctx.id, name);
        };
        ctx.sendEvent = function(name) {
          return Promise.reject(
            pointedError(
              "component instance '" + ctx.id + "' declares no events, so sendEvent('" + name + "') has nothing to call; add a `class Events` to the component."
            )
          );
        };
        ctx.onEvent = function() {
          throw pointedError(
            "component instance '" + ctx.id + "' declares no events, so onEvent cannot target it; add a `class Events` to the component."
          );
        };
      }
    };
    var resolveSendTarget = function(target) {
      if (typeof target === "string") return idToAnchor.get(target) || null;
      if (target && target.nodeType === 1) {
        var id = innermostPhysicalComponentId(target);
        return id && idToAnchor.get(id) || null;
      }
      return null;
    };
    var api = {
      /**
       * Send an event to any instance on the page. `target` is an instance id
       * or an Element inside one; same promise contract as the scoped
       * `sendEvent` (design 5.2).
       */
      send: function(target, name, args, opts) {
        var anchor = resolveSendTarget(target);
        if (!anchor) {
          return Promise.reject(
            pointedError(
              "send() found no interactive component instance for target " + (typeof target === "string" ? "'" + target + "'" : String(target)) + "; pass an instance id from the events manifest or an element inside one."
            )
          );
        }
        var element = typeof target !== "string" && target && target.nodeType === 1 ? target : null;
        try {
          return sendFromAnchor(anchor, name, args, opts, element, element != null);
        } catch (err) {
          return Promise.reject(err);
        }
      },
      /**
       * Listen for server-dispatched events under their raw name, from any
       * instance; sugar over document.addEventListener that unwraps e.detail.
       * Returns the unsubscribe function.
       */
      on: function(name, fn) {
        var handler4 = function(e) {
          fn(e.detail);
        };
        document.addEventListener(name, handler4);
        return function() {
          document.removeEventListener(name, handler4);
        };
      },
      /** Set page-wide runtime defaults once (design 5.2's field table). */
      configure: function(opts) {
        Object.assign(config, opts || {});
      },
      /**
       * Register a transport under a name (design 5.2/6.1): `impl` is
       * `{send(envelope) -> Promise<resultEnvelope>, subscribe?}` (`subscribe`
       * is the v2 push half). The built-in fetch transport registers through
       * this same function; selection is `configure({transport: name})`.
       */
      registerTransport: registerTransportImpl,
      /**
       * The action interpreter as a public entry point (design 5.2's table):
       * apply a result envelope's `actions` array to the page, firing the same
       * lifecycle events. Exposed for tests, custom transports, and pages that
       * override what an action does. Applied with no caller context: no
       * caller promise, no epoch guard, liveness checks as always.
       */
      applyActions: function(actions) {
        if (!Array.isArray(actions)) {
          return Promise.reject(
            pointedError("applyActions expects a result's `actions` array (design 4.3), got " + typeof actions + ".")
          );
        }
        if (!actions.every(validateWireAction) || actions.filter(function(action) {
          return action.action === "data";
        }).length > 1) {
          return Promise.reject(pointedError("applyActions received an invalid citry-events/1 action array."));
        }
        return applyResult({ ok: true, actions }, null);
      },
      // The hook the $component payload decorator delegates to. The bootstrap
      // stub registers the decorator wrapper with citry.js and routes it here
      // the moment this runtime replaces the stub.
      _decorate: decorateComponentContext,
      // Late-bound payload readers used by the bootstrap stub. A component
      // callback that ran before this bundle arrived keeps synchronous
      // loading/error functions which begin reading the live anchor now.
      _loadingFor: readPayloadLoading,
      _errorFor: readPayloadError,
      // Instance-scoped subscribe by component id. Payloads the bootstrap stub
      // decorated before this runtime arrived hold `onEvent` closures that
      // delegate here at call time, so a late subscription still lands on the
      // live runtime instead of the stub's drained queue.
      _onFor: subscribeForId,
      // The events-runtime half of the `$component` config form (design
      // 5.5): the dependency manager resolves a registration's declared props
      // through this, late-bound like `_decorate`, so prop validation and
      // reactivity live here while the registration shape lives in citry.js.
      _resolveProps: resolveDeclaredProps
    };
    api._internal = {
      alpineStarted: false,
      anchors,
      idToAnchor,
      classes,
      config,
      getAnchor: function(componentId) {
        return idToAnchor.get(componentId) || null;
      },
      linkRenderedInstance,
      finishRender,
      setTransport: function(fn) {
        transportImpl = fn;
      },
      sendCalls,
      sendFromElement,
      sendBoundary,
      boundaryScope,
      queue: {
        snapshot: function() {
          return queueNodes.map(function(node) {
            var waitsOn = [];
            node.deps.forEach(function(dep) {
              waitsOn.push(dep.seq);
            });
            waitsOn.sort(function(a, b) {
              return a - b;
            });
            return {
              seq: node.seq,
              event: node.name,
              anchor: node.anchor.anchorId,
              dispatched: node.dispatched,
              waitsOn
            };
          });
        }
      },
      debug: function() {
        var anchorIntervals = 0;
        var elementIntervalCount = 0;
        var formEffects = 0;
        anchors.forEach(function(anchor) {
          anchorIntervals += anchor.timers.size;
        });
        polledElements.forEach(function(el) {
          var intervals = elementIntervals.get(el);
          if (intervals) elementIntervalCount += intervals.size;
        });
        boundControls.forEach(function(el) {
          var record = controlBindings.get(el);
          if (record) formEffects += record.effects.length;
        });
        return Object.freeze({
          anchors: anchors.size,
          renderIds: idToAnchor.size,
          classes: classes.size,
          delegatedListenerTypes: installedListenerTypes.size,
          polledElements: polledElements.size,
          anchorIntervals,
          elementIntervals: elementIntervalCount,
          boundControls: boundControls.size,
          formEffects,
          pendingFlushes: pendingTwoWayFlushes.size,
          queuedCalls: queueNodes.length
        });
      },
      stageEventsManifest,
      processEventsManifests: processExistingEventsManifests,
      applyResult,
      applyEnvelope,
      retireAnchor,
      sweepRetiredAnchors,
      drafts: {
        mark: function(el) {
          unsentDrafts.add(el);
        },
        clear: function(el) {
          unsentDrafts.delete(el);
        },
        has: function(el) {
          return unsentDrafts.has(el);
        }
      },
      forms: {
        snapshot: function(el) {
          var record = controlBindings.get(el);
          var flushes = 0;
          pendingTwoWayFlushes.forEach(function(state) {
            if (state.el === el && state.flushTimer) flushes += 1;
          });
          return { effects: record ? record.effects.length : 0, flushes };
        }
      },
      timers: {
        registerAnchorInterval,
        registerElementInterval
      }
    };
    C.events = api;
    alpineRuntime._register({
      root: function() {
        return "[data-citry-root],[data-cid]";
      },
      init: function(el) {
        if (!el.hasAttribute || !el.hasAttribute("data-cid")) return;
        if (boundaryAttached.has(el)) return;
        processExistingEventsManifests();
        if (boundaryAttached.has(el)) return;
        var ids = (el.getAttribute("data-cid") || "").trim().split(/\s+/).filter(Boolean);
        var known = false;
        ids.forEach(function(id) {
          var anchor = idToAnchor.get(id);
          if (anchor) {
            known = true;
            anchor.seenInDom = true;
          }
        });
        if (known) attachBoundaryScope(el);
      },
      mutations: function(mutations) {
        if (!mutations.length) processExistingEventsManifests();
        mutations.forEach(function(mutation) {
          mutation.addedNodes.forEach(function(node) {
            if (node.nodeType !== 1) return;
            if (node.matches && node.matches(EVENTS_MANIFEST_SELECTOR)) {
              processEventsManifestTag(node);
            } else if (node.querySelectorAll) {
              node.querySelectorAll(EVENTS_MANIFEST_SELECTOR).forEach(processEventsManifestTag);
            }
          });
        });
        scheduleAnchorSweep();
        scheduleBindingScan();
      },
      beforeStart: function() {
        processExistingEventsManifests();
        scheduleBindingScan();
      },
      afterStart: function() {
        api._internal.alpineStarted = true;
      }
    });
    processExistingEventsManifests();
    scheduleBindingScan();
    if (bootstrapStub && bootstrapStub._stubQueue) {
      bootstrapStub._stubQueue.forEach(function(entry) {
        if (entry.kind !== "registerTransport") return;
        try {
          api.registerTransport(entry.args[0], entry.args[1]);
        } catch (err) {
          if (entry.reject) entry.reject(err);
          else console.error("[Citry] a queued transport registration failed while the runtime booted:", err);
        }
      });
      bootstrapStub._stubQueue.forEach(function(entry) {
        try {
          if (entry.kind === "registerTransport") {
            return;
          } else if (entry.kind === "send") {
            api.send.apply(null, entry.args).then(entry.resolve, entry.reject);
          } else if (entry.kind === "applyActions") {
            api.applyActions(entry.args[0]).then(entry.resolve, entry.reject);
          } else if (entry.kind === "on") {
            if (!entry.dead) entry.off = api.on(entry.args[0], entry.args[1]);
          } else if (entry.kind === "onEvent") {
            if (!entry.dead)
              entry.off = subscribeForId(
                entry.args[0],
                entry.args[1],
                entry.args[2]
              );
          } else if (entry.kind === "configure") {
            api.configure(entry.args[0]);
          }
        } catch (err) {
          if (entry.reject) entry.reject(err);
          else console.error("[Citry] a queued events call failed while the runtime booted:", err);
        }
      });
      bootstrapStub._stubQueue.length = 0;
    }
    if (C.manager && typeof C.manager.decorateContext === "function") {
      if (!(bootstrapStub && bootstrapStub._decoratorHooked)) {
        C.manager.decorateContext(function(ctx, control) {
          C.events._decorate(ctx, control);
        });
      }
    }
    alpineRuntime._ready();
    alpineRuntime._start();
  })();
})();
