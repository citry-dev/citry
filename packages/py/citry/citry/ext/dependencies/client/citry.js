/**
 * Citry's client-side dependency manager.
 *
 * The server inlines this script into pages rendered with the "document"
 * strategy (or, once a web integration is mounted, serves it at a URL). It
 * has three jobs:
 *
 * 1. Run components' per-instance JS. A component's JS registers a callback
 *    with `$component(...)` (expanded server-side to
 *    `Citry.manager.registerComponent("<classId>", ...)`); the page carries
 *    a JSON manifest naming which instances to call with which data; the
 *    manager matches the two and calls the callback with the instance's
 *    elements (the ones carrying its `data-cid-<id>` marker) and its
 *    `js_data()` result. A callback may return a cleanup function; the
 *    manager runs it before the callback fires again for the same instance
 *    through a correlated update or an explicit graph-independent call.
 *    Instead of a bare callback, `$component` also accepts a config object
 *    `{init, props}` (design events.md 5.5): `init` is the callback,
 *    and `props` declares the props it consumes. Graph-owned instances keep
 *    one lifecycle props controller that evaluates source-owned `$c-props`,
 *    validates updates, and exposes a stable read-only view to init. The
 *    Events helper remains only for legacy graph-independent calls.
 *    Other scripts (e.g. extension runtimes) can add properties to the payload
 *    object the callback receives via `Citry.manager.decorateContext(fn)`:
 *    decorators run on each instance's payload right before its callback,
 *    in registration order, mutating the payload in place (return values
 *    are ignored); a thrown error is logged and the remaining decorators
 *    and the callback still runs; the returned function unregisters the
 *    decorator.
 *
 * 2. Track which scripts/stylesheets are already on the page (by URL), so
 *    an HTML fragment inserted later does not fetch them again.
 *
 * 3. Load the scripts/stylesheets a fragment needs (`loadJs`/`loadCss` from
 *    JSON tag descriptors).
 *
 * 4. Tear an instance down when it leaves the page, and drop a class's
 *    `Component.css` when its last instance is gone. The manager tracks each
 *    instance whose callback has fired (plus any the manifest declares
 *    present for CSS only) and sweeps them against the live DOM on every DOM
 *    mutation and after each render: an instance with no `data-cid-<id>`
 *    element left has its cleanups run, and a class with no instance left has
 *    its `data-citry-css-class` sheet removed. The sheet removal is deferred
 *    to a later task and its count re-checked, so a component that re-renders
 *    in place (retiring its old id just before the new id registers) keeps
 *    its styling instead of losing it on every re-render.
 *
 * 5. Atomically normalize ownership graph revisions into typed lookup
 *    indexes, route graph-linked callbacks, and own the permanent Alpine hook
 *    broker. The broker installs Alpine's non-removable hooks once and lets
 *    Events and later graph adapters replace providers without stacking page
 *    observers, init interceptors, root selectors, magics, or startup calls.
 *
 * Manifests are JSON script tags carrying the `data-citry` attribute. JSON
 * is inert no matter how the HTML lands in the page (innerHTML included), so
 * a MutationObserver watches for inserted manifest tags and processes them;
 * manifests already in the document are processed at startup. String fields
 * inside a manifest ride as base64, so content can never break out of the
 * script tag.
 *
 * Design: docs/design/dependencies.md section 8.
 */
