(function () {
  "use strict";

  const FORMAT = "citry-i18n-rich-relocation-research/2";

  function reject(code, message) {
    const error = new TypeError(`[Citry] i18n rich relocation: ${message}`);
    error.code = code;
    throw error;
  }

  function requireElement(value, code, name) {
    if (!(value instanceof Element)) reject(code, `${name} must be a live Element.`);
    if (!value.isConnected) reject(code, `${name} is no longer connected.`);
    return value;
  }

  function boundaryForPhysical(physical, destination, occurrenceKey) {
    if (!(physical.start instanceof Comment
      && physical.end instanceof Comment
      && physical.start.isConnected
      && physical.end.isConnected
      && physical.start.data === physical.startMarker
      && physical.end.data === physical.endMarker)) {
      reject("I18N_RICH_RANGE_CORRUPT", `occurrence '${occurrenceKey}' lost its live range caps.`);
    }
    const boundary = physical.start.parentElement;
    if (
      !(boundary instanceof HTMLElement)
      || boundary.tagName !== "BDI"
      || boundary.getAttribute("dir") !== "auto"
      || boundary.hasAttribute("lang")
      || boundary.parentElement !== destination
      || physical.end.parentElement !== boundary
    ) {
      reject(
        "I18N_RICH_BOUNDARY_INVALID",
        `occurrence '${occurrenceKey}' needs one direct <bdi dir="auto"> boundary with no lang override.`,
      );
    }
    return boundary;
  }

  function normalizeRegistration(registration, destination) {
    if (registration === null || typeof registration !== "object") {
      reject("I18N_RICH_REGISTRATION_INVALID", "the component registration is missing.");
    }
    const route = registration.graph;
    if (route === null || typeof route !== "object" || typeof route.revision !== "string") {
      reject("I18N_RICH_REGISTRATION_INVALID", "the component registration has no graph route.");
    }
    if (!route.logicalInstance?.active || !route.instance?.active) {
      reject("I18N_RICH_REGISTRATION_STALE", "the component occurrence is no longer active.");
    }
    const output = requireElement(destination, "I18N_RICH_DESTINATION_INVALID", "the destination");
    if (!Array.isArray(registration.els) || !registration.els.includes(output)) {
      reject("I18N_RICH_DESTINATION_INVALID", "the destination is not a root of the registered component.");
    }
    const state = Citry.manager.ownership.get(route.revision);
    if (state === null) {
      reject("I18N_RICH_REGISTRATION_STALE", "the ownership revision is no longer live.");
    }
    const graphId = route.instance.graphId;
    if (!Number.isSafeInteger(graphId) || graphId < 0) {
      reject("I18N_RICH_REGISTRATION_INVALID", "the component route has an invalid graph ID.");
    }
    const declarations = registration.data?.occurrences;
    if (!Array.isArray(declarations) || declarations.length === 0) {
      reject("I18N_RICH_REGISTRATION_INVALID", "the component declared no Slot occurrences.");
    }

    const occurrences = new Map();
    for (const declaration of declarations) {
      if (
        declaration === null
        || typeof declaration !== "object"
        || typeof declaration.key !== "string"
        || declaration.key.length === 0
        || typeof declaration.slot !== "string"
        || declaration.slot.length === 0
        || !Number.isSafeInteger(declaration.regionId)
        || declaration.regionId < 1
      ) {
        reject("I18N_RICH_REGISTRATION_INVALID", "one Slot occurrence declaration is invalid.");
      }
      if (occurrences.has(declaration.key)) {
        reject("I18N_RICH_OCCURRENCE_DUPLICATE", `occurrence '${declaration.key}' is declared twice.`);
      }
      const regionKey = `g${graphId}:r:${declaration.regionId}`;
      const region = state.registry.slotRegions.get(regionKey);
      if (region === undefined || region.receiverRenderId !== registration.id) {
        reject("I18N_RICH_OCCURRENCE_MISSING", `occurrence '${declaration.key}' has no owned Slot region.`);
      }
      const fill = state.registry.fills.get(`g${graphId}:f:${region.fillId}`);
      if (
        fill === undefined
        || fill.receiverRenderId !== registration.id
        || fill.slot !== declaration.slot
        || fill.policy !== "template"
        || fill.ownerRenderId === null
      ) {
        reject("I18N_RICH_SOURCE_MISMATCH", `occurrence '${declaration.key}' has the wrong fill source.`);
      }
      const placements = state.registry.physicalPlacements.get(region.key) || [];
      if (placements.length !== 1) {
        reject(
          "I18N_RICH_SHARED_PLACEMENT",
          `occurrence '${declaration.key}' must have exactly one physical placement.`,
        );
      }
      const physical = placements[0];
      const boundary = boundaryForPhysical(physical, output, declaration.key);
      occurrences.set(declaration.key, { boundary, declaration, fill, physical, region });
    }
    return { graphId, occurrences, output, registration, revision: route.revision, state };
  }

  function validateDisjointRanges(records) {
    const positionsByParent = new Map();
    const intervals = records.map(({ key, value }) => {
      const parent = value.physical.start.parentNode;
      let positions = positionsByParent.get(parent);
      if (positions === undefined) {
        positions = new Map(Array.from(parent.childNodes, (node, index) => [node, index]));
        positionsByParent.set(parent, positions);
      }
      const start = positions.get(value.physical.start);
      const end = positions.get(value.physical.end);
      if (start === undefined || end === undefined || start > end) {
        reject("I18N_RICH_RANGE_CORRUPT", `occurrence '${key}' has invalid cap order.`);
      }
      return { end, key, parent, start };
    }).sort((left, right) => left.start - right.start);
    for (let index = 1; index < intervals.length; index += 1) {
      if (
        intervals[index].parent === intervals[index - 1].parent
        && intervals[index].start <= intervals[index - 1].end
      ) {
        reject("I18N_RICH_RANGE_OVERLAP", "two Slot occurrence ranges overlap.");
      }
    }
    const boundaries = new Set(records.map(({ value }) => value.boundary));
    if (boundaries.size !== records.length) {
      reject("I18N_RICH_RANGE_OVERLAP", "two Slot occurrences share one structural boundary.");
    }
    for (const { key, value } of records) {
      if (value.boundary.firstChild !== value.physical.start || value.boundary.lastChild !== value.physical.end) {
        reject("I18N_RICH_BOUNDARY_INVALID", `occurrence '${key}' does not fill its structural boundary.`);
      }
    }
  }

  function captureFocus(destination) {
    const element = document.activeElement;
    if (!(element instanceof HTMLElement) || !destination.contains(element)) return null;
    const snapshot = { element, end: null, start: null };
    if (element instanceof HTMLInputElement || element instanceof HTMLTextAreaElement) {
      snapshot.start = element.selectionStart;
      snapshot.end = element.selectionEnd;
    }
    return snapshot;
  }

  function restoreFocus(snapshot, fallback) {
    if (snapshot?.element?.isConnected) {
      snapshot.element.focus({ preventScroll: true });
      if (
        snapshot.start !== null
        && (snapshot.element instanceof HTMLInputElement || snapshot.element instanceof HTMLTextAreaElement)
      ) {
        snapshot.element.setSelectionRange(snapshot.start, snapshot.end);
      }
      return;
    }
    if (fallback instanceof HTMLElement && fallback.isConnected) fallback.focus({ preventScroll: true });
  }

  function validateSegments(segments, occurrences) {
    if (!Array.isArray(segments)) {
      reject("I18N_RICH_SEGMENTS_INVALID", "the new message segments must be an array.");
    }
    const used = new Set();
    const normalized = segments.map((segment) => {
      if (segment?.type === "text" && typeof segment.value === "string") {
        return { node: document.createTextNode(segment.value), type: "text" };
      }
      if (segment?.type !== "occurrence" || typeof segment.key !== "string") {
        reject("I18N_RICH_SEGMENTS_INVALID", "one new message segment is invalid.");
      }
      if (used.has(segment.key)) {
        reject("I18N_RICH_OCCURRENCE_DUPLICATE", `occurrence '${segment.key}' appears twice in the commit.`);
      }
      const occurrence = occurrences.get(segment.key);
      if (occurrence === undefined) {
        reject("I18N_RICH_OCCURRENCE_MISSING", `occurrence '${segment.key}' was not rendered by the server.`);
      }
      used.add(segment.key);
      return { key: segment.key, occurrence, type: "occurrence" };
    });
    if (used.size !== occurrences.size) {
      reject("I18N_RICH_OCCURRENCE_MISSING", "the new message omits a server-rendered Slot occurrence.");
    }
    return normalized;
  }

  function prepare(registration, destination, segments) {
    const normalized = normalizeRegistration(registration, destination);
    const normalizedSegments = validateSegments(segments, normalized.occurrences);
    validateDisjointRanges(Array.from(normalized.occurrences, ([key, value]) => ({ key, value })));
    let consumed = false;

    return Object.freeze({
      format: FORMAT,
      commit(options) {
        if (consumed) reject("I18N_RICH_PLAN_CONSUMED", "a relocation plan can be committed only once.");
        consumed = true;
        const provider = requireElement(options?.provider, "I18N_RICH_PROVIDER_INVALID", "the provider");
        if (!provider.contains(normalized.output)) {
          reject("I18N_RICH_PROVIDER_INVALID", "the provider does not own the rich message output.");
        }
        if (typeof options.lang !== "string" || !/^[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*$/.test(options.lang)) {
          reject("I18N_RICH_CONTEXT_INVALID", "the locale is not a canonical locale identifier.");
        }
        if (options.direction !== "ltr" && options.direction !== "rtl") {
          reject("I18N_RICH_CONTEXT_INVALID", "direction must be 'ltr' or 'rtl'.");
        }
        const current = normalizeRegistration(normalized.registration, normalized.output);
        validateDisjointRanges(Array.from(current.occurrences, ([key, value]) => ({ key, value })));
        for (const [key, occurrence] of normalized.occurrences) {
          const currentOccurrence = current.occurrences.get(key);
            if (
              currentOccurrence?.physical !== occurrence.physical
              || currentOccurrence.boundary !== occurrence.boundary
            ) {
              reject("I18N_RICH_PLAN_STALE", `occurrence '${key}' changed after preflight.`);
          }
        }

        const oldNodes = Array.from(normalized.output.childNodes);
        const oldLang = provider.getAttribute("lang");
        const oldDirection = provider.getAttribute("dir");
        const focus = captureFocus(normalized.output);
        const fragment = document.createDocumentFragment();
        try {
          for (const segment of normalizedSegments) {
            if (segment.type === "text") {
              fragment.append(segment.node);
            } else {
              fragment.append(segment.occurrence.boundary);
            }
          }
          provider.setAttribute("lang", options.lang);
          provider.setAttribute("dir", options.direction);
          normalized.output.replaceChildren(fragment);
          restoreFocus(focus, options.focusFallback || provider);
        } catch (error) {
          normalized.output.replaceChildren(...oldNodes);
          if (oldLang === null) provider.removeAttribute("lang");
          else provider.setAttribute("lang", oldLang);
          if (oldDirection === null) provider.removeAttribute("dir");
          else provider.setAttribute("dir", oldDirection);
          restoreFocus(focus, options.focusFallback || provider);
          throw error;
        }
        return Object.freeze({ moved: normalized.occurrences.size, revision: normalized.revision });
      },
    });
  }

  globalThis.CitryRichRelocationCandidate = Object.freeze({ FORMAT, prepare });
})();
