(function() {

const imageReady = "data-citry-image-initialized";
const imageOwner = Symbol.for("citry-ui:image-owner");
const imageScopes = globalThis[Symbol.for("citry-ui:image-mutation-scopes")] ??= new WeakMap();
const watchImage = (root, entry) => {
  let scope;
  let manager;
  let active = true;
  const detach = () => {
    if (manager?.entries.get(root) !== entry) return;
    manager.entries.delete(root);
    if (manager.entries.size === 0) {
      manager.observer.disconnect();
      imageScopes.delete(scope);
    }
  };
  const attach = () => {
    scope = root.getRootNode();
    manager = imageScopes.get(scope);
    if (!manager) {
      const entries = new Map();
      const observer = new MutationObserver((records) => {
        for (const record of records) {
          for (const node of record.addedNodes) {
            if (!(node instanceof Element)) continue;
            const candidates = node.hasAttribute(imageReady)
              ? [node, ...node.querySelectorAll(`[${imageReady}]`)]
              : [...node.querySelectorAll(`[${imageReady}]`)];
            for (const candidate of candidates) {
              if (!candidate[imageOwner]?.active) {
                candidate.removeAttribute(imageReady);
                candidate.removeAttribute("data-status");
                for (const visual of candidate.querySelectorAll(
                  ':scope > [data-citry-ui-part="placeholder"], :scope > [data-citry-ui-part="fallback"]',
                )) visual.hidden = true;
              }
            }
          }
        }
        for (const [candidate, registration] of [...entries]) {
          if (records.some((record) => record.target === candidate
            || candidate.contains(record.target)
            || [...record.addedNodes, ...record.removedNodes].some((node) =>
              node === candidate || node.contains?.(candidate)))) registration.notify();
        }
      });
      observer.observe(scope instanceof Document ? scope.documentElement : scope, {
        subtree: true, childList: true, attributes: true,
      });
      manager = { entries, observer };
      imageScopes.set(scope, manager);
    }
    manager.entries.set(root, entry);
  };
  attach();
  return {
    refresh() {
      if (active && root.getRootNode() !== scope) {
        detach();
        attach();
      }
    },
    cleanup() {
      active = false;
      detach();
    },
  };
};
__citryRuntime.registerTypeOptions.bind(null, "CImage_2a7af5", "ceadfea9d9447971a87e19f3c9a9f23183d14e8448cb3df4425a7223c19aa1dc")({
  props: {
    src: {}, alt: {}, width: {}, height: {}, srcset: {}, sizes: {},
    loading: {}, decoding: {}, fetchPriority: {}, crossOrigin: {},
    referrerPolicy: {}, fit: {}, position: {}, draggable: {},
    onStatusChange: {},
  },
  onServerRender: ({component}) => {
    const root = component.$el;
    const data = {
      sources: component.sources,
      hasPlaceholder: component.hasPlaceholder,
      hasFallback: component.hasFallback,
      ...component.serverDefaults,
    };
    const props = component.$props;
    const effect = Citry.vue.watchEffect;
    const handoffKey = Symbol.for("citry-ui:image-handoff");
    const previous = root?.[handoffKey] ?? null;
    if (previous?.abort !== null && previous?.abort !== undefined) clearTimeout(previous.abort);
    if (!previous) {
      root?.removeAttribute(imageReady);
      root?.removeAttribute("data-status");
    }
    const abortHandoff = (record) => {
      if (!record) return;
      if (record.abort !== null) clearTimeout(record.abort);
      record.root.removeAttribute(imageReady);
      record.root.removeAttribute("data-status");
      if (record.placeholder) record.placeholder.hidden = true;
      if (record.fallback) record.fallback.hidden = true;
      if (record.root[handoffKey] === record) delete record.root[handoffKey];
    };
    // A matched first child is the template's `<picture>` element, which has `dataset`.
    const picture = root.firstElementChild?.matches('[data-citry-ui-part="picture"]')
      ? /** @type {HTMLElement} */ (root.firstElementChild) : null;
    const image = picture
      ? picture.querySelector(':scope > [data-citry-ui-part="image"]')
      : root.querySelector(':scope > [data-citry-ui-part="image"]');
    const sourceElements = picture ? [...picture.children].slice(0, -1) : [];
    const placeholder = root.querySelector(':scope > [data-citry-ui-part="placeholder"]');
    const fallback = root.querySelector(':scope > [data-citry-ui-part="fallback"]');
    if (!(root instanceof HTMLSpanElement) || !(image instanceof HTMLImageElement)) {
      abortHandoff(previous);
      console.error("[citry-ui] CImage requires one native image and root.");
      return () => {};
    }
    const ownedElements = [root, picture, ...sourceElements, image, placeholder, fallback]
      .filter(Boolean);
    // Citry's reserved event and component markers must not appear on
    // or change within the owned anatomy while this client owns it.
    const frameworkMarker = (attribute) => attribute.name.startsWith("data-cid")
      || attribute.name.startsWith("data-cev");
    const markersAbsent = () => ownedElements.every((element, index) => ![...element.attributes]
      .some((attribute) => attribute.name.startsWith("data-cev") || (index > 0 && frameworkMarker(attribute))));
    const frameworkBaseline = ownedElements.map((element) => JSON.stringify(
      [...element.attributes]
        .filter(frameworkMarker)
        .map((attribute) => [attribute.name, attribute.value])
        .sort(([left], [right]) => left.localeCompare(right)),
    ));
    const token = Symbol();
    const owner = { active: true, token };
    const documentOwner = root.ownerDocument;
    const invalid = new Set();
    const tasks = new Set();
    let active = true;
    let callback = null;
    let configuration = null;
    let generation = 0;
    let status = null;
    let settled = null;
    let decodeToken = null;
    let started = false;
    let watcher = null;

    const queue = (work) => {
      const marker = {};
      tasks.add(marker);
      queueMicrotask(() => {
        if (!tasks.delete(marker) || !active || root[imageOwner] !== owner) return;
        work();
      });
    };
    const describe = (value) => value === null ? "null" : typeof value;
    const report = (name, value) => {
      if (invalid.has(name)) return;
      invalid.add(name);
      console.error(
        `[citry-ui] CImage ${name} received an invalid ${describe(value)}; retaining the last valid value.`,
      );
    };
    const text = (name, optional = false, empty = false) => {
      const supplied = props[name];
      const value = supplied === undefined || (supplied === null && !optional) ? data[name] : supplied;
      if (
        (optional && value === null)
        || (typeof value === "string" && (empty || value.length > 0) && !/[\u0000-\u001f\u007f]/.test(value))
      ) {
        invalid.delete(name);
        return value;
      }
      report(name, value);
      return configuration?.[name] ?? data[name];
    };
    const choice = (name, allowed, optional = false) => {
      const supplied = props[name];
      const value = supplied === undefined || (supplied === null && !optional) ? data[name] : supplied;
      if ((optional && value === null) || allowed.includes(value)) {
        invalid.delete(name);
        return value;
      }
      report(name, value);
      return configuration?.[name] ?? data[name];
    };
    const dimension = (name) => {
      const value = props[name] === undefined || props[name] === null ? data[name] : props[name];
      if (Number.isInteger(value) && value > 0) {
        invalid.delete(name);
        return value;
      }
      report(name, value);
      return configuration?.[name] ?? data[name];
    };
    const bool = (name) => {
      const value = props[name] === undefined || props[name] === null ? data[name] : props[name];
      if (typeof value === "boolean") {
        invalid.delete(name);
        return value;
      }
      report(name, value);
      return configuration?.[name] ?? data[name];
    };
    const resolveCallback = () => {
      const value = props.onStatusChange;
      if (value === undefined || value === null || typeof value === "function") {
        invalid.delete("onStatusChange");
        return value ?? null;
      }
      report("onStatusChange", value);
      return callback;
    };
    const resolve = () => {
      const next = {
        src: text("src"),
        alt: text("alt", false, true),
        width: dimension("width"),
        height: dimension("height"),
        srcset: text("srcset", true),
        sizes: text("sizes", true),
        loading: choice("loading", ["eager", "lazy"]),
        decoding: choice("decoding", ["auto", "sync", "async"]),
        fetchPriority: choice("fetchPriority", ["auto", "high", "low"]),
        crossOrigin: choice("crossOrigin", ["anonymous", "use-credentials"], true),
        referrerPolicy: choice("referrerPolicy", [
          "no-referrer", "no-referrer-when-downgrade", "origin",
          "origin-when-cross-origin", "same-origin", "strict-origin",
          "strict-origin-when-cross-origin", "unsafe-url",
        ], true),
        fit: choice("fit", ["contain", "cover", "fill", "none", "scale-down"]),
        position: text("position"),
        draggable: bool("draggable"),
      };
      const activeSource = (value) => typeof value === "string"
        && /^\s*(?:javascript|vbscript)\s*:/i.test(value);
      const activeSet = (value) => {
        if (typeof value !== "string") return false;
        let index = 0;
        while (index < value.length) {
          while (index < value.length && (/[\s,]/.test(value[index]))) index += 1;
          const start = index;
          while (index < value.length && !/\s/.test(value[index])) index += 1;
          const candidate = value.slice(start, index).replace(/,+$/, "");
          if (/^(?:javascript|vbscript)\s*:/i.test(candidate)) return true;
          if (index > start && value[index - 1] === ",") continue;
          let depth = 0;
          while (index < value.length) {
            const character = value[index++];
            if (character === "(") depth += 1;
            else if (character === ")" && depth) depth -= 1;
            else if (character === "," && depth === 0) break;
          }
        }
        return false;
      };
      if (activeSource(next.src)) {
        report("src", next.src);
        next.src = configuration?.src ?? data.src;
      }
      if (activeSet(next.srcset)) {
        report("srcset", next.srcset);
        next.srcset = configuration?.srcset ?? data.srcset;
      }
      const widthCandidates = typeof next.srcset === "string"
        && /(?:^|,)\s*[^,]+\s+[1-9][0-9]*w\s*(?=,|$)/.test(next.srcset);
      const autoSizes = typeof next.sizes === "string"
        && /^auto(?:\s*,|\s*$)/i.test(next.sizes.trim());
      const sourceAutoSizes = data.sources.some((source) => typeof source.sizes === "string"
        && /^auto(?:\s*,|\s*$)/i.test(source.sizes.trim()));
      if (
        (widthCandidates && !next.sizes)
        || (autoSizes && next.loading !== "lazy")
        || (sourceAutoSizes && (next.loading !== "lazy" || !autoSizes))
      ) {
        report("responsive source", next.srcset);
        next.loading = configuration?.loading ?? data.loading;
        next.srcset = configuration?.srcset ?? data.srcset;
        next.sizes = configuration?.sizes ?? data.sizes;
      }
      if (/[;{}]/.test(next.position) || next.position.includes(String.fromCharCode(92))) {
        report("position", next.position);
        next.position = configuration?.position ?? data.position;
      }
      return next;
    };
    const fingerprint = (value) => JSON.stringify([
      value.src, value.srcset, value.sizes, value.width, data.sources,
      value.crossOrigin, value.referrerPolicy,
    ]);
    const sameAttribute = (element, name, value) => value === null
      ? !element.hasAttribute(name)
      : element.getAttribute(name) === String(value);
    const runtimeAttributesValid = (element, allowed) => [...element.attributes].every((attribute) =>
      !attribute.name.startsWith("data-citry-") || allowed.includes(attribute.name));
    const frameworkMarkersValid = () => ownedElements.every((element, index) => JSON.stringify(
      [...element.attributes]
        .filter(frameworkMarker)
        .map((attribute) => [attribute.name, attribute.value])
        .sort(([left], [right]) => left.localeCompare(right)),
    ) === frameworkBaseline[index]);
    const hasForbidden = (element, names, allAria = false) => [...element.attributes].some(
      (attribute) => names.includes(attribute.name)
        || (allAria && attribute.name.startsWith("aria-")),
    );
    const sourceValid = (element, value) => element instanceof HTMLSourceElement
      && ["srcset", "media", "type", "sizes", "width", "height"].every((name) =>
        sameAttribute(element, name, value[name]))
      && [...element.attributes].every((attribute) =>
        ["srcset", "media", "type", "sizes", "width", "height"].includes(attribute.name)
        || frameworkMarker(attribute));
    const serverImageValid = () => [
      ["src", data.src], ["srcset", data.srcset], ["sizes", data.sizes], ["alt", data.alt],
      ["width", data.width], ["height", data.height], ["loading", data.loading],
      ["decoding", data.decoding], ["fetchpriority", data.fetchPriority],
      ["crossorigin", data.crossOrigin], ["referrerpolicy", data.referrerPolicy],
      ["draggable", data.draggable ? "true" : "false"],
    ].every(([name, value]) => sameAttribute(image, name, value));
    const scopeValid = () => {
      const actual = root.getRootNode();
      return root.ownerDocument === documentOwner && (actual === documentOwner
        || (actual instanceof ShadowRoot
          && actual.host.ownerDocument === documentOwner
          && actual.host.shadowRoot === actual));
    };
    const anatomyValid = (requireReady = true) => {
      const first = picture ?? image;
      const expected = [first];
      if (data.hasPlaceholder) expected.push(placeholder);
      if (data.hasFallback) expected.push(fallback);
      const children = [...root.children];
      if (!scopeValid() || !markersAbsent() || !frameworkMarkersValid()
        || children.length !== expected.length
        || children.some((child, index) => child !== expected[index])
        || root.dataset.citryUiPart !== "image-root"
        || Boolean(picture) !== Boolean(data.sources.length)
        || Boolean(placeholder) !== data.hasPlaceholder
        || Boolean(fallback) !== data.hasFallback
        || root.hasAttribute("data-has-placeholder") !== data.hasPlaceholder
        || root.hasAttribute("data-has-fallback") !== data.hasFallback
        || (!configuration && !serverImageValid())
        || !runtimeAttributesValid(root, ["data-citry-ui-part", imageReady])
        || !runtimeAttributesValid(image, ["data-citry-ui-part"])
        || hasForbidden(root, ["role", "tabindex", "hidden", "inert", "popover"], true)
        || hasForbidden(image, [
          "role", "tabindex", "hidden", "inert", "popover", "aria-hidden", "aria-label",
          "aria-labelledby", "contenteditable", "usemap", "ismap",
        ])
        || image.dataset.citryUiPart !== "image"
        || (requireReady && !root.hasAttribute(imageReady))) return false;
      if (picture) {
        if (picture.dataset.citryUiPart !== "picture"
          || !runtimeAttributesValid(picture, ["data-citry-ui-part"])
          || [...picture.attributes].some((attribute) => !(
            attribute.name === "data-citry-ui-part"
            || frameworkMarker(attribute)
          ))
          || picture.children.length !== data.sources.length + 1
          || picture.lastElementChild !== image
          || sourceElements.length !== data.sources.length
          || sourceElements.some((source, index) => !sourceValid(source, data.sources[index]))) return false;
      }
      for (const [visual, part] of [[placeholder, "placeholder"], [fallback, "fallback"]]) {
        if (visual && (visual.parentElement !== root || visual.dataset.citryUiPart !== part
          || visual.getAttribute("aria-hidden") !== "true" || !visual.hasAttribute("inert")
          || (!started && !previous && !visual.hidden)
          || visual.querySelector(
            "a[href],area[href],button,details,embed,iframe,img,input,label,object,select,textarea,summary,[contenteditable]:not([contenteditable='false']),[tabindex],audio[controls],video[controls]",
          )
          || !runtimeAttributesValid(visual, ["data-citry-ui-part"])
          || [...visual.attributes].some((attribute) => !(
            ["data-citry-ui-part", "hidden", "inert", "aria-hidden"].includes(attribute.name)
            || frameworkMarker(attribute)
          )))) return false;
      }
      if (configuration && (
        !sameAttribute(image, "src", configuration.src)
        || !sameAttribute(image, "srcset", configuration.srcset)
        || !sameAttribute(image, "sizes", configuration.sizes)
        || !sameAttribute(image, "alt", configuration.alt)
        || !sameAttribute(image, "width", configuration.width)
        || !sameAttribute(image, "height", configuration.height)
        || !sameAttribute(image, "loading", configuration.loading)
        || !sameAttribute(image, "decoding", configuration.decoding)
        || !sameAttribute(image, "fetchpriority", configuration.fetchPriority)
        || !sameAttribute(image, "crossorigin", configuration.crossOrigin)
        || !sameAttribute(image, "referrerpolicy", configuration.referrerPolicy)
        || !sameAttribute(image, "draggable", configuration.draggable ? "true" : "false")
        || root.dataset.fit !== configuration.fit
        || root.style.getPropertyValue("--_cui-image-input-fit") !== configuration.fit
        || root.style.getPropertyValue("--_cui-image-input-position") !== configuration.position
        || root.dataset.status !== status
        || (placeholder && placeholder.hidden !== (status !== "loading"))
        || (fallback && fallback.hidden !== (status !== "error"))
      )) return false;
      return true;
    };
    const setAttribute = (name, value) => {
      if (value === null) image.removeAttribute(name);
      else if (image.getAttribute(name) !== String(value)) image.setAttribute(name, String(value));
    };
    const apply = (next) => {
      setAttribute("alt", next.alt);
      setAttribute("width", next.width);
      setAttribute("height", next.height);
      setAttribute("loading", next.loading);
      setAttribute("decoding", next.decoding);
      setAttribute("fetchpriority", next.fetchPriority);
      setAttribute("crossorigin", next.crossOrigin);
      setAttribute("referrerpolicy", next.referrerPolicy);
      setAttribute("draggable", next.draggable ? "true" : "false");
      setAttribute("srcset", next.srcset);
      setAttribute("sizes", next.sizes);
      setAttribute("src", next.src);
      root.dataset.fit = next.fit;
      root.style.setProperty("--_cui-image-input-fit", next.fit);
      root.style.setProperty("--_cui-image-input-position", next.position);
    };
    const detail = (nextStatus) => ({
      status: nextStatus,
      src: configuration.src,
      current_src: image.currentSrc || "",
      natural_width: image.naturalWidth,
      natural_height: image.naturalHeight,
    });
    const syncVisuals = () => {
      if (placeholder) placeholder.hidden = !(status === "loading");
      if (fallback) fallback.hidden = !(status === "error");
    };
    const notify = (nextStatus, currentGeneration) => {
      const snapshot = detail(nextStatus);
      queue(() => {
        if (currentGeneration !== generation) return;
        callback?.(snapshot);
      });
    };
    const setStatus = (nextStatus, currentGeneration, force = false) => {
      if (!force && status === nextStatus && settled
        && settled.currentSrc === image.currentSrc
        && settled.width === image.naturalWidth
        && settled.height === image.naturalHeight) return;
      status = nextStatus;
      settled = {
        currentSrc: image.currentSrc,
        width: image.naturalWidth,
        height: image.naturalHeight,
      };
      root.dataset.status = nextStatus;
      syncVisuals();
      notify(nextStatus, currentGeneration);
    };
    const accept = (nextStatus, currentGeneration, currentSrc) => {
      queue(() => {
        if (
          currentGeneration !== generation
          || image.currentSrc !== currentSrc
          || root[imageOwner] !== owner
        ) return;
        setStatus(nextStatus, currentGeneration);
      });
    };
    const reconcileComplete = (currentGeneration) => {
      if (currentGeneration !== generation || !image.complete || !image.currentSrc) return;
      const currentSrc = image.currentSrc;
      if (image.naturalWidth > 0) {
        accept("loaded", currentGeneration, currentSrc);
        return;
      }
      const probe = {};
      decodeToken = probe;
      if (typeof image.decode !== "function") {
        teardown(true);
        return;
      }
      try {
        const decoding = image.decode();
        const then = decoding?.then;
        if (typeof then !== "function") {
          teardown(true);
          return;
        }
        then.call(
          decoding,
          () => {
            if (decodeToken === probe) accept("loaded", currentGeneration, currentSrc);
          },
          () => {
            if (
              decodeToken === probe
              && image.complete
              && image.currentSrc === currentSrc
            ) accept("error", currentGeneration, currentSrc);
          },
        );
      } catch {
        teardown(true);
      }
    };
    const onLoad = (event) => {
      if (!event.isTrusted) return;
      const currentSrc = image.currentSrc;
      if (!currentSrc) return;
      decodeToken = null;
      accept("loaded", generation, currentSrc);
    };
    const onError = (event) => {
      if (!event.isTrusted) return;
      decodeToken = null;
      accept("error", generation, image.currentSrc);
    };
    if (!anatomyValid(false)) {
      abortHandoff(previous);
      console.error(
        "[citry-ui] CImage received invalid native anatomy; leaving the server fallback unchanged.",
      );
      return () => {};
    }
    const retained = Boolean(previous
      && previous.root === root
      && previous.documentOwner === documentOwner
      && previous.picture === picture
      && previous.image === image
      && previous.sourceElements.length === sourceElements.length
      && sourceElements.every((source, index) => source === previous.sourceElements[index]));
    if (previous && !retained) abortHandoff(previous);
    if (retained) delete root[handoffKey];
    image.addEventListener("load", onLoad);
    image.addEventListener("error", onError);
    root[imageOwner] = owner;

    const teardown = (diagnose = false) => {
      if (!active) return;
      active = false;
      owner.active = false;
      generation += 1;
      decodeToken = null;
      tasks.clear();
      image.removeEventListener("load", onLoad);
      image.removeEventListener("error", onError);
      watcher?.cleanup();
      if (root[imageOwner] === owner) {
        delete root[imageOwner];
        root.removeAttribute(imageReady);
        root.removeAttribute("data-status");
        if (placeholder) placeholder.hidden = true;
        if (fallback) fallback.hidden = true;
      }
      if (diagnose) console.error(
        "[citry-ui] CImage lost its owned native anatomy; component behavior was removed.",
      );
    };
    const registration = {
      notify() {
        if (!active) return;
        if (configuration) {
          if (root.style.getPropertyValue("--_cui-image-input-fit") !== configuration.fit) {
            root.style.setProperty("--_cui-image-input-fit", configuration.fit);
          }
          if (root.style.getPropertyValue("--_cui-image-input-position") !== configuration.position) {
            root.style.setProperty("--_cui-image-input-position", configuration.position);
          }
        }
        if (!root.isConnected) {
          teardown();
          return;
        }
        if (!anatomyValid()) {
          teardown(true);
          return;
        }
        watcher.refresh();
      },
    };
    watcher = watchImage(root, registration);

    effect(() => {
      if (!active) return;
      callback = resolveCallback();
      const next = resolve();
      const nextFingerprint = fingerprint(next);
      if (!started && retained && previous.fingerprint === nextFingerprint) {
        configuration = next;
        generation = previous.generation;
        status = previous.status;
        settled = previous.settled;
        started = true;
        apply(next);
        root.dataset.status = status;
        syncVisuals();
        root.setAttribute(imageReady, "");
        return;
      }
      if (!started && retained) generation = previous.generation;
      const changed = configuration === null || fingerprint(configuration) !== nextFingerprint;
      configuration = next;
      apply(next);
      if (!started || changed) {
        started = true;
        generation += 1;
        decodeToken = null;
        setStatus("loading", generation, true);
        const currentGeneration = generation;
        queue(() => reconcileComplete(currentGeneration));
      }
      root.setAttribute(imageReady, "");
    });

    return () => {
      if (!active) return;
      const ownsRoot = root[imageOwner] === owner;
      const canHandoff = ownsRoot && root.isConnected && anatomyValid();
      const record = canHandoff ? {
        root, picture, image, sourceElements: [...sourceElements], placeholder, fallback,
        documentOwner,
        fingerprint: fingerprint(configuration), configuration, generation,
        status, settled, abort: null,
      } : null;
      active = false;
      owner.active = false;
      generation += 1;
      decodeToken = null;
      tasks.clear();
      image.removeEventListener("load", onLoad);
      image.removeEventListener("error", onError);
      watcher?.cleanup();
      if (!ownsRoot) return;
      delete root[imageOwner];
      if (record) {
        // The runtime runs this cleanup before it knows whether the
        // revision keeps or unmounts this root, so the ready marker goes
        // now. A retained root restores it from the handoff record when
        // its next server-render callback runs.
        root.removeAttribute(imageReady);
        root[handoffKey] = record;
        record.abort = setTimeout(() => {
          if (root[handoffKey] === record && !root[imageOwner]?.active) abortHandoff(record);
        }, 1000);
        // Vue removes a keyed old root just after running its cleanup.
        // If the root is detached, the handoff cannot be consumed by a
        // later render, so clear its readiness marker after this patch.
        // A connected root keeps the short handoff window used by
        // same-root updates.
        globalThis.setTimeout(() => {
          if (root[handoffKey] === record && !root.isConnected && !root[imageOwner]?.active) {
            abortHandoff(record);
          }
        }, 0);
        return;
      }
      root.removeAttribute(imageReady);
      root.removeAttribute("data-status");
      if (placeholder) placeholder.hidden = true;
      if (fallback) fallback.hidden = true;
      delete root[handoffKey];
    };
  },
});

})();