(function () {
  "use strict";

  if (globalThis.Citry && globalThis.Citry.manager) {
    return; // already loaded (e.g. both a document page and a fragment included it)
  }

  // ----- state -----

  // URLs already on the page, per type ("js" / "css").
  var loaded = { js: new Set(), css: new Set() };
  // URL -> the shared Promise for a script request that has started but has
  // not settled. Loaded-URL dedupe alone prevents a duplicate element, but
  // callers must also wait for the first request before running dependent
  // component callbacks.
  var loadingJs = new Map();
  // URL -> {element, promise, resolve}. Stylesheet requests follow the same
  // in-flight dedupe contract as scripts. Keeping the element and resolver in
  // the entry also lets class CSS collection settle a request whose link is
  // removed before its load event fires.
  var loadingCss = new Map();
  // classId -> the class's single $component registration.
  var componentRegistrations = new Map();
  // "classId:varsHash" -> the registered js_data() payload.
  var componentData = new Map();
  // "classId:varsHash" -> active call/instance owners. Data scripts are
  // content-addressed and shared. Ownership references are released after
  // the final pending call or live instance lets go; the payload itself stays
  // paired with the page-lifetime loaded-script cache.
  var componentDataReferences = new Map();
  // componentId -> the data key held by a graph-independent live instance.
  // Graph-owned instances hold the key on their lifecycle.
  var instanceDataKeys = new Map();
  // Calls whose callback or data has not arrived yet.
  var pendingCalls = [];
  // Callback-payload decorators (see decorateContext), in registration order.
  var decorators = [];
  // "classId:componentId" -> cleanup functions the instance's callback
  // returned on its last run, to call before the callback runs again.
  var cleanups = new Map();
  // componentId -> classId for every instance the manager is tracking as
  // live: one whose $component callback has fired, and one a manifest
  // declared present for CSS only (a Component.css instance with no
  // $component JS). This one set is what both the removal reconciler (run
  // an instance's cleanups when it leaves the page) and the per-class
  // Component.css cleanup count against.
  var liveInstances = new Map();
  // Whether a removal sweep is already queued, so many DOM mutations in one
  // batch coalesce into a single sweep on the next microtask.
  var sweepScheduled = false;
  // Class ids with a deferred Component.css collection already queued, so a
  // burst of retirements queues one re-check per class, not many.
  var cssGcPending = new Set();
  // revision -> fully validated, decoded ownership graph. A revision is
  // committed only after every logical reference and physical comment cap
  // passes validation.
  var ownershipGraphs = new Map();
  // revision -> dependency manifests waiting for their graph transaction.
  var graphBlockedManifests = new Map();
  // revision -> callbacks registered through ownership.whenReady().
  var graphWaiters = new Map();
  // revision -> the error that made one ownership transaction fail. A
  // dependency or Events manifest waiting on that revision must reject
  // instead of waiting forever or applying a partial transaction.
  var graphFailures = new Map();
  // Reusing one graph revision in a second dependency transaction would
  // clone concrete component IDs and caps. One revision feeds one dependency
  // manifest only.
  var consumedGraphDependencies = new Set();
  // Script-node identity must not ride a cloneable data-* marker. A moved
  // node is ignored, while cloneNode/outerHTML creates a fresh node that
  // must enter normal duplicate-revision/transaction validation.
  var processedDependencyTags = new WeakSet();
  var processedGraphTags = new WeakSet();
  // Graph tags discovered while the HTML parser is still running cannot be
  // validated until trailing physical caps have landed. Keep them iterable
  // so the Citry-owned Alpine start barrier can commit them before its first
  // DOM walk, independent of DOMContentLoaded listener registration order.
  var deferredGraphTags = new Set();
  // revision -> graph-linked Events adoption status. The Events runtime
  // explicitly acknowledges success or failure so dependency callbacks do
  // not run against a partially adopted anchor registry.
  var graphEvents = new Map();
  // Permanent page-wide Alpine broker state. The pinned Alpine bundle may
  // arrive after graph and component manifests in a fragment, so the core
  // manager owns registrations before Alpine itself exists. Alpine APIs that
  // cannot unregister are installed exactly once and dispatch through these
  // replaceable provider maps.
  var alpineOwner = null;
  var alpineReady = false;
  var alpineStarted = false;
  var alpineStarting = false;
  var alpineStartRequested = false;
  var alpineStartListenerRegistered = false;
  var alpineStartHolds = 0;
  var alpineStartError = null;
  var alpineBeforeStart = [];
  var alpineRootProviders = new Map();
  var alpinePreBoundaryProviders = new Map();
  var alpineInitProviders = new Map();
  var alpineMagicProviders = new Map();
  var alpineMutationProviders = new Map();
  var alpineStartProviders = new Map();
  var reservedAlpineMagics = new Set(["provide", "inject", "unprovide"]);
  var alpineProviderCounter = 0;
  var alpineHookCounts = { installs: 0, roots: 0, init: 0, morph: 0, starts: 0 };
  var alpineLastForeign = null;
  var alpineBoundaryRoot = null;
  // A3 keeps several live revisions at once (the document plus independent
  // fragments). These indexes route render IDs and stable anchors without a
  // page-global "current revision" shortcut.
  var ownershipStates = new Map();
  var browserAnchors = new Map();
  // Permanent replay ledger. One compact revision string is stored for
  // every graph accepted by this document so a retired fragment cannot be
  // cloned and reinserted with concrete IDs and caps that were already used.
  var seenOwnershipRevisions = new Set();
  var ownershipPruneScheduled = false;
  var scheduleOwnershipPrune = null;
  var runtimePlacementCounter = 0;
  // Stable component lifecycle is keyed by logical identity, never by the
  // per-render id. A correlated replacement therefore keeps its reactive
  // scope and live `els` array while replacing only the render invocation.
  var componentLifecycles = new Map();
  var lifecycleReconcileScheduled = false;
  var rangeMorphDepth = 0;
  var ownershipAdoptionDepth = 0;
  var rootScopeOwners = new WeakMap();
  var physicalCorruptionReports = new WeakSet();
  var expectedPhysicalRetirements = new WeakSet();
  var rootHolds = new WeakMap();
  var preBoundarySeen = new WeakSet();
  // One component boundary controller manages every client binding resolved
  // from one nested tag, such as <c-card $c-props="{ theme }" x-on:select="select()" />.
  var componentBoundariesByTarget = new Map();
  var liveComponentBoundaries = new Set();
  var fillSourceDescriptors = new Map();
  var fillRegionRoutes = new Map();
  var fillRoutesByElement = new WeakMap();
  var retiredFillRoots = new WeakSet();
  var fillReconcileScheduled = false;
  var installFillSourceDirective = null;
  var installAmbientContext = null;
  var createAmbientDirectiveControl = null;
  var runAmbientDirective = null;
  var activeAmbientDirective = null;
  var ambientDirectiveControlsByCleanup = new WeakMap();
  var ambientDirectiveEvaluatedAttributesByElement = new WeakMap();
  var ambientCloneSources = new WeakMap();
  var ambientContextRevision = null;
  var touchAmbientContext = null;
  var callWaitsForAmbientMagic = null;
  var ambientMagicFrames = new Set();
  var ambientMagicFramesByElement = new WeakMap();
  var ambientWriteCounter = 0;
  var FILL_SOURCE_FRAME = Symbol("citry-fill-source-frame");
  var FILL_SOURCE_ATTR = "x-citry-fill-source";
  var RETIRED_FILL_SCOPE = Object.freeze({});
  var flushingCalls = false;
  var flushAgain = false;
  // Assigned after graph routing is defined. Keeping the broker callback
  // here lets the embedded Alpine install before any graph exists.
  var isolateRootScope = null;

  var pointedAlpineError = function (message) {
    return new Error("[Citry] Alpine: " + message);
  };

  var rejectStructuralComponentClones = function (root) {
    if (!root || typeof root.querySelectorAll !== "function") return;
    var templates = [];
    if (
      root instanceof HTMLTemplateElement &&
      (root.hasAttribute("x-for") || root.hasAttribute("x-if") || root.hasAttribute("x-teleport"))
    ) templates.push(root);
    root.querySelectorAll("template[x-for],template[x-if],template[x-teleport]").forEach(function (template) {
      templates.push(template);
    });
    templates.forEach(function (template) {
      if (!template.content.querySelector("[data-citry-root]")) return;
      var directive = template.hasAttribute("x-for")
        ? "x-for"
        : template.hasAttribute("x-if")
        ? "x-if"
        : "x-teleport";
      throw pointedAlpineError(
        "native " + directive + " cannot clone a server-rendered client-active Citry component. " +
          "Use server <c-for> for server component lists, or keep the Alpine structural directive inside " +
          "an existing Citry component. A browser blueprint protocol must mint fresh graph, lifecycle, " +
          "source, region, and Events identity before client component instantiation can be supported."
      );
    });
    if (
      root instanceof Element && root._x_refreshXForScope &&
      (root.hasAttribute("data-citry-root") || root.querySelector("[data-citry-root]"))
    ) {
      throw pointedAlpineError(
        "native x-for cannot clone a server-rendered client-active Citry component. " +
          "Use server <c-for> for server component lists, or keep the Alpine loop inside an existing Citry " +
          "component. A browser blueprint protocol must mint fresh graph and lifecycle identity first."
      );
    }
  };

  var warnForeignAlpine = function (foreign) {
    if (!foreign || foreign === alpineOwner || foreign === alpineLastForeign) return;
    alpineLastForeign = foreign;
    console.warn(
      "[Citry] Alpine: another Alpine instance is already on this page. " +
        "Citry owns one pinned instance and restored it as globalThis.Alpine; " +
        "remove the separate Alpine include to prevent duplicate initialization."
    );
  };

  var ensureOwnedAlpineGlobal = function () {
    if (!alpineOwner) return;
    warnForeignAlpine(globalThis.Alpine);
    globalThis.Alpine = alpineOwner;
  };

  var runAlpineBeforeStart = function (callback) {
    try {
      callback(alpineOwner);
    } catch (err) {
      alpineStartError = err;
      throw err;
    }
  };

  var dispatchAlpineMutations = function (mutations) {
    if (
      ambientContextRevision && touchAmbientContext &&
      mutations.some(function (mutation) {
        if (mutation.type !== "childList") return false;
        return Array.from(mutation.addedNodes).concat(Array.from(mutation.removedNodes)).some(function (node) {
          return node.nodeType === Node.ELEMENT_NODE || node.nodeType === Node.COMMENT_NODE;
        });
      })
    ) touchAmbientContext();
    Array.from(alpineMutationProviders.values()).forEach(function (provider) {
      try {
        provider(mutations);
      } catch (err) {
        console.error("[Citry] Alpine mutation provider failed:", err);
      }
    });
  };

  var startOwnedAlpine = function () {
    if (!alpineStartRequested || alpineStarted || alpineStarting || !alpineReady || alpineStartHolds > 0) return;
    if (alpineStartError) {
      console.error("[Citry] Alpine startup was cancelled because a beforeStart callback failed:", alpineStartError);
      return;
    }
    var start = function () {
      if (alpineStarted || alpineStartHolds > 0) return;
      ensureOwnedAlpineGlobal();
      alpineStarting = true;
      try {
        flushDeferredGraphTags();
        drainClientManifests();
        Array.from(alpineStartProviders.values()).forEach(function (provider) {
          if (provider.before) provider.before();
        });
        alpineOwner.start();
        alpineStarted = true;
        flushCalls();
        alpineHookCounts.starts += 1;
        Array.from(alpineStartProviders.values()).forEach(function (provider) {
          if (provider.after) provider.after();
        });
      } catch (err) {
        alpineStartError = err;
        console.error("[Citry] Alpine startup failed:", err);
      } finally {
        alpineStarting = false;
      }
    };
    if (document.readyState === "loading") {
      if (!alpineStartListenerRegistered) {
        alpineStartListenerRegistered = true;
        document.addEventListener("DOMContentLoaded", start, { once: true });
      }
    } else {
      start();
    }
  };

  var installAlpine = function (alpine, morphPlugin) {
    if (!alpine || typeof alpine.start !== "function") {
      throw pointedAlpineError("the bundled runtime tried to install an invalid Alpine object.");
    }
    ["closestDataStack", "evaluateRaw", "reactive", "effect", "release", "cloneNode"].forEach(function (name) {
      if (typeof alpine[name] !== "function") {
        throw pointedAlpineError("the pinned runtime is missing required API Alpine." + name + ".");
      }
    });
    rejectStructuralComponentClones(document);
    if (alpineOwner) {
      if (alpineOwner !== alpine) {
        console.warn(
          "[Citry] Alpine: a second Citry Alpine bundle was evaluated. " +
            "The original runtime and all of its registrations were preserved."
        );
      }
      ensureOwnedAlpineGlobal();
      return alpineOwner === alpine;
    }
    warnForeignAlpine(globalThis.Alpine);
    alpineOwner = alpine;
    globalThis.Alpine = alpine;
    var cloneNode = alpine.cloneNode;
    alpine.cloneNode = function (from, to) {
      ambientCloneSources.set(to, from);
      return cloneNode(from, to);
    };
    alpine.plugin(morphPlugin);
    var registerOwnedMagic = alpine.magic.bind(alpine);
    if (installAmbientContext) installAmbientContext(alpine, registerOwnedMagic);
    alpine.magic = function (name, callback) {
      if (reservedAlpineMagics.has(name)) {
        throw pointedAlpineError("$" + name + " is reserved by Citry and cannot be overwritten.");
      }
      return registerOwnedMagic(name, callback);
    };
    if (installFillSourceDirective) installFillSourceDirective(alpine);
    var citryBoundaryDirective = function (el) {
      el.removeAttribute("x-citry-boundary");
      if (!preBoundarySeen.has(el)) {
        preBoundarySeen.add(el);
        Array.from(alpinePreBoundaryProviders.values()).forEach(function (provider) {
          provider(el);
        });
      }
      promoteRootHold(el);
      alpineBoundaryRoot = el;
      try {
        reconcileComponentLifecycles();
        flushCalls();
        Array.from(alpineInitProviders.values()).forEach(function (provider) {
          provider(el);
        });
      } finally {
        alpineBoundaryRoot = null;
      }
    };
    citryBoundaryDirective.inline = function (el) {
      var hold = rootHolds.get(el);
      if (hold && !hold.promoted) promoteRootHold(el);
    };
    alpine.directive("citry-boundary", citryBoundaryDirective).before("data");
    alpineHookCounts.installs += 1;
    alpine.addRootSelector(function () {
      var selectors = [];
      Array.from(alpineRootProviders.values()).forEach(function (provider) {
        var selector = provider();
        if (typeof selector === "string" && selector) selectors.push(selector);
      });
      // A selector callback must always return valid CSS, even before the
      // first provider registers.
      return selectors.length ? selectors.join(",") : "[data-citry-alpine-root]";
    });
    alpineHookCounts.roots += 1;
    alpine.interceptInit(function (el, skip) {
      rejectStructuralComponentClones(el);
      drainClientManifests();
      if (el.hasAttribute && el.hasAttribute("data-citry-root")) {
        // Alpine collects a whole initTree's directive callbacks before it
        // runs any of them. Skip descendants here, but let the root's first
        // citry-boundary handle run its inline phase. That phase promotes the
        // hold, so later root directives are not queued. The deferred boundary
        // handle then runs after already-queued ancestor directives and can
        // capture the initialized parent stack without deadlocking props.
        var hold = rootHolds.get(el);
        if (hold && !hold.promoted) {
          if (!preBoundarySeen.has(el)) el.setAttribute("x-citry-boundary", "");
          skip();
          return;
        }
        if (!preBoundarySeen.has(el)) el.setAttribute("x-citry-boundary", "");
      } else {
        Array.from(alpineInitProviders.values()).forEach(function (provider) {
          provider(el);
        });
      }
    });
    alpineHookCounts.init += 1;
    var queued = alpineBeforeStart;
    alpineBeforeStart = [];
    queued.forEach(runAlpineBeforeStart);
    return true;
  };

  var registerAlpineProvider = function (options) {
    alpineProviderCounter += 1;
    var token = alpineProviderCounter;
    if (options.root) alpineRootProviders.set(token, options.root);
    if (options.beforeBoundary) alpinePreBoundaryProviders.set(token, options.beforeBoundary);
    if (options.init) alpineInitProviders.set(token, options.init);
    if (options.mutations) alpineMutationProviders.set(token, options.mutations);
    if (options.beforeStart || options.afterStart) {
      alpineStartProviders.set(token, { before: options.beforeStart || null, after: options.afterStart || null });
    }
    return function () {
      alpineRootProviders.delete(token);
      alpinePreBoundaryProviders.delete(token);
      alpineInitProviders.delete(token);
      alpineMutationProviders.delete(token);
      alpineStartProviders.delete(token);
    };
  };

  var registerAlpineMagic = function (name, provider) {
    if (typeof name !== "string" || !name || typeof provider !== "function") {
      throw pointedAlpineError("a magic provider needs a non-empty name and a callback.");
    }
    if (reservedAlpineMagics.has(name)) {
      throw pointedAlpineError("$" + name + " is reserved by Citry and cannot be registered by an extension.");
    }
    var providers = alpineMagicProviders.get(name);
    if (!providers) {
      providers = new Map();
      alpineMagicProviders.set(name, providers);
      if (!alpineOwner) throw pointedAlpineError("the pinned runtime must install before internal magics register.");
      alpineOwner.magic(name, function (el) {
        var active = Array.from(providers.values());
        var current = active[active.length - 1];
        return current ? current(el) : undefined;
      });
    }
    alpineProviderCounter += 1;
    var token = alpineProviderCounter;
    providers.set(token, provider);
    return function () { providers.delete(token); };
  };

  // A10's deployment and performance canaries need counts from the owning
  // registries, not browser-specific heap heuristics. Keep this deliberately
  // aggregate: it exposes no author data, nodes, callbacks, or mutable
  // collections, and every number is recomputed from the current live state.
  var alpineRuntimeDebug = function () {
    var lifecycles = 0;
    var rootGroups = 0;
    var rootBindings = 0;
    var nativeListenerTargets = 0;
    var propsEffects = 0;
    var managedEffects = 0;
    var managedResources = 0;
    componentLifecycles.forEach(function (lifecycle) {
      if (!lifecycle.active) return;
      lifecycles += 1;
      if (lifecycle.rootGroup) {
        rootGroups += 1;
        lifecycle.rootGroup.bindings.forEach(function (binding) {
          rootBindings += 1;
          if (binding.targets instanceof Set) nativeListenerTargets += binding.targets.size;
        });
      }
      if (lifecycle.propsController && lifecycle.propsController.effectStop) propsEffects += 1;
      if (lifecycle.invocation && lifecycle.invocation.active) {
        managedEffects += lifecycle.invocation.effectStops.length;
        managedResources += lifecycle.invocation.resources.length;
        if (lifecycle.invocation.userCleanup) managedResources += 1;
      }
    });
    return Object.freeze({
      registrations: componentRegistrations.size,
      componentData: componentData.size,
      componentDataReferences: componentDataReferences.size,
      instanceDataOwners: instanceDataKeys.size,
      lifecycles: lifecycles,
      liveInstances: liveInstances.size,
      ownershipRevisions: ownershipGraphs.size,
      ownershipStates: ownershipStates.size,
      replayRevisions: seenOwnershipRevisions.size,
      dependencyClaims: consumedGraphDependencies.size,
      graphFailures: graphFailures.size,
      browserAnchors: browserAnchors.size,
      componentBoundaries: liveComponentBoundaries.size,
      fillSources: fillSourceDescriptors.size,
      rootGroups: rootGroups,
      rootBindings: rootBindings,
      nativeListenerTargets: nativeListenerTargets,
      propsEffects: propsEffects,
      managedEffects: managedEffects,
      managedResources: managedResources,
      ambientMagicFrames: ambientMagicFrames.size,
      pendingCalls: pendingCalls.length,
    });
  };

  var alpineApi = {
    beforeStart: function (callback) {
      if (typeof callback !== "function") throw pointedAlpineError("beforeStart(callback) needs a callback.");
      if (alpineStarted || alpineStarting || alpineStartError) {
        throw pointedAlpineError("beforeStart(callback) was called after Citry-owned startup.");
      }
      if (alpineOwner) runAlpineBeforeStart(callback);
      else alpineBeforeStart.push(callback);
    },
    _install: installAlpine,
    _ready: function () {
      if (!alpineOwner) throw pointedAlpineError("the runtime cannot become ready before Alpine installs.");
      alpineReady = true;
      flushCalls();
      startOwnedAlpine();
    },
    _start: function () {
      alpineStartRequested = true;
      startOwnedAlpine();
    },
    _holdStart: function () {
      alpineStartHolds += 1;
      var released = false;
      return function () {
        if (released) return;
        released = true;
        alpineStartHolds -= 1;
        startOwnedAlpine();
      };
    },
    _register: registerAlpineProvider,
    _magic: registerAlpineMagic,
    _runDirective: function (el, attributeName, registerCleanup, callback) {
      if (typeof runAmbientDirective !== "function") return callback();
      return runAmbientDirective(el, attributeName, registerCleanup, callback);
    },
    _morph: function (from, to, options) {
      if (!alpineOwner || typeof alpineOwner.morph !== "function") {
        throw pointedAlpineError("morph was requested before the pinned morph plugin installed.");
      }
      ensureOwnedAlpineGlobal();
      alpineHookCounts.morph += 1;
      return alpineOwner.morph(from, to, options);
    },
    _isolateScope: function (root, scope) {
      if (!alpineOwner) throw pointedAlpineError("scope attachment was requested before Alpine installed.");
      if (isolateRootScope) return isolateRootScope(root, scope);
      alpineOwner.addScopeToNode(root, scope);
      root._x_dataStack = root._x_dataStack.slice(0, 1);
    },
    _drain: function () { drainClientManifests(); },
    _isReady: function () { return alpineReady; },
    _isStarted: function () { return alpineStarted; },
    _debug: function () {
      return Object.freeze({
        installed: Boolean(alpineOwner),
        ready: alpineReady,
        started: alpineStarted,
        providers: alpineRootProviders.size,
        preBoundaryProviders: alpinePreBoundaryProviders.size,
        mutationProviders: alpineMutationProviders.size,
        magicNames: Array.from(alpineMagicProviders.keys()).sort(),
        hooks: Object.freeze(Object.assign({}, alpineHookCounts)),
        runtime: alpineRuntimeDebug(),
      });
    },
  };

  var utf8FromBinary = function (binary) {
    return decodeURIComponent(
      Array.prototype.map
        .call(binary, function (ch) {
          return "%" + ("00" + ch.charCodeAt(0).toString(16)).slice(-2);
        })
        .join("")
    );
  };

  var fromBase64 = function (value) {
    return utf8FromBinary(atob(value)); // atob alone mangles non-ASCII
  };

  var OWNERSHIP_COMMENT_PREFIX = "citry:g1";
  var OWNERSHIP_COMMENT_RE = new RegExp(
    "^" + OWNERSHIP_COMMENT_PREFIX + ":([0-9a-f]{64}):(\\d+):([ir]):(\\d+):([se])$"
  );

  // Construct same JSON as came from the server, so a SHA-256 hash of it can be compared
  // to the manifest's 'revision' attribute.
  // The server uses a canonical JSON encoder that sorts object keys and omits whitespace.
  // The client must do the same to avoid false mismatches.
  // NOTE: This is NOT a security feature. It is only a sanity check to detect accidental
  //       corruption of the manifest.
  var canonicalJson = function (value) {
    if (value === null || typeof value !== "object") return JSON.stringify(value);
    if (Array.isArray(value)) return "[" + value.map(canonicalJson).join(",") + "]";
    return (
      "{" +
      Object.keys(value)
        .sort()
        .map(function (key) { return JSON.stringify(key) + ":" + canonicalJson(value[key]); })
        .join(",") +
      "}"
    );
  };

  // Synchronous SHA-256 keeps graph validation available on ordinary HTTP
  // origins where SubtleCrypto may be unavailable.
  var sha256 = function (value) {
    var bytes = new TextEncoder().encode(value);
    var paddedLength = Math.ceil((bytes.length + 9) / 64) * 64;
    var padded = new Uint8Array(paddedLength);
    padded.set(bytes);
    padded[bytes.length] = 0x80;
    var view = new DataView(padded.buffer);
    view.setUint32(paddedLength - 8, Math.floor(bytes.length / 0x20000000), false);
    view.setUint32(paddedLength - 4, (bytes.length << 3) >>> 0, false);
    var constants = new Uint32Array([
      0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4,
      0xab1c5ed5, 0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe,
      0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f,
      0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
      0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc,
      0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b,
      0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116,
      0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
      0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7,
      0xc67178f2,
    ]);
    var hash = new Uint32Array([
      0x6a09e667,
      0xbb67ae85,
      0x3c6ef372,
      0xa54ff53a,
      0x510e527f,
      0x9b05688c,
      0x1f83d9ab,
      0x5be0cd19,
    ]);
    var words = new Uint32Array(64);
    var rotate = function (word, count) { return (word >>> count) | (word << (32 - count)); };
    for (var offset = 0; offset < paddedLength; offset += 64) {
      for (var index = 0; index < 16; index += 1) words[index] = view.getUint32(offset + index * 4, false);
      for (var expanded = 16; expanded < 64; expanded += 1) {
        var before15 = words[expanded - 15];
        var before2 = words[expanded - 2];
        var sigma0 = rotate(before15, 7) ^ rotate(before15, 18) ^ (before15 >>> 3);
        var sigma1 = rotate(before2, 17) ^ rotate(before2, 19) ^ (before2 >>> 10);
        words[expanded] = (words[expanded - 16] + sigma0 + words[expanded - 7] + sigma1) >>> 0;
      }
      var a = hash[0];
      var b = hash[1];
      var c = hash[2];
      var d = hash[3];
      var e = hash[4];
      var f = hash[5];
      var g = hash[6];
      var h = hash[7];
      for (var round = 0; round < 64; round += 1) {
        var sum1 = rotate(e, 6) ^ rotate(e, 11) ^ rotate(e, 25);
        var choice = (e & f) ^ (~e & g);
        var temporary1 = (h + sum1 + choice + constants[round] + words[round]) >>> 0;
        var sum0 = rotate(a, 2) ^ rotate(a, 13) ^ rotate(a, 22);
        var majority = (a & b) ^ (a & c) ^ (b & c);
        var temporary2 = (sum0 + majority) >>> 0;
        h = g;
        g = f;
        f = e;
        e = (d + temporary1) >>> 0;
        d = c;
        c = b;
        b = a;
        a = (temporary1 + temporary2) >>> 0;
      }
      hash[0] = (hash[0] + a) >>> 0;
      hash[1] = (hash[1] + b) >>> 0;
      hash[2] = (hash[2] + c) >>> 0;
      hash[3] = (hash[3] + d) >>> 0;
      hash[4] = (hash[4] + e) >>> 0;
      hash[5] = (hash[5] + f) >>> 0;
      hash[6] = (hash[6] + g) >>> 0;
      hash[7] = (hash[7] + h) >>> 0;
    }
    return Array.prototype.map
      .call(hash, function (word) { return ("00000000" + word.toString(16)).slice(-8); })
      .join("");
  };

  var ownershipRevision = function (manifest) {
    var unsigned = {};
    Object.keys(manifest).forEach(function (key) {
      if (key !== "revision") unsigned[key] = manifest[key];
    });
    return sha256(canonicalJson(unsigned));
  };

  var deepFreeze = function (value) {
    if (value === null || typeof value !== "object" || Object.isFrozen(value)) return value;
    Object.keys(value).forEach(function (key) { deepFreeze(value[key]); });
    return Object.freeze(value);
  };

  var isObject = function (value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
  };

  var exactKeys = function (value, keys, where) {
    if (!isObject(value)) throw new TypeError("[Citry] graph: " + where + " must be an object.");
    var actual = Object.keys(value).sort();
    var expected = keys.slice().sort();
    if (actual.length !== expected.length || actual.some(function (key, i) { return key !== expected[i]; })) {
      throw new TypeError("[Citry] graph: " + where + " has unknown or missing fields.");
    }
  };

  var integer = function (value, where, minimum) {
    if (!Number.isSafeInteger(value) || value < minimum) {
      throw new TypeError("[Citry] graph: " + where + " must be an integer >= " + minimum + ".");
    }
    return value;
  };

  var requiredString = function (value, where) {
    if (typeof value !== "string") {
      throw new TypeError("[Citry] graph: " + where + " must be a string.");
    }
    return value;
  };

  var nullableString = function (value, where) {
    return value === null ? null : requiredString(value, where);
  };

  var nullableInteger = function (value, where, minimum) {
    return value === null ? null : integer(value, where, minimum);
  };

  var uniqueId = function (set, value, where) {
    integer(value, where, 1);
    if (set.has(value)) throw new TypeError("[Citry] graph: duplicate " + where + " " + value + ".");
    set.add(value);
  };

  // In development the manifest carries source-location records and every
  // location reference resolves to one; in production sourceLocations is empty
  // and every reference is null. `provenance` is true only in development and
  // gates every check that looks a source-location record up.
  var validateClientBinding = function (clientBinding, locations, provenance, where) {
    exactKeys(clientBinding, ["key", "locationId", "payload", "source"], where);
    var bindingKey = requiredString(clientBinding.key, where + ".key");
    if (provenance) {
      if (!locations.has(integer(clientBinding.locationId, where + ".locationId", 1))) {
        throw new TypeError("[Citry] graph: " + where + " references an unknown location.");
      }
    } else if (clientBinding.locationId !== null) {
      throw new TypeError("[Citry] graph: " + where + ".locationId must be null in production.");
    }
    if (["direct", "server-dynamic", "spread"].indexOf(clientBinding.source) === -1) {
      throw new TypeError("[Citry] graph: " + where + ".source is invalid.");
    }
    var payload = clientBinding.payload;
    if (!isObject(payload) || typeof payload.type !== "string") {
      throw new TypeError("[Citry] graph: " + where + ".payload is invalid.");
    }
    if (payload.type === "props" || payload.type === "alpine-handler") {
      exactKeys(payload, ["expression", "type"], where + ".payload");
      requiredString(payload.expression, where + ".payload.expression");
      if (payload.type === "props" && bindingKey !== "$c-props") {
        throw new TypeError("[Citry] graph: a props client binding must use the $c-props key.");
      }
      if (
        payload.type === "alpine-handler" &&
        !(
          (bindingKey.indexOf("@") === 0 && bindingKey.indexOf("@c-") !== 0) ||
          bindingKey.indexOf("x-on:") === 0
        )
      ) {
        throw new TypeError("[Citry] graph: an Alpine-handler client binding has a non-Alpine key.");
      }
      return;
    }
    if (payload.type === "citry-dom-event") {
      exactKeys(
        payload,
        ["args", "classId", "debounce", "event", "handler", "key", "once", "prevent", "self", "stop", "throttle", "type"],
        where + ".payload"
      );
      ["once", "prevent", "self", "stop"].forEach(function (key) {
        if (typeof payload[key] !== "boolean") throw new TypeError("[Citry] graph: " + where + ".payload." + key + " must be boolean.");
      });
      requiredString(payload.classId, where + ".payload.classId");
      requiredString(payload.event, where + ".payload.event");
      requiredString(payload.handler, where + ".payload.handler");
      nullableString(payload.args, where + ".payload.args");
      nullableString(payload.key, where + ".payload.key");
      nullableInteger(payload.debounce, where + ".payload.debounce", 0);
      nullableInteger(payload.throttle, where + ".payload.throttle", 0);
      // The event segment decides poll-vs-DOM-event, matching the server's
      // classifier: "@c-poll.5s" is a poll, "@c-pollchange" is a DOM event.
      if (bindingKey.indexOf("@c-") !== 0 || bindingKey.slice(3).split(".")[0] === "poll") {
        throw new TypeError("[Citry] graph: a Citry DOM-event client binding has a non-event key.");
      }
      if (bindingKey.slice(3).split(".")[0] !== payload.event) {
        throw new TypeError("[Citry] graph: the Citry DOM-event client binding disagrees with its key.");
      }
      return;
    }
    if (payload.type === "citry-poll") {
      exactKeys(payload, ["args", "classId", "handler", "interval", "type"], where + ".payload");
      requiredString(payload.classId, where + ".payload.classId");
      requiredString(payload.handler, where + ".payload.handler");
      nullableString(payload.args, where + ".payload.args");
      integer(payload.interval, where + ".payload.interval", 1);
      if (bindingKey.indexOf("@c-poll.") !== 0) {
        throw new TypeError("[Citry] graph: a Citry poll client binding must use an @c-poll key.");
      }
      return;
    }
    throw new TypeError("[Citry] graph: " + where + ".payload.type is unknown.");
  };

  var validatePhysicalCaps = function (delimiterPrefix, revision, expected, root) {
    root = root || document;
    var prefix = delimiterPrefix + ":" + revision + ":";
    var comments = document.createTreeWalker(root, NodeFilter.SHOW_COMMENT);
    var found = new Map();
    var stack = [];
    var openSlotRegionsByGraph = new Map();
    var node;
    while ((node = comments.nextNode())) {
      var text = node.data.trim();
      if (text.indexOf(prefix) !== 0) continue;
      var match = /^(\d+):([ir]):(\d+):([se])$/.exec(text.slice(prefix.length));
      if (!match) throw new TypeError("[Citry] graph: malformed physical cap.");
      var graphId = match[1];
      var kind = match[2];
      var recordId = match[3];
      var side = match[4];
      var key = graphId + ":" + kind + ":" + recordId;
      if (!expected.has(key)) throw new TypeError("[Citry] graph: physical cap names an unknown record " + key + ".");
      var pair = found.get(key) || {};
      if (pair[side]) throw new TypeError("[Citry] graph: duplicate physical cap " + key + ".");
      pair[side] = node;
      found.set(key, pair);
      var openSlotRegions = openSlotRegionsByGraph.get(graphId) || [];
      if (side === "s") {
        pair.parentRegion = openSlotRegions.length ? openSlotRegions[openSlotRegions.length - 1] : null;
        stack.push(key);
        if (kind === "r") {
          openSlotRegions.push(Number(recordId));
          openSlotRegionsByGraph.set(graphId, openSlotRegions);
        }
      } else {
        if (stack.pop() !== key) throw new TypeError("[Citry] graph: physical caps cross or close out of order.");
        if (kind === "r") {
          if (openSlotRegions.pop() !== Number(recordId)) {
            throw new TypeError("[Citry] graph: physical slot region caps close out of order.");
          }
          if (!openSlotRegions.length) openSlotRegionsByGraph.delete(graphId);
        }
        var implicitDocumentBody =
          root === document && pair.s && pair.s.parentNode === document && node.parentNode === document.body;
        if (!pair.s || (pair.s.parentNode !== node.parentNode && !implicitDocumentBody)) {
          throw new TypeError("[Citry] graph: physical cap endpoints must share one parent.");
        }
      }
    }
    if (stack.length) throw new TypeError("[Citry] graph: an opening physical cap is unclosed.");
    expected.forEach(function (key) {
      var pair = found.get(key);
      if (!pair || !pair.s || !pair.e) {
        throw new TypeError(
          "[Citry] graph: missing physical cap " + key + ". " +
            "Preserve Citry ownership comments beginning with " + OWNERSHIP_COMMENT_PREFIX +
            " through minification, sanitization, and client DOM updates."
        );
      }
    });
    return found;
  };

  var stageOwnershipManifest = function (manifest, capRoot) {
    exactKeys(manifest, ["delimiters", "graphs", "mode", "protocol", "revision"], "manifest");
    if (manifest.protocol !== "citry-client-graph/1") throw new TypeError("[Citry] graph: unsupported protocol.");
    if (!/^[0-9a-f]{64}$/.test(manifest.revision)) throw new TypeError("[Citry] graph: revision must be lowercase SHA-256 hex.");
    if (ownershipRevision(manifest) !== manifest.revision) {
      throw new TypeError("[Citry] graph: revision does not match the canonical manifest.");
    }
    exactKeys(manifest.delimiters, ["format"], "delimiters");
    if (manifest.delimiters.format !== OWNERSHIP_COMMENT_PREFIX) throw new TypeError("[Citry] graph: unsupported delimiter format.");
    // Development ships source-location records; production keeps the
    // sourceLocations arrays empty and nulls every location reference.
    // `provenance` is true only in development.
    if (manifest.mode !== "production" && manifest.mode !== "development") {
      throw new TypeError("[Citry] graph: mode must be 'production' or 'development'.");
    }
    var provenance = manifest.mode === "development";
    if (!Array.isArray(manifest.graphs)) throw new TypeError("[Citry] graph: graphs must be an array.");
    var expectedCaps = new Set();
    var graphIds = new Set();
    var instancesByInvocationByGraph = [];
    var stagedGraphs = manifest.graphs.map(function (graph, graphIndex) {
      exactKeys(graph, ["componentClasses", "componentExecutionOrderConstraints", "componentInstances", "fills", "graphId", "nestedComponents", "slotRegions", "sourceLocations"], "graphs[" + graphIndex + "]");
      integer(graph.graphId, "graphs[" + graphIndex + "].graphId", 0);
      if (graphIds.has(graph.graphId)) throw new TypeError("[Citry] graph: duplicate graph id.");
      graphIds.add(graph.graphId);
      if (graph.graphId !== graphIndex) throw new TypeError("[Citry] graph: graph ids must be dense and ordered.");
      ["componentClasses", "componentExecutionOrderConstraints", "componentInstances", "fills", "nestedComponents", "slotRegions", "sourceLocations"].forEach(function (key) {
        if (!Array.isArray(graph[key])) throw new TypeError("[Citry] graph: graphs[" + graphIndex + "]." + key + " must be an array.");
      });
      // Production carries no source-location records; fail closed if any leak.
      if (!provenance && graph.sourceLocations.length) {
        throw new TypeError("[Citry] graph: production graphs must carry no sourceLocations records.");
      }
      var classIds = new Set();
      graph.componentClasses.forEach(function (record, index) {
        var where = "graphs[" + graphIndex + "].componentClasses[" + index + "]";
        exactKeys(record, ["classId", "className"], where);
        var classId = record.classId;
        if (classIds.has(classId)) throw new TypeError("[Citry] graph: duplicate class id.");
        classIds.add(classId);
      });
      var instanceIds = new Set();
      var renderIds = new Set();
      var instanceRecords = [];
      var instancesByInvocation = new Map();
      var instancesById = new Map();
      var classesByRender = new Map();
      graph.componentInstances.forEach(function (record, index) {
        var where = "graphs[" + graphIndex + "].componentInstances[" + index + "]";
        exactKeys(record, ["classId", "instanceId", "invocationId", "parentRenderId", "renderId", "transparent"], where);
        uniqueId(instanceIds, record.instanceId, where + ".instanceId");
        var render = record.renderId;
        if (!/^[a-z0-9_-]+$/.test(render)) {
          throw new TypeError("[Citry] graph: render ID must be safe for a case-insensitive HTML attribute name.");
        }
        if (renderIds.has(render)) throw new TypeError("[Citry] graph: duplicate render id.");
        renderIds.add(render);
        var classId = record.classId;
        if (!classIds.has(classId)) throw new TypeError("[Citry] graph: instance class is unknown.");
        nullableInteger(record.invocationId, where + ".invocationId", 1);
        if (typeof record.transparent !== "boolean") throw new TypeError("[Citry] graph: transparent must be boolean.");
        expectedCaps.add(graphIndex + ":i:" + record.instanceId);
        instanceRecords.push(record);
        if (record.invocationId != null) {
          var invocationTargets = instancesByInvocation.get(record.invocationId) || [];
          invocationTargets.push(record);
          instancesByInvocation.set(record.invocationId, invocationTargets);
        }
        instancesById.set(record.instanceId, { render: render, classId: classId });
        classesByRender.set(render, classId);
      });
      instanceRecords.forEach(function (record) {
        var parent = record.parentRenderId;
        if (parent != null && !renderIds.has(parent)) {
          throw new TypeError("[Citry] graph: instance parent is unknown.");
        }
      });
      var logicalParents = new Map();
      instanceRecords.forEach(function (record) {
        logicalParents.set(record.renderId, record.parentRenderId);
      });
      var visitingInstances = new Set();
      var visitedInstances = new Set();
      var visitInstance = function (renderId) {
        if (visitingInstances.has(renderId)) {
          throw new TypeError("[Citry] graph: logical instance ancestry contains a cycle.");
        }
        if (visitedInstances.has(renderId)) return;
        visitingInstances.add(renderId);
        var parentRenderId = logicalParents.get(renderId);
        if (parentRenderId != null) visitInstance(parentRenderId);
        visitingInstances.delete(renderId);
        visitedInstances.add(renderId);
      };
      renderIds.forEach(visitInstance);
      var renderRef = function (value, where, nullable) {
        if (value == null) {
          if (nullable) return null;
          throw new TypeError("[Citry] graph: " + where + " is an unknown render.");
        }
        if (!renderIds.has(value)) {
          throw new TypeError("[Citry] graph: " + where + " is an unknown render.");
        }
        return value;
      };
      var classRef = function (value, where, nullable) {
        if (value == null) {
          if (nullable) return null;
          throw new TypeError("[Citry] graph: " + where + " is an unknown class.");
        }
        if (!classIds.has(value)) {
          throw new TypeError("[Citry] graph: " + where + " is an unknown class.");
        }
        return value;
      };
      // Empty in production (asserted above), so this loop runs only in development.
      var locations = new Set();
      var locationRecords = new Map();
      graph.sourceLocations.forEach(function (record, index) {
        var where = "graphs[" + graphIndex + "].sourceLocations[" + index + "]";
        exactKeys(record, ["carrierInstanceId", "kind", "locationId", "mappingIndex", "mappingKey", "origin", "ownerClassId", "ownerRenderId", "sourceOffset", "sourcePos"], where);
        uniqueId(locations, record.locationId, where + ".locationId");
        var carrierId = integer(record.carrierInstanceId, where + ".carrierInstanceId", 1);
        if (!instanceIds.has(carrierId)) throw new TypeError("[Citry] graph: unknown source carrier.");
        var locationClass = record.ownerClassId;
        var locationOwner = record.ownerRenderId;
        if (!classIds.has(locationClass) || !renderIds.has(locationOwner)) throw new TypeError("[Citry] graph: source owner is unknown.");
        if (classesByRender.get(locationOwner) !== locationClass) {
          throw new TypeError("[Citry] graph: source owner and class do not match.");
        }
        var carrier = instancesById.get(carrierId);
        if (!carrier || carrier.render !== locationOwner) {
          throw new TypeError("[Citry] graph: source carrier and owner do not match.");
        }
        if (["component-call", "component-tag-client-binding", "implicit-fill", "named-fill", "fallback-fill", "slot-outlet"].indexOf(record.kind) === -1) {
          throw new TypeError("[Citry] graph: source location kind is invalid.");
        }
        nullableInteger(record.mappingIndex, where + ".mappingIndex", 0);
        exactKeys(record.sourceOffset, ["end", "start"], where + ".sourceOffset");
        integer(record.sourceOffset.start, where + ".sourceOffset.start", 0);
        integer(record.sourceOffset.end, where + ".sourceOffset.end", record.sourceOffset.start);
        exactKeys(record.sourcePos, ["column", "line"], where + ".sourcePos");
        integer(record.sourcePos.line, where + ".sourcePos.line", 1);
        integer(record.sourcePos.column, where + ".sourcePos.column", 1);
        locationRecords.set(record.locationId, { owner: locationOwner, classId: locationClass, kind: record.kind });
      });
      var invocationIds = new Set();
      var invocationRecords = new Map();
      graph.nestedComponents.forEach(function (record, index) {
        var where = "graphs[" + graphIndex + "].nestedComponents[" + index + "]";
        exactKeys(record, ["invocationId", "locationId", "parentRegionId", "clientBindings", "sourceClassId", "sourceRenderId", "tagName", "targetClassId", "targetRenderId"], where);
        uniqueId(invocationIds, record.invocationId, where + ".invocationId");
        if (provenance) {
          if (!locations.has(integer(record.locationId, where + ".locationId", 1))) throw new TypeError("[Citry] graph: invocation location is unknown.");
        } else if (record.locationId !== null) {
          throw new TypeError("[Citry] graph: " + where + ".locationId must be null in production.");
        }
        var source = record.sourceRenderId;
        var sourceClass = record.sourceClassId;
        var target = record.targetRenderId;
        var targetClass = record.targetClassId;
        if (!renderIds.has(source) || !renderIds.has(target)) throw new TypeError("[Citry] graph: invocation endpoint is unknown.");
        if (!classIds.has(sourceClass) || !classIds.has(targetClass)) throw new TypeError("[Citry] graph: invocation class is unknown.");
        if (classesByRender.get(source) !== sourceClass || classesByRender.get(target) !== targetClass) {
          throw new TypeError("[Citry] graph: invocation endpoint and class do not match.");
        }
        if (provenance) {
          var invocationLocation = locationRecords.get(record.locationId);
          if (!invocationLocation || invocationLocation.owner !== source || invocationLocation.classId !== sourceClass) {
            throw new TypeError("[Citry] graph: invocation location has the wrong source owner.");
          }
          if (invocationLocation.kind !== "component-call") {
            throw new TypeError("[Citry] graph: invocation location has the wrong kind.");
          }
        }
        nullableInteger(record.parentRegionId, where + ".parentRegionId", 1);
        if (!Array.isArray(record.clientBindings)) throw new TypeError("[Citry] graph: clientBindings must be an array.");
        record.clientBindings.forEach(function (clientBinding, clientBindingIndex) {
          validateClientBinding(clientBinding, locations, provenance, where + ".clientBindings[" + clientBindingIndex + "]");
          if (provenance) {
            var clientBindingLocation = locationRecords.get(clientBinding.locationId);
            if (!clientBindingLocation || clientBindingLocation.owner !== source || clientBindingLocation.classId !== sourceClass) {
              throw new TypeError("[Citry] graph: component-tag client binding location has the wrong source owner.");
            }
            if (clientBindingLocation.kind !== "component-tag-client-binding") {
              throw new TypeError("[Citry] graph: component-tag client binding location has the wrong kind.");
            }
          }
          if (
            (clientBinding.payload.type === "citry-dom-event" || clientBinding.payload.type === "citry-poll") &&
            clientBinding.payload.classId !== sourceClass
          ) {
            throw new TypeError("[Citry] graph: Citry client-binding handler class is not the source parent.");
          }
        });
        invocationRecords.set(record.invocationId, { parent: source, child: target });
      });
      instanceRecords.forEach(function (record) {
        var render = record.renderId;
        var parent = record.parentRenderId;
        if (record.invocationId == null) {
          if (parent != null) throw new TypeError("[Citry] graph: an uninvoked instance cannot name a parent.");
          return;
        }
        var invocation = invocationRecords.get(record.invocationId);
        if (!invocation) throw new TypeError("[Citry] graph: instance invocation is unknown.");
        if (invocation.child !== render || invocation.parent !== parent) {
          throw new TypeError("[Citry] graph: instance endpoints do not match their invocation.");
        }
      });
      invocationRecords.forEach(function (invocation, invocationId) {
        var target = instancesByInvocation.get(invocationId) || [];
        if (target.length !== 1) {
          throw new TypeError("[Citry] graph: every invocation must bind exactly one target instance.");
        }
      });
      var fillIds = new Set();
      var fillRecords = new Map();
      graph.fills.forEach(function (record, index) {
        var where = "graphs[" + graphIndex + "].fills[" + index + "]";
        exactKeys(record, ["fallbackLocationId", "fillId", "kind", "locationId", "ownerClassId", "ownerRenderId", "policy", "receiverClassId", "receiverRenderId", "slotName", "sourceInvocationId"], where);
        uniqueId(fillIds, record.fillId, where + ".fillId");
        if (["implicit", "named", "fallback", "python", "typed-default"].indexOf(record.kind) === -1) throw new TypeError("[Citry] graph: fill kind is invalid.");
        if (["template", "python-detached", "typed-default-detached"].indexOf(record.policy) === -1) throw new TypeError("[Citry] graph: fill policy is invalid.");
        var owner = renderRef(record.ownerRenderId, where + ".ownerRenderId", true);
        var ownerClass = classRef(record.ownerClassId, where + ".ownerClassId", true);
        var receiver = renderRef(record.receiverRenderId, where + ".receiverRenderId", true);
        var receiverClass = classRef(record.receiverClassId, where + ".receiverClassId", true);
        if ((owner == null) !== (ownerClass == null) || (owner != null && classesByRender.get(owner) !== ownerClass)) {
          throw new TypeError("[Citry] graph: fill owner and class do not match.");
        }
        if (
          (receiver == null) !== (receiverClass == null) ||
          (receiver != null && classesByRender.get(receiver) !== receiverClass)
        ) {
          throw new TypeError("[Citry] graph: fill receiver and class do not match.");
        }
        if (provenance) {
          ["locationId", "fallbackLocationId"].forEach(function (key) {
            var value = nullableInteger(record[key], where + "." + key, 1);
            if (value != null && !locations.has(value)) throw new TypeError("[Citry] graph: fill location is unknown.");
          });
        } else if (record.locationId !== null || record.fallbackLocationId !== null) {
          throw new TypeError("[Citry] graph: fill location references must be null in production.");
        }
        var sourceLocation = record.locationId == null ? null : locationRecords.get(record.locationId);
        var fallbackLocation = record.fallbackLocationId == null ? null : locationRecords.get(record.fallbackLocationId);
        var sourceInvocation = nullableInteger(record.sourceInvocationId, where + ".sourceInvocationId", 1);
        if (sourceInvocation != null && !invocationIds.has(sourceInvocation)) {
          throw new TypeError("[Citry] graph: fill source invocation is unknown.");
        }
        // Source-location consistency lives only in development; production
        // carries no locations, so these are checked only when provenance is on.
        if (provenance) {
          if ((owner == null) !== (sourceLocation == null)) {
            throw new TypeError("[Citry] graph: fill owner and source location must be present together.");
          }
          if (sourceLocation && (sourceLocation.owner !== owner || sourceLocation.classId !== ownerClass)) {
            throw new TypeError("[Citry] graph: fill source location has the wrong owner.");
          }
          if (fallbackLocation && (fallbackLocation.owner !== receiver || fallbackLocation.classId !== receiverClass)) {
            throw new TypeError("[Citry] graph: fill fallback location has the wrong receiver.");
          }
        }
        if (record.policy === "template") {
          if (owner == null || receiver == null || ["implicit", "named", "fallback"].indexOf(record.kind) === -1) {
            throw new TypeError("[Citry] graph: template fill ownership is inconsistent.");
          }
          if (provenance) {
            var expectedSourceKind = {
              implicit: "implicit-fill",
              named: "named-fill",
              fallback: "fallback-fill",
            }[record.kind];
            if (!sourceLocation || sourceLocation.kind !== expectedSourceKind) {
              throw new TypeError("[Citry] graph: template fill source location has the wrong kind.");
            }
          }
          if (record.kind === "fallback") {
            // A fallback fill never names a source call; its slot-outlet source
            // location is dev-only, so only its kind check is gated.
            if (sourceInvocation != null) {
              throw new TypeError("[Citry] graph: fallback fill source carrier is inconsistent.");
            }
            if (provenance && (!fallbackLocation || fallbackLocation.kind !== "slot-outlet")) {
              throw new TypeError("[Citry] graph: fallback fill source carrier is inconsistent.");
            }
          } else {
            var supplyInvocation = sourceInvocation == null ? null : invocationRecords.get(sourceInvocation);
            if (
              !supplyInvocation || supplyInvocation.parent !== owner ||
              fallbackLocation != null
            ) {
              throw new TypeError("[Citry] graph: supplied fill source carrier is inconsistent.");
            }
          }
        } else if (record.policy === "python-detached") {
          if (
            record.kind !== "python" || owner != null || receiver == null ||
            sourceInvocation != null || fallbackLocation != null
          ) {
            throw new TypeError("[Citry] graph: detached Python fill ownership is inconsistent.");
          }
        } else if (
          record.kind !== "typed-default" || owner != null || receiver == null ||
          sourceInvocation != null || fallbackLocation != null
        ) {
          throw new TypeError("[Citry] graph: detached typed-default fill ownership is inconsistent.");
        }
        fillRecords.set(record.fillId, {
          owner: owner,
          receiver: receiver,
          sourceLocation: record.locationId,
          sourceInvocation: sourceInvocation,
        });
      });
      var slotRegionIds = new Set();
      var slotRegionRecords = new Map();
      graph.slotRegions.forEach(function (record, index) {
        var where = "graphs[" + graphIndex + "].slotRegions[" + index + "]";
        exactKeys(record, ["fillId", "ownerRenderId", "parentRegionId", "receiverRenderId", "regionId", "resultOwnerRenderId", "slotLocationId", "sourceLocationId", "transitionFromRenderId"], where);
        uniqueId(slotRegionIds, record.regionId, where + ".regionId");
        if (!fillIds.has(integer(record.fillId, where + ".fillId", 1))) throw new TypeError("[Citry] graph: slot region fill is unknown.");
        var owner = renderRef(record.ownerRenderId, where + ".ownerRenderId", true);
        var receiver = renderRef(record.receiverRenderId, where + ".receiverRenderId", true);
        renderRef(record.resultOwnerRenderId, where + ".resultOwnerRenderId", true);
        var transitionFrom = renderRef(record.transitionFromRenderId, where + ".transitionFromRenderId", true);
        if (provenance) {
          ["slotLocationId", "sourceLocationId"].forEach(function (key) {
            var value = nullableInteger(record[key], where + "." + key, 1);
            if (value != null && !locations.has(value)) throw new TypeError("[Citry] graph: slot region location is unknown.");
          });
        } else if (record.slotLocationId !== null || record.sourceLocationId !== null) {
          throw new TypeError("[Citry] graph: slot region location references must be null in production.");
        }
        nullableInteger(record.parentRegionId, where + ".parentRegionId", 1);
        var fill = fillRecords.get(record.fillId);
        if (!fill || fill.owner !== owner || fill.receiver !== receiver || fill.sourceLocation !== record.sourceLocationId) {
          throw new TypeError("[Citry] graph: slot region ownership does not match its logical fill.");
        }
        if (provenance) {
          var slotLocation = record.slotLocationId == null ? null : locationRecords.get(record.slotLocationId);
          if (slotLocation && slotLocation.owner !== receiver) {
            throw new TypeError("[Citry] graph: slot region location has the wrong receiver.");
          }
          if (slotLocation && slotLocation.kind !== "slot-outlet") {
            throw new TypeError("[Citry] graph: slot region location has the wrong kind.");
          }
        }
        slotRegionRecords.set(record.regionId, {
          owner: owner,
          receiver: receiver,
          parent: record.parentRegionId,
          transitionFrom: transitionFrom,
        });
        expectedCaps.add(graphIndex + ":r:" + record.regionId);
      });
      graph.slotRegions.forEach(function (record) {
        if (record.parentRegionId != null && !slotRegionIds.has(record.parentRegionId)) throw new TypeError("[Citry] graph: parent slot region is unknown.");
      });
      graph.nestedComponents.forEach(function (record) {
        if (record.parentRegionId != null && !slotRegionIds.has(record.parentRegionId)) throw new TypeError("[Citry] graph: nested component parent slot region is unknown.");
      });
      var executionConstraintsByParent = new Map();
      graph.componentExecutionOrderConstraints.forEach(function (record, index) {
        var where = "graphs[" + graphIndex + "].componentExecutionOrderConstraints[" + index + "]";
        exactKeys(record, ["childRenderId", "invocationId", "parentRenderId"], where);
        if (!invocationIds.has(integer(record.invocationId, where + ".invocationId", 1))) throw new TypeError("[Citry] graph: component execution order constraint references an unknown nested component.");
        var parent = record.parentRenderId;
        var child = record.childRenderId;
        if (!renderIds.has(parent) || !renderIds.has(child)) throw new TypeError("[Citry] graph: component execution order constraint endpoint is unknown.");
        var invocation = invocationRecords.get(record.invocationId);
        if (!invocation || invocation.parent !== parent || invocation.child !== child) {
          throw new TypeError(
            "[Citry] graph: component execution order constraint does not match its invocation."
          );
        }
        var children = executionConstraintsByParent.get(parent) || [];
        children.push(child);
        executionConstraintsByParent.set(parent, children);
      });
      var visiting = new Set();
      var visited = new Set();
      var visit = function (render) {
        if (visiting.has(render)) {
          throw new TypeError("[Citry] graph: component execution order contains a cycle.");
        }
        if (visited.has(render)) return;
        visiting.add(render);
        (executionConstraintsByParent.get(render) || []).forEach(visit);
        visiting.delete(render);
        visited.add(render);
      };
      renderIds.forEach(visit);
      var visitingSlotRegions = new Set();
      var visitedSlotRegions = new Set();
      var visitSlotRegion = function (regionId) {
        if (visitingSlotRegions.has(regionId)) throw new TypeError("[Citry] graph: slot region ancestry contains a cycle.");
        if (visitedSlotRegions.has(regionId)) return;
        visitingSlotRegions.add(regionId);
        var region = slotRegionRecords.get(regionId);
        if (region && region.parent != null) visitSlotRegion(region.parent);
        visitingSlotRegions.delete(regionId);
        visitedSlotRegions.add(regionId);
      };
      slotRegionIds.forEach(visitSlotRegion);
      slotRegionRecords.forEach(function (region) {
        var expectedTransition = region.parent == null ? region.receiver : slotRegionRecords.get(region.parent).owner;
        if (region.transitionFrom !== expectedTransition) {
          throw new TypeError("[Citry] graph: slot region scope transition does not match its ancestry.");
        }
      });
      instancesByInvocationByGraph[graphIndex] = instancesByInvocation;
      return graph;
    });
    var caps = validatePhysicalCaps(manifest.delimiters.format, manifest.revision, expectedCaps, capRoot || document);
    stagedGraphs.forEach(function (graph, graphIndex) {
      graph.slotRegions.forEach(function (region) {
        var pair = caps.get(graphIndex + ":r:" + region.regionId);
        if (!pair || pair.parentRegion !== region.parentRegionId) {
          throw new TypeError("[Citry] graph: slot region ancestry does not match physical cap nesting.");
        }
      });
      graph.nestedComponents.forEach(function (invocation) {
        var targets = instancesByInvocationByGraph[graphIndex].get(invocation.invocationId) || [];
        var target = targets[0];
        var pair = target && caps.get(graphIndex + ":i:" + target.instanceId);
        if (!pair || pair.parentRegion !== invocation.parentRegionId) {
          throw new TypeError("[Citry] graph: nested component parent slot region does not match physical cap nesting.");
        }
      });
    });
    caps.forEach(Object.freeze);
    stagedGraphs.forEach(deepFreeze);
    return Object.freeze({ revision: manifest.revision, graphs: Object.freeze(stagedGraphs), caps: caps });
  };

  // A read-only Map-shaped view. Object.freeze(new Map()) does not prevent
  // callers from mutating its entries, so committed registry indexes expose
  // snapshots through this small query-only surface instead.
  var readOnlyIndex = function (map, snapshot) {
    var expose = snapshot || function (value) { return value; };
    return Object.freeze({
      get size() { return map.size; },
      has: function (key) { return map.has(key); },
      get: function (key) {
        var value = map.get(key);
        return value === undefined ? undefined : expose(value);
      },
      keys: function () { return Array.from(map.keys()); },
      values: function () { return Array.from(map.values()).map(expose); },
      entries: function () {
        return Array.from(map.entries()).map(function (entry) { return [entry[0], expose(entry[1])]; });
      },
    });
  };

  var qualifiedGraphId = function (graphId, kind, localId) {
    return "g" + graphId + ":" + kind + ":" + localId;
  };

  var decodeClientBindingPayload = function (payload) {
    if (payload.type === "props" || payload.type === "alpine-handler") {
      return Object.freeze({ type: payload.type, expression: payload.expression });
    }
    if (payload.type === "citry-poll") {
      return Object.freeze({
        type: payload.type,
        classId: payload.classId,
        handler: payload.handler,
        args: payload.args,
        interval: payload.interval,
      });
    }
    return Object.freeze({
      type: payload.type,
      classId: payload.classId,
      event: payload.event,
      handler: payload.handler,
      args: payload.args,
      key: payload.key,
      once: payload.once,
      prevent: payload.prevent,
      self: payload.self,
      stop: payload.stop,
      debounce: payload.debounce,
      throttle: payload.throttle,
    });
  };

  var makeClientIdentity = function (revision, graphId, instanceId, renderId, classId) {
    var anchorState = {
      id: "a:" + revision + ":" + graphId + ":" + instanceId,
      active: true,
      revision: revision,
      renderId: renderId,
      classId: classId,
      logical: null,
      events: null,
      generation: 1,
    };
    var logicalState = {
      id: "l:" + revision + ":" + graphId + ":" + instanceId + ":1",
      active: true,
      revision: revision,
      renderId: renderId,
      classId: classId,
      anchor: null,
      generation: 1,
      lifecycle: null,
      scope: null,
      els: [],
      parentLogical: null,
    };
    var anchor = {};
    Object.defineProperties(anchor, {
      id: { value: anchorState.id, enumerable: true },
      active: { get: function () { return anchorState.active; }, enumerable: true },
      revision: { get: function () { return anchorState.revision; }, enumerable: true },
      renderId: { get: function () { return anchorState.renderId; }, enumerable: true },
      classId: { get: function () { return anchorState.classId; }, enumerable: true },
      logicalInstance: { get: function () { return anchorState.logical; }, enumerable: true },
      events: { get: function () { return anchorState.events; }, enumerable: true },
    });
    Object.freeze(anchor);
    var logical = {};
    Object.defineProperties(logical, {
      id: { value: logicalState.id, enumerable: true },
      generation: { value: logicalState.generation, enumerable: true },
      active: { get: function () { return logicalState.active; }, enumerable: true },
      revision: { get: function () { return logicalState.revision; }, enumerable: true },
      renderId: { get: function () { return logicalState.renderId; }, enumerable: true },
      classId: { get: function () { return logicalState.classId; }, enumerable: true },
      anchor: { get: function () { return logicalState.anchor; }, enumerable: true },
    });
    Object.freeze(logical);
    anchorState.logical = logical;
    logicalState.anchor = anchor;
    return { anchor: anchor, anchorState: anchorState, logical: logical, logicalState: logicalState };
  };

  // Decode the fully validated A2 arrays into graph-qualified records and
  // query indexes. No global registry changes happen here, so a failure in a
  // later record leaves every previously committed revision untouched.
  var normalizeOwnershipRevision = function (staged) {
    var graphs = new Map();
    var componentClasses = new Map();
    var componentInstances = new Map();
    var renderIds = new Map();
    var sourceLocations = new Map();
    var nestedComponents = new Map();
    var fills = new Map();
    var slotRegions = new Map();
    var slotRegionsByFill = new Map();
    var physicalRegions = new Map();
    var physicalPlacements = new Map();
    var componentExecutionOrderConstraints = new Map();
    var anchors = new Map();
    var logicalInstances = new Map();
    var renderLinks = new Map();
    var childrenByParent = new Map();
    var executionOrderParentByChild = new Map();
    var rangeGroups = new Map();
    var rangeGroupStates = new Map();

    staged.graphs.forEach(function (graph) {
      var graphRecord = Object.freeze({ id: graph.graphId });
      graphs.set(graph.graphId, graphRecord);
      graph.componentClasses.forEach(function (record) {
        var key = qualifiedGraphId(graph.graphId, "c", record.classId);
        componentClasses.set(key, Object.freeze({
          key: key,
          graphId: graph.graphId,
          classId: record.classId,
          name: record.className,
        }));
      });
      graph.componentInstances.forEach(function (record) {
        var key = qualifiedGraphId(graph.graphId, "i", record.instanceId);
        var renderId = record.renderId;
        if (renderIds.has(renderId)) {
          throw new TypeError("[Citry] graph: render id '" + renderId + "' appears in more than one graph.");
        }
        var identity = makeClientIdentity(staged.revision, graph.graphId, record.instanceId, renderId, record.classId);
        var link = { active: true, anchor: identity.anchor, logical: identity.logical };
        var instance = {
          key: key,
          graphId: graph.graphId,
          instanceId: record.instanceId,
          renderId: renderId,
          classId: record.classId,
          parentRenderId: record.parentRenderId,
          invocationId: record.invocationId,
          transparent: record.transparent,
        };
        Object.defineProperties(instance, {
          active: { get: function () { return link.active; }, enumerable: true },
          anchor: { get: function () { return link.anchor; }, enumerable: true },
          logicalInstance: { get: function () { return link.logical; }, enumerable: true },
        });
        Object.freeze(instance);
        componentInstances.set(key, instance);
        renderIds.set(renderId, instance);
        anchors.set(identity.anchor.id, identity.anchor);
        logicalInstances.set(identity.logical.id, identity.logical);
        renderLinks.set(renderId, {
          record: instance,
          link: link,
          anchorState: identity.anchorState,
          logicalState: identity.logicalState,
        });
        if (instance.parentRenderId != null) {
          var children = childrenByParent.get(instance.parentRenderId) || [];
          children.push(renderId);
          childrenByParent.set(instance.parentRenderId, children);
        }
      });
      graph.sourceLocations.forEach(function (record) {
        var key = qualifiedGraphId(graph.graphId, "l", record.locationId);
        sourceLocations.set(key, Object.freeze({
          key: key,
          graphId: graph.graphId,
          locationId: record.locationId,
          kind: record.kind,
          ownerRenderId: record.ownerRenderId,
          classId: record.ownerClassId,
          carrierInstanceId: record.carrierInstanceId,
          origin: record.origin,
          start: record.sourceOffset.start,
          end: record.sourceOffset.end,
          line: record.sourcePos.line,
          column: record.sourcePos.column,
          mappingKey: record.mappingKey,
          mappingIndex: record.mappingIndex,
        }));
      });
      graph.nestedComponents.forEach(function (record) {
        var key = qualifiedGraphId(graph.graphId, "v", record.invocationId);
        var clientBindings = record.clientBindings.map(function (clientBinding) {
          return Object.freeze({
            key: clientBinding.key,
            locationId: clientBinding.locationId,
            source: clientBinding.source,
            payload: decodeClientBindingPayload(clientBinding.payload),
          });
        });
        nestedComponents.set(key, Object.freeze({
          key: key,
          graphId: graph.graphId,
          invocationId: record.invocationId,
          locationId: record.locationId,
          parentRegionId: record.parentRegionId,
          sourceRenderId: record.sourceRenderId,
          sourceClassId: record.sourceClassId,
          tag: record.tagName,
          targetRenderId: record.targetRenderId,
          targetClassId: record.targetClassId,
          clientBindings: Object.freeze(clientBindings),
        }));
      });
      graph.fills.forEach(function (record) {
        var key = qualifiedGraphId(graph.graphId, "f", record.fillId);
        fills.set(key, Object.freeze({
          key: key,
          graphId: graph.graphId,
          fillId: record.fillId,
          kind: record.kind,
          policy: record.policy,
          slot: record.slotName,
          ownerRenderId: record.ownerRenderId,
          ownerClassId: record.ownerClassId,
          receiverRenderId: record.receiverRenderId,
          receiverClassId: record.receiverClassId,
          sourceLocationId: record.locationId,
          sourceInvocationId: record.sourceInvocationId,
          fallbackLocationId: record.fallbackLocationId,
        }));
      });
      graph.slotRegions.forEach(function (record) {
        var key = qualifiedGraphId(graph.graphId, "r", record.regionId);
        var cap = staged.caps.get(graph.graphId + ":r:" + record.regionId);
        var physical = Object.freeze({
          key: key,
          graphId: graph.graphId,
          regionId: record.regionId,
          start: cap.s,
          end: cap.e,
          startMarker: cap.s.data,
          endMarker: cap.e.data,
          parentRegionId: cap.parentRegion,
          topology: cap.s.parentNode === cap.e.parentNode ? "same-parent" : "document-body",
        });
        physicalRegions.set(key, physical);
        physicalPlacements.set(key, [physical]);
        slotRegions.set(key, Object.freeze({
          key: key,
          graphId: graph.graphId,
          regionId: record.regionId,
          fillId: record.fillId,
          ownerRenderId: record.ownerRenderId,
          receiverRenderId: record.receiverRenderId,
          resultOwnerRenderId: record.resultOwnerRenderId,
          transitionFromRenderId: record.transitionFromRenderId,
          parentRegionId: record.parentRegionId,
          slotLocationId: record.slotLocationId,
          sourceLocationId: record.sourceLocationId,
          physical: physical,
        }));
        var fillKey = qualifiedGraphId(graph.graphId, "f", record.fillId);
        var fillSlotRegions = slotRegionsByFill.get(fillKey) || [];
        fillSlotRegions.push(slotRegions.get(key));
        slotRegionsByFill.set(fillKey, fillSlotRegions);
      });
      graph.componentInstances.forEach(function (record) {
        var cap = staged.caps.get(graph.graphId + ":i:" + record.instanceId);
        var key = qualifiedGraphId(graph.graphId, "i", record.instanceId);
        var physical = Object.freeze({
          key: key,
          graphId: graph.graphId,
          instanceId: record.instanceId,
          start: cap.s,
          end: cap.e,
          startMarker: cap.s.data,
          endMarker: cap.e.data,
          parentRegionId: cap.parentRegion,
          topology: cap.s.parentNode === cap.e.parentNode ? "same-parent" : "document-body",
        });
        physicalRegions.set(key, physical);
        physicalPlacements.set(key, [physical]);
      });
      graph.componentExecutionOrderConstraints.forEach(function (record, index) {
        var key = qualifiedGraphId(graph.graphId, "d", index + 1);
        componentExecutionOrderConstraints.set(key, Object.freeze({
          key: key,
          graphId: graph.graphId,
          parentRenderId: record.parentRenderId,
          childRenderId: record.childRenderId,
          invocationId: record.invocationId,
        }));
        executionOrderParentByChild.set(record.childRenderId, record.parentRenderId);
      });
    });

    renderLinks.forEach(function (link) {
      if (link.record.parentRenderId == null) return;
      var parent = renderLinks.get(link.record.parentRenderId);
      if (parent) link.logicalState.parentLogical = parent.logicalState;
    });

    fills.forEach(function (fill) {
      var key = qualifiedGraphId(fill.graphId, "f", fill.fillId);
      var groupedRegions = slotRegionsByFill.get(key) || [];
      if (!groupedRegions.length) return;
      var groupState = {
        active: true,
        retired: false,
        els: [],
        liveSlotRegions: groupedRegions.slice(),
        slotRegions: groupedRegions,
      };
      var group = {
        key: key,
        graphId: fill.graphId,
        fillId: fill.fillId,
        slotRegions: Object.freeze(groupedRegions.slice()),
        els: groupState.els,
      };
      Object.defineProperties(group, {
        active: { enumerable: true, get: function () { return groupState.active; } },
        liveSlotRegions: {
          enumerable: true,
          get: function () { return Object.freeze(groupState.liveSlotRegions.slice()); },
        },
      });
      Object.freeze(group);
      rangeGroups.set(key, group);
      rangeGroupStates.set(key, groupState);
    });

    var registry = Object.freeze({
      graphs: readOnlyIndex(graphs),
      componentClasses: readOnlyIndex(componentClasses),
      componentInstances: readOnlyIndex(componentInstances),
      renderIds: readOnlyIndex(renderIds),
      sourceLocations: readOnlyIndex(sourceLocations),
      nestedComponents: readOnlyIndex(nestedComponents),
      fills: readOnlyIndex(fills),
      slotRegions: readOnlyIndex(slotRegions),
      physicalRegions: readOnlyIndex(physicalRegions),
      physicalPlacements: readOnlyIndex(physicalPlacements, function (placements) {
        return Object.freeze(placements.slice());
      }),
      componentExecutionOrderConstraints: readOnlyIndex(componentExecutionOrderConstraints),
      anchors: readOnlyIndex(anchors),
      logicalInstances: readOnlyIndex(logicalInstances),
      rangeGroups: readOnlyIndex(rangeGroups),
    });
    var publicRevision = Object.freeze({
      revision: staged.revision,
      graphs: staged.graphs,
      caps: readOnlyIndex(staged.caps),
      registry: registry,
    });
    return {
      publicRevision: publicRevision,
      registry: registry,
      caps: staged.caps,
      physicalRegions: physicalRegions,
      physicalPlacements: physicalPlacements,
      slotRegions: slotRegions,
      renderIds: renderIds,
      renderLinks: renderLinks,
      anchors: anchors,
      logicalInstances: logicalInstances,
      childrenByParent: childrenByParent,
      executionOrderParentByChild: executionOrderParentByChild,
      rangeGroupStates: rangeGroupStates,
      graphCalls: new Map(),
      provisional: false,
      adoption: null,
    };
  };

  var resolveOwnershipRoute = function (revision, renderId, classId) {
    var state = ownershipStates.get(revision);
    if (!state) {
      throw new TypeError("[Citry] graph: callback references unknown revision " + revision + ".");
    }
    var instance = state.renderIds.get(renderId);
    if (!instance || !instance.active) {
      throw new TypeError(
        "[Citry] graph: callback references inactive or unknown render id '" + renderId + "' in revision " + revision + "."
      );
    }
    if (classId != null && instance.classId !== classId) {
      throw new TypeError(
        "[Citry] graph: render id '" + renderId + "' belongs to class '" + instance.classId +
          "', not callback class '" + classId + "'."
      );
    }
    return Object.freeze({
      revision: revision,
      instance: instance,
      logicalInstance: instance.logicalInstance,
      anchor: instance.anchor,
    });
  };

  // ----- graph-owned component lifecycle and Alpine scope projection -----

  var replaceArrayContents = function (target, values) {
    target.splice.apply(target, [0, target.length].concat(values));
  };

  var routeForLifecycle = function (lifecycle) {
    if (!lifecycle.logicalState.active) return null;
    try {
      return resolveOwnershipRoute(
        lifecycle.logicalState.revision,
        lifecycle.logicalState.renderId,
        lifecycle.logicalState.classId
      );
    } catch (_err) {
      return null;
    }
  };

  var nodePrecedes = function (before, after) {
    return Boolean(before.compareDocumentPosition(after) & Node.DOCUMENT_POSITION_FOLLOWING);
  };

  var physicalRangesForKey = function (state, key) {
    var placements = state && state.physicalPlacements && state.physicalPlacements.get(key);
    if (placements) return placements;
    var physical = state && state.registry.physicalRegions.get(key);
    return physical ? [physical] : [];
  };

  var physicalRangeIsLive = function (state, physical) {
    if (!physical) return false;
    var staged = state.provisional && !physical.start.isConnected && !physical.end.isConnected;
    if (!staged && (!physical.start.isConnected || !physical.end.isConnected)) return false;
    if (physical.start.data !== physical.startMarker || physical.end.data !== physical.endMarker) return false;
    var topologyLive = staged
      ? physical.start.parentNode === physical.end.parentNode
      : physical.topology === "document-body"
      ? physical.start.parentNode === document && physical.end.parentNode === document.body
      : physical.start.parentNode === physical.end.parentNode;
    if (!topologyLive || !nodePrecedes(physical.start, physical.end)) return false;
    if (physical.parentRegionId != null) {
      var parent = physical.parentPlacement || state.registry.physicalRegions.get(
        qualifiedGraphId(physical.graphId, "r", physical.parentRegionId)
      );
      if (
        !parent || !physicalRangeIsLive(state, parent) ||
        !nodePrecedes(parent.start, physical.start) || !nodePrecedes(physical.end, parent.end)
      ) return false;
    }
    return true;
  };

  var physicalRangeCorruption = function (state, physical) {
    if (!physical || !physical.start.isConnected || !physical.end.isConnected) return null;
    if (physical.start.data !== physical.startMarker || physical.end.data !== physical.endMarker) {
      return "one of its load-bearing comment caps was changed";
    }
    var topologyLive = physical.topology === "document-body"
      ? physical.start.parentNode === document && physical.end.parentNode === document.body
      : physical.start.parentNode === physical.end.parentNode;
    if (!topologyLive) return "its comment caps no longer share the validated parent topology";
    if (!nodePrecedes(physical.start, physical.end)) return "its comment caps are reversed";
    if (physical.parentRegionId != null) {
      var parent = physical.parentPlacement || state.registry.physicalRegions.get(
        qualifiedGraphId(physical.graphId, "r", physical.parentRegionId)
      );
      if (
        !parent || !physicalRangeIsLive(state, parent) ||
        !nodePrecedes(parent.start, physical.start) || !nodePrecedes(physical.end, parent.end)
      ) return "it moved outside its recorded parent region";
    }
    return null;
  };

  var reportPhysicalRangeCorruption = function (state, physical) {
    var reason = physicalRangeCorruption(state, physical);
    if (!reason || expectedPhysicalRetirements.has(physical) || physicalCorruptionReports.has(physical)) return;
    physicalCorruptionReports.add(physical);
    console.error(
      "[Citry] ownership range '" + physical.key + "' was retired because " + reason +
        ". Preserve Citry ownership comments beginning with " + OWNERSHIP_COMMENT_PREFIX +
        " through minification, sanitization, and client DOM updates."
    );
  };

  var physicalRangeElements = function (physical) {
    var roots = [];
    var node = null;
    if (physical.topology === "document-body") {
      // A complete-document fragment can put the opening cap under Document
      // and the closing cap under body. Its markerless physical roots are the
      // direct body element children in the exact document-order interval.
      // This is the same narrow parser topology validated at adoption; it is
      // not a license to enumerate arbitrary marked nodes from the document.
      for (node = document.body.firstChild; node && node !== physical.end; node = node.nextSibling) {
        if (node instanceof Element && nodePrecedes(physical.start, node)) roots.push(node);
      }
      return roots;
    }
    if (physical.start.parentNode !== physical.end.parentNode) return roots;
    for (node = physical.start.nextSibling; node && node !== physical.end; node = node.nextSibling) {
      if (node instanceof Element) roots.push(node);
    }
    return roots;
  };

  var physicalRangeRoots = function (physical, renderId) {
    if (physical.topology === "same-parent") {
      var marker = "data-cid-" + renderId;
      var roots = [];
      physicalRangeElements(physical).forEach(function (topLevel) {
        if (topLevel.hasAttribute(marker)) {
          roots.push(topLevel);
          return;
        }
        // Serialization extensions may insert an unmarked visual wrapper
        // around the component's authored marked roots. Stay inside the exact
        // caps, select only the outermost matching descendants, and never
        // promote the extension wrapper into the component's public `els`.
        topLevel.querySelectorAll("[" + marker + "]").forEach(function (candidate) {
          var ancestor = candidate.parentElement;
          while (ancestor && ancestor !== topLevel) {
            if (ancestor.hasAttribute(marker)) return;
            ancestor = ancestor.parentElement;
          }
          roots.push(candidate);
        });
      });
      return roots;
    }
    // The HTML parser may place a complete-document opening cap under
    // Document and its closing cap under body. A2 validates this one narrow
    // topology, whose roots cannot be enumerated as ordinary siblings. The
    // document query is only a candidate source; both comparisons keep the
    // result inside the exact cap interval.
    return Array.prototype.slice.call(document.querySelectorAll("[data-cid-" + renderId + "]")).filter(
      function (candidate) {
        return nodePrecedes(physical.start, candidate) && nodePrecedes(candidate, physical.end);
      }
    );
  };

  var reconcilePhysicalRangeGroups = function () {
    ownershipStates.forEach(function (state) {
      state.rangeGroupStates.forEach(function (group) {
        if (group.retired) return;
        var livePlacements = [];
        group.slotRegions.forEach(function (region) {
          physicalRangesForKey(state, region.key).forEach(function (physical) {
            var isLive = physicalRangeIsLive(state, physical);
            if (!isLive) reportPhysicalRangeCorruption(state, physical);
            if (isLive) livePlacements.push({ region: region, physical: physical });
          });
        });
        livePlacements.sort(function (left, right) {
          if (nodePrecedes(left.physical.start, right.physical.start)) return -1;
          if (nodePrecedes(right.physical.start, left.physical.start)) return 1;
          return 0;
        });
        group.liveSlotRegions = livePlacements.map(function (entry) { return entry.region; });
        replaceArrayContents(group.els, livePlacements.flatMap(function (entry) {
          return physicalRangeElements(entry.physical);
        }));
        if (livePlacements.length) return;
        group.active = false;
        group.retired = true;
      });
    });
  };

  var RANGE_ISLAND_ATTR = "data-citry-range-island";
  var rangeCapInfo = function (node) {
    if (!(node instanceof Comment)) return null;
    var match = OWNERSHIP_COMMENT_RE.exec(node.data.trim());
    if (match) {
      return {
        key: OWNERSHIP_COMMENT_PREFIX + ":" + match[1] + ":" + match[2] + ":" + match[3] + ":" + match[4],
        side: match[5],
      };
    }
    match = /^citry:p1:([0-9a-f]{64}):([A-Za-z0-9_-]+):(\d+):([ir]):(\d+):([se])$/.exec(node.data.trim());
    if (!match) return null;
    return {
      key: "citry:p1:" + match[1] + ":" + match[2] + ":" + match[3] + ":" + match[4] + ":" + match[5],
      side: match[6],
    };
  };

  var directRangePairs = function (parent) {
    var stack = [];
    var pairs = [];
    Array.prototype.slice.call(parent.childNodes).forEach(function (node) {
      var info = rangeCapInfo(node);
      if (!info) return;
      if (info.side === "s") {
        stack.push({ key: info.key, start: node });
        return;
      }
      var opened = stack.pop();
      if (!opened || opened.key !== info.key) {
        throw new TypeError("[Citry] range morph received crossed or unmatched ownership caps near " + info.key + ".");
      }
      pairs.push({ key: info.key, start: opened.start, end: node, depth: stack.length });
    });
    if (stack.length) {
      throw new TypeError("[Citry] range morph received an ownership opening cap without its closing cap.");
    }
    return pairs.filter(function (pair) { return pair.depth === 0; });
  };

  var collapseRangePair = function (pair, stableAnchor) {
    var placeholder = document.createElement("template");
    placeholder.setAttribute(RANGE_ISLAND_ATTR, pair.key);
    placeholder.setAttribute("key", "citry-range:" + stableAnchor);
    if (pair.topology === "document-body") {
      var firstBodyNode = document.body.firstChild;
      placeholder._citryDocumentStart = {
        nodes: [],
        next: document.documentElement,
      };
      document.body.insertBefore(placeholder, firstBodyNode);
      for (var documentNode = pair.start; documentNode && documentNode !== document.documentElement;) {
        var documentNext = documentNode.nextSibling;
        placeholder._citryDocumentStart.nodes.push(documentNode);
        placeholder.content.append(documentNode);
        documentNode = documentNext;
      }
      for (var bodyNode = firstBodyNode; bodyNode;) {
        var bodyNext = bodyNode.nextSibling;
        placeholder.content.append(bodyNode);
        if (bodyNode === pair.end) break;
        bodyNode = bodyNext;
      }
      return placeholder;
    }
    pair.start.before(placeholder);
    for (var node = pair.start; node;) {
      var next = node.nextSibling;
      placeholder.content.append(node);
      if (node === pair.end) break;
      node = next;
    }
    return placeholder;
  };

  var rangePairCanCollapse = function (pair) {
    if (pair.topology === "document-body") {
      if (pair.start.parentNode !== document || pair.end.parentNode !== document.body) return false;
      for (var node = pair.start; node && node !== document.documentElement; node = node.nextSibling) {
        if (!(node instanceof Comment)) return false;
      }
      return node === document.documentElement;
    }
    return pair.start.parentNode instanceof Element && pair.start.parentNode === pair.end.parentNode;
  };

  var assertRangePairCanCollapse = function (pair) {
    if (rangePairCanCollapse(pair)) return;
    throw new TypeError(
      "[Citry] range morph cannot protect nested ownership caps with unsupported parent topology near " +
        pair.key + "."
    );
  };

  var physicalRangeContainsNode = function (physical, node) {
    return nodePrecedes(physical.start, node) && nodePrecedes(node, physical.end);
  };

  var physicalStableAnchor = function (state, physical) {
    var instance = state.registry.componentInstances.get(physical.key);
    if (instance) return instance.logicalInstance.id;
    var region = state.registry.slotRegions.get(physical.key);
    return region ? "fill:" + region.graphId + ":" + region.fillId + ":" + region.regionId : physical.key;
  };

  var nestedPhysicalRanges = function (state, outer) {
    var candidates = [];
    ownershipStates.forEach(function (candidateState) {
      candidateState.physicalPlacements.forEach(function (placements) {
        placements.forEach(function (physical) {
        if (
          (candidateState !== state || physical !== outer) &&
          physicalRangeIsLive(candidateState, physical) &&
          physicalRangeContainsNode(outer, physical.start) &&
          physicalRangeContainsNode(outer, physical.end)
        ) candidates.push({ state: candidateState, physical: physical });
        });
      });
    });
    return candidates.filter(function (candidate) {
      return !candidates.some(function (other) {
        return other !== candidate &&
          physicalRangeContainsNode(other.physical, candidate.physical.start) &&
          physicalRangeContainsNode(other.physical, candidate.physical.end);
      });
    });
  };

  var collapseIncomingRanges = function (root, correspondence) {
    var visit = function (parent) {
      var pairs = directRangePairs(parent);
      var covered = new Set();
      pairs.forEach(function (pair) {
        for (var node = pair.start; node;) {
          covered.add(node);
          if (node === pair.end) break;
          node = node.nextSibling;
        }
        var stable = correspondence && Object.prototype.hasOwnProperty.call(correspondence, pair.key)
          ? correspondence[pair.key]
          : "incoming:" + pair.key;
        collapseRangePair(pair, stable);
      });
      Array.prototype.slice.call(parent.children).forEach(function (child) {
        if (!covered.has(child) && !child.hasAttribute(RANGE_ISLAND_ATTR)) visit(child);
      });
    };
    visit(root);
  };

  var contextualRangeContainer = function (start, end, html) {
    if (!(start.parentElement instanceof Element) || start.parentNode !== end.parentNode) {
      throw new TypeError("[Citry] range morph needs operational comment caps under one Element parent.");
    }
    var range = document.createRange();
    range.setStartAfter(start);
    range.collapse(true);
    var fragment = range.createContextualFragment(html);
    var container = start.parentElement.cloneNode(false);
    container.removeAttribute("id");
    container.append(fragment);
    return container;
  };

  var expandRangePlaceholder = function (placeholder) {
    var documentStart = placeholder._citryDocumentStart;
    if (documentStart) {
      for (var index = 0; index < documentStart.nodes.length; index += 1) {
        var expected = documentStart.nodes[index];
        if (placeholder.content.firstChild !== expected) {
          throw new TypeError("[Citry] document-body ownership island lost one of its document-level caps.");
        }
        document.insertBefore(expected, documentStart.next);
      }
    }
    placeholder.before(placeholder.content);
    placeholder.remove();
  };

  var expandRangeIslands = function (physical) {
    var placeholders = [];
    physicalRangeElements(physical).forEach(function (root) {
      if (root.hasAttribute(RANGE_ISLAND_ATTR)) placeholders.push(root);
      root.querySelectorAll("template[" + RANGE_ISLAND_ATTR + "]").forEach(function (item) {
        placeholders.push(item);
      });
    });
    placeholders.forEach(function (placeholder) {
      if (!placeholder.isConnected || !physicalRangeContainsNode(physical, placeholder)) return;
      expandRangePlaceholder(placeholder);
    });
  };

  var morphOwnershipRange = function (revision, physicalKey, html, options) {
    if (typeof revision !== "string" || typeof physicalKey !== "string" || typeof html !== "string") {
      throw new TypeError("[Citry] range morph needs a revision, physical range key, and HTML string.");
    }
    options = options || {};
    var state = ownershipStates.get(revision);
    var physical = options.physical || (state && state.registry.physicalRegions.get(physicalKey));
    if (!state || !physical || !physicalRangeIsLive(state, physical)) {
      throw new TypeError("[Citry] range morph target is unknown, retired, or corrupt.");
    }
    if (!alpineOwner || typeof alpineOwner.morphBetween !== "function") {
      throw pointedAlpineError("range morph was requested before the pinned morphBetween adapter installed.");
    }
    var livePlaceholders = [];
    var nestedRanges = nestedPhysicalRanges(state, physical);
    var targetCanMorph = physical.topology === "document-body"
      ? physical.start.parentNode === document && physical.end.parentNode === document.body
      : physical.start.parentNode instanceof Element && physical.start.parentNode === physical.end.parentNode;
    if (!targetCanMorph) {
      throw new TypeError("[Citry] range morph target has unsupported parent topology.");
    }
    nestedRanges.forEach(function (nested) {
      assertRangePairCanCollapse({
        key: nested.physical.startMarker.slice(0, -2),
        start: nested.physical.start,
        end: nested.physical.end,
        topology: nested.physical.topology,
      });
    });
    var morphCursor = null;
    rangeMorphDepth += 1;
    try {
      nestedRanges.forEach(function (nested) {
        livePlaceholders.push(collapseRangePair(
          {
            key: nested.physical.startMarker.slice(0, -2),
            start: nested.physical.start,
            end: nested.physical.end,
            topology: nested.physical.topology,
          },
          physicalStableAnchor(nested.state, nested.physical)
        ));
      });
      var morphStart = physical.start;
      if (physical.topology === "document-body") {
        morphCursor = document.createComment("citry:range-morph-cursor");
        document.body.insertBefore(morphCursor, document.body.firstChild);
        morphStart = morphCursor;
      }
      var container = contextualRangeContainer(morphStart, physical.end, html);
      collapseIncomingRanges(container, options.correspondence || null);
      alpineOwner.morphBetween(morphStart, physical.end, container, {
        key: function (element) {
          if (element.hasAttribute(RANGE_ISLAND_ATTR)) return element.getAttribute("key");
          if (typeof options.key === "function") return options.key(element);
          return element.getAttribute("data-citry-key") || element.getAttribute("key") || element.id;
        },
      });
    } finally {
      try {
        expandRangeIslands(physical);
        livePlaceholders.forEach(function (placeholder) {
          // A removed nested island stays detached inside its inert holder;
          // normal cap liveness retirement owns its cleanup.
          if (placeholder.isConnected) placeholder.remove();
        });
        if (morphCursor && morphCursor.isConnected) morphCursor.remove();
      } finally {
        rangeMorphDepth -= 1;
        if (rangeMorphDepth === 0 && ownershipAdoptionDepth === 0) reconcileComponentLifecycles();
      }
    }
    return physical;
  };

  var lifecyclePhysicalRange = function (lifecycle) {
    var route = routeForLifecycle(lifecycle);
    var state = route && ownershipStates.get(route.revision);
    var physicals = state && route ? physicalRangesForKey(state, route.instance.key) : [];
    return {
      route: route,
      state: state,
      physical: physicals.length ? physicals[0] : null,
      physicals: physicals,
    };
  };

  // A component boundary is one logical listener surface even when its
  // rendered component has several element roots. Modifier state and global
  // listeners therefore belong to this group, not to individual elements.
  var ROOT_GROUP_ENTER_LEAVE = new Set(["mouseenter", "mouseleave", "pointerenter", "pointerleave"]);

  var rootGroupUnique = function (roots) {
    var seen = new Set();
    return roots.filter(function (root) {
      if (!(root instanceof Element)) throw new TypeError("[Citry] RootGroup members must be Elements.");
      if (seen.has(root)) return false;
      seen.add(root);
      return true;
    });
  };

  var rootGroupKebab = function (value) {
    if (value === " " || value === "_") return value;
    return value.replace(/([a-z])([A-Z])/g, "$1-$2").replace(/[_\s]/, "-").toLowerCase();
  };

  var rootGroupKeyAliases = function (key) {
    if (!key) return [];
    key = rootGroupKebab(key);
    var aliases = {
      ctrl: "control", slash: "/", space: " ", spacebar: " ", cmd: "meta", esc: "escape",
      up: "arrow-up", down: "arrow-down", left: "arrow-left", right: "arrow-right",
      period: ".", comma: ",", equal: "=", minus: "-", underscore: "_",
    };
    aliases[key] = key;
    return Object.keys(aliases).filter(function (name) { return aliases[name] === key; });
  };

  var rootGroupIsKeyEvent = function (event) { return event === "keydown" || event === "keyup"; };
  var rootGroupIsClickEvent = function (event) {
    return ["contextmenu", "click", "mouse"].some(function (part) { return event.indexOf(part) !== -1; });
  };
  var rootGroupIsNumeric = function (value) { return !Array.isArray(value) && !Number.isNaN(Number(value)); };
  var rootGroupTiming = function (modifiers, name) {
    var next = modifiers[modifiers.indexOf(name) + 1] || "invalid-wait";
    return rootGroupIsNumeric(next.split("ms")[0]) ? Number(next.split("ms")[0]) : 250;
  };

  var rootGroupMissesKeyFilter = function (event, modifiers) {
    var ignored = [
      "window", "document", "prevent", "stop", "once", "capture", "self", "away", "outside",
      "passive", "preserve-scroll", "blur", "change", "lazy",
    ];
    var keys = modifiers.filter(function (item) { return ignored.indexOf(item) === -1; });
    ["debounce", "throttle"].forEach(function (timing) {
      if (keys.indexOf(timing) === -1) return;
      var index = keys.indexOf(timing);
      var next = keys[index + 1] || "invalid-wait";
      keys.splice(index, rootGroupIsNumeric(next.split("ms")[0]) ? 2 : 1);
    });
    if (!keys.length) return false;
    if (keys.length === 1 && rootGroupKeyAliases(event.key).indexOf(keys[0]) !== -1) return false;
    var system = ["ctrl", "shift", "alt", "meta", "cmd", "super"];
    var selected = system.filter(function (name) { return keys.indexOf(name) !== -1; });
    keys = keys.filter(function (name) { return selected.indexOf(name) === -1; });
    if (selected.length) {
      var active = selected.filter(function (name) {
        var property = name === "cmd" || name === "super" ? "meta" : name;
        return event[property + "Key"];
      });
      if (active.length === selected.length) {
        if (rootGroupIsClickEvent(event.type)) return false;
        if (rootGroupKeyAliases(event.key).indexOf(keys[0]) !== -1) return false;
      }
    }
    return true;
  };

  var rootGroupPathContains = function (event, root) {
    var path = typeof event.composedPath === "function" ? event.composedPath() : [];
    if (path.indexOf(root) !== -1) return true;
    return path.some(function (candidate) {
      return candidate instanceof Node && root.contains(candidate);
    });
  };

  var RootGroup = function (els, isLogicalLive) {
    this.els = els;
    this.bindings = new Set();
    this.destroyed = false;
    this.isLogicalLive = isLogicalLive;
  };
  RootGroup.prototype.setRoots = function (next) {
    if (this.destroyed) return;
    var roots = rootGroupUnique(Array.from(next || []));
    replaceArrayContents(this.els, roots);
    this.bindings.forEach(function (binding) { binding.syncRoots(); });
  };
  RootGroup.prototype.hasLive = function (root) {
    return this.isLogicalLive() && this.els.indexOf(root) !== -1 && root.isConnected;
  };
  RootGroup.prototype.firstLive = function () {
    if (!this.isLogicalLive()) return null;
    return this.els.find(function (root) { return root.isConnected; }) || null;
  };
  RootGroup.prototype.containsNode = function (node) {
    return node instanceof Node && this.els.some(function (root) { return root === node || root.contains(node); });
  };
  RootGroup.prototype.containsEvent = function (event) {
    return this.els.some(function (root) { return rootGroupPathContains(event, root); });
  };
  RootGroup.prototype.hasVisibleRoot = function () {
    return this.els.some(function (root) {
      return root.isConnected && root._x_isShown !== false && (root.offsetWidth >= 1 || root.offsetHeight >= 1);
    });
  };
  RootGroup.prototype.on = function (event, modifiers, callback, citrySpec) {
    if (this.destroyed) throw new Error("[Citry] cannot bind a destroyed RootGroup.");
    var binding = new RootGroupBinding(this, event, modifiers, callback, citrySpec || null);
    this.bindings.add(binding);
    binding.syncRoots([], this.els);
    return function () { binding.cleanup(); };
  };
  RootGroup.prototype.poll = function (interval, callback) {
    if (!(interval > 0)) throw new TypeError("[Citry] RootGroup poll intervals must be positive.");
    var group = this;
    var active = true;
    var timer = window.setInterval(function () {
      if (!active || document.hidden || !group.isLogicalLive()) return;
      callback(group.firstLive());
    }, interval);
    var binding = {
      syncRoots: function () {},
      cleanup: function () {
        if (!active) return;
        active = false;
        window.clearInterval(timer);
        group.bindings.delete(binding);
      },
    };
    this.bindings.add(binding);
    return binding.cleanup;
  };
  RootGroup.prototype.destroy = function () {
    if (this.destroyed) return;
    this.destroyed = true;
    Array.from(this.bindings).forEach(function (binding) { binding.cleanup(); });
    replaceArrayContents(this.els, []);
  };

  var RootGroupBinding = function (group, event, modifiers, callback, citrySpec) {
    this.group = group;
    this.modifiers = Array.from(modifiers || []);
    this.event = this.modifiers.indexOf("dot") !== -1
      ? event.replace(/-/g, ".")
      : this.modifiers.indexOf("camel") !== -1
        ? event.toLowerCase().replace(/-(\w)/g, function (_match, ch) { return ch.toUpperCase(); })
        : event;
    this.callback = callback;
    this.citrySpec = citrySpec;
    this.targets = new Set();
    this.cancelTimers = [];
    this.listening = true;
    this.destroyed = false;
    this.options = {};
    if (this.modifiers.indexOf("capture") !== -1) this.options.capture = true;
    if (this.modifiers.indexOf("passive") !== -1) {
      this.options.passive = this.modifiers[this.modifiers.indexOf("passive") + 1] !== "false";
    }
    var binding = this;
    this.handleEvent = function (domEvent) {
      var direct = domEvent.currentTarget instanceof Element;
      var carrier = direct ? domEvent.currentTarget : binding.group.firstLive();
      binding.handler({ event: domEvent, carrier: carrier, direct: direct });
    };
    this.handler = citrySpec ? this.buildCitryHandler() : this.buildAlpineHandler();
  };
  RootGroupBinding.prototype.targetMode = function () {
    if (this.modifiers.indexOf("away") !== -1 || this.modifiers.indexOf("outside") !== -1) return "outside";
    if (this.modifiers.indexOf("document") !== -1) return "document";
    if (this.modifiers.indexOf("window") !== -1) return "window";
    return "direct";
  };
  RootGroupBinding.prototype.eventTargets = function () {
    var mode = this.targetMode();
    if (mode === "window") return this.group.els.length ? [window] : [];
    if (mode === "document" || mode === "outside") return this.group.els.length ? [document] : [];
    return this.group.els;
  };
  RootGroupBinding.prototype.syncRoots = function () {
    if (!this.listening || this.destroyed) return;
    var binding = this;
    var expected = new Set(this.eventTargets());
    Array.from(this.targets).forEach(function (target) {
      if (expected.has(target)) return;
      target.removeEventListener(binding.event, binding.handleEvent, binding.options);
      binding.targets.delete(target);
    });
    expected.forEach(function (target) {
      if (binding.targets.has(target)) return;
      target.addEventListener(binding.event, binding.handleEvent, binding.options);
      binding.targets.add(target);
    });
  };
  RootGroupBinding.prototype.stopListening = function () {
    if (!this.listening) return;
    var binding = this;
    this.listening = false;
    this.targets.forEach(function (target) {
      target.removeEventListener(binding.event, binding.handleEvent, binding.options);
    });
    this.targets.clear();
  };
  RootGroupBinding.prototype.deliver = function (context) {
    if (this.destroyed || !this.group.isLogicalLive()) return;
    var carrier = context.carrier;
    if (context.direct) {
      if (!carrier || !this.group.hasLive(carrier)) return;
    } else if (!carrier || !this.group.hasLive(carrier)) {
      carrier = this.group.firstLive();
      if (!carrier) return;
    }
    this.callback(context.event, carrier);
  };
  RootGroupBinding.prototype.buildAlpineHandler = function () {
    var binding = this;
    var wrap = function (next, wrapper) { return function (context) { wrapper(next, context); }; };
    var handler = function (context) { binding.deliver(context); };
    if (this.modifiers.indexOf("debounce") !== -1) {
      var debounceWait = rootGroupTiming(this.modifiers, "debounce");
      var debounceTimer = 0;
      handler = (function (next) {
        return function (context) {
          window.clearTimeout(debounceTimer);
          debounceTimer = window.setTimeout(function () { debounceTimer = 0; next(context); }, debounceWait);
        };
      })(handler);
      this.cancelTimers.push(function () { window.clearTimeout(debounceTimer); });
    }
    if (this.modifiers.indexOf("throttle") !== -1) {
      var throttleWait = rootGroupTiming(this.modifiers, "throttle");
      var throttled = false;
      var throttleTimer = 0;
      handler = (function (next) {
        return function (context) {
          if (throttled) return;
          next(context);
          throttled = true;
          throttleTimer = window.setTimeout(function () { throttled = false; throttleTimer = 0; }, throttleWait);
        };
      })(handler);
      this.cancelTimers.push(function () { window.clearTimeout(throttleTimer); throttled = false; });
    }
    if (this.modifiers.indexOf("prevent") !== -1) handler = wrap(handler, function (next, c) { c.event.preventDefault(); next(c); });
    if (this.modifiers.indexOf("stop") !== -1) handler = wrap(handler, function (next, c) { c.event.stopPropagation(); next(c); });
    if (this.modifiers.indexOf("once") !== -1) handler = wrap(handler, function (next, c) { next(c); binding.stopListening(); });
    if (this.targetMode() === "outside") {
      handler = wrap(handler, function (next, c) {
        if (binding.group.containsEvent(c.event)) return;
        if (c.event.target && c.event.target.isConnected === false) return;
        if (!binding.group.hasVisibleRoot()) return;
        next(c);
      });
    }
    if (this.modifiers.indexOf("self") !== -1) {
      handler = wrap(handler, function (next, c) { if (binding.group.els.indexOf(c.event.target) !== -1) next(c); });
    }
    if (ROOT_GROUP_ENTER_LEAVE.has(this.event)) {
      handler = wrap(handler, function (next, c) {
        if (c.event.relatedTarget && binding.group.containsNode(c.event.relatedTarget)) return;
        next(c);
      });
    }
    if (this.event === "submit") {
      handler = wrap(handler, function (next, c) {
        var updates = c.event.target && c.event.target._x_pendingModelUpdates;
        if (updates) updates.forEach(function (update) { update(); });
        next(c);
      });
    }
    if (rootGroupIsKeyEvent(this.event) || rootGroupIsClickEvent(this.event)) {
      handler = wrap(handler, function (next, c) { if (!rootGroupMissesKeyFilter(c.event, binding.modifiers)) next(c); });
    }
    return handler;
  };
  RootGroupBinding.prototype.buildCitryHandler = function () {
    var binding = this;
    var exhausted = false;
    var debounceTimer = 0;
    var throttleUntil = 0;
    this.cancelTimers.push(function () { window.clearTimeout(debounceTimer); });
    return function (context) {
      var spec = binding.citrySpec;
      if (
        ROOT_GROUP_ENTER_LEAVE.has(binding.event) && context.event.relatedTarget &&
        binding.group.containsNode(context.event.relatedTarget)
      ) return;
      if (spec.key) {
        var expected = { enter: "Enter", escape: "Escape" }[spec.key];
        if (!expected || context.event.key !== expected) return;
      }
      if (spec.self === true && binding.group.els.indexOf(context.event.target) === -1) return;
      if (spec.once === true) {
        if (exhausted) return;
        exhausted = true;
        binding.stopListening();
      }
      if (spec.prevent === true) context.event.preventDefault();
      if (spec.stop === true) context.event.stopPropagation();
      var now = Date.now();
      if (spec.throttle > 0) {
        if (throttleUntil > now) return;
        throttleUntil = now + spec.throttle;
      }
      if (!(spec.debounce > 0)) {
        binding.deliver(context);
        return;
      }
      window.clearTimeout(debounceTimer);
      debounceTimer = window.setTimeout(function () { debounceTimer = 0; binding.deliver(context); }, spec.debounce);
    };
  };
  RootGroupBinding.prototype.cleanup = function () {
    if (this.destroyed) return;
    this.destroyed = true;
    this.stopListening();
    this.cancelTimers.splice(0).forEach(function (cancel) { cancel(); });
    this.group.bindings.delete(this);
  };

  var PROP_BLOCKED_KEYS = new Set(["__proto__", "prototype", "constructor"]);
  var propTypeName = function (ctor) { return typeof ctor === "function" && ctor.name ? ctor.name : String(ctor); };
  var propValueType = function (value) {
    if (Array.isArray(value)) return "an array";
    return "a " + typeof value;
  };
  var propMatchesType = function (value, ctor) {
    if (ctor === String) return typeof value === "string";
    if (ctor === Number) return typeof value === "number";
    if (ctor === Boolean) return typeof value === "boolean";
    if (ctor === Function) return typeof value === "function";
    if (ctor === Symbol) return typeof value === "symbol";
    if (ctor === BigInt) return typeof value === "bigint";
    if (ctor === Array) return Array.isArray(value);
    if (ctor === Object) return value !== null && typeof value === "object";
    return typeof ctor === "function" && value instanceof ctor;
  };
  var plainPropsObject = function (value) {
    if (value === null || typeof value !== "object" || Array.isArray(value)) return false;
    if (typeof value.then === "function") return false;
    var prototype = Object.getPrototypeOf(value);
    return prototype === Object.prototype || prototype === null;
  };

  var createPropsController = function (lifecycle, declarations, expectsSupply) {
    var classId = lifecycle.classId;
    var declarationIsObject = declarations !== null && typeof declarations === "object" && !Array.isArray(declarations);
    var definitions = declarationIsObject ? declarations : {};
    var target = alpineOwner.reactive({});
    var defaults = {};
    var episodes = new Map();
    var declarationErrors = new Map();
    var declaredNames = Object.keys(definitions);
    var controller = {
      target: target,
      view: null,
      defaults: defaults,
      definitions: definitions,
      expectsSupply: expectsSupply,
      initialSettled: false,
      currentValid: false,
      effectStop: null,
      sourceBoundary: null,
    };

    var report = function (key, message) {
      if (episodes.get(key) === message) return;
      episodes.set(key, message);
      console.error("[Citry] component " + classId + " props for render '" + lifecycle.renderId + "': " + message);
    };
    var recover = function (failures) {
      Array.from(episodes.keys()).forEach(function (key) {
        if (!failures.has(key)) episodes.delete(key);
      });
    };

    if (!declarationIsObject) {
      declarationErrors.set("$declaration", "the props declaration must be an object.");
      declaredNames = [];
    }
    declaredNames.forEach(function (name) {
      var definition = definitions[name];
      if (PROP_BLOCKED_KEYS.has(name)) {
        declarationErrors.set(name, "prop '" + name + "' uses a prototype-sensitive key and is not allowed.");
        return;
      }
      if (definition === null || typeof definition !== "object" || Array.isArray(definition)) {
        declarationErrors.set(name, "prop '" + name + "' must be an object with type, required, and/or default.");
        return;
      }
      if (definition.required != null && typeof definition.required !== "boolean") {
        declarationErrors.set(name, "prop '" + name + "' has a non-boolean required option.");
      }
      if (definition.type != null) {
        var types = Array.isArray(definition.type) ? definition.type : [definition.type];
        if (!types.length || types.some(function (ctor) { return typeof ctor !== "function"; })) {
          declarationErrors.set(name, "prop '" + name + "' type must be a constructor or a non-empty array of constructors.");
        }
      }
      if (Object.prototype.hasOwnProperty.call(definition, "default")) {
        if (definition.default !== null && typeof definition.default === "object") {
          declarationErrors.set(name, "prop '" + name + "' has an object or array default; use a per-instance factory.");
          return;
        }
        try {
          defaults[name] = typeof definition.default === "function" ? definition.default() : definition.default;
        } catch (err) {
          declarationErrors.set(name, "prop '" + name + "' default factory threw: " + (err && err.message ? err.message : String(err)));
        }
      } else {
        defaults[name] = undefined;
      }
    });

    controller.view = new Proxy(target, {
      set: function (_object, name) {
        throw new TypeError("[Citry] props are read-only; assign child-local values to scope instead of props." + String(name));
      },
      deleteProperty: function () {
        throw new TypeError("[Citry] props are read-only; top-level prop keys cannot be deleted.");
      },
      defineProperty: function () {
        throw new TypeError("[Citry] props are read-only; top-level prop keys cannot be redefined.");
      },
    });

    controller.apply = function (supplied, supplierError) {
      var failures = new Map(declarationErrors);
      var shapeValid = supplierError == null && plainPropsObject(supplied);
      if (!shapeValid) {
        var shapeMessage = supplierError
          ? "the $c-props supplier threw: " + (supplierError.message || String(supplierError))
          : "the $c-props supplier must synchronously return a plain object; Promises, thenables, arrays, and class instances are invalid.";
        failures.set("$supplier", shapeMessage);
        declaredNames.forEach(function (name) { target[name] = undefined; });
      } else {
        Object.keys(supplied).forEach(function (name) {
          if (PROP_BLOCKED_KEYS.has(name)) {
            failures.set("unknown:" + name, "ignored prototype-sensitive supplied key '" + name + "'.");
          } else if (!Object.prototype.hasOwnProperty.call(definitions, name)) {
            failures.set("unknown:" + name, "ignored unknown supplied prop '" + name + "'.");
          }
        });
        declaredNames.forEach(function (name) {
          if (declarationErrors.has(name)) {
            target[name] = undefined;
            return;
          }
          var definition = definitions[name];
          var value = Object.prototype.hasOwnProperty.call(supplied, name) ? supplied[name] : defaults[name];
          if (value === undefined && definition.required === true) {
            failures.set(name, "prop '" + name + "' is required, but the current supply and declaration default are both undefined.");
            target[name] = undefined;
            return;
          }
          if (value !== undefined && value !== null && definition.type != null) {
            var accepted = Array.isArray(definition.type) ? definition.type : [definition.type];
            if (!accepted.some(function (ctor) { return propMatchesType(value, ctor); })) {
              failures.set(
                name,
                "prop '" + name + "' expected " + accepted.map(propTypeName).join(" or ") + ", got " + propValueType(value) + "."
              );
              target[name] = undefined;
              return;
            }
          }
          target[name] = value;
        });
      }
      recover(failures);
      failures.forEach(function (message, key) { report(key, message); });
      controller.currentValid = Array.from(failures.keys()).every(function (key) {
        return String(key).indexOf("unknown:") === 0;
      });
      if (!controller.initialSettled) controller.initialSettled = true;
      return controller.currentValid;
    };
    controller.applyNoSupply = function () { return controller.apply({}); };
    controller.destroy = function () {
      if (controller.effectStop) {
        try { controller.effectStop(); } catch (_err) {}
        controller.effectStop = null;
      }
    };
    return controller;
  };

  var lifecycleCapsAreLive = function (lifecycle) {
    // Graph-backed lifecycles use exact canonical or runtime-placement caps.
    // A compatibility render id belongs only to the legacy no-graph path; its
    // Events anchor owns retirement after the DOM liveness sweep.
    if (lifecycle.compatRenderId) return true;
    var range = lifecyclePhysicalRange(lifecycle);
    return Boolean(
      range.route && range.state && range.physicals.some(function (physical) {
        return physicalRangeIsLive(range.state, physical);
      })
    );
  };

  var rootsForRender = function (renderId) {
    return Array.prototype.slice.call(document.querySelectorAll("[data-cid-" + renderId + "]"));
  };

  var lifecycleForRender = function (renderId) {
    var found = null;
    ownershipStates.forEach(function (state) {
      if (found) return;
      var link = state.renderLinks.get(renderId);
      if (link && link.link.active && link.logicalState.lifecycle && link.logicalState.lifecycle.active) {
        found = link.logicalState.lifecycle;
      }
    });
    if (!found) {
      componentLifecycles.forEach(function (lifecycle) {
        if (!found && lifecycle.active && lifecycle.compatRenderId === renderId) found = lifecycle;
      });
    }
    return found;
  };

  var rootsForLifecycle = function (lifecycle) {
    if (lifecycle.compatRenderId) return rootsForRender(lifecycle.compatRenderId);
    var range = lifecyclePhysicalRange(lifecycle);
    if (!range.route || !range.state) return [];
    var roots = [];
    range.physicals.forEach(function (physical) {
      if (!physicalRangeIsLive(range.state, physical)) return;
      roots = roots.concat(physicalRangeRoots(physical, range.route.instance.renderId));
    });
    roots.sort(function (left, right) {
      if (nodePrecedes(left, right)) return -1;
      if (nodePrecedes(right, left)) return 1;
      return 0;
    });
    return roots;
  };

  var lifecycleOwnsRoot = function (lifecycle, root) {
    return lifecycle.active && rootsForLifecycle(lifecycle).indexOf(root) !== -1;
  };

  var innermostLifecycleForRoot = function (root) {
    if (!root || !root.getAttribute) return null;
    var ids = (root.getAttribute("data-cid") || "").trim().split(/\s+/).filter(Boolean);
    for (var index = ids.length - 1; index >= 0; index -= 1) {
      var lifecycle = lifecycleForRender(ids[index]);
      if (lifecycle && lifecycleOwnsRoot(lifecycle, root)) return lifecycle;
    }
    return null;
  };

  var localAlpineLayers = function (root, previous) {
    var stack = root._x_dataStack ? root._x_dataStack.slice() : [];
    if (previous) {
      var previousIndex = stack.indexOf(previous.router);
      if (previousIndex !== -1) return stack.slice(0, previousIndex);
    }
    var parent = root.parentElement;
    while (parent && !parent._x_dataStack) parent = parent.parentElement;
    if (!parent || !parent._x_dataStack) return stack;
    var inherited = new Set(parent._x_dataStack);
    var firstInherited = stack.findIndex(function (layer) { return inherited.has(layer); });
    return firstInherited === -1 ? stack : stack.slice(0, firstInherited);
  };

  var makeScopeRouter = function (scope) {
    var owner = alpineOwner.reactive({ current: scope });
    var router = new Proxy({}, {
      ownKeys: function () { return owner.current ? Reflect.ownKeys(owner.current) : []; },
      has: function (_target, name) { return Boolean(owner.current && Reflect.has(owner.current, name)); },
      get: function (_target, name) {
        return owner.current ? Reflect.get(owner.current, name, owner.current) : undefined;
      },
      set: function (_target, name, value) {
        if (!owner.current) return true;
        return Reflect.set(owner.current, name, value, owner.current);
      },
      deleteProperty: function (_target, name) {
        if (!owner.current) return true;
        return Reflect.deleteProperty(owner.current, name);
      },
      getOwnPropertyDescriptor: function (_target, name) {
        if (!owner.current) return undefined;
        var descriptor = Reflect.getOwnPropertyDescriptor(owner.current, name);
        return descriptor ? Object.assign({}, descriptor, { configurable: true }) : undefined;
      },
    });
    return { owner: owner, router: router };
  };

  isolateRootScope = function (root, fallbackScope) {
    var lifecycle = innermostLifecycleForRoot(root);
    var scope = lifecycle && lifecycle.scope ? lifecycle.scope : fallbackScope;
    var previous = rootScopeOwners.get(root) || null;
    var fillRoute = fillRoutesByElement.get(root) || null;
    if (fillRoute && fillRoute.descriptor && fillRoute.descriptor.active) {
      var fillLocal = localAlpineLayers(root, previous);
      var fillFrameIndex = fillLocal.indexOf(fillRoute.descriptor.frame);
      fillLocal = fillFrameIndex === -1 ? [] : fillLocal.slice(0, fillFrameIndex + 1);
      if (previous) {
        try { previous.remove(); } catch (_err) {}
        rootScopeOwners.delete(root);
      }
      // A slot-only receiver can share its physical root with caller-owned
      // fill markup. That expression surface belongs wholly to the fill
      // source; the receiver router must not remain as a fallback for names
      // missing at the caller.
      root._x_dataStack = fillLocal.length ? fillLocal : [fillRoute.descriptor.frame];
      return function () {};
    }
    if (previous && root._x_dataStack && root._x_dataStack.indexOf(previous.router) !== -1) {
      previous.scope = scope;
      previous.owner.current = scope;
      return previous.remove;
    }
    var local = localAlpineLayers(root, previous);
    if (previous) {
      try { previous.remove(); } catch (_err) {}
    }
    var routed = makeScopeRouter(scope);
    var remove = alpineOwner.addScopeToNode(root, routed.router);
    // Same-root user x-data remains above the Citry layer. Inherited parent
    // layers are deliberately absent, which is the component isolation rule.
    root._x_dataStack = local.concat([routed.router]);
    var record = { scope: scope, owner: routed.owner, router: routed.router, remove: remove };
    rootScopeOwners.set(root, record);
    return remove;
  };

  // ----- graph-owned slot source projection -----

  var fillDescriptorIsLive = function (descriptor) {
    if (!descriptor.active || !descriptor.groupState || descriptor.groupState.retired) return false;
    if (!descriptor.groupState.active) return false;
    if (descriptor.ownerLifecycle && !descriptor.ownerLifecycle.active) return false;
    if (descriptor.sourceState && descriptor.sourcePhysicalKey) {
      return physicalRangesForKey(descriptor.sourceState, descriptor.sourcePhysicalKey).some(function (physical) {
        return physicalRangeIsLive(descriptor.sourceState, physical);
      });
    }
    return descriptor.detached || Boolean(descriptor.ownerLifecycle);
  };

  var fillRouteToken = function (state, localKey) {
    return state.publicRevision.revision + ":" + localKey;
  };

  var fillDescriptorStack = function (descriptor) {
    if (!fillDescriptorIsLive(descriptor)) return [];
    var stack = descriptor.sourceOrigin instanceof Element
      ? alpineOwner.closestDataStack(descriptor.sourceOrigin).slice()
      : [];
    var sourceScope = descriptor.ownerLifecycle && descriptor.ownerLifecycle.scope;
    if (sourceScope && stack.indexOf(sourceScope) === -1) stack.push(sourceScope);
    return stack;
  };

  var makeFillSourceFrame = function (descriptor) {
    descriptor.frameVersion = alpineOwner.reactive({ current: 0 });
    var liveScope = function () {
      descriptor.frameVersion.current;
      return alpineOwner.mergeProxies(fillDescriptorStack(descriptor));
    };
    return new Proxy({}, {
      ownKeys: function () {
        return Array.from(new Set([FILL_SOURCE_FRAME].concat(Reflect.ownKeys(liveScope()))));
      },
      has: function (_target, name) {
        return name === FILL_SOURCE_FRAME || Reflect.has(liveScope(), name);
      },
      get: function (_target, name) {
        if (name === FILL_SOURCE_FRAME) return descriptor;
        return Reflect.get(liveScope(), name);
      },
      set: function (_target, name, value) {
        if (name === FILL_SOURCE_FRAME) return false;
        return Reflect.set(liveScope(), name, value);
      },
      deleteProperty: function (_target, name) {
        if (name === FILL_SOURCE_FRAME) return false;
        return Reflect.deleteProperty(liveScope(), name);
      },
      getOwnPropertyDescriptor: function (_target, name) {
        if (name === FILL_SOURCE_FRAME) {
          return { configurable: true, enumerable: false, value: descriptor };
        }
        if (!Reflect.has(liveScope(), name)) return undefined;
        return {
          configurable: true,
          enumerable: true,
          get: function () { return Reflect.get(liveScope(), name); },
          set: function (value) { Reflect.set(liveScope(), name, value); },
        };
      },
    });
  };

  var fillDescriptorInStack = function (el) {
    if (!alpineOwner || !(el instanceof Element)) return null;
    var stack = el._x_dataStack || alpineOwner.closestDataStack(el);
    for (var index = 0; index < stack.length; index += 1) {
      try {
        var descriptor = stack[index] && stack[index][FILL_SOURCE_FRAME];
        if (descriptor) return descriptor;
      } catch (_err) {}
    }
    return null;
  };

  var fillBacklinkOwner = function (el) {
    var current = el;
    while (current._x_teleportBack && current._x_teleportBack._x_teleport === current) {
      current = current._x_teleportBack;
    }
    return current;
  };

  var clearFillMagicCaches = function (root) {
    alpineOwner.walk(root, function (el) {
      delete el._x_refs_proxy;
      delete el._x_id;
    });
  };

  var unlinkFillRoot = function (el, descriptor) {
    descriptor.roots.delete(el);
    var currentRoute = fillRoutesByElement.get(el);
    if (currentRoute && currentRoute.descriptor !== descriptor) return;
    fillRoutesByElement.delete(el);
    var owner = el._x_citryFillBacklinkOwner;
    delete el._x_citryFillBacklinkOwner;
    if (!owner || owner._x_citryFillBacklink !== descriptor) return;
    var stillUsed = Array.from(descriptor.roots).some(function (root) {
      return root._x_citryFillBacklinkOwner === owner;
    });
    if (stillUsed) return;
    delete owner._x_citryFillBacklink;
    delete owner._x_teleportBack;
  };

  var linkFillRoot = function (el, route) {
    var descriptor = route.descriptor;
    retiredFillRoots.delete(el);
    fillRoutesByElement.set(el, route);
    descriptor.routesByRoot.set(el, route.token);
    var owner = fillBacklinkOwner(el);
    if (owner._x_teleportBack && owner._x_citryFillBacklink !== descriptor) {
      throw pointedAlpineError("a slot source cannot replace an unrelated Alpine teleport backlink.");
    }
    owner._x_citryFillBacklink = descriptor;
    owner._x_teleportBack = descriptor.carrier;
    el._x_citryFillBacklinkOwner = owner;
    descriptor.roots.add(el);
  };

  var fillRouteForDirective = function (expression) {
    var route = fillRegionRoutes.get(expression.trim());
    if (!route || !route.descriptor.active) {
      throw pointedAlpineError("a slot source directive refers to an inactive or unknown ownership region.");
    }
    return route;
  };

  installFillSourceDirective = function (alpine) {
    ["addScopeToNode", "closestDataStack", "mergeProxies", "onElRemoved", "walk", "closestRoot"].forEach(
      function (name) {
        if (typeof alpine[name] !== "function") {
          throw pointedAlpineError("the pinned runtime is missing required slot-scope API Alpine." + name + ".");
        }
      }
    );
    var emptyReference = document.createDocumentFragment();
    var handler = function (el, directive, utilities) {
      var route = fillRouteForDirective(directive.expression);
      var descriptor = route.descriptor;
      var ownStack = Object.prototype.hasOwnProperty.call(el, "_x_dataStack") ? el._x_dataStack || [] : [];
      var alreadyLinked = ownStack.some(function (layer) {
        try { return layer && layer[FILL_SOURCE_FRAME] === descriptor; } catch (_err) { return false; }
      });
      var undo = alreadyLinked
        ? function () {}
        : alpine.addScopeToNode(el, descriptor.frame, emptyReference);
      var released = false;
      var release = function () {
        if (released) return;
        released = true;
        undo();
        if (descriptor.rootReleases.get(el) === release) descriptor.rootReleases.delete(el);
        retiredFillRoots.add(el);
        unlinkFillRoot(el, descriptor);
      };
      descriptor.rootReleases.set(el, release);
      utilities.cleanup(release);
    };
    handler.inline = function (el, directive) {
      var route = fillRouteForDirective(directive.expression);
      if (
        el.tagName === "TEMPLATE" &&
        (el.hasAttribute("x-if") || el.hasAttribute("x-for") || el.hasAttribute("x-teleport"))
      ) {
        var generatedRoot = el.content.firstElementChild;
        if (!generatedRoot) {
          throw pointedAlpineError("a structural slot fill needs one element root.");
        }
        var existing = generatedRoot.getAttribute(FILL_SOURCE_ATTR);
        if (existing && existing !== directive.expression.trim()) {
          throw pointedAlpineError("one structural root cannot belong to two slot sources.");
        }
        generatedRoot.setAttribute(FILL_SOURCE_ATTR, directive.expression.trim());
      }
      linkFillRoot(el, route);
    };
    alpine.directive("citry-fill-source", handler).before("ref");

    // Stock `$root` stops at a shared receiver/fill `data-citry-root` before
    // following `_x_teleportBack`. A local x-data root remains physical; an
    // otherwise shared root follows the graph-selected lexical carrier.
    alpine.magic("root", function (el) {
      var descriptor = fillDescriptorInStack(el);
      var physical = alpine.closestRoot(el);
      if (!descriptor || !fillDescriptorIsLive(descriptor) || (physical && physical.hasAttribute("x-data"))) {
        return physical;
      }
      return alpine.closestRoot(descriptor.carrier);
    });
  };

  var fillRegionDirectElements = function (state, region) {
    var elements = [];
    physicalRangesForKey(state, region.key).forEach(function (physical) {
      if (!physicalRangeIsLive(state, physical)) return;
      var nested = [];
      state.physicalPlacements.forEach(function (placements) {
        placements.forEach(function (candidate) {
          if (
            candidate !== physical && candidate.graphId === region.graphId &&
            candidate.placementId === physical.placementId &&
            candidate.parentRegionId === region.regionId && physicalRangeIsLive(state, candidate)
          ) nested.push(candidate);
        });
      });
      physicalRangeElements(physical).forEach(function (element) {
        if (nested.some(function (candidate) { return physicalRangeContainsNode(candidate, element); })) return;
        if (element.hasAttribute("data-citry-root")) {
          var ids = (element.getAttribute("data-cid") || "").trim().split(/\s+/).filter(Boolean);
          if (region.receiverRenderId != null && ids.indexOf(region.receiverRenderId) === -1) return;
        }
        elements.push(element);
      });
    });
    return elements;
  };

  var fallbackSourceOrigin = function (state, region) {
    var cursor = region;
    while (cursor.parentRegionId != null) {
      var parent = state.registry.slotRegions.get(qualifiedGraphId(cursor.graphId, "r", cursor.parentRegionId));
      if (!parent) break;
      if (parent.transitionFromRenderId === region.ownerRenderId) {
        var parentPhysical = state.registry.physicalRegions.get(parent.key);
        return parentPhysical && parentPhysical.start.parentElement;
      }
      cursor = parent;
    }
    var physical = state.registry.physicalRegions.get(region.key);
    return physical && physical.start.parentElement;
  };

  var preflightGraphFillSources = function (state) {
    var plans = [];
    state.registry.fills.values().forEach(function (fill) {
      var groupState = state.rangeGroupStates.get(fill.key);
      if (!groupState || !groupState.slotRegions.length) return;
      var sourceInvocation = fill.sourceInvocationId == null
        ? null
        : state.registry.nestedComponents.get(qualifiedGraphId(fill.graphId, "v", fill.sourceInvocationId));
      var sourceInstance = sourceInvocation
        ? state.registry.renderIds.get(sourceInvocation.targetRenderId)
        : null;
      var sourcePhysical = sourceInstance && state.registry.physicalRegions.get(sourceInstance.key);
      if (fill.policy === "template" && fill.kind !== "fallback" && (!sourceInvocation || !sourcePhysical)) {
        throw pointedAlpineError("a supplied slot fill has no validated source invocation carrier.");
      }
      var plan = {
        state: state,
        fill: fill,
        groupState: groupState,
        sourceInvocation: sourceInvocation,
        sourcePhysical: sourcePhysical,
        slotRegions: groupState.slotRegions.slice(),
      };
      plan.slotRegions.forEach(function (region) {
        fillRegionDirectElements(state, region).forEach(function (element) {
          if (alpineStarted && element._x_marker) {
            throw pointedAlpineError(
              "a delayed slot region arrived after Alpine initialized; adopt its graph and DOM atomically."
            );
          }
        });
      });
      plans.push(plan);
    });
    return plans;
  };

  // Alpine evaluators capture the data-stack frame object when their
  // directive initializes. Morph can preserve a physical fill element while
  // its graph route changes, so replacing only the element's route would
  // leave existing effects attached to a retired frame. Preserve the live
  // descriptor object and retarget its graph fields instead. The reactive
  // frame version then reruns bindings against the incoming source without
  // destroying same-root local Alpine state.
  var adoptFillSourceDescriptor = function (previous, incoming) {
    if (previous === incoming) return previous;
    var previousKey = previous.key;
    var previousRegions = previous.slotRegions.slice();
    previous.slotRegions.forEach(function (region) {
      var token = fillRouteToken(previous.state, region.key);
      var route = fillRegionRoutes.get(token);
      if (route && route.descriptor === previous) fillRegionRoutes.delete(token);
    });

    previous.key = incoming.key;
    previous.state = incoming.state;
    previous.fill = incoming.fill;
    previous.groupState = incoming.groupState;
    previous.slotRegions = incoming.slotRegions;
    previous.ownerRenderId = incoming.ownerRenderId;
    previous.ownerLifecycle = incoming.ownerLifecycle;
    previous.sourceState = incoming.sourceState;
    previous.sourcePhysical = incoming.sourcePhysical;
    previous.sourcePhysicalKey = incoming.sourcePhysicalKey;
    previous.sourceOrigin = incoming.sourceOrigin;
    previous.detached = incoming.detached;
    previous.active = true;
    if (previous.sourceOrigin instanceof Element) {
      previous.carrier._x_teleportBack = previous.sourceOrigin;
    } else {
      delete previous.carrier._x_teleportBack;
    }

    incoming.slotRegions.forEach(function (region) {
      var token = fillRouteToken(incoming.state, region.key);
      var route = fillRegionRoutes.get(token);
      if (route) route.descriptor = previous;
    });
    Array.from(previous.roots).forEach(function (root) {
      var oldToken = previous.routesByRoot.get(root);
      var oldRegion = oldToken && previousRegions.find(function (region) {
        return oldToken.slice(65) === region.key;
      });
      var oldIndex = oldRegion ? previousRegions.indexOf(oldRegion) : 0;
      var nextRegion = incoming.slotRegions[oldIndex] || incoming.slotRegions[0];
      if (!nextRegion) return;
      var token = fillRouteToken(incoming.state, nextRegion.key);
      var route = fillRegionRoutes.get(token);
      if (!route) return;
      fillRoutesByElement.set(root, route);
      previous.routesByRoot.set(root, token);
      if (root.getAttribute(FILL_SOURCE_ATTR) !== token) root.setAttribute(FILL_SOURCE_ATTR, token);
      clearFillMagicCaches(root);
    });

    previous.frameVersion.current += 1;

    incoming.active = false;
    fillSourceDescriptors.delete(previousKey);
    fillSourceDescriptors.delete(incoming.key);
    fillSourceDescriptors.set(previous.key, previous);
    return previous;
  };

  var stampFillRoutes = function () {
    Array.from(fillSourceDescriptors.values()).forEach(function (descriptor) {
      if (!descriptor.active) return;
      descriptor.slotRegions.forEach(function (region) {
        var token = fillRouteToken(descriptor.state, region.key);
        var route = fillRegionRoutes.get(token);
        fillRegionDirectElements(descriptor.state, region).forEach(function (element) {
          var previousRoute = fillRoutesByElement.get(element);
          if (
            previousRoute && previousRoute.descriptor !== descriptor &&
            previousRoute.descriptor.active && element._x_marker
          ) {
            descriptor = adoptFillSourceDescriptor(previousRoute.descriptor, descriptor);
            route.descriptor = descriptor;
          }
          fillRoutesByElement.set(element, route);
          descriptor.routesByRoot.set(element, token);
          if (element.getAttribute(FILL_SOURCE_ATTR) !== token) {
            element.setAttribute(FILL_SOURCE_ATTR, token);
          }
        });
      });
    });
  };

  var retireFillSource = function (descriptor) {
    if (!descriptor.active) return;
    descriptor.active = false;
    Array.from(descriptor.roots).forEach(function (root) {
      var currentRoute = fillRoutesByElement.get(root);
      if (currentRoute && currentRoute.descriptor !== descriptor) {
        var handedOffRelease = descriptor.rootReleases.get(root);
        if (handedOffRelease) handedOffRelease();
        descriptor.routesByRoot.delete(root);
        return;
      }
      clearFillMagicCaches(root);
      retiredFillRoots.add(root);
      var release = descriptor.rootReleases.get(root);
      if (release) release();
      // A teleported clone can outlive the source template physically. Keep
      // that retired DOM isolated instead of revealing receiver or placement
      // scopes after the live source frame is removed.
      root._x_dataStack = [RETIRED_FILL_SCOPE];
      if (root.getAttribute(FILL_SOURCE_ATTR) === descriptor.routesByRoot.get(root)) {
        root.removeAttribute(FILL_SOURCE_ATTR);
      }
      descriptor.routesByRoot.delete(root);
      unlinkFillRoot(root, descriptor);
    });
    descriptor.slotRegions.forEach(function (region) {
      fillRegionRoutes.delete(fillRouteToken(descriptor.state, region.key));
    });
    fillSourceDescriptors.delete(descriptor.key);
    if (scheduleOwnershipPrune) scheduleOwnershipPrune();
  };

  var reconcileFillSources = function () {
    fillReconcileScheduled = false;
    reconcilePhysicalRangeGroups();
    fillSourceDescriptors.forEach(function (descriptor) {
      if (!fillDescriptorIsLive(descriptor)) {
        retireFillSource(descriptor);
      }
    });
    stampFillRoutes();
  };

  var scheduleFillSourceReconcile = function () {
    if (fillReconcileScheduled) return;
    fillReconcileScheduled = true;
    queueMicrotask(reconcileFillSources);
  };

  var activateGraphFillSources = function (state, plans) {
    plans.forEach(function (plan) {
      var fill = plan.fill;
      var ownerLifecycle = null;
      if (fill.ownerRenderId != null) {
        ownerLifecycle = ensureLifecycle(resolveOwnershipRoute(state.publicRevision.revision, fill.ownerRenderId, null), true);
      }
      if (fill.receiverRenderId != null) {
        ensureLifecycle(resolveOwnershipRoute(state.publicRevision.revision, fill.receiverRenderId, null), true);
      }
      var descriptor = {
        key: fillRouteToken(state, fill.key),
        state: state,
        fill: fill,
        groupState: plan.groupState,
        slotRegions: plan.slotRegions,
        ownerRenderId: fill.ownerRenderId,
        ownerLifecycle: ownerLifecycle,
        sourceState: plan.sourcePhysical ? state : null,
        sourcePhysical: plan.sourcePhysical,
        sourcePhysicalKey: plan.sourcePhysical ? plan.sourcePhysical.key : null,
        sourceOrigin: null,
        carrier: document.createElement("span"),
        frame: null,
        roots: new Set(),
        rootReleases: new Map(),
        routesByRoot: new WeakMap(),
        detached: fill.policy !== "template",
        active: true,
      };
      if (fill.policy === "template" && fill.kind === "fallback") {
        descriptor.sourceOrigin = fallbackSourceOrigin(state, plan.slotRegions[0]);
      } else if (plan.sourcePhysical) {
        descriptor.sourceOrigin = plan.sourcePhysical.start.parentElement;
      }
      descriptor.frame = makeFillSourceFrame(descriptor);
      descriptor.carrier._x_dataStack = [descriptor.frame];
      if (descriptor.sourceOrigin instanceof Element) descriptor.carrier._x_teleportBack = descriptor.sourceOrigin;
      fillSourceDescriptors.set(descriptor.key, descriptor);
      plan.slotRegions.forEach(function (region) {
        var token = fillRouteToken(state, region.key);
        fillRegionRoutes.set(token, { descriptor: descriptor, region: region, token: token });
      });
    });
    stampFillRoutes();
  };

  var refreshGraphFillSources = function (state) {
    fillSourceDescriptors.forEach(function (descriptor) {
      if (descriptor.state !== state || !descriptor.active) return;
      if (descriptor.sourcePhysicalKey) {
        var sourcePhysical = physicalRangesForKey(state, descriptor.sourcePhysicalKey).filter(function (physical) {
          return physicalRangeIsLive(state, physical);
        })[0] || null;
        descriptor.sourcePhysical = sourcePhysical;
        descriptor.sourceOrigin = sourcePhysical ? sourcePhysical.start.parentElement : null;
      } else if (descriptor.fill.policy === "template" && descriptor.fill.kind === "fallback") {
        descriptor.sourceOrigin = fallbackSourceOrigin(state, descriptor.slotRegions[0]);
      }
      if (descriptor.sourceOrigin instanceof Element) {
        descriptor.carrier._x_teleportBack = descriptor.sourceOrigin;
      } else {
        delete descriptor.carrier._x_teleportBack;
      }
    });
    stampFillRoutes();
  };

  var fillSourceOwnerForElement = function (el) {
    for (var current = el; current instanceof Element; current = current.parentElement) {
      if (retiredFillRoots.has(current)) return null;
    }
    var descriptor = fillDescriptorInStack(el);
    if (!descriptor || !fillDescriptorIsLive(descriptor)) return undefined;
    return descriptor.detached ? null : descriptor.ownerRenderId;
  };

  var holdRootForCall = function (root, call) {
    if (!root || !root.isConnected || root._x_marker || call.heldRoots.has(root)) return;
    var hold = rootHolds.get(root);
    if (!hold) {
      hold = {
        reasons: new Set(),
        ownedIgnore: !root._x_ignore,
        suppressedDescendants: [],
        promoted: false,
        releaseQueued: false,
      };
      rootHolds.set(root, hold);
    }
    hold.reasons.add(call);
    call.heldRoots.add(root);
  };

  var promoteRootHold = function (root) {
    var hold = rootHolds.get(root);
    if (!hold || hold.promoted) return;
    hold.promoted = true;
    if (hold.ownedIgnore) root._x_ignore = true;
    delete root._x_marker;
    root.querySelectorAll("*").forEach(function (descendant) {
      delete descendant._x_marker;
      if (descendant._x_ignoreSelf) return;
      descendant._x_ignoreSelf = true;
      hold.suppressedDescendants.push(descendant);
    });
  };

  var releaseRootHold = function (root, call) {
    var hold = rootHolds.get(root);
    if (!hold) return;
    hold.reasons.delete(call);
    call.heldRoots.delete(root);
    if (hold.reasons.size || hold.releaseQueued) return;
    hold.releaseQueued = true;
    queueMicrotask(function () {
      var current = rootHolds.get(root);
      if (current !== hold || current.reasons.size) {
        if (current) current.releaseQueued = false;
        return;
      }
      rootHolds.delete(root);
      if (hold.promoted && hold.ownedIgnore) delete root._x_ignore;
      hold.suppressedDescendants.forEach(function (descendant) {
        delete descendant._x_ignoreSelf;
      });
      if (alpineStarted && root.isConnected && !root._x_marker) {
        try {
          alpineOwner.initTree(root);
        } catch (err) {
          console.error("[Citry] Alpine initialization after component callback settlement failed:", err);
        }
      }
    });
  };

  var releaseCallHolds = function (call) {
    Array.from(call.heldRoots).forEach(function (root) { releaseRootHold(root, call); });
  };

  var disposeInvocation = function (lifecycle) {
    var invocation = lifecycle.invocation;
    if (!invocation || !invocation.active) return;
    invocation.active = false;
    if (invocation.ambientFrame) {
      var hadAmbientWrites = invocation.ambientFrame.writes.size > 0;
      invocation.ambientFrame.active = false;
      invocation.ambientFrame.open = false;
      invocation.ambientFrame.writes.clear();
      if (hadAmbientWrites && touchAmbientContext) touchAmbientContext();
    }
    invocation.effectStops.splice(0).forEach(function (stop) {
      try { stop(); } catch (err) {
        console.error("[Citry] managed component effect cleanup failed:", err);
      }
    });
    invocation.resources.splice(0).forEach(function (cleanup) {
      try { cleanup(); } catch (err) {
        console.error("[Citry] managed component resource cleanup failed:", err);
      }
    });
    if (invocation.userCleanup) {
      try { invocation.userCleanup(); } catch (err) {
        console.error("[Citry] component cleanup for '" + lifecycle.classId + "' failed:", err);
      }
    }
    lifecycle.invocation = null;
  };

  var destroyComponentBoundary = null;

  var cancelLifecycleCalls = function (lifecycle, reason) {
    var cancelled = false;
    Array.from(lifecycle.calls).forEach(function (call) {
      if (call.status === "settled" || call.status === "cancelled") return;
      cancelled = true;
      call.status = "cancelled";
      releaseCallHolds(call);
      releaseCallData(call);
      if (reason) {
        console.warn(
          "[Citry] cancelled component callback for retired render id '" + call.componentId + "': " + reason
        );
      }
    });
    lifecycle.calls.clear();
    if (cancelled) queueMicrotask(flushCalls);
  };

  var destroyLifecycle = function (lifecycle, reason) {
    if (!lifecycle || !lifecycle.active) return;
    lifecycle.active = false;
    cancelLifecycleCalls(lifecycle, reason || "its ownership caps left the document");
    disposeInvocation(lifecycle);
    Array.from(lifecycle.componentBoundaries || []).forEach(function (boundary) {
      if (destroyComponentBoundary) destroyComponentBoundary(boundary);
    });
    if (lifecycle.propsController) lifecycle.propsController.destroy();
    lifecycle.els.forEach(function (root) {
      var owner = rootScopeOwners.get(root);
      if (!owner || owner.scope !== lifecycle.scope) return;
      owner.scope = null;
      owner.owner.current = null;
    });
    if (lifecycle.rootGroup) lifecycle.rootGroup.destroy();
    else replaceArrayContents(lifecycle.els, []);
    releaseComponentDataKey(lifecycle.dataKey);
    lifecycle.dataKey = null;
    componentLifecycles.delete(lifecycle.logical.id);
    if (lifecycle.logicalState.lifecycle === lifecycle) lifecycle.logicalState.lifecycle = null;
    liveInstances.delete(lifecycle.renderId);
    if (lifecycle.compatRenderId) liveInstances.delete(lifecycle.compatRenderId);
    scheduleCssGc(lifecycle.classId);
    scheduleLifecycleReconcile();
  };

  var deactivateRenderLink = function (state, link) {
    if (!link || !link.link.active) return;
    link.link.active = false;
    link.anchorState.active = false;
    link.logicalState.active = false;
    browserAnchors.delete(link.anchorState.id);
    link.anchorState.revision = null;
    link.anchorState.renderId = null;
    link.logicalState.revision = null;
    link.logicalState.renderId = null;
    if (scheduleOwnershipPrune) scheduleOwnershipPrune();
  };

  var ensureLifecycle = function (route, cascade, visited) {
    var state = ownershipStates.get(route.revision);
    var link = state && state.renderLinks.get(route.instance.renderId);
    if (!link || !link.link.active) return null;
    var lifecycle = link.logicalState.lifecycle;
    if (!lifecycle || !lifecycle.active) {
      lifecycle = {
        active: true,
        logical: link.link.logical,
        logicalState: link.logicalState,
        classId: route.instance.classId,
        revision: route.revision,
        renderId: route.instance.renderId,
        compatRenderId: null,
        scope: link.logicalState.scope || (alpineOwner ? alpineOwner.reactive({}) : null),
        els: link.logicalState.els,
        calls: new Set(),
        dataKey: null,
        invocation: null,
        componentBoundaries: new Set(),
        propsController: null,
        rootGroup: null,
      };
      lifecycle.rootGroup = new RootGroup(lifecycle.els, function () {
        return lifecycle.active && lifecycleCapsAreLive(lifecycle);
      });
      link.logicalState.lifecycle = lifecycle;
      link.logicalState.scope = lifecycle.scope;
      componentLifecycles.set(lifecycle.logical.id, lifecycle);
    } else {
      lifecycle.classId = route.instance.classId;
      lifecycle.revision = route.revision;
      lifecycle.renderId = route.instance.renderId;
      if (!lifecycle.scope && alpineOwner) {
        lifecycle.scope = alpineOwner.reactive({});
        link.logicalState.scope = lifecycle.scope;
      }
    }
    liveInstances.set(lifecycle.renderId, lifecycle.classId);
    if (cascade) {
      visited = visited || new Set();
      if (visited.has(route.instance.renderId)) return lifecycle;
      visited.add(route.instance.renderId);
      (state.childrenByParent.get(route.instance.renderId) || []).forEach(function (childRenderId) {
        try { ensureLifecycle(resolveOwnershipRoute(route.revision, childRenderId, null), true, visited); } catch (_err) {}
      });
    }
    scheduleLifecycleReconcile();
    return lifecycle;
  };

  var reconcileComponentLifecycles = function () {
    lifecycleReconcileScheduled = false;
    if (rangeMorphDepth > 0 || ownershipAdoptionDepth > 0) {
      scheduleLifecycleReconcile();
      return;
    }
    reconcilePhysicalRangeGroups();
    componentLifecycles.forEach(function (lifecycle) {
      if (!lifecycle.active) return;
      if (!lifecycleCapsAreLive(lifecycle)) {
        var failedRange = lifecyclePhysicalRange(lifecycle);
        var failedLink = failedRange.state && failedRange.route
          ? failedRange.state.renderLinks.get(failedRange.route.instance.renderId)
          : null;
        if (failedRange.state) reportPhysicalRangeCorruption(failedRange.state, failedRange.physical);
        destroyLifecycle(lifecycle);
        if (failedRange.state && failedLink && failedLink.logicalState === lifecycle.logicalState) {
          deactivateRenderLink(failedRange.state, failedLink);
        }
        return;
      }
      var route = routeForLifecycle(lifecycle);
      if (!route) {
        destroyLifecycle(lifecycle);
        return;
      }
      lifecycle.revision = route.revision;
      lifecycle.renderId = route.instance.renderId;
      lifecycle.classId = route.instance.classId;
      if (!lifecycle.scope && alpineOwner) lifecycle.scope = alpineOwner.reactive({});
      var roots = rootsForLifecycle(lifecycle);
      if (lifecycle.rootGroup) lifecycle.rootGroup.setRoots(roots);
      else replaceArrayContents(lifecycle.els, roots);
      lifecycle.calls.forEach(function (call) {
        if (call.status === "staged" || call.status === "waiting") {
          roots.forEach(function (root) { holdRootForCall(root, call); });
        }
      });
    });
    if (alpineOwner) {
      document.querySelectorAll("[data-citry-root]").forEach(function (root) {
        var lifecycle = innermostLifecycleForRoot(root);
        if (
          lifecycle &&
          lifecycle.scope &&
          (root === alpineBoundaryRoot || (root._x_marker && !root.hasAttribute("x-citry-boundary")))
        ) {
          isolateRootScope(root, lifecycle.scope);
        } else if (!lifecycle) {
          var owner = rootScopeOwners.get(root);
          if (owner) {
            owner.scope = null;
            owner.owner.current = null;
          }
        }
      });
    }
  };

  var scheduleLifecycleReconcile = function () {
    if (lifecycleReconcileScheduled) return;
    lifecycleReconcileScheduled = true;
    queueMicrotask(reconcileComponentLifecycles);
  };

  var boundaryIsLive = function (boundary, carrier) {
    if (boundary.destroyed || !boundary.sourceLifecycle.active || !boundary.targetLifecycle.active) return false;
    if (boundary.sourceOrigin && !boundary.sourceOrigin.isConnected) return false;
    if (!lifecycleCapsAreLive(boundary.sourceLifecycle) || !lifecycleCapsAreLive(boundary.targetLifecycle)) return false;
    if (carrier) return boundary.targetLifecycle.rootGroup.hasLive(carrier);
    return true;
  };

  var boundaryEventsScope = function (boundary, carrier) {
    var events = globalThis.Citry && globalThis.Citry.events;
    if (events && events._internal && typeof events._internal.boundaryScope === "function") {
      return events._internal.boundaryScope(
        boundary.invocation.sourceRenderId,
        carrier || null,
        function () { return boundaryIsLive(boundary, carrier || null); }
      );
    }
    return {
      $state: Object.freeze({}),
      $loading: function () { return false; },
      $error: null,
      $sendEvent: function () {
        return Promise.reject(new Error("[Citry] the source component declares no Events runtime."));
      },
      $onEvent: function () { return function () {}; },
    };
  };

  var boundaryPhysicalScope = function (boundary, event, carrier) {
    var scope = {};
    Object.defineProperties(scope, Object.getOwnPropertyDescriptors(boundaryEventsScope(boundary, carrier)));
    Object.defineProperties(scope, {
      $el: { enumerable: true, value: carrier },
      $event: { enumerable: true, value: event },
      $dispatch: {
        enumerable: true,
        value: function (name, detail, options) {
          if (!carrier) return false;
          return carrier.dispatchEvent(new CustomEvent(name, Object.assign({
            detail: detail == null ? {} : detail,
            bubbles: true,
            composed: true,
            cancelable: true,
          }, options || {})));
        },
      },
    });
    return scope;
  };

  var boundarySourceScope = function (boundary) {
    var origin = boundary.sourceOrigin;
    var scope = {};
    Object.defineProperties(scope, Object.getOwnPropertyDescriptors(boundaryEventsScope(boundary, null)));
    Object.defineProperties(scope, {
      $el: { enumerable: true, value: origin },
      $dispatch: {
        enumerable: true,
        value: function (name, detail, options) {
          if (!origin) return false;
          return origin.dispatchEvent(new CustomEvent(name, Object.assign({
            detail: detail == null ? {} : detail,
            bubbles: true,
            composed: true,
            cancelable: true,
          }, options || {})));
        },
      },
    });
    return scope;
  };

  var observeRejectedThenable = function (value, onRejected) {
    if (value === null || (typeof value !== "object" && typeof value !== "function")) return;
    var then;
    try { then = value.then; } catch (err) {
      onRejected(err);
      return;
    }
    if (typeof then !== "function") return;
    try { then.call(value, function () {}, onRejected); } catch (err) { onRejected(err); }
  };

  var evaluateBoundaryExpression = function (boundary, expression, event, carrier, physical) {
    if (!boundary.sourceCarrier || !boundaryIsLive(boundary, carrier || null)) {
      throw new Error("[Citry] a component-boundary expression was dropped because its source or target is no longer live.");
    }
    var scope = physical
      ? boundaryPhysicalScope(boundary, event, carrier)
      : boundarySourceScope(boundary);
    return alpineOwner.evaluateRaw(boundary.sourceCarrier, expression, {
      scope: scope,
      params: event ? [event] : [],
    });
  };

  var propsBoundaryForLifecycle = function (lifecycle) {
    var found = null;
    lifecycle.componentBoundaries.forEach(function (boundary) {
      if (found || boundary.targetLifecycle !== lifecycle) return;
      if (boundary.invocation.clientBindings.some(function (clientBinding) { return clientBinding.payload.type === "props"; })) found = boundary;
    });
    return found;
  };

  var lifecycleExpectsPropsSupply = function (lifecycle) {
    var route = routeForLifecycle(lifecycle);
    var state = route && ownershipStates.get(route.revision);
    var expected = false;
    if (!state) return false;
    state.registry.nestedComponents.values().forEach(function (invocation) {
      if (expected || invocation.targetRenderId !== route.instance.renderId) return;
      expected = invocation.clientBindings.some(function (clientBinding) { return clientBinding.payload.type === "props"; });
    });
    return expected;
  };

  var installPropsSupplier = function (boundary) {
    var lifecycle = boundary.targetLifecycle;
    var controller = lifecycle.propsController;
    if (!controller || controller.effectStop || !boundary.sourceCarrier) return;
    var clientBinding = boundary.invocation.clientBindings.find(function (candidate) { return candidate.payload.type === "props"; });
    if (!clientBinding) return;
    controller.sourceBoundary = boundary;
    var runner = alpineOwner.effect(function () {
      var value;
      var error = null;
      try {
        value = evaluateBoundaryExpression(boundary, clientBinding.payload.expression, null, null, false);
      } catch (err) {
        error = err;
      }
      observeRejectedThenable(value, function () {});
      controller.apply(value, error);
      flushCalls();
    });
    controller.effectStop = function () { alpineOwner.release(runner); };
  };

  var ensureLifecycleProps = function (lifecycle, entry) {
    var supplyBoundary = propsBoundaryForLifecycle(lifecycle);
    var expectsSupply = Boolean(supplyBoundary) || lifecycleExpectsPropsSupply(lifecycle);
    if (!entry.hasProps && !expectsSupply) return null;
    if (!lifecycle.propsController) {
      lifecycle.propsController = createPropsController(
        lifecycle,
        entry.hasProps ? entry.props : {},
        expectsSupply
      );
      if (!expectsSupply) lifecycle.propsController.applyNoSupply();
    }
    if (supplyBoundary) installPropsSupplier(supplyBoundary);
    return lifecycle.propsController;
  };

  var parseAlpineBoundaryKey = function (key) {
    var name = key.indexOf("x-on:") === 0 ? key.slice(5) : key.slice(1);
    var parts = name.split(".");
    return { event: parts.shift(), modifiers: parts };
  };

  var reportRootlessBoundaryHandler = function (boundary, clientBinding) {
    console.error(
      "[Citry] component boundary handler '" + clientBinding.key + "' cannot attach to render '" +
        boundary.invocation.targetRenderId + "' because the child rendered no HTML element root. " +
        "Add an element root or remove the DOM handler; $c-props, init, and @c-poll remain valid."
    );
  };

  var installBoundaryHandlers = function (boundary) {
    var group = boundary.targetLifecycle.rootGroup;
    boundary.invocation.clientBindings.forEach(function (clientBinding) {
      var payload = clientBinding.payload;
      if (payload.type === "props") return;
      if (payload.type !== "citry-poll" && group.els.length === 0) {
        reportRootlessBoundaryHandler(boundary, clientBinding);
      }
      if (payload.type === "alpine-handler") {
        var parsed = parseAlpineBoundaryKey(clientBinding.key);
        boundary.cleanups.push(group.on(parsed.event, parsed.modifiers, function (event, carrier) {
          try {
            var result = evaluateBoundaryExpression(boundary, payload.expression, event, carrier, true);
            observeRejectedThenable(result, function (err) {
              console.error("[Citry] relocated Alpine handler '" + clientBinding.key + "' failed:", err);
            });
          } catch (err) {
            console.error("[Citry] relocated Alpine handler '" + clientBinding.key + "' failed:", err);
          }
        }));
        return;
      }
      var dispatchCitry = function (event, carrier) {
        var args = null;
        try {
          if (payload.args != null) {
            args = evaluateBoundaryExpression(boundary, "(" + payload.args + ")", event, carrier, Boolean(carrier));
            if (args === null || typeof args !== "object" || Array.isArray(args) || typeof args.then === "function") {
              observeRejectedThenable(args, function () {});
              throw new TypeError("the Citry boundary argument expression must synchronously return an object.");
            }
          }
          var events = globalThis.Citry && globalThis.Citry.events;
          if (!events || !events._internal || typeof events._internal.sendBoundary !== "function") {
            throw new Error("the Events runtime is not available.");
          }
          var promise = events._internal.sendBoundary(
            boundary.invocation.sourceRenderId,
            payload.handler,
            args,
            payload.type === "citry-poll"
              ? { recurring: boundary.key + ":" + clientBinding.key }
              : undefined,
            carrier || null,
            function () { return boundaryIsLive(boundary, carrier || null); },
            event || null
          );
          if (promise) promise.then(null, function () {});
        } catch (err) {
          console.error("[Citry] relocated Citry handler '" + clientBinding.key + "' failed:", err);
        }
      };
      if (payload.type === "citry-poll") {
        boundary.cleanups.push(group.poll(payload.interval, function (carrier) { dispatchCitry(null, carrier); }));
      } else {
        boundary.cleanups.push(group.on(payload.event, [], dispatchCitry, payload));
      }
    });
  };

  var captureBoundarySource = function (boundary, targetRoot, sourceOrigin) {
    if (boundary.destroyed || boundary.sourceCarrier) return;
    var sharedSourceRoot = targetRoot && (targetRoot.getAttribute("data-cid") || "")
      .trim()
      .split(/\s+/)
      .indexOf(boundary.invocation.sourceRenderId) !== -1;
    var origin = sourceOrigin || (
      targetRoot && (sharedSourceRoot ? targetRoot : targetRoot._x_teleportBack || targetRoot.parentElement || targetRoot)
    );
    if (origin && !origin.isConnected) return;
    // The target root can already carry a child-owned stack from an earlier
    // registry pass. The physical source origin is the lexical side of the
    // vanished component tag, so capture from it instead.
    var stack = origin ? alpineOwner.closestDataStack(origin).slice() : [];
    var sourceScope = boundary.sourceLifecycle.scope;
    if (sourceScope && stack.indexOf(sourceScope) === -1) stack.unshift(sourceScope);
    var carrier = document.createElement("span");
    carrier._x_dataStack = stack;
    if (origin) carrier._x_teleportBack = origin;
    boundary.sourceCarrier = carrier;
    boundary.sourceOrigin = origin;
    installBoundaryHandlers(boundary);
    installPropsSupplier(boundary);
  };

  var activateBoundariesForRoot = function (root) {
    if (!root || !root.getAttribute) return;
    var ids = (root.getAttribute("data-cid") || "").trim().split(/\s+/).filter(Boolean);
    ids.forEach(function (renderId) {
      (componentBoundariesByTarget.get(renderId) || []).forEach(function (boundary) {
        captureBoundarySource(boundary, root, null);
      });
    });
  };

  var activateRootlessBoundaries = function () {
    liveComponentBoundaries.forEach(function (boundary) {
      if (boundary.destroyed || boundary.sourceCarrier) return;
      if (!lifecycleCapsAreLive(boundary.targetLifecycle)) return;
      if (boundary.targetLifecycle.els.length) {
        var targetRoot = boundary.targetLifecycle.els.find(function (root) {
          return root.isConnected && root._x_marker;
        });
        if (targetRoot) captureBoundarySource(boundary, targetRoot, null);
        return;
      }
      var route = routeForLifecycle(boundary.targetLifecycle);
      var state = route && ownershipStates.get(route.revision);
      var physical = state && state.registry.physicalRegions.get(route.instance.key);
      var origin = physical && physical.start && physical.start.parentNode;
      if (origin instanceof Element) captureBoundarySource(boundary, null, origin);
      else if (physical && physical.topology === "document-body") captureBoundarySource(boundary, null, null);
    });
  };

  var adoptBoundaryEndpoint = function (state, renderId, provisionalLifecycle, adoptedLifecycle) {
    if (!state || !provisionalLifecycle || !adoptedLifecycle) return;
    Array.from(provisionalLifecycle.componentBoundaries).forEach(function (boundary) {
      if (boundary.revision !== state.publicRevision.revision) return;
      if (
        boundary.invocation.sourceRenderId === renderId &&
        boundary.sourceLifecycle === provisionalLifecycle
      ) {
        provisionalLifecycle.componentBoundaries.delete(boundary);
        boundary.sourceLifecycle = adoptedLifecycle;
        adoptedLifecycle.componentBoundaries.add(boundary);
      }
      if (
        boundary.invocation.targetRenderId === renderId &&
        boundary.targetLifecycle === provisionalLifecycle
      ) {
        provisionalLifecycle.componentBoundaries.delete(boundary);
        boundary.targetLifecycle = adoptedLifecycle;
        adoptedLifecycle.componentBoundaries.add(boundary);
      }
    });
  };

  var retireSupersededComponentBoundaries = function (state) {
    var incomingSources = new Set();
    state.renderLinks.forEach(function (link) {
      var lifecycle = link.link.active && link.logicalState.lifecycle;
      if (lifecycle) incomingSources.add(lifecycle);
    });
    Array.from(liveComponentBoundaries).forEach(function (candidate) {
      if (
        candidate.destroyed ||
        candidate.revision === state.publicRevision.revision ||
        !incomingSources.has(candidate.sourceLifecycle)
      ) return;
      var successor = null;
      state.registry.nestedComponents.values().forEach(function (invocation) {
        if (successor) return;
        var sourceLink = state.renderLinks.get(invocation.sourceRenderId);
        var targetLink = state.renderLinks.get(invocation.targetRenderId);
        if (
          sourceLink && targetLink &&
          sourceLink.logicalState.lifecycle === candidate.sourceLifecycle &&
          targetLink.logicalState.lifecycle === candidate.targetLifecycle
        ) successor = invocation;
      });
      var controller = candidate.targetLifecycle.propsController;
      destroyComponentBoundary(candidate);
      if (!controller) return;
      controller.sourceBoundary = null;
      controller.expectsSupply = Boolean(successor && successor.clientBindings.some(function (clientBinding) {
        return clientBinding.payload.type === "props";
      }));
      if (controller.expectsSupply) {
        controller.initialSettled = false;
        controller.currentValid = false;
      } else {
        // A compatible adoption creates its successor client binding later in the
        // same transaction. Do not emit a transient "required prop missing"
        // episode in that gap; settle no-supply only after boundary
        // reconciliation has had its microtask to attach a successor.
        queueMicrotask(function () {
          if (
            !candidate.targetLifecycle.active ||
            candidate.targetLifecycle.propsController !== controller ||
            controller.sourceBoundary ||
            propsBoundaryForLifecycle(candidate.targetLifecycle) ||
            lifecycleExpectsPropsSupply(candidate.targetLifecycle)
          ) return;
          controller.applyNoSupply();
          flushCalls();
        }, 0);
      }
    });
  };

  destroyComponentBoundary = function (boundary) {
    if (!boundary || boundary.destroyed) return;
    boundary.destroyed = true;
    boundary.cleanups.splice(0).forEach(function (cleanup) {
      try { cleanup(); } catch (_err) {}
    });
    if (
      boundary.targetLifecycle.propsController &&
      boundary.targetLifecycle.propsController.sourceBoundary === boundary
    ) {
      boundary.targetLifecycle.propsController.destroy();
    }
    boundary.sourceLifecycle.componentBoundaries.delete(boundary);
    boundary.targetLifecycle.componentBoundaries.delete(boundary);
    liveComponentBoundaries.delete(boundary);
    var targets = componentBoundariesByTarget.get(boundary.invocation.targetRenderId) || [];
    targets = targets.filter(function (candidate) { return candidate !== boundary; });
    if (targets.length) componentBoundariesByTarget.set(boundary.invocation.targetRenderId, targets);
    else componentBoundariesByTarget.delete(boundary.invocation.targetRenderId);
    boundary.sourceCarrier = null;
    boundary.sourceOrigin = null;
    if (scheduleOwnershipPrune) scheduleOwnershipPrune();
  };

  var activateGraphClientBindings = function (revision) {
    var state = ownershipStates.get(revision);
    if (!state) return;
    state.registry.nestedComponents.values().forEach(function (invocation) {
      if (!invocation.clientBindings.length) return;
      var sourceLifecycle = null;
      var targetLifecycle = null;
      try {
        sourceLifecycle = ensureLifecycle(resolveOwnershipRoute(revision, invocation.sourceRenderId, null), true);
        targetLifecycle = ensureLifecycle(resolveOwnershipRoute(revision, invocation.targetRenderId, null), true);
      } catch (_err) {
        return;
      }
      if (!sourceLifecycle || !targetLifecycle) return;
      var boundary = {
        key: revision + ":" + invocation.key,
        revision: revision,
        invocation: invocation,
        sourceLifecycle: sourceLifecycle,
        targetLifecycle: targetLifecycle,
        sourceCarrier: null,
        sourceOrigin: null,
        cleanups: [],
        destroyed: false,
      };
      sourceLifecycle.componentBoundaries.add(boundary);
      targetLifecycle.componentBoundaries.add(boundary);
      liveComponentBoundaries.add(boundary);
      var targets = componentBoundariesByTarget.get(invocation.targetRenderId) || [];
      targets.push(boundary);
      componentBoundariesByTarget.set(invocation.targetRenderId, targets);
    });
  };

  registerAlpineProvider({
    root: function () { return "[data-citry-root]"; },
    beforeBoundary: activateBoundariesForRoot,
    init: function (el) {
      if (!el.hasAttribute || !el.hasAttribute("data-citry-root")) return;
      var lifecycle = innermostLifecycleForRoot(el);
      if (lifecycle && lifecycle.scope) isolateRootScope(el, lifecycle.scope);
    },
    mutations: function () {
      scheduleLifecycleReconcile();
      scheduleFillSourceReconcile();
      queueMicrotask(activateRootlessBoundaries);
    },
    afterStart: function () {
      reconcileComponentLifecycles();
      reconcileFillSources();
      activateRootlessBoundaries();
    },
  });

  var preflightEventsBridge = function (revision, entries) {
    return entries.map(function (entry) {
      var route = resolveOwnershipRoute(revision, entry.componentId, entry.classId);
      var link = ownershipStates.get(revision).renderLinks.get(entry.componentId);
      if (link.anchorState.events) {
        throw new TypeError("[Citry] graph: render id '" + entry.componentId + "' already has an Events anchor.");
      }
      return route;
    });
  };

  var attachEventsBridge = function (revision, renderId, classId, eventsAnchor) {
    var route = resolveOwnershipRoute(revision, renderId, classId);
    ensureLifecycle(route, true);
    var link = ownershipStates.get(revision).renderLinks.get(renderId);
    if (link.anchorState.events && link.anchorState.events !== eventsAnchor) {
      throw new TypeError("[Citry] graph: render id '" + renderId + "' already has an Events anchor.");
    }
    link.anchorState.events = eventsAnchor;
    return route.anchor;
  };

  var detachEventsBridge = function (generalAnchor, eventsAnchor) {
    if (!generalAnchor) return;
    ownershipStates.forEach(function (state) {
      state.renderLinks.forEach(function (link) {
        if (link.link.anchor === generalAnchor && link.anchorState.events === eventsAnchor) {
          link.anchorState.events = null;
        }
      });
    });
  };

  // A graph-backed adoption calls this while the incoming revision is private.
  // The explicit transaction transfers the stable anchor and, for a
  // same-class match, the logical lifecycle. The fallback below remains
  // for legacy Events responses that do not carry an ownership graph.
  var transitionEventsBridge = function (generalAnchor, renderId, classId) {
    if (!generalAnchor || typeof renderId !== "string" || typeof classId !== "string") return;
    var source = null;
    var target = null;
    ownershipStates.forEach(function (state, revision) {
      state.renderLinks.forEach(function (link) {
        if (!source && link.link.active && link.link.anchor === generalAnchor) {
          source = { revision: revision, link: link };
        }
      });
      var candidate = state.renderLinks.get(renderId);
      if (state.provisional && candidate && candidate.link.active && candidate.record.classId === classId) {
        target = { revision: revision, link: candidate };
      }
    });
    if (source && target && source.link !== target.link) {
      replaceOwnership([{
        fromRevision: source.revision,
        fromRenderId: source.link.record.renderId,
        toRevision: target.revision,
        toRenderId: target.link.record.renderId,
        preserveLogical: source.link.record.classId === target.link.record.classId,
      }]);
      return;
    }
    var lifecycle = null;
    ownershipStates.forEach(function (state) {
      if (lifecycle) return;
      state.renderLinks.forEach(function (link) {
        if (
          !lifecycle &&
          link.link.active &&
          link.link.anchor === generalAnchor &&
          link.logicalState.lifecycle &&
          link.logicalState.lifecycle.active
        ) {
          lifecycle = link.logicalState.lifecycle;
        }
      });
    });
    if (!lifecycle) return;
    if (lifecycle.classId !== classId) {
      destroyLifecycle(lifecycle, "an Events compatibility render changed component class");
      return;
    }
    if (lifecycle.compatRenderId) liveInstances.delete(lifecycle.compatRenderId);
    else liveInstances.delete(lifecycle.renderId);
    lifecycle.compatRenderId = renderId;
    liveInstances.set(renderId, classId);
    scheduleLifecycleReconcile();
  };

  var retireEventsBridge = function (generalAnchor) {
    if (!generalAnchor) return;
    var lifecycles = [];
    var retiredLinks = [];
    ownershipStates.forEach(function (state) {
      state.renderLinks.forEach(function (link) {
        var lifecycle = link.logicalState.lifecycle;
        if (
          link.link.active &&
          link.link.anchor === generalAnchor &&
          lifecycle &&
          lifecycle.active &&
          lifecycles.indexOf(lifecycle) === -1
        ) {
          lifecycles.push(lifecycle);
        }
        if (link.link.active && link.link.anchor === generalAnchor) retiredLinks.push({ state: state, link: link });
      });
    });
    lifecycles.forEach(function (lifecycle) {
      destroyLifecycle(lifecycle, "its Events anchor was retired");
    });
    retiredLinks.forEach(function (retired) {
      var link = retired.link;
      physicalRangesForKey(retired.state, link.record.key).forEach(function (physical) {
        if (
          physical.start.data === physical.startMarker &&
          physical.end.data === physical.endMarker
        ) {
          physical.start.remove();
          physical.end.remove();
        }
      });
      deactivateRenderLink(retired.state, link);
    });
  };

  var isOwnershipAnchorLive = function (generalAnchor) {
    if (!generalAnchor || !generalAnchor.active) return false;
    var live = false;
    ownershipStates.forEach(function (state) {
      if (live) return;
      state.renderLinks.forEach(function (link) {
        if (live || !link.link.active || link.link.anchor !== generalAnchor) return;
        var lifecycle = link.logicalState.lifecycle;
        if (
          lifecycle &&
          lifecycle.active &&
          lifecycle.compatRenderId &&
          document.querySelector("[data-cid-" + lifecycle.compatRenderId + "]")
        ) {
          live = true;
          return;
        }
        live = physicalRangesForKey(state, link.record.key).some(function (physical) {
          return physicalRangeIsLive(state, physical);
        });
      });
    });
    return live;
  };

  // A8 supplies these explicit correspondences from its atomic DOM+graph
  // transaction. The complete proposal is validated first and correspondence
  // is never guessed from class or DOM position.
  var replaceOwnership = function (replacements) {
    if (!Array.isArray(replacements) || !replacements.length) {
      throw new TypeError("[Citry] graph: replacement needs a non-empty correspondence array.");
    }
    var staged = [];
    var fromKeys = new Set();
    var toKeys = new Set();
    var fromLinks = new Set();
    var toLinks = new Set();
    replacements.forEach(function (record, index) {
      if (!record || typeof record !== "object") {
        throw new TypeError("[Citry] graph: replacement[" + index + "] must be an object.");
      }
      var fromState = ownershipStates.get(record.fromRevision);
      var from = fromState && fromState.renderLinks.get(record.fromRenderId);
      if (!from || !from.link.active) {
        throw new TypeError("[Citry] graph: replacement source is unknown or inactive.");
      }
      var fromKey = record.fromRevision + ":" + record.fromRenderId;
      if (fromKeys.has(fromKey)) throw new TypeError("[Citry] graph: replacement repeats a source render.");
      fromKeys.add(fromKey);
      fromLinks.add(from);
      var to = null;
      var toState = null;
      if (record.toRevision != null || record.toRenderId != null) {
        if (typeof record.toRevision !== "string" || typeof record.toRenderId !== "string") {
          throw new TypeError("[Citry] graph: replacement target needs both revision and render id.");
        }
        toState = ownershipStates.get(record.toRevision);
        to = toState && toState.renderLinks.get(record.toRenderId);
        if (!to || !to.link.active) throw new TypeError("[Citry] graph: replacement target is unknown or inactive.");
        var toKey = record.toRevision + ":" + record.toRenderId;
        if (toKeys.has(toKey)) throw new TypeError("[Citry] graph: replacement repeats a target render.");
        toKeys.add(toKey);
        toLinks.add(to);
        if (record.preserveLogical === true && from.record.classId !== to.record.classId) {
          throw new TypeError("[Citry] graph: logical identity can be preserved only across the same component class.");
        }
        if (to.anchorState.events) {
          throw new TypeError("[Citry] graph: replacement target already owns an Events anchor.");
        }
      } else if (record.preserveLogical === true) {
        throw new TypeError("[Citry] graph: plain retirement cannot preserve logical identity.");
      }
      staged.push({
        fromState: fromState,
        from: from,
        to: to,
        toState: toState,
        preserveLogical: record.preserveLogical === true,
      });
    });
    toLinks.forEach(function (link) {
      if (fromLinks.has(link)) {
        throw new TypeError("[Citry] graph: one replacement transaction cannot use a render as both source and target.");
      }
    });

    staged.forEach(function (record) {
      var from = record.from;
      var sourceLifecycle = from.logicalState.lifecycle;
      var sourceRoots = sourceLifecycle
        ? sourceLifecycle.els.slice()
        : physicalRangesForKey(record.fromState, from.record.key).flatMap(function (physical) {
            return physicalRangeRoots(physical, from.record.renderId);
          });
      var targetLifecycle = record.to && record.to.logicalState.lifecycle;
      var targetCall =
        record.preserveLogical && record.toState
          ? record.toState.graphCalls.get(record.to.record.renderId) || null
          : null;
      if (record.preserveLogical) {
        if (targetLifecycle && targetLifecycle !== sourceLifecycle) {
          adoptBoundaryEndpoint(
            record.toState,
            record.to.record.renderId,
            targetLifecycle,
            sourceLifecycle
          );
          destroyLifecycle(targetLifecycle, "a correlated replacement adopted the source logical identity");
        }
        if (sourceLifecycle) {
          cancelLifecycleCalls(sourceLifecycle, null);
          disposeInvocation(sourceLifecycle);
        }
      } else if (sourceLifecycle) {
        destroyLifecycle(
          sourceLifecycle,
          record.to ? "a class replacement created a fresh logical instance" : "the logical instance was retired"
        );
      }
      if (!record.to) {
        deactivateRenderLink(record.fromState, from);
        return;
      }
      from.link.active = false;
      var to = record.to;
      var provisionalAnchor = to.link.anchor;
      var provisionalAnchorState = to.anchorState;
      var provisionalLogical = to.link.logical;
      var provisionalLogicalState = to.logicalState;
      var targetRevision = provisionalAnchorState.revision;
      provisionalAnchorState.active = false;
      browserAnchors.delete(provisionalAnchor.id);
      to.link.anchor = from.link.anchor;
      to.anchorState = from.anchorState;
      from.anchorState.active = true;
      from.anchorState.revision = targetRevision;
      from.anchorState.renderId = to.record.renderId;
      from.anchorState.classId = to.record.classId;
      if (record.preserveLogical) {
        provisionalLogicalState.active = false;
        to.link.logical = from.link.logical;
        to.logicalState = from.logicalState;
        from.logicalState.active = true;
        from.logicalState.revision = from.anchorState.revision;
        from.logicalState.renderId = to.record.renderId;
        record.toState.logicalInstances.delete(provisionalLogical.id);
        record.toState.logicalInstances.set(from.link.logical.id, from.link.logical);
        if (sourceLifecycle) {
          sourceLifecycle.active = true;
          sourceLifecycle.logical = from.link.logical;
          sourceLifecycle.logicalState = from.logicalState;
          sourceLifecycle.revision = targetRevision;
          sourceLifecycle.renderId = to.record.renderId;
          sourceLifecycle.compatRenderId = null;
          sourceLifecycle.classId = to.record.classId;
          from.logicalState.lifecycle = sourceLifecycle;
          componentLifecycles.set(sourceLifecycle.logical.id, sourceLifecycle);
          liveInstances.delete(from.record.renderId);
          liveInstances.set(to.record.renderId, to.record.classId);
          if (targetCall) {
            targetCall.lifecycle = sourceLifecycle;
            targetCall.route = resolveOwnershipRoute(targetRevision, to.record.renderId, to.record.classId);
            targetCall.status = targetCall.dependenciesReady ? "waiting" : "staged";
            targetCall.heldRoots = new Set();
            // A settled call transferred its data reference to the
            // provisional lifecycle. Destroying that lifecycle above releases
            // the reference, so retain it again before the fresh render is
            // queued against the preserved logical instance.
            retainCallData(targetCall);
            sourceLifecycle.calls.add(targetCall);
            if (pendingCalls.indexOf(targetCall) === -1) pendingCalls.push(targetCall);
          }
        }
      } else {
        from.logicalState.active = false;
        to.link.logical = to.record.logicalInstance;
        provisionalLogicalState.anchor = from.link.anchor;
        from.anchorState.logical = to.link.logical;
      }
      // Keep the target record's dynamic getters routed through the updated
      // link cell; the provisional anchor is intentionally retired.
      to.link.active = true;
      record.toState.anchors.delete(provisionalAnchor.id);
      record.toState.anchors.set(from.link.anchor.id, from.link.anchor);
      if (record.toState.adoption) {
        record.toState.adoption.transfers.set(
          to.record.key,
          physicalRangesForKey(record.fromState, from.record.key).slice()
        );
        record.toState.adoption.markerTransfers.push({
          fromRenderId: from.record.renderId,
          toRenderId: to.record.renderId,
          targetKey: to.record.key,
          roots: sourceRoots,
        });
      }
      scheduleLifecycleReconcile();
      if (targetCall && sourceLifecycle) flushCalls();
    });
    if (scheduleOwnershipPrune) scheduleOwnershipPrune();
  };

  var mintRuntimePlacementId = function () {
    runtimePlacementCounter += 1;
    return "p" + runtimePlacementCounter.toString(36);
  };

  var validateRuntimePlacementCaps = function (revision, expected) {
    var prefix = "citry:p1:" + revision + ":";
    var comments = document.createTreeWalker(document, NodeFilter.SHOW_COMMENT);
    var placements = new Map();
    var stacks = new Map();
    var node;
    while ((node = comments.nextNode())) {
      var text = node.data.trim();
      if (text.indexOf(prefix) !== 0) continue;
      var match = /^citry:p1:([0-9a-f]{64}):([A-Za-z0-9_-]+):(\d+):([ir]):(\d+):([se])$/.exec(text);
      if (!match || match[1] !== revision) {
        throw new TypeError("[Citry] graph: malformed runtime placement cap.");
      }
      var placementId = match[2];
      var key = match[3] + ":" + match[4] + ":" + match[5];
      if (!expected.has(key)) {
        throw new TypeError("[Citry] graph: runtime placement cap names an unknown record " + key + ".");
      }
      var found = placements.get(placementId);
      if (!found) {
        found = new Map();
        placements.set(placementId, found);
      }
      var pair = found.get(key) || {};
      if (pair[match[6]]) {
        throw new TypeError("[Citry] graph: duplicate runtime placement cap " + placementId + ":" + key + ".");
      }
      pair[match[6]] = node;
      found.set(key, pair);
      var stack = stacks.get(placementId) || [];
      stacks.set(placementId, stack);
      if (match[6] === "s") {
        var graphPrefix = match[3] + ":r:";
        pair.parentRegion = null;
        for (var index = stack.length - 1; index >= 0; index -= 1) {
          if (stack[index].indexOf(graphPrefix) === 0) {
            pair.parentRegion = Number(stack[index].slice(graphPrefix.length));
            break;
          }
        }
        stack.push(key);
      } else {
        if (stack.pop() !== key) {
          throw new TypeError("[Citry] graph: runtime placement caps cross or close out of order.");
        }
        if (!pair.s || pair.s.parentNode !== node.parentNode || !nodePrecedes(pair.s, node)) {
          throw new TypeError("[Citry] graph: runtime placement cap endpoints must share one ordered parent.");
        }
      }
    }
    placements.forEach(function (found, placementId) {
      if ((stacks.get(placementId) || []).length) {
        throw new TypeError("[Citry] graph: a runtime placement opening cap is unclosed.");
      }
      expected.forEach(function (key) {
        var pair = found.get(key);
        if (!pair || !pair.s || !pair.e) {
          throw new TypeError("[Citry] graph: runtime placement '" + placementId + "' is missing cap " + key + ".");
        }
      });
    });
    return placements;
  };

  var buildPhysicalPlacementSet = function (caps, placementId) {
    var physicals = new Map();
    caps.forEach(function (pair, localKey) {
      var parts = localKey.split(":");
      var graphId = Number(parts[0]);
      var kind = parts[1];
      var localId = Number(parts[2]);
      var key = qualifiedGraphId(graphId, kind, localId);
      physicals.set(key, {
        key: key,
        graphId: graphId,
        regionId: kind === "r" ? localId : undefined,
        instanceId: kind === "i" ? localId : undefined,
        start: pair.s,
        end: pair.e,
        startMarker: pair.s.data,
        endMarker: pair.e.data,
        parentRegionId: pair.parentRegion,
        parentPlacement: null,
        placementId: placementId,
        topology: pair.s.parentNode === pair.e.parentNode ? "same-parent" : "document-body",
      });
    });
    physicals.forEach(function (physical) {
      if (physical.parentRegionId != null) {
        physical.parentPlacement = physicals.get(
          qualifiedGraphId(physical.graphId, "r", physical.parentRegionId)
        ) || null;
      }
      Object.freeze(physical);
    });
    return physicals;
  };

  var applyAdoptionTransfers = function (state) {
    state.adoption.transfers.forEach(function (candidates, key) {
      var parts = key.slice(1).split(":");
      var live = candidates.filter(function (physical) {
        return physical.start.isConnected && physical.end.isConnected;
      });
      live.forEach(function (physical, index) {
        var placementId = index === 0 ? null : physical.placementId || mintRuntimePlacementId();
        var prefix = placementId == null
          ? OWNERSHIP_COMMENT_PREFIX + ":" + state.publicRevision.revision + ":"
          : "citry:p1:" + state.publicRevision.revision + ":" + placementId + ":";
        physical.start.data = prefix + parts[0] + ":" + parts[1] + ":" + parts[2] + ":s";
        physical.end.data = prefix + parts[0] + ":" + parts[1] + ":" + parts[2] + ":e";
      });
    });
  };

  var adoptLivePhysicalPlacements = function (state) {
    var expected = new Set(state.caps.keys());
    var canonical = validatePhysicalCaps(OWNERSHIP_COMMENT_PREFIX, state.publicRevision.revision, expected, document);
    var runtime = validateRuntimePlacementCaps(state.publicRevision.revision, expected);
    var byKey = new Map();
    var canonicalPhysical = buildPhysicalPlacementSet(canonical, null);
    canonicalPhysical.forEach(function (physical, key) {
      byKey.set(key, [physical]);
      state.physicalRegions.set(key, physical);
    });
    runtime.forEach(function (caps, placementId) {
      buildPhysicalPlacementSet(caps, placementId).forEach(function (physical, key) {
        var placements = byKey.get(key) || [];
        placements.push(physical);
        byKey.set(key, placements);
      });
    });
    state.caps.clear();
    canonical.forEach(function (pair, key) {
      Object.freeze(pair);
      state.caps.set(key, pair);
    });
    state.physicalPlacements.clear();
    byKey.forEach(function (placements, key) {
      state.physicalPlacements.set(key, placements);
    });
  };

  var prepareOwnershipAdoption = function (manifest, capRoot) {
    if (graphFailures.has(manifest.revision) || seenOwnershipRevisions.has(manifest.revision) || ownershipStates.has(manifest.revision)) {
      throw new TypeError("[Citry] graph: incoming revision was already used.");
    }
    rejectStructuralComponentClones(capRoot);
    var staged = stageOwnershipManifest(manifest, capRoot);
    var normalized = normalizeOwnershipRevision(staged);
    normalized.renderIds.forEach(function (_instance, renderId) {
      ownershipStates.forEach(function (liveState) {
        var live = liveState.renderLinks.get(renderId);
        if (live && live.link.active) {
          throw new TypeError("[Citry] graph: live render id '" + renderId + "' appears in more than one revision.");
        }
      });
    });
    normalized.provisional = true;
    normalized.adoption = {
      transfers: new Map(),
      markerTransfers: [],
      status: "prepared",
      activated: false,
    };
    ownershipStates.set(staged.revision, normalized);
    ownershipAdoptionDepth += 1;
    try {
      normalized.renderIds.forEach(function (instance) {
        ensureLifecycle(resolveOwnershipRoute(staged.revision, instance.renderId, instance.classId), false);
      });
    } catch (err) {
      ownershipStates.delete(staged.revision);
      ownershipAdoptionDepth = Math.max(0, ownershipAdoptionDepth - 1);
      throw err;
    }
    return {
      revision: staged.revision,
      state: normalized,
      status: "prepared",
    };
  };

  var activateOwnershipAdoption = function (transaction) {
    if (!transaction || transaction.status !== "prepared") {
      throw new TypeError("[Citry] graph: ownership adoption transaction is not prepared.");
    }
    var state = transaction.state;
    if (state.adoption.activated) return;
    var fillPlans = preflightGraphFillSources(state);
    activateGraphFillSources(state, fillPlans);
    activateGraphClientBindings(transaction.revision);
    state.adoption.activated = true;
  };

  var adoptionRoot = function (transaction) {
    if (!transaction || transaction.status !== "prepared") {
      throw new TypeError("[Citry] graph: ownership adoption transaction is not prepared.");
    }
    var roots = [];
    transaction.state.renderLinks.forEach(function (link) {
      if (link.record.parentRenderId == null) roots.push(link.record);
    });
    if (!roots.length) return null;
    if (roots.length !== 1) {
      throw new TypeError("[Citry] graph: an adopted component render must have one logical root instance.");
    }
    return { componentId: roots[0].renderId, classId: roots[0].classId };
  };

  var deactivateOwnershipAdoption = function (state) {
    Array.from(fillSourceDescriptors.values()).forEach(function (descriptor) {
      if (descriptor.state === state) retireFillSource(descriptor);
    });
    Array.from(liveComponentBoundaries).forEach(function (boundary) {
      if (boundary.revision === state.publicRevision.revision && destroyComponentBoundary) {
        destroyComponentBoundary(boundary);
      }
    });
  };

  var pruneInactiveOwnershipRevisions = function () {
    ownershipPruneScheduled = false;
    if (ownershipAdoptionDepth > 0 || rangeMorphDepth > 0) {
      setTimeout(scheduleOwnershipPrune, 0);
      return;
    }
    ownershipStates.forEach(function (state, revision) {
      if (state.provisional || !ownershipGraphs.has(revision)) return;
      var active = false;
      state.renderLinks.forEach(function (link) {
        if (link.link.active) active = true;
      });
      state.graphCalls.forEach(function (call) {
        if (call.status !== "settled" && call.status !== "cancelled") active = true;
      });
      fillSourceDescriptors.forEach(function (descriptor) {
        if (descriptor.active && descriptor.state === state) active = true;
      });
      liveComponentBoundaries.forEach(function (boundary) {
        if (!boundary.destroyed && boundary.revision === revision) active = true;
      });
      var eventsTransaction = graphEvents.get(revision);
      if (eventsTransaction && eventsTransaction.state === "pending") active = true;
      if (active) return;
      ownershipGraphs.delete(revision);
      ownershipStates.delete(revision);
      graphEvents.delete(revision);
      consumedGraphDependencies.delete(revision);
    });
  };

  scheduleOwnershipPrune = function () {
    if (ownershipPruneScheduled) return;
    ownershipPruneScheduled = true;
    queueMicrotask(pruneInactiveOwnershipRevisions);
  };

  var abortOwnershipAdoption = function (transaction, error) {
    if (!transaction || transaction.status !== "prepared") return;
    var state = transaction.state;
    var failure = error instanceof Error ? error : new Error("[Citry] graph: ownership adoption was aborted.");
    deactivateOwnershipAdoption(state);
    state.renderLinks.forEach(function (link) {
      if (link.logicalState.lifecycle) destroyLifecycle(link.logicalState.lifecycle, "an incoming transaction was aborted");
      deactivateRenderLink(state, link);
    });
    state.adoption.transfers.forEach(function (physicals) {
      physicals.forEach(function (physical) {
        if (physical.start.isConnected) physical.start.remove();
        if (physical.end.isConnected) physical.end.remove();
      });
    });
    var canonicalPrefix = OWNERSHIP_COMMENT_PREFIX + ":" + transaction.revision + ":";
    var runtimePrefix = "citry:p1:" + transaction.revision + ":";
    var comments = document.createTreeWalker(document, NodeFilter.SHOW_COMMENT);
    var ownedComments = [];
    for (var node = comments.nextNode(); node; node = comments.nextNode()) {
      var marker = node.data.trim();
      if (marker.indexOf(canonicalPrefix) === 0 || marker.indexOf(runtimePrefix) === 0) ownedComments.push(node);
    }
    ownedComments.forEach(function (node) { node.remove(); });
    ownershipGraphs.delete(transaction.revision);
    ownershipStates.delete(transaction.revision);
    ownershipAdoptionDepth = Math.max(0, ownershipAdoptionDepth - 1);
    transaction.status = "aborted";
    state.adoption.status = "aborted";
    failOwnershipManifest(transaction.revision, failure);
  };

  var forceAdoptionRootMarkers = function (state) {
    state.adoption.markerTransfers.forEach(function (transfer) {
      var physicals = physicalRangesForKey(state, transfer.targetKey);
      transfer.roots.forEach(function (root) {
        if (
          !(root instanceof Element) || !root.isConnected ||
          !root.hasAttribute("data-cid-" + transfer.fromRenderId) ||
          !physicals.some(function (physical) { return physicalRangeContainsNode(physical, root); })
        ) return;
        root.removeAttribute("data-cid-" + transfer.fromRenderId);
        root.setAttribute("data-cid-" + transfer.toRenderId, "");
        var ids = (root.getAttribute("data-cid") || "").trim().split(/\s+/).filter(Boolean);
        ids = ids.map(function (id) {
          return id === transfer.fromRenderId ? transfer.toRenderId : id;
        });
        if (ids.indexOf(transfer.toRenderId) === -1) ids.push(transfer.toRenderId);
        root.setAttribute("data-cid", Array.from(new Set(ids)).join(" "));
      });
    });
  };

  var commitOwnershipAdoption = function (transaction) {
    if (!transaction || transaction.status !== "prepared") {
      throw new TypeError("[Citry] graph: ownership adoption transaction is not prepared.");
    }
    var state = transaction.state;
    applyAdoptionTransfers(state);
    retireSupersededComponentBoundaries(state);
    state.renderLinks.forEach(function (link) {
      var parent = link.record.parentRenderId == null ? null : state.renderLinks.get(link.record.parentRenderId);
      link.logicalState.parentLogical = parent && parent.link.active ? parent.logicalState : null;
    });
    adoptLivePhysicalPlacements(state);
    forceAdoptionRootMarkers(state);
    if (!state.adoption.activated) activateOwnershipAdoption(transaction);
    ownershipGraphs.set(transaction.revision, state.publicRevision);
    seenOwnershipRevisions.add(transaction.revision);
    state.anchors.forEach(function (anchor, anchorId) {
      browserAnchors.set(anchorId, anchor);
    });
    state.provisional = false;
    state.adoption.status = "committed";
    refreshGraphFillSources(state);
    var waiters = graphWaiters.get(transaction.revision) || [];
    graphWaiters.delete(transaction.revision);
    waiters.forEach(function (waiter) { waiter.resolve(state.publicRevision); });
    transaction.status = "committed";
    ownershipAdoptionDepth = Math.max(0, ownershipAdoptionDepth - 1);
    scheduleLifecycleReconcile();
    scheduleFillSourceReconcile();
    queueMicrotask(activateRootlessBoundaries);
    return state.publicRevision;
  };

  var failOwnershipManifest = function (revision, error) {
    if (typeof revision !== "string" || !/^[0-9a-f]{64}$/.test(revision) || ownershipGraphs.has(revision)) {
      return;
    }
    graphFailures.set(revision, error);
    var waiters = graphWaiters.get(revision) || [];
    graphWaiters.delete(revision);
    waiters.forEach(function (waiter) { waiter.reject(error); });
    var blocked = graphBlockedManifests.get(revision) || [];
    graphBlockedManifests.delete(revision);
    if (blocked.length) {
      console.error(
        "[Citry] discarded " + blocked.length + " dependency manifest(s) blocked on failed ownership graph " + revision + "."
      );
    }
  };

  var commitOwnershipManifest = function (manifest) {
    if (graphFailures.has(manifest.revision)) {
      throw new TypeError("[Citry] graph: revision " + manifest.revision + " belongs to a failed transaction.");
    }
    if (seenOwnershipRevisions.has(manifest.revision)) {
      throw new TypeError("[Citry] graph: revision " + manifest.revision + " was inserted more than once.");
    }
    var staged = stageOwnershipManifest(manifest);
    var normalized = normalizeOwnershipRevision(staged);
    var fillPlans = preflightGraphFillSources(normalized);
    normalized.renderIds.forEach(function (_instance, renderId) {
      ownershipStates.forEach(function (liveState) {
        var live = liveState.renderLinks.get(renderId);
        if (live && live.link.active) {
          throw new TypeError("[Citry] graph: live render id '" + renderId + "' appears in more than one revision.");
        }
      });
    });
    // Publication is the first global mutation. Every wire record, cap, and
    // secondary index above has already succeeded, so consumers cannot see a
    // partially normalized revision.
    ownershipStates.set(staged.revision, normalized);
    ownershipGraphs.set(staged.revision, normalized.publicRevision);
    seenOwnershipRevisions.add(staged.revision);
    normalized.anchors.forEach(function (anchor, anchorId) {
      browserAnchors.set(anchorId, anchor);
    });
    activateGraphFillSources(normalized, fillPlans);
    activateGraphClientBindings(staged.revision);
    var waiters = graphWaiters.get(staged.revision) || [];
    graphWaiters.delete(staged.revision);
    waiters.forEach(function (waiter) { waiter.resolve(normalized.publicRevision); });
    var blocked = graphBlockedManifests.get(staged.revision) || [];
    graphBlockedManifests.delete(staged.revision);
    blocked.forEach(function (dependencyManifest) {
      try {
        loadComponentScripts(dependencyManifest);
      } catch (err) {
        console.error("[Citry] failed to process graph-blocked dependency manifest:", err);
      }
    });
    return normalized.publicRevision;
  };

  // ----- loaded-URL bookkeeping -----

  var markScriptLoaded = function (type, url) {
    loaded[type].add(url);
  };

  var isScriptLoaded = function (type, url) {
    return loaded[type].has(url);
  };

  // ----- element creation from {tag, attrs, content} descriptors -----

  var createElement = function (descriptor) {
    var el = document.createElement(descriptor.tag);
    Object.keys(descriptor.attrs || {}).forEach(function (name) {
      var value = descriptor.attrs[name];
      if (value === true) el.setAttribute(name, "");
      else if (value !== false && value != null) el.setAttribute(name, String(value));
    });
    if (descriptor.content) el.textContent = descriptor.content;
    return el;
  };

  // Append a <script> descriptor to <body>; resolves once it has loaded.
  var loadJs = function (descriptor) {
    var url = descriptor.attrs && descriptor.attrs.src;
    if (url && loadingJs.has(url)) return loadingJs.get(url);
    if (url && isScriptLoaded("js", url)) return Promise.resolve();
    var el = createElement(descriptor);
    if (!url) {
      document.body.appendChild(el); // inline scripts run synchronously
      return Promise.resolve();
    }
    var resolveLoad = null;
    var rejectLoad = null;
    var load = new Promise(function (resolve, reject) {
      resolveLoad = resolve;
      rejectLoad = reject;
    });
    loadingJs.set(url, load);
    markScriptLoaded("js", url);
    el.onload = function () {
      loadingJs.delete(url);
      resolveLoad();
    };
    el.onerror = function (event) {
      loadingJs.delete(url);
      loaded.js.delete(url);
      rejectLoad(event);
    };
    document.body.appendChild(el);
    return load;
  };

  // Append a <link rel="stylesheet"> (or inline <style>) descriptor to <head>.
  var loadCss = function (descriptor) {
    var url = descriptor.attrs && descriptor.attrs.href;
    if (url && loadingCss.has(url)) return loadingCss.get(url).promise;
    if (url && isScriptLoaded("css", url)) return Promise.resolve();
    var el = createElement(descriptor);
    if (!url) {
      document.head.appendChild(el);
      return Promise.resolve();
    }
    var resolveLoad = null;
    var rejectLoad = null;
    var load = new Promise(function (resolve, reject) {
      resolveLoad = resolve;
      rejectLoad = reject;
    });
    var entry = { element: el, promise: load, resolve: resolveLoad };
    loadingCss.set(url, entry);
    markScriptLoaded("css", url);
    el.onload = function () {
      if (loadingCss.get(url) !== entry) return;
      loadingCss.delete(url);
      resolveLoad();
    };
    el.onerror = function (event) {
      if (loadingCss.get(url) !== entry) return;
      loadingCss.delete(url);
      loaded.css.delete(url);
      rejectLoad(event);
    };
    document.head.appendChild(el);
    return load;
  };

  // ----- component registrations and data -----

  var registerComponent = function (classId, definition) {
    if (componentRegistrations.has(classId)) {
      throw new Error(
        "[Citry] component '" +
          classId +
          "' is already defined; only one $component registration is allowed per class."
      );
    }
    // The registration preserves whether the config actually declared
    // `props`, including falsy invalid declarations. The
    // `$component` config form (design events.md 5.5) carries both as
    // `{init, props}`; flushCalls resolves the declaration right before
    // init runs.
    var entry;
    if (typeof definition === "function") {
      entry = { fn: definition, props: null, hasProps: false };
    } else if (definition !== null && typeof definition === "object" && typeof definition.init === "function") {
      var hasProps = Object.prototype.hasOwnProperty.call(definition, "props");
      entry = { fn: definition.init, props: hasProps ? definition.props : null, hasProps: hasProps };
    } else {
      throw new TypeError(
        "[Citry] component '" +
          classId +
          "' definition must be a callback function or a config object with an init function."
      );
    }
    componentRegistrations.set(classId, entry);
    componentLifecycles.forEach(function (lifecycle) {
      if (lifecycle.active && lifecycle.classId === classId) ensureLifecycleProps(lifecycle, entry);
    });
    flushCalls();
  };

  // Other extensions enrich the callback payload through `fn(ctx)`.
  // This is called with each instance's payload object just before its callback
  // and adds members by mutating it (its return value is ignored). Returns a
  // function that unregisters the decorator.
  var decorateContext = function (fn) {
    decorators.push(fn);
    return function () {
      var idx = decorators.indexOf(fn);
      if (idx !== -1) decorators.splice(idx, 1);
    };
  };

  var registerComponentData = function (classId, varsHash, data) {
    componentData.set(classId + ":" + varsHash, data);
    flushCalls();
  };

  var retainCallData = function (call) {
    if (call.varsHash == null || call.dataKey != null) return;
    var key = call.classId + ":" + call.varsHash;
    call.dataKey = key;
    componentDataReferences.set(key, (componentDataReferences.get(key) || 0) + 1);
  };

  var releaseComponentDataKey = function (key) {
    if (key == null) return;
    var references = componentDataReferences.get(key);
    if (references == null) return;
    if (references > 1) {
      componentDataReferences.set(key, references - 1);
      return;
    }
    componentDataReferences.delete(key);
    // The data payload has the same page lifetime as its content-addressed
    // variables-script URL in loaded.js. Keep it cached so a later fragment
    // reusing this hash can skip the script request and still settle its call.
  };

  var releaseCallData = function (call) {
    if (call.dataKey == null) return;
    releaseComponentDataKey(call.dataKey);
    call.dataKey = null;
  };

  var transferCallDataToInstance = function (call, lifecycle) {
    var previous = lifecycle ? lifecycle.dataKey : instanceDataKeys.get(call.componentId);
    releaseComponentDataKey(previous);
    if (lifecycle) lifecycle.dataKey = call.dataKey;
    else if (call.dataKey == null) instanceDataKeys.delete(call.componentId);
    else instanceDataKeys.set(call.componentId, call.dataKey);
    // The live instance now owns the reference that the call held.
    call.dataKey = null;
  };

  var callComponent = function (classId, componentId, varsHash, revision) {
    var route = revision == null ? null : resolveOwnershipRoute(revision, componentId, classId);
    var lifecycle = revision == null ? lifecycleForRender(componentId) : null;
    var call = {
      classId: classId,
      componentId: componentId,
      varsHash: varsHash,
      dataKey: null,
      revision: revision || null,
      route: route,
      status: "waiting",
      dependenciesReady: true,
      parentCall: null,
      heldRoots: new Set(),
      lifecycle: lifecycle,
    };
    if (lifecycle) lifecycle.calls.add(call);
    retainCallData(call);
    pendingCalls.push(call);
    flushCalls();
  };

  var isCallReady = function (call) {
    if (call.status === "settled" || call.status === "cancelled" || call.status === "running") return false;
    if (call.revision && (!alpineReady || !call.dependenciesReady)) return false;
    if (call.revision) {
      try {
        call.route = resolveOwnershipRoute(call.revision, call.componentId, call.classId);
      } catch (_err) {
        call.status = "cancelled";
        releaseCallHolds(call);
        releaseCallData(call);
        return false;
      }
    }
    if (call.parentCall && call.parentCall.status !== "settled" && call.parentCall.status !== "cancelled") return false;
    if (!componentRegistrations.has(call.classId)) return false;
    if (call.dataKey != null && !componentData.has(call.dataKey)) return false;
    if (call.lifecycle) {
      var props = ensureLifecycleProps(call.lifecycle, componentRegistrations.get(call.classId));
      if (props && !props.initialSettled) return false;
      if (callWaitsForAmbientMagic && callWaitsForAmbientMagic(call)) return false;
    }
    return true;
  };

  // ----- rendered ambient context -----

  var AMBIENT_BLOCKED = Symbol("citry-ambient-blocked");

  var validateAmbientKey = function (key) {
    if ((typeof key !== "string" || key.length === 0) && typeof key !== "symbol") {
      throw new TypeError("[Citry] provide/inject keys must be a non-empty string or a symbol.");
    }
    return key;
  };

  var ambientKeyLabel = function (key) {
    return typeof key === "symbol" ? String(key) : "'" + key + "'";
  };

  // Native Alpine teleports keep their authored template as the ambient
  // parent. Citry fill backlinks are lexical-scope carriers and are ignored
  // here, because ambient lookup follows the slot's rendered position.
  var ambientElementPath = function (el) {
    var path = [];
    var seen = new Set();
    var current = el;
    while (current instanceof Element && !seen.has(current)) {
      seen.add(current);
      path.push(current);
      if (!current.isConnected && ambientCloneSources.has(current)) {
        current = ambientCloneSources.get(current);
      } else if (
        current._x_teleportBack instanceof Element &&
        current._x_teleportBack._x_teleport === current
      ) {
        current = current._x_teleportBack;
      } else if (current.parentElement) {
        current = current.parentElement;
      } else if (current.parentNode instanceof ShadowRoot) {
        current = current.parentNode.host;
      } else {
        current = null;
      }
    }
    return path;
  };

  var ambientRangeContainsElement = function (physical, el) {
    return ambientElementPath(el).some(function (candidate) {
      return physicalRangeContainsNode(physical, candidate);
    });
  };

  var ambientElementContainsRange = function (el, physical) {
    var points = physicalRangeElements(physical);
    if (!points.length && physical.start.parentElement) points = [physical.start.parentElement];
    return points.length > 0 && points.every(function (point) {
      return ambientElementPath(point).indexOf(el) !== -1;
    });
  };

  var ambientRangeContainsRange = function (outer, inner) {
    return outer === inner || (
      physicalRangeContainsNode(outer, inner.start) &&
      physicalRangeContainsNode(outer, inner.end)
    );
  };

  var ambientContainerContains = function (outer, inner) {
    if (outer.kind === "range" && inner.kind === "range") {
      return ambientRangeContainsRange(outer.physical, inner.physical);
    }
    if (outer.kind === "range" && inner.kind === "element") {
      return ambientRangeContainsElement(outer.physical, inner.element);
    }
    if (outer.kind === "element" && inner.kind === "range") {
      return ambientElementContainsRange(outer.element, inner.physical);
    }
    return ambientElementPath(inner.element).indexOf(outer.element) !== -1;
  };

  var ambientElementHasRoute = function (el) {
    var found = false;
    ownershipStates.forEach(function (state) {
      if (found) return;
      state.renderLinks.forEach(function (link) {
        if (found || !link.link.active) return;
        physicalRangesForKey(state, link.record.key).forEach(function (physical) {
          if (
            !found &&
            physicalRangeIsLive(state, physical) &&
            ambientRangeContainsElement(physical, el)
          ) found = true;
        });
      });
    });
    return found;
  };

  var ambientElementDeclaresWrite = function (el) {
    return Array.from(el.attributes || []).some(function (attribute) {
      var name = attribute.name.toLowerCase();
      if (name !== "x-init" && name !== "x-effect" && name !== "x-data" && name !== "x-bind") return false;
      return /\$(?:provide|unprovide)\b/.test(attribute.value);
    });
  };

  var ambientElementHasPendingWrite = function (el) {
    var evaluated = ambientDirectiveEvaluatedAttributesByElement.get(el) || new Map();
    return Array.from(el.attributes || []).some(function (attribute) {
      var name = attribute.name.toLowerCase();
      if (name !== "x-init" && name !== "x-effect" && name !== "x-data" && name !== "x-bind") return false;
      return /\$(?:provide|unprovide)\b/.test(attribute.value) && !(evaluated.get(attribute.name) > 0);
    });
  };

  callWaitsForAmbientMagic = function (call) {
    var lifecycle = call.lifecycle;
    if (!lifecycle || !lifecycle.active) return false;
    var range = lifecyclePhysicalRange(lifecycle);
    if (!range.state) return false;
    var targetRanges = range.physicals.filter(function (physical) {
      return physicalRangeIsLive(range.state, physical);
    });
    if (!targetRanges.length) return false;
    return Array.prototype.some.call(document.querySelectorAll("[x-init],[x-effect],[x-data]"), function (element) {
      if (!ambientElementDeclaresWrite(element) || !ambientElementHasPendingWrite(element)) return false;
      return targetRanges.some(function (physical) {
        return !ambientRangeContainsElement(physical, element) && ambientElementContainsRange(element, physical);
      });
    });
  };

  var assertAmbientElementRoute = function (el) {
    if (!(el instanceof Element) || !ambientElementHasRoute(el)) {
      throw new Error(
        "[Citry] client context needs an element inside a live Citry render. " +
          "Move this expression into a Citry component template."
      );
    }
  };

  var ambientMagicValue = function (frame, key) {
    for (var index = frame.writes.length - 1; index >= 0; index -= 1) {
      if (frame.writes[index].key === key) return { present: true, value: frame.writes[index].value };
    }
    return { present: false, value: undefined };
  };

  var ambientComponentValue = function (frame, key) {
    if (!frame.writes.has(key)) return { present: false, value: undefined };
    return { present: true, value: frame.writes.get(key) };
  };

  var ambientCandidates = function (target, excludedFrame) {
    var candidates = [];
    componentLifecycles.forEach(function (lifecycle) {
      var invocation = lifecycle.invocation;
      var frame = invocation && invocation.ambientFrame;
      if (!frame || !frame.active || frame === excludedFrame || !frame.writes.size) return;
      var range = lifecyclePhysicalRange(lifecycle);
      if (!range.state) return;
      range.physicals.forEach(function (physical) {
        if (!physicalRangeIsLive(range.state, physical)) return;
        var container = { kind: "range", physical: physical };
        if (ambientContainerContains(container, target)) {
          candidates.push({ frame: frame, container: container, read: ambientComponentValue });
        }
      });
    });
    ambientMagicFrames.forEach(function (frame) {
      if (!frame.active || frame === excludedFrame || !frame.writes.length || !frame.element.isConnected) return;
      if (target.kind === "range" && ambientRangeContainsElement(target.physical, frame.element)) return;
      var container = { kind: "element", element: frame.element };
      if (ambientContainerContains(container, target)) {
        candidates.push({ frame: frame, container: container, read: ambientMagicValue });
      }
    });
    candidates.sort(function (left, right) {
      var leftContainsRight = ambientContainerContains(left.container, right.container);
      var rightContainsLeft = ambientContainerContains(right.container, left.container);
      if (leftContainsRight && !rightContainsLeft) return 1;
      if (rightContainsLeft && !leftContainsRight) return -1;
      if (leftContainsRight && rightContainsLeft && left.container.kind !== right.container.kind) {
        return left.container.kind === "element" ? -1 : 1;
      }
      return 0;
    });
    return candidates;
  };

  var ambientLookup = function (target, key, excludedFrame) {
    if (!ambientContextRevision) ambientContextRevision = alpineOwner.reactive({ value: Object.freeze({}) });
    ambientContextRevision.value;
    var candidates = ambientCandidates(target, excludedFrame);
    for (var index = 0; index < candidates.length; index += 1) {
      var entry = candidates[index].read(candidates[index].frame, key);
      if (!entry.present) continue;
      if (entry.value === AMBIENT_BLOCKED) return { found: false, blocked: true, value: undefined };
      return { found: true, blocked: false, value: entry.value };
    }
    return { found: false, blocked: false, value: undefined };
  };

  var missingAmbientInjection = function (key, owner) {
    throw new Error(
      "[Citry] " + owner + " tried to inject " + ambientKeyLabel(key) +
        ", but no rendered ancestor provided it. Add provide() or $provide() above this call."
    );
  };

  var requireAmbientInvocation = function (frame, operation, writes) {
    if (!frame.active || !frame.invocation.active) {
      throw new Error("[Citry] " + operation + "() used a component context whose invocation has been disposed.");
    }
    if (writes && !frame.open) {
      throw new Error(
        "[Citry] " + operation + "() can only be called during synchronous $component initialization. " +
          "Provide one stable reactive value when later updates are needed."
      );
    }
  };

  var ambientComponentWrite = function (frame, key, value, operation) {
    requireAmbientInvocation(frame, operation, true);
    validateAmbientKey(key);
    frame.writes.set(key, value);
    touchAmbientContext();
  };

  var ambientComponentInject = function (frame, key, hasDefault, defaultValue) {
    requireAmbientInvocation(frame, "inject", false);
    validateAmbientKey(key);
    var range = lifecyclePhysicalRange(frame.lifecycle);
    var physicals = range.state
      ? range.physicals.filter(function (physical) { return physicalRangeIsLive(range.state, physical); })
      : [];
    if (!physicals.length) {
      throw new Error("[Citry] inject() cannot resolve because this component has no live rendered placement.");
    }
    var outcomes = physicals.map(function (physical) {
      return ambientLookup({ kind: "range", physical: physical }, key, frame);
    });
    var first = outcomes[0];
    var agrees = outcomes.every(function (outcome) {
      return outcome.found === first.found && (!first.found || Object.is(outcome.value, first.value));
    });
    if (!agrees) {
      throw new Error(
        "[Citry] inject(" + ambientKeyLabel(key) + ") is ambiguous because this shared component's " +
          "rendered placements have different ancestor values. Inject at the placement with $inject(), " +
          "or make every placement inherit the same value."
      );
    }
    if (first.found) return first.value;
    if (hasDefault) return defaultValue;
    return missingAmbientInjection(key, "component '" + frame.lifecycle.classId + "'");
  };

  var ambientMagicFrame = function (el) {
    var frame = ambientMagicFramesByElement.get(el);
    if (frame && frame.active) return frame;
    frame = { active: true, element: el, writes: [] };
    ambientMagicFramesByElement.set(el, frame);
    ambientMagicFrames.add(frame);
    return frame;
  };

  var retireAmbientMagicFrameIfEmpty = function (frame) {
    if (frame.writes.length) return;
    frame.active = false;
    ambientMagicFrames.delete(frame);
    if (ambientMagicFramesByElement.get(frame.element) === frame) {
      ambientMagicFramesByElement.delete(frame.element);
    }
  };

  touchAmbientContext = function () {
    if (!ambientContextRevision) ambientContextRevision = alpineOwner.reactive({ value: Object.freeze({}) });
    ambientContextRevision.value = Object.freeze({});
  };

  createAmbientDirectiveControl = function (el, attributeName) {
    var token = {
      active: true,
      open: true,
      evaluated: false,
      element: el,
      attributeName: attributeName,
      frame: null,
    };
    var close = function () {
      token.open = false;
    };
    var control = {
      run: function (callback) {
        if (!token.active) return callback();
        var previous = activeAmbientDirective;
        activeAmbientDirective = token;
        try {
          return callback();
        } finally {
          var evaluated = ambientDirectiveEvaluatedAttributesByElement.get(el);
          if (!evaluated) {
            evaluated = new Map();
            ambientDirectiveEvaluatedAttributesByElement.set(el, evaluated);
          }
          if (!token.evaluated) {
            token.evaluated = true;
            evaluated.set(attributeName, (evaluated.get(attributeName) || 0) + 1);
          }
          activeAmbientDirective = previous;
        }
      },
      close: close,
      dispose: function () {
        if (!token.active) return;
        token.active = false;
        close();
        var evaluated = ambientDirectiveEvaluatedAttributesByElement.get(el);
        if (evaluated && token.evaluated) {
          var remaining = (evaluated.get(attributeName) || 1) - 1;
          if (remaining > 0) evaluated.set(attributeName, remaining);
          else evaluated.delete(attributeName);
          if (!evaluated.size) ambientDirectiveEvaluatedAttributesByElement.delete(el);
        }
        if (!token.frame) return;
        var frame = token.frame;
        token.frame = null;
        var priorLength = frame.writes.length;
        frame.writes = frame.writes.filter(function (write) { return write.token !== token; });
        if (frame.writes.length !== priorLength) touchAmbientContext();
        retireAmbientMagicFrameIfEmpty(frame);
      },
    };
    token.control = control;
    return Object.freeze(control);
  };

  runAmbientDirective = function (el, attributeName, registerCleanup, callback) {
    var control = ambientDirectiveControlsByCleanup.get(registerCleanup);
    if (!control) {
      var dispose = function () {
        control.dispose();
        if (ambientDirectiveControlsByCleanup.get(registerCleanup) === control) {
          ambientDirectiveControlsByCleanup.delete(registerCleanup);
        }
      };
      control = createAmbientDirectiveControl(el, attributeName);
      ambientDirectiveControlsByCleanup.set(registerCleanup, control);
      registerCleanup(dispose);
      queueMicrotask(function () {
        control.close();
        flushCalls();
      });
    }
    return control.run(callback);
  };

  var ambientMagicWrite = function (el, key, value, operation) {
    validateAmbientKey(key);
    var token = activeAmbientDirective;
    var ownerElement = token && token.active ? token.element : el;
    if (!token || !token.active || !token.open) {
      throw new Error(
        "[Citry] $" + operation + "() can only be called during a synchronous Alpine directive's " +
          "initial evaluation. Use x-init, or provide one stable reactive value for later updates."
      );
    }
    if (!ownerElement.isConnected) {
      throw new Error(
        "[Citry] $" + operation + "() cannot write while Alpine initializes a detached morph clone. " +
          "Declare the provider in x-init on the live component template."
      );
    }
    assertAmbientElementRoute(ownerElement);
    var frame = ambientMagicFrame(ownerElement);
    token.frame = frame;
    ambientWriteCounter += 1;
    frame.writes.push({ key: key, value: value, token: token, order: ambientWriteCounter });
    touchAmbientContext();
  };

  var ambientMagicInject = function (el, key, hasDefault, defaultValue) {
    validateAmbientKey(key);
    var ownerElement = el;
    assertAmbientElementRoute(ownerElement);
    var ownFrame = ambientMagicFramesByElement.get(ownerElement) || null;
    var outcome = ambientLookup({ kind: "element", element: ownerElement }, key, ownFrame);
    if (outcome.found) return outcome.value;
    if (hasDefault) return defaultValue;
    return missingAmbientInjection(key, "an Alpine expression");
  };

  installAmbientContext = function (_alpine, registerMagic) {
    registerMagic("provide", function (el) {
      return function (key, value) { ambientMagicWrite(el, key, value, "provide"); };
    });
    registerMagic("inject", function (el) {
      return function (key, defaultValue) {
        return ambientMagicInject(el, key, arguments.length > 1, defaultValue);
      };
    });
    registerMagic("unprovide", function (el) {
      return function (key) { ambientMagicWrite(el, key, AMBIENT_BLOCKED, "unprovide"); };
    });
  };

  var makeInvocation = function (lifecycle) {
    var invocation = {
      active: true,
      effectStops: [],
      resources: [],
      userCleanup: null,
      ambientFrame: null,
    };
    invocation.ambientFrame = {
      active: true,
      open: true,
      lifecycle: lifecycle,
      invocation: invocation,
      writes: new Map(),
    };
    lifecycle.invocation = invocation;
    return invocation;
  };

  var invocationControl = function (invocation) {
    return Object.freeze({
      registerCleanup: function (cleanup) {
        if (typeof cleanup !== "function") {
          throw new TypeError("[Citry] a context decorator tried to register a non-function cleanup.");
        }
        var active = true;
        var once = function () {
          if (!active) return;
          active = false;
          cleanup();
        };
        if (!invocation.active) once();
        else invocation.resources.push(once);
        return once;
      },
    });
  };

  var addLifecycleContext = function (ctx, lifecycle, invocation) {
    var ambientFrame = invocation.ambientFrame;
    ctx.scope = lifecycle.scope;
    ctx.els = lifecycle.els;
    ctx.provide = function (key, value) {
      ambientComponentWrite(ambientFrame, key, value, "provide");
    };
    ctx.inject = function (key, defaultValue) {
      return ambientComponentInject(ambientFrame, key, arguments.length > 1, defaultValue);
    };
    ctx.unprovide = function (key) {
      ambientComponentWrite(ambientFrame, key, AMBIENT_BLOCKED, "unprovide");
    };
    ctx.reactive = function (value) {
      if (!invocation.active) {
        throw new Error("[Citry] reactive() cannot be called after this component invocation was disposed.");
      }
      if (value === null || typeof value !== "object") {
        throw new TypeError("[Citry] reactive(value) needs an object or array.");
      }
      return alpineOwner.reactive(value);
    };
    ctx.effect = function (callback) {
      if (!invocation.active) {
        throw new Error("[Citry] effect() cannot be called after this component invocation was disposed.");
      }
      if (typeof callback !== "function") throw new TypeError("[Citry] effect(callback) needs a callback.");
      var active = true;
      var reference = alpineOwner.effect(function () {
        if (!active || !invocation.active) return;
        try { callback(); } catch (err) {
          console.error("[Citry] managed component effect failed:", err);
        }
      });
      var stop = function () {
        if (!active) return;
        active = false;
        alpineOwner.release(reference);
      };
      invocation.effectStops.push(stop);
      return stop;
    };
  };

  var storeCleanup = function (call, cleanup) {
    var key = call.classId + ":" + call.componentId;
    var fns = cleanups.get(key);
    if (!fns) cleanups.set(key, (fns = []));
    fns.push(cleanup);
  };

  // Run (and discard) the cleanups stored for one instance. A later
  // graph-independent call for the same id re-runs its callback, so whatever
  // it set up last time is torn down first.
  var runCleanups = function (call) {
    var fns = cleanups.get(call.classId + ":" + call.componentId);
    if (!fns) return;
    cleanups.delete(call.classId + ":" + call.componentId);
    fns.forEach(function (cleanup) {
      try {
        cleanup();
      } catch (err) {
        console.error("[Citry] component cleanup for '" + call.classId + "' failed:", err);
      }
    });
  };

  // ----- instance lifecycle: teardown on removal and Component.css cleanup -----

  // How many tracked instances of a class are still live. Counted straight
  // from liveInstances every time, so the number can never drift from the set
  // of instances actually tracked.
  var classLiveCount = function (classId) {
    var n = 0;
    liveInstances.forEach(function (cls) {
      if (cls === classId) n += 1;
    });
    return n;
  };

  // Remove a class-level Component.css sheet, the one the server tags with
  // data-citry-css-class. A sheet whose class has no live instance left has
  // nothing to style, so it is dropped.
  var removeClassCss = function (classId) {
    document.querySelectorAll('[data-citry-css-class="' + classId + '"]').forEach(function (el) {
      var url = el.getAttribute("href");
      if (url) {
        loaded.css.delete(url);
        var loading = loadingCss.get(url);
        if (loading && loading.element === el) {
          loadingCss.delete(url);
          loading.resolve();
        }
      }
      el.remove();
    });
  };

  // Collect a class's Component.css, but on a later task, not now. A component
  // that re-renders in place retires its old instance id before it registers
  // the fresh one, so at the moment of retirement a class's only instance can
  // momentarily look like its last even though a same-class render is about
  // to land. Dropping the sheet right then would remove it on every such
  // re-render, and a sheet served from a URL is recorded as loaded (so it is
  // not fetched again), which would lose the class's styling for good. So the
  // check is deferred and the live count re-read then: a fresh same-class
  // instance that arrived in the meantime cancels the collection, while a
  // class that is genuinely gone still has its sheet removed. One re-check is
  // queued per class so a burst of retirements does not pile up timers.
  var scheduleCssGc = function (classId) {
    if (cssGcPending.has(classId)) return;
    cssGcPending.add(classId);
    setTimeout(function () {
      cssGcPending.delete(classId);
      if (classLiveCount(classId) === 0) removeClassCss(classId);
    }, 0);
  };

  // Run the teardown for every tracked instance whose last element has left
  // the DOM (a real node removal, or the same node's data-cid-<id> swapped
  // for a new one in place), then forget it. When that empties a class, the
  // class's Component.css is queued for the deferred collection above.
  var sweepRemovedInstances = function () {
    sweepScheduled = false;
    reconcileComponentLifecycles();
    liveInstances.forEach(function (classId, componentId) {
      var lifecycle = lifecycleForRender(componentId);
      if (lifecycle && lifecycleCapsAreLive(lifecycle)) return;
      if (document.querySelector("[data-cid-" + componentId + "]")) return;
      liveInstances.delete(componentId);
      var dataKey = instanceDataKeys.get(componentId);
      instanceDataKeys.delete(componentId);
      releaseComponentDataKey(dataKey);
      // A CSS-only instance has no stored cleanups, so runCleanups is a no-op
      // for it; a JS instance's cleanups run here exactly once.
      runCleanups({ classId: classId, componentId: componentId });
      if (classLiveCount(classId) === 0) scheduleCssGc(classId);
    });
  };

  // Queue a removal sweep for the next microtask. Debounced so a morph's
  // remove-then-add churn within one mutation batch is seen whole: an id
  // removed and re-added in the same batch is present again when the sweep
  // runs, so it is not misread as a removal.
  var scheduleSweep = function () {
    if (sweepScheduled) return;
    sweepScheduled = true;
    Promise.resolve().then(sweepRemovedInstances);
  };

  // Record an instance the manifest declared present for CSS only (a
  // Component.css instance with no $component JS), so its class counts as
  // live even though nothing calls it. See the cssInstances note in
  // loadComponentScripts for the manifest shape WP10 emits.
  var trackCssInstance = function (classId, componentId) {
    liveInstances.set(componentId, classId);
  };

  // Run every pending call whose callback and data have both arrived. Calls
  // stay queued (in order) until they are ready, so the manifest, the
  // component's JS, and the data script may arrive in any order.
  var flushCalls = function () {
    if (flushingCalls) {
      flushAgain = true;
      return;
    }
    flushingCalls = true;
    try {
      do {
        flushAgain = false;
        var batch = pendingCalls;
        pendingCalls = [];
        var progressed = false;
        batch.forEach(function (call) {
          if (call.status === "cancelled" || call.status === "settled") return;
          if (!isCallReady(call)) {
            if (call.status !== "cancelled") pendingCalls.push(call);
            return;
          }
          progressed = true;
          call.status = "running";
          var lifecycle = call.lifecycle;
          var invocation = null;
          var control = null;
          if (lifecycle) {
            disposeInvocation(lifecycle);
            reconcileComponentLifecycles();
            invocation = makeInvocation(lifecycle);
            control = invocationControl(invocation);
          } else {
            runCleanups(call);
          }

          var data = call.dataKey == null ? null : componentData.get(call.dataKey);
          var els = lifecycle ? lifecycle.els : rootsForRender(call.componentId);
          var ctx = { id: call.componentId, els: els, data: data };
          if (call.route) ctx.graph = call.route;
          if (lifecycle) addLifecycleContext(ctx, lifecycle, invocation);
          decorators.slice().forEach(function (decorate) {
            try {
              decorate(ctx, control);
            } catch (err) {
              console.error("[Citry] context decorator failed (calling '" + call.classId + "'):", err);
            }
          });
          var entry = componentRegistrations.get(call.classId);
          var runCallback = true;
          var lifecycleProps = lifecycle ? ensureLifecycleProps(lifecycle, entry) : null;
          if (lifecycleProps) {
            ctx.props = lifecycleProps.view;
            if (!lifecycleProps.currentValid) runCallback = false;
          } else if (entry.hasProps) {
            var events = globalThis.Citry.events;
            if (!events || typeof events._resolveProps !== "function") {
              console.error(
                "[Citry] component callback for '" + call.classId +
                  "' declares props, which need the events extension's client runtime;" +
                  " the runtime is not loaded, so the callback was skipped."
              );
              runCallback = false;
            } else {
              try {
                ctx.props = events._resolveProps(call.classId, entry.props);
              } catch (err) {
                console.error(
                  "[Citry] component callback for '" + call.classId + "' skipped, its props failed validation:",
                  err
                );
                runCallback = false;
              }
            }
          }
          if (runCallback) {
            try {
              var cleanup = entry.fn(ctx);
              if (invocation && invocation.ambientFrame) invocation.ambientFrame.open = false;
              if (typeof cleanup === "function") {
                if (invocation) invocation.userCleanup = cleanup;
                else storeCleanup(call, cleanup);
              } else if (cleanup && typeof cleanup.then === "function") {
                console.error(
                  "[Citry] component callback for '" + call.classId +
                    "' returned a Promise. Async component init is unsupported; the init DAG settled synchronously."
                );
                Promise.resolve(cleanup).catch(function (err) {
                  console.error("[Citry] unsupported async component callback for '" + call.classId + "' rejected:", err);
                });
              }
            } catch (err) {
              if (invocation && invocation.ambientFrame) invocation.ambientFrame.open = false;
              console.error("[Citry] component callback for '" + call.classId + "' failed:", err);
              if (lifecycle) disposeInvocation(lifecycle);
            }
          } else if (lifecycle) {
            if (invocation && invocation.ambientFrame) invocation.ambientFrame.open = false;
            disposeInvocation(lifecycle);
          }
          call.status = "settled";
          releaseCallHolds(call);
          if (lifecycle) lifecycle.calls.delete(call);
          transferCallDataToInstance(call, lifecycle);
          liveInstances.set(call.componentId, call.classId);
        });
        if (progressed && pendingCalls.length) flushAgain = true;
      } while (flushAgain);
    } finally {
      flushingCalls = false;
    }
    scheduleSweep();
  };

  // ----- manifests -----

  // Process one manifest object (already JSON-parsed; string fields base64):
  //   markLoaded: {js: [url...], css: [url...]}   already on the page
  //   fetch:      {js: [tag descriptor JSON...], css: [...]}   load now
  //   calls:      [[classId, componentId, varsHash | null], ...]
  var stageManifestCalls = function (manifest, revision) {
    var calls = (manifest.calls || []).map(function (call) {
      var staged = {
        classId: fromBase64(call[0]),
        componentId: fromBase64(call[1]),
        varsHash: call[2] == null ? null : fromBase64(call[2]),
        dataKey: null,
        revision: revision || null,
        route: null,
        status: revision ? "staged" : "waiting",
        dependenciesReady: !revision,
        parentCall: null,
        heldRoots: new Set(),
        lifecycle: null,
      };
      if (revision) staged.route = resolveOwnershipRoute(revision, staged.componentId, staged.classId);
      return staged;
    });
    if (!revision) {
      calls.forEach(function (call) {
        call.lifecycle = lifecycleForRender(call.componentId);
        if (call.lifecycle) call.lifecycle.calls.add(call);
        retainCallData(call);
      });
      return calls;
    }

    var state = ownershipStates.get(revision);
    var local = new Map();
    calls.forEach(function (call) {
      if (local.has(call.componentId) || state.graphCalls.has(call.componentId)) {
        throw new TypeError(
          "[Citry] graph-linked dependency manifest repeats callback render id '" + call.componentId + "'."
        );
      }
      local.set(call.componentId, call);
    });
    calls.forEach(function (call) {
      call.lifecycle = ensureLifecycle(call.route, true);
      if (!call.lifecycle) {
        throw new TypeError("[Citry] graph-linked callback could not activate its logical instance.");
      }
    });
    calls.forEach(function (call) {
      var parentRenderId = state.executionOrderParentByChild.get(call.componentId);
      var visited = new Set();
      while (parentRenderId != null && !visited.has(parentRenderId)) {
        visited.add(parentRenderId);
        var parentCall = local.get(parentRenderId) || state.graphCalls.get(parentRenderId);
        if (parentCall) {
          call.parentCall = parentCall;
          break;
        }
        var parentLink = state.renderLinks.get(parentRenderId);
        parentRenderId =
          state.executionOrderParentByChild.get(parentRenderId) ||
          (parentLink ? parentLink.record.parentRenderId : null);
      }
      state.graphCalls.set(call.componentId, call);
      call.lifecycle.calls.add(call);
      retainCallData(call);
      pendingCalls.push(call);
    });
    // This synchronous pass is what places per-root Alpine holds before the
    // owned Alpine MutationObserver sees a just-inserted fragment.
    reconcileComponentLifecycles();
    return calls;
  };

  var cancelStagedCalls = function (calls, reason) {
    calls.forEach(function (call) {
      if (call.status === "settled" || call.status === "cancelled") return;
      call.status = "cancelled";
      releaseCallHolds(call);
      releaseCallData(call);
      if (call.lifecycle) call.lifecycle.calls.delete(call);
    });
    flushCalls();
    if (reason) console.error("[Citry] component callback branch was cancelled because an asset failed:", reason);
  };

  var prepareComponentAssets = function (manifest) {
    var markLoaded = manifest.markLoaded || {};
    (markLoaded.js || []).forEach(function (url) {
      markScriptLoaded("js", fromBase64(url));
    });
    (markLoaded.css || []).forEach(function (url) {
      markScriptLoaded("css", fromBase64(url));
    });

    var fetch = manifest.fetch || {};
    var hasAsyncAssets = false;
    var styles = (fetch.css || []).map(function (encoded) {
      var descriptor = JSON.parse(fromBase64(encoded));
      if (descriptor.attrs && descriptor.attrs.href) hasAsyncAssets = true;
      return loadCss(descriptor);
    });
    var scripts = (fetch.js || []).map(function (encoded) {
      var descriptor = JSON.parse(fromBase64(encoded));
      if (descriptor.attrs && descriptor.attrs.src) hasAsyncAssets = true;
      return descriptor;
    });
    return {
      styles: styles,
      scripts: scripts,
      hasAsyncAssets: hasAsyncAssets,
    };
  };

  var applyStagedManifest = function (manifest, calls) {
    calls.forEach(function (call) {
      if (!call.revision) pendingCalls.push(call);
      else {
        call.dependenciesReady = true;
        if (call.status === "staged") call.status = "waiting";
      }
    });
    flushCalls();

    // Instances the manifest declares present for CSS only: a Component.css
    // instance with no $component JS, which nothing else would register, so
    // a class made only of such instances is still counted as live for the
    // Component.css cleanup. Shape (the contract WP10 emits): a `cssInstances`
    // list of [classId, componentId] pairs, base64-armored like `calls`.
    (manifest.cssInstances || []).forEach(function (entry) {
      trackCssInstance(fromBase64(entry[0]), fromBase64(entry[1]));
    });
  };

  var applyComponentScripts = function (manifest) {
    var calls = stageManifestCalls(manifest, null);
    var assets = prepareComponentAssets(manifest);
    // Preserve the graph-independent inline-manifest contract: inline styles
    // and scripts execute, and their callbacks flush, before this private
    // manager call returns. URL assets necessarily use the asynchronous path.
    if (!assets.hasAsyncAssets) {
      assets.scripts.forEach(loadJs);
      applyStagedManifest(manifest, calls);
      return Promise.resolve();
    }
    var chain = Promise.all(assets.styles);
    assets.scripts.forEach(function (descriptor) {
      chain = chain.then(function () { return loadJs(descriptor); });
    });
    return chain.then(
      function () {
        applyStagedManifest(manifest, calls);
      },
      function (err) {
        cancelStagedCalls(calls, err);
        throw err;
      }
    );
  };

  var applyGraphComponentScripts = function (manifest, calls) {
    var assets = prepareComponentAssets(manifest);
    var hasAssets = assets.styles.length || assets.scripts.length;
    var releaseStart = hasAssets ? alpineApi._holdStart() : function () {};
    var chain = Promise.all(assets.styles);
    assets.scripts.forEach(function (descriptor) {
      chain = chain.then(function () { return loadJs(descriptor); });
    });
    return chain.then(
      function () {
        releaseStart();
        return whenGraphEventsReady(manifest.graph);
      },
      function (err) {
        releaseStart();
        cancelStagedCalls(calls, err);
        throw err;
      }
    ).then(function () {
      applyStagedManifest(manifest, calls);
    });
  };

  var preflightAdoptionDependency = function (manifest, revision) {
    if (!manifest || typeof manifest !== "object" || Array.isArray(manifest) || manifest.graph !== revision) {
      throw new TypeError("[Citry] dependency manifest does not match its prepared ownership revision.");
    }
    var requireArray = function (value, label) {
      if (value == null) return [];
      if (!Array.isArray(value)) throw new TypeError("[Citry] dependency manifest field '" + label + "' must be an array.");
      return value;
    };
    var requireObject = function (value, label) {
      if (value == null) return {};
      if (typeof value !== "object" || Array.isArray(value)) {
        throw new TypeError("[Citry] dependency manifest field '" + label + "' must be an object.");
      }
      return value;
    };
    var decode = function (value, label) {
      if (typeof value !== "string") {
        throw new TypeError("[Citry] dependency manifest field '" + label + "' must contain base64 strings.");
      }
      return fromBase64(value);
    };
    var seen = new Set();
    requireArray(manifest.calls, "calls").forEach(function (call) {
      if (!Array.isArray(call) || call.length !== 3) {
        throw new TypeError("[Citry] graph-linked dependency call must be a three-item tuple.");
      }
      var classId = decode(call[0], "calls");
      var renderId = decode(call[1], "calls");
      if (seen.has(renderId)) {
        throw new TypeError("[Citry] graph-linked dependency manifest repeats callback render id '" + renderId + "'.");
      }
      seen.add(renderId);
      resolveOwnershipRoute(revision, renderId, classId);
      if (call[2] != null) decode(call[2], "calls");
    });

    requireArray(manifest.cssInstances, "cssInstances").forEach(function (entry) {
      if (!Array.isArray(entry) || entry.length !== 2) {
        throw new TypeError("[Citry] graph-linked css instance must be a two-item tuple.");
      }
      var classId = decode(entry[0], "cssInstances");
      var renderId = decode(entry[1], "cssInstances");
      resolveOwnershipRoute(revision, renderId, classId);
    });

    var markLoaded = requireObject(manifest.markLoaded, "markLoaded");
    ["css", "js"].forEach(function (kind) {
      requireArray(markLoaded[kind], "markLoaded." + kind).forEach(function (encoded) {
        decode(encoded, "markLoaded." + kind);
      });
    });

    var fetch = requireObject(manifest.fetch, "fetch");
    ["css", "js"].forEach(function (kind) {
      requireArray(fetch[kind], "fetch." + kind).forEach(function (encoded) {
        var descriptor = JSON.parse(decode(encoded, "fetch." + kind));
        if (
          !descriptor || typeof descriptor !== "object" || Array.isArray(descriptor) ||
          typeof descriptor.tag !== "string" ||
          (descriptor.attrs != null && (typeof descriptor.attrs !== "object" || Array.isArray(descriptor.attrs))) ||
          (descriptor.content != null && typeof descriptor.content !== "string")
        ) {
          throw new TypeError("[Citry] dependency asset descriptor is invalid.");
        }
        // Prove tag and attribute names while the element is detached. Script
        // and stylesheet execution still starts only after graph commit.
        createElement(descriptor);
      });
    });
    return manifest;
  };

  var applyAdoptionDependency = function (transaction, manifest, tag) {
    if (!transaction || transaction.status !== "committed" || manifest.graph !== transaction.revision) {
      return Promise.reject(new TypeError("[Citry] dependency adoption requires a committed matching graph."));
    }
    if (consumedGraphDependencies.has(transaction.revision)) {
      return Promise.reject(new TypeError("[Citry] dependency manifest repeats ownership graph " + transaction.revision + "."));
    }
    if (tag) {
      processedDependencyTags.add(tag);
      tag.dataset.citryProcessed = "";
    }
    consumedGraphDependencies.add(transaction.revision);
    var calls = stageManifestCalls(manifest, transaction.revision);
    return applyGraphComponentScripts(manifest, calls);
  };

  var beginGraphEvents = function (revision) {
    if (typeof revision !== "string" || !/^[0-9a-f]{64}$/.test(revision)) {
      throw new TypeError("[Citry] Events manifest carries an invalid graph revision.");
    }
    if (graphEvents.has(revision)) {
      throw new TypeError("[Citry] ownership graph " + revision + " already has an Events transaction.");
    }
    var transaction = {
      state: "pending",
      error: null,
      waiters: [],
      releaseStart: alpineApi._holdStart(),
    };
    graphEvents.set(revision, transaction);
  };

  var finishGraphEvents = function (revision, error) {
    var transaction = graphEvents.get(revision);
    if (!transaction || transaction.state !== "pending") {
      throw new TypeError("[Citry] ownership graph " + revision + " has no pending Events transaction.");
    }
    transaction.state = error == null ? "ready" : "failed";
    transaction.error = error;
    transaction.waiters.forEach(function (waiter) {
      if (error == null) waiter.resolve();
      else waiter.reject(error);
    });
    transaction.waiters = [];
    transaction.releaseStart();
    if (scheduleOwnershipPrune) scheduleOwnershipPrune();
  };

  var whenGraphEventsReady = function (revision) {
    var transaction = graphEvents.get(revision);
    // No Events manifest was claimed for this graph. Components without
    // Events still use graph-linked dependency callbacks.
    if (!transaction) return Promise.resolve();
    if (transaction.state === "ready") return Promise.resolve();
    if (transaction.state === "failed") return Promise.reject(transaction.error);
    return new Promise(function (resolve, reject) {
      transaction.waiters.push({ resolve: resolve, reject: reject });
    });
  };

  var loadComponentScripts = function (manifest) {
    if (manifest.graph != null) {
      if (typeof manifest.graph !== "string" || !/^[0-9a-f]{64}$/.test(manifest.graph)) {
        throw new TypeError("[Citry] dependency manifest carries an invalid graph revision.");
      }
      if (graphFailures.has(manifest.graph)) {
        throw new TypeError("[Citry] dependency manifest requires a failed ownership graph " + manifest.graph + ".");
      }
      if (!ownershipGraphs.has(manifest.graph)) {
        var blocked = graphBlockedManifests.get(manifest.graph) || [];
        blocked.push(manifest);
        graphBlockedManifests.set(manifest.graph, blocked);
        return;
      }
      if (consumedGraphDependencies.has(manifest.graph)) {
        throw new TypeError("[Citry] dependency manifest repeats ownership graph " + manifest.graph + ".");
      }
      consumedGraphDependencies.add(manifest.graph);
      // Activate and hold every callback branch in this observer turn. The
      // actual assets and Events adoption may settle in later tasks.
      var calls;
      try {
        calls = stageManifestCalls(manifest, manifest.graph);
      } catch (err) {
        console.error("[Citry] discarded graph-linked dependency manifest:", err);
        return;
      }
      // Let the Events manifest observer adopt this graph-linked transaction
      // before component callbacks can run. Mutation observers and graph
      // waiter promise jobs finish before this next task. Keeping dependency
      // script injection out of the insertion microtask also lets the host's
      // fragment-insertion promise settle normally.
      setTimeout(function () {
        Promise.resolve().then(function () {
          return applyGraphComponentScripts(manifest, calls);
        }).then(
          function () {},
          function (err) {
            cancelStagedCalls(calls, err);
            console.error("[Citry] discarded graph-linked dependency manifest:", err);
          }
        );
      }, 0);
      return;
    }
    applyComponentScripts(manifest).catch(function (err) {
      console.error("[Citry] discarded dependency manifest:", err);
    });
  };

  var processManifestTag = function (el) {
    if (processedDependencyTags.has(el)) return;
    processedDependencyTags.add(el);
    // Kept as an observable diagnostic marker only. Identity comes from the
    // WeakSet above, so a clone that copies this attribute is still processed.
    el.dataset.citryProcessed = "";
    try {
      loadComponentScripts(JSON.parse(el.textContent));
    } catch (err) {
      console.error("[Citry] failed to process dependency manifest:", err);
    }
  };

  var commitGraphTag = function (el) {
    var manifest = null;
    try {
      rejectStructuralComponentClones(document);
      manifest = JSON.parse(el.textContent);
      commitOwnershipManifest(manifest);
    } catch (err) {
      failOwnershipManifest(manifest && manifest.revision, err);
      var reason = err && err.message ? err.message : String(err);
      console.error("[Citry] failed to process ownership graph manifest: " + reason);
    }
  };

  var commitDeferredGraphTag = function (el) {
    if (!deferredGraphTags.delete(el)) return;
    commitGraphTag(el);
  };

  var flushDeferredGraphTags = function () {
    Array.from(deferredGraphTags).forEach(commitDeferredGraphTag);
  };

  var processGraphTag = function (el) {
    if (processedGraphTags.has(el)) return;
    processedGraphTags.add(el);
    el.dataset.citryGraphProcessed = "";
    // A document can place <c-js> inside the component it closes. During HTML
    // parsing the graph tag then appears before that outer instance's closing
    // cap. Fragments arrive as complete DOM insertions, but parser-created
    // documents must wait until all trailing caps have landed.
    if (document.readyState === "loading") {
      deferredGraphTags.add(el);
      document.addEventListener("DOMContentLoaded", function () { commitDeferredGraphTag(el); }, { once: true });
      return;
    }
    commitGraphTag(el);
  };

  var manifestSelector = 'script[type="application/json"][data-citry]';
  var graphSelector = 'script[type="application/json"][data-citry-graph]';

  var processInsertedGraphs = function (node) {
    if (node.matches && node.matches(graphSelector)) processGraphTag(node);
    else if (node.querySelectorAll) node.querySelectorAll(graphSelector).forEach(processGraphTag);
  };

  var processInsertedDependencies = function (node) {
    if (node.matches && node.matches(manifestSelector)) processManifestTag(node);
    else if (node.querySelectorAll) node.querySelectorAll(manifestSelector).forEach(processManifestTag);
  };

  new MutationObserver(function (mutations) {
    mutations.forEach(function (mutation) {
      mutation.addedNodes.forEach(function (node) {
        if (node.nodeType !== 1) return;
        processInsertedGraphs(node);
      });
    });
    // Extension consumers, including Events, see the batch after every graph
    // tag has staged and before any graph-linked dependency manifest runs.
    dispatchAlpineMutations(mutations);
    mutations.forEach(function (mutation) {
      mutation.addedNodes.forEach(function (node) {
        if (node.nodeType !== 1) return;
        processInsertedDependencies(node);
      });
    });
    // Any DOM change may have removed an instance's last element, or swapped a
    // persisting node's data-cid-<id> for a new one; reconcile on the next
    // microtask. Watching attributes is what makes the in-place id swap
    // visible: the attribute name carries the id, so it cannot be named in an
    // attributeFilter ahead of time.
    scheduleSweep();
  }).observe(document, { childList: true, subtree: true, attributes: true, characterData: true });

  // ----- public surface -----

  globalThis.Citry = globalThis.Citry || {};
  globalThis.Citry.alpine = alpineApi;
  globalThis.Citry.manager = {
    registerComponent: registerComponent,
    registerComponentData: registerComponentData,
    callComponent: callComponent,
    decorateContext: decorateContext,
    loadJs: loadJs,
    loadCss: loadCss,
    markScriptLoaded: markScriptLoaded,
    isScriptLoaded: isScriptLoaded,
    ownership: {
      has: function (revision) { return ownershipGraphs.has(revision); },
      get: function (revision) { return ownershipGraphs.get(revision) || null; },
      whenReady: function (revision) {
        if (typeof revision !== "string" || !/^[0-9a-f]{64}$/.test(revision)) {
          return Promise.reject(new TypeError("[Citry] graph: whenReady needs a lowercase SHA-256 revision."));
        }
        if (ownershipGraphs.has(revision)) return Promise.resolve(ownershipGraphs.get(revision));
        if (graphFailures.has(revision)) return Promise.reject(graphFailures.get(revision));
        if (seenOwnershipRevisions.has(revision)) {
          return Promise.reject(new TypeError("[Citry] graph: ownership revision " + revision + " is retired."));
        }
        return new Promise(function (resolve, reject) {
          var waiters = graphWaiters.get(revision) || [];
          waiters.push({ resolve: resolve, reject: reject });
          graphWaiters.set(revision, waiters);
        });
      },
      revisions: function () { return Array.from(ownershipGraphs.keys()); },
      forRender: function (revision, renderId) {
        if (!ownershipGraphs.has(revision)) return null;
        try {
          return resolveOwnershipRoute(revision, renderId, null);
        } catch (_err) {
          return null;
        }
      },
      anchors: function () { return Array.from(browserAnchors.values()); },
      _ownerForElement: fillSourceOwnerForElement,
      _replace: replaceOwnership,
      _morphRange: morphOwnershipRange,
      _prepareAdoption: prepareOwnershipAdoption,
      _adoptionRoot: adoptionRoot,
      _activateAdoption: activateOwnershipAdoption,
      _commitAdoption: commitOwnershipAdoption,
      _abortAdoption: abortOwnershipAdoption,
      _rejectAdoption: failOwnershipManifest,
      _mintPlacement: mintRuntimePlacementId,
      _placementIds: function (generalAnchor) {
        var ids = [];
        ownershipStates.forEach(function (state, revision) {
          if (!ownershipGraphs.has(revision)) return;
          state.renderLinks.forEach(function (link) {
            if (link.link.anchor !== generalAnchor) return;
            physicalRangesForKey(state, link.record.key).forEach(function (physical) {
              if (physicalRangeIsLive(state, physical)) ids.push(physical.placementId);
            });
          });
        });
        return ids;
      },
      _placementRoots: function (generalAnchor) {
        var placements = [];
        ownershipStates.forEach(function (state, revision) {
          if (!ownershipGraphs.has(revision)) return;
          state.renderLinks.forEach(function (link) {
            if (!link.link.active || link.link.anchor !== generalAnchor) return;
            physicalRangesForKey(state, link.record.key).forEach(function (physical) {
              // Provisional adoption ranges are structurally valid but still
              // detached. Instance-target actions patch only the currently
              // live DOM placements, never the incoming fragment itself.
              if (!physical.start.isConnected || !physical.end.isConnected || !physicalRangeIsLive(state, physical)) {
                return;
              }
              placements.push(physicalRangeRoots(physical, link.record.renderId));
            });
          });
        });
        return placements;
      },
      _hasPlacements: function (generalAnchor) {
        return this._placementIds(generalAnchor).length > 0;
      },
      _relatedEvents: function (generalAnchor) {
        var source = null;
        ownershipStates.forEach(function (state) {
          state.renderLinks.forEach(function (link) {
            if (!source && link.link.active && link.link.anchor === generalAnchor) source = link.logicalState;
          });
        });
        if (!source) return [];
        var isAncestor = function (ancestor, child) {
          for (var current = child; current; current = current.parentLogical) {
            if (current === ancestor) return true;
          }
          return false;
        };
        var related = [];
        ownershipStates.forEach(function (state) {
          state.renderLinks.forEach(function (link) {
            if (!link.link.active || !link.anchorState.events) return;
            if (
              link.logicalState === source ||
              isAncestor(source, link.logicalState) ||
              isAncestor(link.logicalState, source)
            ) related.push(link.anchorState.events);
          });
        });
        return related;
      },
      _classForRender: function (renderId) {
        var classId = null;
        ownershipStates.forEach(function (state) {
          var link = state.renderLinks.get(renderId);
          if (link && link.link.active) classId = link.record.classId;
        });
        return classId;
      },
      _correspond: function (fromRenderId, toRenderId) {
        var source = null;
        var target = null;
        ownershipStates.forEach(function (state, revision) {
          var from = state.renderLinks.get(fromRenderId);
          if (from && from.link.active && ownershipGraphs.has(revision)) source = { revision: revision, link: from };
          var to = state.renderLinks.get(toRenderId);
          if (to && to.link.active && state.provisional) target = { revision: revision, link: to };
        });
        if (!source || !target || source.link.record.classId !== target.link.record.classId) return null;
        replaceOwnership([{
          fromRevision: source.revision,
          fromRenderId: fromRenderId,
          toRevision: target.revision,
          toRenderId: toRenderId,
          preserveLogical: true,
        }]);
        return target.link.link.anchor;
      },
      _morphPlacement: function (generalAnchor, index, html, options) {
        var selected = null;
        ownershipStates.forEach(function (state, revision) {
          if (selected || !ownershipGraphs.has(revision)) return;
          state.renderLinks.forEach(function (link) {
            if (selected || link.link.anchor !== generalAnchor) return;
            var placements = physicalRangesForKey(state, link.record.key).filter(function (physical) {
              return physicalRangeIsLive(state, physical);
            });
            if (placements[index]) {
              selected = { state: state, revision: revision, link: link, physical: placements[index] };
            }
          });
        });
        if (!selected) throw new TypeError("[Citry] graph: runtime placement morph target is not live.");
        options = options || {};
        options.physical = selected.physical;
        return morphOwnershipRange(selected.revision, selected.link.record.key, html, options);
      },
      _expectRetirement: function (renderIds) {
        var wanted = new Set(Array.isArray(renderIds) ? renderIds : []);
        ownershipStates.forEach(function (state, revision) {
          if (!ownershipGraphs.has(revision)) return;
          wanted.forEach(function (renderId) {
            var link = state.renderLinks.get(renderId);
            if (!link) return;
            physicalRangesForKey(state, link.record.key).forEach(function (physical) {
              expectedPhysicalRetirements.add(physical);
              ownershipStates.forEach(function (candidateState) {
                candidateState.physicalPlacements.forEach(function (placements) {
                  placements.forEach(function (candidate) {
                    if (
                      candidate !== physical &&
                      physicalRangeContainsNode(physical, candidate.start) &&
                      physicalRangeContainsNode(physical, candidate.end)
                    ) expectedPhysicalRetirements.add(candidate);
                  });
                });
              });
            });
          });
        });
      },
      _claimTag: function (el) {
        if (!el || !el.matches) return;
        if (el.matches(graphSelector)) processedGraphTags.add(el);
        if (el.matches(manifestSelector)) processedDependencyTags.add(el);
      },
      _preflightDependency: preflightAdoptionDependency,
      _applyDependency: applyAdoptionDependency,
      _preflightEvents: preflightEventsBridge,
      _attachEvents: attachEventsBridge,
      _detachEvents: detachEventsBridge,
      _transitionEvents: transitionEventsBridge,
      _retireEvents: retireEventsBridge,
      _isLive: isOwnershipAnchorLive,
      _beginEvents: beginGraphEvents,
      _finishEvents: finishGraphEvents,
    },
    _loadComponentScripts: loadComponentScripts,
    _stageOwnershipManifest: stageOwnershipManifest,
  };

  // Manifests that were already in the document before this script ran.
  var drainClientManifests = function () {
    document.querySelectorAll(graphSelector).forEach(processGraphTag);
    // A provider's empty-batch path drains its own already-present manifest
    // tags. This is what lets the one Alpine init interceptor close a late
    // fragment race synchronously.
    dispatchAlpineMutations([]);
    document.querySelectorAll(manifestSelector).forEach(processManifestTag);
  };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", drainClientManifests);
  } else {
    drainClientManifests();
  }
})();
