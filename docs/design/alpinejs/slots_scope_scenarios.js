/* Browser scenarios for the research-only Alpine slot-scope adapter. */
(() => {
  const settle = async () => {
    await Promise.resolve();
    await Alpine.nextTick();
    await Promise.resolve();
    await new Promise((resolve) => setTimeout(resolve, 0));
  };

  const byId = (id) => document.getElementById(id);
  const evaluate = (el, expression) => Alpine.evaluate(el, expression);
  const refId = (el, name) => evaluate(el, `$refs.${name}?.id ?? null`);

  function ordinaryScope() {
    const source = byId("ordering-source");
    const fill = byId("ordering-fill");
    const local = byId("local-fill");
    const before = source._x_dataStack[0].count;
    evaluate(fill, "count += 2");
    return {
      failedInterceptorControl: {
        text: byId("old-interceptor-fill").textContent,
        stackKeys: Object.keys(byId("old-interceptor-fill")._x_dataStack[0]),
      },
      fill: {
        childOnlyType: evaluate(fill, "typeof childOnly"),
        dataOwner: evaluate(fill, "$data.owner"),
        el: evaluate(fill, "$el.id"),
        fillRef: refId(fill, "fillOwned"),
        id: evaluate(fill, "$id('scope-id')"),
        owner: evaluate(fill, "owner"),
        parentOnly: evaluate(fill, "parentOnly"),
        root: evaluate(fill, "$root.id"),
        sameRef: refId(fill, "same"),
        childRef: refId(fill, "childOnlyRef"),
        text: fill.textContent,
      },
      local: {
        childOnlyType: evaluate(local, "typeof childOnly"),
        localOnly: evaluate(local, "localOnly"),
        owner: evaluate(local, "owner"),
        parentOnly: evaluate(local, "parentOnly"),
        root: evaluate(local, "$root.id"),
      },
      source: {
        countBefore: before,
        countAfter: source._x_dataStack[0].count,
        id: evaluate(source, "$id('scope-id')"),
        fillRef: refId(source, "fillOwned"),
      },
    };
  }

  async function directTemplateRoots() {
    const source = byId("clone-source");
    const snapshotIf = (root) => {
      const child = root.querySelector("#if-generated-child");
      const nested = root.querySelector("#if-nested-clone");
      const localId = evaluate(root, "$id('if-local-id')");
      return {
        child: {
          directSource: child._x_citrySlotSource?.token ?? null,
          id: evaluate(child, "$id('if-local-id')"),
          localRef: refId(child, "ifChild"),
          owner: evaluate(child, "owner"),
          root: evaluate(child, "$root.id"),
          sourceOnly: evaluate(child, "sourceOnly"),
          sourceRef: refId(child, "sourceRef"),
        },
        directSource: root._x_citrySlotSource?.token ?? null,
        hasMarker: root.hasAttribute("x-cfill"),
        localId,
        localRootRef: refId(root, "ifOwned"),
        nested: {
          directSource: nested._x_citrySlotSource?.token ?? null,
          localRef: refId(nested, "nestedIf"),
          owner: evaluate(nested, "owner"),
          root: evaluate(nested, "$root.id"),
          sourceOnly: evaluate(nested, "sourceOnly"),
        },
        owner: evaluate(root, "owner"),
        root: evaluate(root, "$root.id"),
        sourceOnly: evaluate(root, "sourceOnly"),
        sourceRef: refId(root, "sourceRef"),
        sourceToken: SlotsScopeSpike.sourceOf(root)?.token ?? null,
      };
    };

    const firstIf = byId("if-generated");
    const firstSnapshot = snapshotIf(firstIf);

    source._x_dataStack[0].show = false;
    await settle();
    const absent = byId("if-generated") === null;
    source._x_dataStack[0].show = true;
    await settle();
    const secondIf = byId("if-generated");
    const secondSnapshot = {
      ...snapshotIf(secondIf),
      freshNode: secondIf !== firstIf,
    };

    secondIf.insertAdjacentHTML(
      "beforeend",
      '<aside id="if-late-root" x-data="{ owner: \'late-local\' }" x-id="[\'late-local-id\']"><span id="if-late-child" x-ref="lateChild"></span></aside>',
    );
    const lateRoot = byId("if-late-root");
    Alpine.initTree(lateRoot);
    await settle();
    const lateChild = byId("if-late-child");

    const forRoots = Array.from(document.querySelectorAll(".for-generated"));
    return {
      sourceLocalRefs: {
        forChild: refId(source, "forChild"),
        forOwned: refId(source, "forOwned"),
        ifChild: refId(source, "ifChild"),
        ifOwned: refId(source, "ifOwned"),
        lateChild: refId(source, "lateChild"),
      },
      xIf: {
        first: firstSnapshot,
        absent,
        second: secondSnapshot,
        late: {
          childDirectSource: lateChild._x_citrySlotSource?.token ?? null,
          directSource: lateRoot._x_citrySlotSource?.token ?? null,
          id: evaluate(lateRoot, "$id('late-local-id')"),
          childId: evaluate(lateChild, "$id('late-local-id')"),
          localRef: refId(lateChild, "lateChild"),
          owner: evaluate(lateChild, "owner"),
          root: evaluate(lateChild, "$root.id"),
          sourceOnly: evaluate(lateChild, "sourceOnly"),
          sourceRef: refId(lateChild, "sourceRef"),
        },
      },
      xFor: forRoots.map((root) => {
        const child = root.querySelector(".for-generated-child");
        const nested = root.querySelector(".for-nested-clone");
        return {
          childDirectSource: child._x_citrySlotSource?.token ?? null,
          childId: evaluate(child, "$id('for-local-id')"),
          childRef: refId(child, "forChild"),
          childRoot: evaluate(child, "$root.id"),
          childText: child.textContent,
          directSource: root._x_citrySlotSource?.token ?? null,
          hasMarker: root.hasAttribute("x-cfill"),
          item: evaluate(root, "item"),
          localId: evaluate(root, "$id('for-local-id')"),
          localRootRef: refId(root, "forOwned"),
          nestedDirectSource: nested?._x_citrySlotSource?.token ?? null,
          nestedOwner: nested ? evaluate(nested, "owner") : null,
          nestedRoot: nested ? evaluate(nested, "$root.id") : null,
          nestedRef: nested ? refId(nested, "nestedFor") : null,
          owner: evaluate(root, "owner"),
          root: evaluate(root, "$root.id"),
          sourceOnly: evaluate(root, "sourceOnly"),
          sourceRef: refId(root, "sourceRef"),
          sourceToken: SlotsScopeSpike.sourceOf(root)?.token ?? null,
        };
      }),
    };
  }

  function clientLoopCallSites() {
    return Array.from(document.querySelectorAll(".loop-call-fill")).map((el) => {
      const source = SlotsScopeSpike.sourceOf(el);
      return {
        item: evaluate(el, "item"),
        owner: evaluate(el, "owner"),
        strategy: source?.strategy ?? null,
        text: el.textContent,
      };
    });
  }

  function nestedOwnership() {
    const outer = byId("nested-ordinary");
    const inner = byId("nested-component-template");
    const collision = byId("collision-component-template");
    return {
      ordinary: {
        owner: evaluate(outer, "owner"),
        parentOnly: evaluate(outer, "parentOnly"),
      },
      nestedComponent: {
        closestOuterFill: Boolean(inner.closest("[x-cfill]")),
        owner: evaluate(inner, "owner"),
        parentOnlyType: evaluate(inner, "typeof parentOnly"),
        innerOnly: evaluate(inner, "innerOnly"),
      },
      markedComponentCollision: {
        owner: evaluate(collision, "owner"),
        parentOnlyType: evaluate(collision, "typeof parentOnly"),
        parentOnly: evaluate(collision, "parentOnly"),
      },
    };
  }

  function fallbackOwnership() {
    const outer = byId("fallback-outer");
    const childFallback = byId("fallback-child-owned");
    const unmarked = byId("fallback-unmarked-control");
    return {
      outer: evaluate(outer, "owner"),
      childFallback: evaluate(childFallback, "owner"),
      unmarkedControl: evaluate(unmarked, "owner"),
    };
  }

  function nativeEvents() {
    window.__nativeOrder.length = 0;
    window.__fillEvent = null;
    const child = byId("ordering-child");
    const fill = byId("ordering-fill");
    const boundaryListener = () => window.__nativeOrder.push("component-boundary");
    child.addEventListener("scope-event", boundaryListener);
    const event = new CustomEvent("scope-event", {
      bubbles: true,
      cancelable: true,
      composed: true,
      detail: { marker: "native" },
    });
    fill.dispatchEvent(event);
    child.removeEventListener("scope-event", boundaryListener);
    return {
      exactEvent: window.__fillEvent === event,
      order: [...window.__nativeOrder],
      sourceCount: byId("ordering-source")._x_dataStack[0].count,
      target: event.target.id,
    };
  }

  function syntheticForwardingControl() {
    const source = byId("synthetic-source");
    const comment = SlotsScopeSpike.sourceComments("synthetic")[0];
    const child = byId("synthetic-child");
    const fill = byId("synthetic-fill");
    const order = [];
    let forwarded = null;
    let forwardedPath = [];
    let originalPath = [];

    const documentCapture = (event) => {
      if (event.type === "synthetic-probe") order.push(event === original ? "document-capture-original" : "document-capture-new");
    };
    const documentBubble = (event) => {
      if (event.type === "synthetic-probe") order.push(event === original ? "document-bubble-original" : "document-bubble-new");
    };
    document.addEventListener("synthetic-probe", documentCapture, true);
    document.addEventListener("synthetic-probe", documentBubble);
    source.addEventListener("synthetic-probe", (event) => {
      order.push("source-bubble-new");
      forwardedPath = event.composedPath().map((node) => node.id || node.nodeName);
      event.preventDefault();
    });
    child.addEventListener("synthetic-probe", () => order.push("child-capture-original"), true);
    child.addEventListener("synthetic-probe", () => order.push("component-boundary-original"));
    fill.addEventListener("synthetic-probe", (event) => {
      order.push("fill-target-original");
      originalPath = event.composedPath().map((node) => node.id || node.nodeName);
    });
    fill.addEventListener("synthetic-probe", (event) => {
      order.push("forwarder-original");
      event.stopPropagation();
      forwarded = new event.constructor(event.type, event);
      comment.dispatchEvent(forwarded);
    });

    const original = new CustomEvent("synthetic-probe", {
      bubbles: true,
      cancelable: true,
      composed: true,
      detail: { marker: "original" },
    });
    const dispatchResult = fill.dispatchEvent(original);
    document.removeEventListener("synthetic-probe", documentCapture, true);
    document.removeEventListener("synthetic-probe", documentBubble);

    return {
      dispatchResult,
      forwarded: {
        defaultPrevented: forwarded.defaultPrevented,
        detail: forwarded.detail,
        exactEvent: forwarded === original,
        path: forwardedPath,
        target: forwarded.target.nodeName,
        trusted: forwarded.isTrusted,
      },
      order,
      original: {
        defaultPrevented: original.defaultPrevented,
        path: originalPath,
        target: original.target.id,
        trusted: original.isTrusted,
      },
    };
  }

  function teleportedScope() {
    const source = byId("teleport-source");
    const fill = byId("teleport-fill");
    window.__teleportOrder.length = 0;
    window.__teleportEvent = null;
    const event = new CustomEvent("teleport-probe", { bubbles: true, composed: true });
    fill.dispatchEvent(event);
    const local = byId("teleport-local");
    const localChild = byId("teleport-local-child");
    const localId = evaluate(local, "$id('teleport-shared-id')");
    const nestedOuter = byId("teleport-outer-template");
    const nestedInner = byId("teleport-inner-template");
    const nestedLocal = byId("teleport-nested-local");
    const nestedChild = byId("teleport-nested-child");
    const nestedId = evaluate(nestedLocal, "$id('teleport-shared-id')");
    return {
      directTemplate: {
        childDirectSource: localChild._x_citrySlotSource?.token ?? null,
        childId: evaluate(localChild, "$id('teleport-shared-id')"),
        childRef: refId(localChild, "teleportLocalChild"),
        childRoot: evaluate(localChild, "$root.id"),
        destination: local.parentElement.id,
        localId,
        localRootRef: refId(local, "teleportLocalRoot"),
        nativeOrigin: local._x_teleportBack?.id ?? null,
        owner: evaluate(localChild, "owner"),
        sameRef: refId(localChild, "same"),
        sourceLocalChildRef: refId(source, "teleportLocalChild"),
        sourceSameRef: refId(source, "same"),
        sourceOnly: evaluate(localChild, "sourceOnly"),
        sourceRef: refId(localChild, "sourceRef"),
      },
      nestedTemplate: {
        chain: [
          nestedLocal._x_teleportBack?.id ?? null,
          nestedInner._x_teleportBack?.id ?? null,
          nestedOuter._x_teleportBack?.id ?? null,
        ],
        childDirectSource: nestedChild._x_citrySlotSource?.token ?? null,
        childId: evaluate(nestedChild, "$id('teleport-shared-id')"),
        childRef: refId(nestedChild, "teleportNestedChild"),
        childRoot: evaluate(nestedChild, "$root.id"),
        destination: nestedLocal.parentElement.id,
        directSource: nestedLocal._x_citrySlotSource?.token ?? null,
        localId: nestedId,
        localRootRef: refId(nestedLocal, "teleportNestedRoot"),
        nativePairs: [
          nestedInner._x_teleport === nestedLocal,
          nestedOuter._x_teleport === nestedInner,
        ],
        owner: evaluate(nestedChild, "owner"),
        sameRef: refId(nestedChild, "same"),
        sourceId: evaluate(source, "$id('teleport-shared-id')"),
        sourceLocalChildRef: refId(source, "teleportNestedChild"),
        sourceSameRef: refId(source, "same"),
        sourceOnly: evaluate(nestedChild, "sourceOnly"),
        sourceRef: refId(nestedChild, "sourceRef"),
      },
      destination: fill.parentElement.id,
      event: {
        exact: window.__teleportEvent === event,
        order: [...window.__teleportOrder],
        target: event.target.id,
      },
      scope: {
        childOnlyType: evaluate(fill, "typeof childOnly"),
        owner: evaluate(fill, "owner"),
        root: evaluate(fill, "$root.id"),
        sourceRef: refId(fill, "sourceRef"),
        teleportedRefAtSource: refId(source, "teleportedOwned"),
      },
    };
  }

  function multiRootScope() {
    const source = byId("multi-source");
    const roots = [byId("multi-a"), byId("multi-b")];
    evaluate(roots[0], "count += 1");
    evaluate(roots[1], "count += 10");
    return {
      count: source._x_dataStack[0].count,
      roots: roots.map((root) => ({
        el: evaluate(root, "$el.id"),
        owner: evaluate(root, "owner"),
        source: SlotsScopeSpike.sourceOf(root)?.token ?? null,
      })),
    };
  }

  async function morphAndRestamp() {
    const morphFill = byId("morph-fill");
    const identity = morphFill;
    Alpine.morph(
      morphFill,
      '<div id="morph-fill" x-cfill="ordering" x-data="{ owner: \'morph-local\', localOnly: \'kept\' }"><span id="morph-child" x-text="owner + \':\' + parentOnly"></span></div>',
    );
    await settle();
    const afterMorph = {
      identity: byId("morph-fill") === identity,
      localOnly: evaluate(morphFill, "localOnly"),
      owner: evaluate(morphFill, "owner"),
      parentOnly: evaluate(morphFill, "parentOnly"),
      text: byId("morph-child").textContent,
    };

    const restamp = byId("restamp-fill");
    const beforeRestamp = {
      localOnly: evaluate(restamp, "localOnly"),
      owner: evaluate(restamp, "owner"),
      stackLength: restamp._x_dataStack.length,
    };
    SlotsScopeSpike.destructiveRestamp(restamp);
    const afterRestamp = {
      localOnlyType: evaluate(restamp, "typeof localOnly"),
      owner: evaluate(restamp, "owner"),
      stackLength: restamp._x_dataStack.length,
    };
    return { afterMorph, beforeRestamp, afterRestamp };
  }

  async function sourceReplacement() {
    const oldSource = byId("dynamic-source-old");
    const fill = byId("dynamic-fill");
    const before = {
      id: evaluate(fill, "$id('dynamic-id')"),
      owner: evaluate(fill, "owner"),
      ref: refId(fill, "same"),
      root: evaluate(fill, "$root.id"),
      text: fill.textContent,
    };
    oldSource.remove();
    await settle();
    const detached = {
      ownerType: evaluate(fill, "typeof owner"),
      root: evaluate(fill, "$root")?.id ?? null,
    };
    byId("dynamic-host").insertAdjacentHTML(
      "beforebegin",
      '<section id="dynamic-source-new" data-cid="dynamic-source-new" x-data="{ owner: \'new-source\' }" x-id="[\'dynamic-id\']"><span id="dynamic-new-ref" x-ref="same"></span><!--citry-fill-source:dynamic--></section>',
    );
    await settle();
    SlotsScopeSpike.refreshFor(fill);
    await settle();
    const after = {
      id: evaluate(fill, "$id('dynamic-id')"),
      owner: evaluate(fill, "owner"),
      ref: refId(fill, "same"),
      root: evaluate(fill, "$root.id"),
      sourceId: evaluate(byId("dynamic-source-new"), "$id('dynamic-id')"),
      text: fill.textContent,
    };
    return { before, detached, after };
  }

  async function runSlotsScopeScenarios() {
    await settle();
    const result = {
      alpineVersion: Alpine.version,
      ordinaryScope: ordinaryScope(),
      directTemplateRoots: await directTemplateRoots(),
      clientLoopCallSites: clientLoopCallSites(),
      fallbackOwnership: fallbackOwnership(),
      nestedOwnership: nestedOwnership(),
      nativeEvents: nativeEvents(),
      syntheticForwardingControl: syntheticForwardingControl(),
      teleportedScope: teleportedScope(),
      multiRootScope: multiRootScope(),
      morphAndRestamp: await morphAndRestamp(),
      sourceReplacement: await sourceReplacement(),
    };
    return result;
  }

  globalThis.runSlotsScopeScenarios = runSlotsScopeScenarios;
})();
