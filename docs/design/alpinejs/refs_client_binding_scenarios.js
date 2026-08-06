/* Browser scenarios for the throwaway boundary-handler scope prototype. */
(() => {
  const { RootGroup } = window.RootGroupSpike;
  const { BoundaryScopeClientBinding, SourceScopeAnchor } = window.BoundaryScopeSpike;
  const sleep = (milliseconds) => new Promise((resolve) => window.setTimeout(resolve, milliseconds));
  const settle = async () => {
    await Promise.resolve();
    await Alpine.nextTick();
    await Promise.resolve();
  };

  function fixture(markup) {
    const host = document.createElement("section");
    host.className = "refs-fixture";
    host.innerHTML = markup;
    document.body.append(host);
    return host;
  }

  function dispatch(target, type = "refs-probe") {
    const event = new CustomEvent(type, {
      bubbles: true,
      cancelable: true,
      composed: true,
    });
    target.dispatchEvent(event);
    return event;
  }

  function refId(carrier, name) {
    return Alpine.evaluateRaw(carrier, `$refs.${name}?.id`);
  }

  function snapshotExpression(names = ["same", "parentOnly", "childOnly"]) {
    const fields = names.map((name) => `${name}: $refs.${name}?.id`).join(",");
    return `({${fields}, el: $el.id, current: $event.currentTarget?.id ?? null})`;
  }

  async function singleRootCollision() {
    const host = fixture(`
			<div
        id="parent"
        data-cid="parent"
        x-data="{ owner: 'parent', parentOnly: 'parent-only', hits: 0 }"
      >
				<span id="parent-same" x-ref="same"></span>
				<span id="parent-only-ref" x-ref="parentOnlyRef"></span>
				<div id="source-location">
					<button
            id="child"
            data-cid="child"
            x-data="{
              owner: 'child',
              childOnly: 'child-only',
              facadeOwner: 'child-facade',
              facadeHits: 1000,
              hits: 100
            }"
            @local-scope="
              hits += 1;
              window.__localScopeEvent = $event;
              window.__localScopeValue = {
                owner,
                childOnly,
                facadeOwner,
                facadeHits,
                parentOnlyType: typeof parentOnly,
                dataOwner: $data.owner,
                dataParentOnlyType: typeof $data.parentOnly,
                sameRef: $refs.same?.id ?? null,
                childOnlyRef: $refs.childOnlyRef?.id ?? null,
                root: $root.id,
                alpineId: $id('boundary-scope'),
                el: $el.id,
                target: $event.target.id,
                current: $event.currentTarget?.id ?? null,
                marker: $event.scopeMarker
              };
            "
          >
						<span id="child-same" x-ref="same"></span>
						<span id="child-only-ref" x-ref="childOnlyRef"></span>
					</button>
				</div>
			</div>
		`);
    await settle();
    const parent = host.querySelector("#parent");
    const source = host.querySelector("#source-location");
    const child = host.querySelector("#child");
    const group = new RootGroup([child]);
    const anchor = new SourceScopeAnchor(source, "single-parent");
    const clientBinding = new BoundaryScopeClientBinding(group, anchor);
    const alpineBoundary = [];
    const citryBoundary = [];
    const dispatchedFrom = [];
    const sourceFacadeState = Alpine.reactive({
      facadeHits: 0,
      facadeOwner: "parent-facade",
    });
    // Deliberately use Alpine's merge proxy. Its virtual keys falsify a naive
    // nested `scope: Alpine.mergeProxies([...])` write-through claim.
    const sourceFacade = Alpine.mergeProxies([sourceFacadeState]);
    child.addEventListener("refs-dispatched", (event) => {
      dispatchedFrom.push({
        profile: event.detail.profile,
        target: event.target.id,
      });
    });
    const boundaryExpression = (profile) => `(() => {
      hits += 1;
      facadeHits += 1;
      $dispatch('refs-dispatched', { profile: '${profile}' });
      return {
        profile: '${profile}',
        owner,
        parentOnly,
        facadeOwner,
        facadeHits,
        childOnlyType: typeof childOnly,
        dataOwner: $data.owner,
        dataChildOnlyType: typeof $data.childOnly,
        sameRef: $refs.same?.id ?? null,
        parentOnlyRef: $refs.parentOnlyRef?.id ?? null,
        childOnlyRef: $refs.childOnlyRef?.id ?? null,
        root: $root.id,
        alpineId: $id('boundary-scope'),
        el: $el.id,
        target: $event.target.id,
        current: $event.currentTarget?.id ?? null,
        marker: $event.scopeMarker
      };
    })()`;
    const stopAlpine = clientBinding.onAlpine(
      "boundary-alpine",
      [],
      boundaryExpression("alpine"),
      (value, event) => alpineBoundary.push({ ...value, exactEvent: event === alpineEvent }),
      sourceFacade,
    );
    const stopCitry = clientBinding.onCitry(
      "boundary-citry",
      {},
      boundaryExpression("citry"),
      (value, event) => citryBoundary.push({ ...value, exactEvent: event === citryEvent }),
      sourceFacade,
    );

    const alpineEvent = new CustomEvent("boundary-alpine", {
      bubbles: true,
      composed: true,
    });
    alpineEvent.scopeMarker = "alpine-event";
    child.dispatchEvent(alpineEvent);
    const citryEvent = new CustomEvent("boundary-citry", {
      bubbles: true,
      composed: true,
    });
    citryEvent.scopeMarker = "citry-event";
    child.dispatchEvent(citryEvent);

    window.__localScopeEvent = null;
    window.__localScopeValue = null;
    const localEvent = new CustomEvent("local-scope", {
      bubbles: true,
      composed: true,
    });
    localEvent.scopeMarker = "local-event";
    child.dispatchEvent(localEvent);

    const result = {
      alpineBoundary,
      childHits: child._x_dataStack[0].hits,
      citryBoundary,
      dispatchedFrom,
      facadeState: { ...sourceFacadeState },
      local: {
        ...window.__localScopeValue,
        exactEvent: window.__localScopeEvent === localEvent,
      },
      parentHits: parent._x_dataStack[0].hits,
      source: {
        alpineId: Alpine.evaluateRaw(source, "$id('boundary-scope')"),
        owner: Alpine.evaluateRaw(source, "owner"),
        same: refId(source, "same"),
        parentOnlyRef: refId(source, "parentOnlyRef"),
        childOnlyRef: refId(source, "childOnlyRef"),
      },
    };
    stopCitry();
    stopAlpine();
    clientBinding.destroy();
    group.destroy();
    host.remove();
    return result;
  }

  async function groupedTargetAndExactSource() {
    const host = fixture(`
			<div id="source-a" data-cid="source" x-data>
				<span id="a-same" x-ref="same"></span>
				<span id="a-only" x-ref="aOnly"></span>
			</div>
			<div id="source-b" data-cid="source" x-data>
				<span id="b-same" x-ref="same"></span>
				<span id="b-only" x-ref="bOnly"></span>
				<div id="authored-here">
					<button id="target-a" data-cid="target-a" x-data>
						<span id="target-a-same" x-ref="same"></span>
					</button>
					<button id="target-b" data-cid="target-b" x-data>
						<span id="target-b-same" x-ref="same"></span>
					</button>
				</div>
			</div>
		`);
    await settle();
    const source = host.querySelector("#authored-here");
    const sourceA = host.querySelector("#source-a");
    const sourceB = host.querySelector("#source-b");
    const a = host.querySelector("#target-a");
    const b = host.querySelector("#target-b");
    // These are two physical roots of one logical source instance. The
    // handler is authored under root B, while root A is deliberately first.
    const sourceGroup = new RootGroup([sourceA, sourceB]);
    const group = new RootGroup([a, b]);
    const anchor = new SourceScopeAnchor(source, "source-root-b");
    const clientBinding = new BoundaryScopeClientBinding(group, anchor);
    const delivered = [];
    clientBinding.onCitry("refs-grouped", {}, snapshotExpression(["same", "aOnly", "bOnly"]), (value) => delivered.push(value));
    dispatch(a, "refs-grouped");
    dispatch(b, "refs-grouped");
    const controls = {
      aNative: refId(a, "same"),
      bNative: refId(b, "same"),
      sourceFirstRoot: refId(sourceGroup.els[0], "same"),
      sourceExactLocation: refId(source, "same"),
    };

    const c = document.createElement("button");
    c.id = "target-c";
    c.setAttribute("data-cid", "target-c");
    c.setAttribute("x-data", "{}");
    c.innerHTML = '<span id="target-c-same" x-ref="same"></span>';
    source.append(c);
    await settle();
    group.removeRoot(a);
    group.addRoot(c);
    dispatch(a, "refs-grouped");
    dispatch(c, "refs-grouped");

    const result = {
      controls,
      delivered,
      liveRoots: group.els.map((root) => root.id),
    };
    clientBinding.destroy();
    group.destroy();
    sourceGroup.destroy();
    host.remove();
    return result;
  }

  async function sharedPhysicalRoot() {
    const host = fixture(`
			<div id="source-one" data-cid="source-one" x-data>
				<span id="one-same" x-ref="same"></span>
				<div id="one-location"></div>
			</div>
			<div id="source-two" data-cid="source-two" x-data>
				<span id="two-same" x-ref="same"></span>
				<div id="two-location"></div>
			</div>
			<div id="target-host">
				<button id="shared-root" data-cid="wrapper child" x-data>
					<span id="shared-same" x-ref="same"></span>
					<span id="shared-only" x-ref="childOnly"></span>
				</button>
			</div>
		`);
    await settle();
    const root = host.querySelector("#shared-root");
    const group = new RootGroup([root]);
    const values = [];
    const clientBindings = [
      new BoundaryScopeClientBinding(group, new SourceScopeAnchor(host.querySelector("#one-location"), "one")),
      new BoundaryScopeClientBinding(group, new SourceScopeAnchor(host.querySelector("#two-location"), "two")),
    ];
    for (const [index, clientBinding] of clientBindings.entries()) {
      clientBinding.onCitry("refs-shared", {}, snapshotExpression(["same", "childOnly"]), (value) =>
        values.push({ clientBinding: index + 1, ...value }),
      );
    }
    dispatch(root, "refs-shared");
    const result = {
      native: {
        same: refId(root, "same"),
        childOnly: refId(root, "childOnly"),
      },
      values,
    };
    for (const clientBinding of clientBindings) clientBinding.destroy();
    group.destroy();
    host.remove();
    return result;
  }

  async function dynamicRefsAndSourceReplacement() {
    const host = fixture(`
			<div id="source-old" data-cid="source-old" x-data>
				<span id="old-ref" x-ref="same"></span>
				<div id="old-location"></div>
			</div>
			<button id="dynamic-target" data-cid="dynamic-target" x-data></button>
		`);
    await settle();
    const target = host.querySelector("#dynamic-target");
    const oldSourceRoot = host.querySelector("#source-old");
    const oldLocation = host.querySelector("#old-location");
    const group = new RootGroup([target]);
    const anchor = new SourceScopeAnchor(oldLocation, "replaceable-source");
    const clientBinding = new BoundaryScopeClientBinding(group, anchor);
    const seen = [];
    clientBinding.onCitry("refs-dynamic", {}, snapshotExpression(["same"]), (value) => seen.push(value.same));
    dispatch(target, "refs-dynamic");

    const oldRef = host.querySelector("#old-ref");
    Alpine.morph(oldRef, '<strong id="morphed-ref" x-ref="same"></strong>');
    await settle();
    dispatch(target, "refs-dynamic");

    const morphedRef = host.querySelector("#morphed-ref");
    morphedRef.removeAttribute("x-ref");
    await settle();
    dispatch(target, "refs-dynamic");
    morphedRef.setAttribute("x-ref", "same");
    await settle();
    dispatch(target, "refs-dynamic");

    const replacement = document.createElement("div");
    replacement.id = "source-new";
    replacement.setAttribute("data-cid", "source-new");
    replacement.setAttribute("x-data", "{}");
    replacement.innerHTML = '<span id="new-source-ref" x-ref="same"></span><div id="new-location"></div>';
    oldSourceRoot.after(replacement);
    await settle();
    anchor.setCarrier(replacement.querySelector("#new-location"));
    oldSourceRoot.remove();
    await settle();
    dispatch(target, "refs-dynamic");

    const result = { seen };
    clientBinding.destroy();
    anchor.destroy();
    group.destroy();
    host.remove();
    return result;
  }

  async function delayedLivenessAndFreshness() {
    const host = fixture(`
			<div id="delay-source" data-cid="delay-source" x-data>
				<span id="delay-old" x-ref="same"></span>
				<div id="delay-location"></div>
			</div>
			<button id="delay-target" data-cid="delay-target" x-data></button>
		`);
    await settle();
    const sourceRoot = host.querySelector("#delay-source");
    const sourceLocation = host.querySelector("#delay-location");
    const target = host.querySelector("#delay-target");
    const group = new RootGroup([target]);
    const drops = [];
    const logicalSource = { live: true };
    const clientBinding = new BoundaryScopeClientBinding(
      group,
      new SourceScopeAnchor(sourceLocation, "delayed-source", () => logicalSource.live),
      {
        onDrop: (reason) => drops.push(reason),
      },
    );
    const delivered = [];
    clientBinding.onCitry("refs-delay", { debounce: 18 }, snapshotExpression(["same"]), (value) => delivered.push(value));
    dispatch(target, "refs-delay");
    const old = host.querySelector("#delay-old");
    old.remove();
    await settle();
    const fresh = document.createElement("span");
    fresh.id = "delay-fresh";
    fresh.setAttribute("x-ref", "same");
    sourceRoot.prepend(fresh);
    await settle();
    await sleep(28);

    dispatch(target, "refs-delay");
    // The logical source retires while its physical Alpine root and carrier
    // stay connected, as can happen when identities share a physical root.
    logicalSource.live = false;
    await sleep(28);

    const replacementSource = document.createElement("div");
    replacementSource.id = "delay-source-2";
    replacementSource.setAttribute("data-cid", "delay-source-2");
    replacementSource.setAttribute("x-data", "{}");
    replacementSource.innerHTML = '<span id="delay-third" x-ref="same"></span><div id="delay-location-2"></div>';
    host.prepend(replacementSource);
    await settle();
    logicalSource.live = true;
    clientBinding.source.setCarrier(replacementSource.querySelector("#delay-location-2"));
    dispatch(target, "refs-delay");
    group.removeRoot(target);
    await sleep(28);

    clientBinding.source.setCarrier(replacementSource.querySelector("#delay-location-2"));
    group.addRoot(target);
    dispatch(target, "refs-delay");
    clientBinding.destroy();
    clientBinding.destroy();
    await sleep(28);

    const result = { delivered, drops };
    group.destroy();
    host.remove();
    return result;
  }

  async function teleportOracle() {
    const host = fixture(`
			<div id="teleport-destination" data-cid="destination" x-data>
				<span id="destination-same" x-ref="same"></span>
			</div>
			<div id="teleport-origin" data-cid="origin" x-data>
				<span id="origin-same" x-ref="same"></span>
				<template id="teleport-template" x-teleport="#teleport-destination">
					<button id="teleported-target" data-cid="teleported-target">target</button>
				</template>
			</div>
		`);
    await settle();
    const template = host.querySelector("#teleport-template");
    const target = host.querySelector("#teleported-target");
    const group = new RootGroup([target]);
    const clientBinding = new BoundaryScopeClientBinding(group, new SourceScopeAnchor(template, "teleport-origin"));
    const seen = [];
    clientBinding.onCitry("refs-teleport", {}, snapshotExpression(["same"]), (value) => seen.push(value));
    dispatch(target, "refs-teleport");
    const result = {
      destination: refId(host.querySelector("#teleport-destination"), "same"),
      nativeTarget: refId(target, "same"),
      origin: refId(template, "same"),
      seen,
    };
    clientBinding.destroy();
    group.destroy();
    host.remove();
    return result;
  }

  async function nativeConditionalAndLoopCanaries() {
    const host = fixture(`
			<div id="native-source" data-cid="native-source" x-data="{ show: true, items: ['a', 'b'] }">
				<div id="native-location"></div>
				<template x-if="show">
					<span id="conditional-ref" x-ref="conditional"></span>
				</template>
				<template x-for="item in items" :key="item">
					<span x-ref="repeated" :data-item="item"></span>
				</template>
			</div>
		`);
    await settle();
    const source = host.querySelector("#native-location");
    const data = host.querySelector("#native-source")._x_dataStack[0];
    const read = () => ({
      conditional: refId(source, "conditional") || null,
      repeated: Alpine.evaluateRaw(source, "$refs.repeated?.dataset.item") || null,
    });
    const initial = read();
    data.show = false;
    await settle();
    const hidden = read();
    data.show = true;
    data.items = ["b", "a"];
    await settle();
    const restoredAndReordered = read();
    data.items = ["b"];
    await settle();
    const removedOtherClone = read();
    data.items = [];
    await settle();
    data.items = ["c"];
    await settle();
    const freshClone = read();
    host.remove();
    return {
      freshClone,
      hidden,
      initial,
      removedOtherClone,
      restoredAndReordered,
    };
  }

  async function shadowAndRootlessBoundaries() {
    const host = fixture(`
			<div id="shadow-source" data-cid="shadow-source" x-data>
				<span id="light-ref" x-ref="light"></span>
				<div id="shadow-host"></div>
			</div>
		`);
    await settle();
    const shadowHost = host.querySelector("#shadow-host");
    const shadow = shadowHost.attachShadow({ mode: "open" });
    shadow.innerHTML = '<span id="shadow-ref" x-ref="shadowOnly"></span><div id="shadow-location"></div>';
    Alpine.initTree(shadow);
    await settle();
    const location = shadow.querySelector("#shadow-location");
    const shadowResult = {
      light: refId(location, "light"),
      shadowOnly: refId(location, "shadowOnly"),
    };
    Alpine.destroyTree(shadow);

    const emptyGroup = new RootGroup([]);
    const clientBinding = new BoundaryScopeClientBinding(
      emptyGroup,
      new SourceScopeAnchor(host.querySelector("#shadow-source"), "rootless"),
    );
    const rootlessErrors = {};
    for (const profile of ["alpine", "citry"]) {
      try {
        if (profile === "alpine") {
          clientBinding.onAlpine("rootless-probe", [], "({})", () => {});
        } else {
          clientBinding.onCitry("rootless-probe", {}, "({})", () => {});
        }
      } catch (error) {
        rootlessErrors[profile] = error.message;
      }
    }
    clientBinding.destroy();
    emptyGroup.destroy();
    host.remove();
    return { rootlessErrors, shadow: shadowResult };
  }

  window.runBoundaryScopeScenarios = async () => ({
    delayedLivenessAndFreshness: await delayedLivenessAndFreshness(),
    dynamicRefsAndSourceReplacement: await dynamicRefsAndSourceReplacement(),
    groupedTargetAndExactSource: await groupedTargetAndExactSource(),
    nativeConditionalAndLoopCanaries: await nativeConditionalAndLoopCanaries(),
    shadowAndRootlessBoundaries: await shadowAndRootlessBoundaries(),
    sharedPhysicalRoot: await sharedPhysicalRoot(),
    singleRootCollision: await singleRootCollision(),
    teleportOracle: await teleportOracle(),
  });
})();
