import { FluentBundle, FluentResource } from "@fluent/bundle";

const MARKER_PREFIX = "__CITRY_SLOT_";
const SLOT_NAMES = ["help_link", "terms_link"];
const DIRECTIONS = { "ar": "rtl", "en-US": "ltr" };


class ProbeError extends Error {
  constructor(code, message) {
    super(message);
    this.code = code;
  }
}


function require(condition, message) {
  if (!condition) throw new Error(message);
}


function native(value) {
  return value?.valueOf?.() ?? value;
}


function randomHex() {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return [...bytes].map((value) => value.toString(16).padStart(2, "0")).join("");
}


function markerFor(hex, slotName) {
  return `${MARKER_PREFIX}${hex}_${slotName}__`;
}


function allocateMarkers(source, scalarValues, slotNames, nextHex = randomHex) {
  const markers = {};
  const accepted = new Set();
  let attempts = 0;
  for (const slotName of slotNames) {
    let marker = null;
    for (let retry = 0; retry < 16; retry += 1) {
      attempts += 1;
      const candidate = markerFor(nextHex(), slotName);
      const collides = source.includes(candidate)
        || scalarValues.some((value) => typeof value === "string" && value.includes(candidate))
        || accepted.has(candidate);
      if (!collides) {
        marker = candidate;
        break;
      }
    }
    if (marker === null) {
      throw new ProbeError("I18N_SLOT_MARKER_EXHAUSTED", `could not allocate a marker for ${slotName}`);
    }
    markers[slotName] = marker;
    accepted.add(marker);
  }
  return { attempts, markers };
}


function slotFunction(positional, named) {
  if (Object.keys(named).length !== 0 || positional.length !== 1) {
    throw new TypeError("SLOT accepts exactly one positional argument");
  }
  const marker = native(positional[0]);
  if (typeof marker !== "string" || !marker.startsWith(MARKER_PREFIX)) {
    throw new TypeError("SLOT accepts only a current Citry marker");
  }
  return marker;
}


function splitFormatted(value, markers, requiredSlotNames) {
  const markerEntries = Object.entries(markers);
  const counts = Object.fromEntries(requiredSlotNames.map((name) => [name, 0]));
  const tokens = [];
  let cursor = 0;
  while (cursor < value.length) {
    let match = null;
    for (const [name, marker] of markerEntries) {
      const index = value.indexOf(marker, cursor);
      if (index !== -1 && (match === null || index < match.index)) match = { index, marker, name };
    }
    if (match === null) {
      if (cursor < value.length) tokens.push({ kind: "text", value: value.slice(cursor) });
      break;
    }
    if (match.index > cursor) tokens.push({ kind: "text", value: value.slice(cursor, match.index) });
    const occurrence = counts[match.name];
    counts[match.name] += 1;
    tokens.push({ kind: "slot", name: match.name, occurrence });
    cursor = match.index + match.marker.length;
  }
  for (const name of requiredSlotNames) {
    if (counts[name] === 0) {
      throw new ProbeError("I18N_SLOT_MISSING", `rich message did not use required Slot $${name}`);
    }
  }
  const leakedMarker = tokens.some((token) => token.kind === "text" && token.value.includes(MARKER_PREFIX));
  if (leakedMarker) throw new ProbeError("I18N_SLOT_MARKER_LEAK", "an unknown Slot marker survived formatting");
  return { counts, tokens };
}


function formatRich(locale, source, scalarValues = {}, nextHex = randomHex) {
  const allocation = allocateMarkers(source, Object.values(scalarValues), SLOT_NAMES, nextHex);
  const bundle = new FluentBundle(locale, {
    functions: { SLOT: slotFunction },
    useIsolating: false,
  });
  const parseErrors = bundle.addResource(new FluentResource(source));
  if (parseErrors.length !== 0) {
    throw new ProbeError("I18N_BROWSER_ARTIFACT", parseErrors.map(String).join("; "));
  }
  const message = bundle.getMessage("rich");
  if (message?.value === null || message?.value === undefined) {
    throw new ProbeError("I18N_BROWSER_ARTIFACT", "compiled artifact does not define rich");
  }
  const errors = [];
  const value = bundle.formatPattern(message.value, { ...scalarValues, ...allocation.markers }, errors);
  if (errors.length !== 0) {
    throw new ProbeError("I18N_BROWSER_FORMAT", errors.map(String).join("; "));
  }
  const split = splitFormatted(value, allocation.markers, SLOT_NAMES);
  return { ...allocation, ...split };
}


function nodesInclusive(start, end) {
  const nodes = [];
  let current = start;
  while (current !== null) {
    const next = current.nextSibling;
    nodes.push(current);
    if (current === end) return nodes;
    current = next;
  }
  throw new Error("Slot ownership range lost its closing cap");
}


function nodeInside(instance, target) {
  return nodesInclusive(instance.start, instance.end).some(
    (node) => node === target || (node instanceof Element && node.contains(target)),
  );
}


function moveInstance(instance, fragment) {
  for (const node of nodesInclusive(instance.start, instance.end)) fragment.append(node);
}


function clearBetween(start, end) {
  let current = start.nextSibling;
  while (current !== null && current !== end) {
    const next = current.nextSibling;
    current.remove();
    current = next;
  }
}


function captureFocus(element) {
  if (!(element instanceof HTMLElement)) return null;
  return {
    element,
    selectionDirection: element instanceof HTMLInputElement ? element.selectionDirection : null,
    selectionEnd: element instanceof HTMLInputElement ? element.selectionEnd : null,
    selectionStart: element instanceof HTMLInputElement ? element.selectionStart : null,
  };
}


function restoreFocus(snapshot) {
  if (snapshot === null || !snapshot.element.isConnected) return false;
  snapshot.element.focus({ preventScroll: true });
  if (
    snapshot.element instanceof HTMLInputElement
    && snapshot.selectionStart !== null
    && snapshot.selectionEnd !== null
  ) {
    snapshot.element.setSelectionRange(
      snapshot.selectionStart,
      snapshot.selectionEnd,
      snapshot.selectionDirection ?? undefined,
    );
  }
  return document.activeElement === snapshot.element;
}


class RichRegion {
  constructor(provider, tracker) {
    this.provider = provider;
    this.tracker = tracker;
    this.instances = new Map();
    this.start = document.createComment("citry:i18n-message:start:rich");
    this.end = document.createComment("citry:i18n-message:end:rich");
    provider.append(this.start, this.end);
  }

  createInstance(name, key) {
    const generation = (this.tracker.generations[key] ?? 0) + 1;
    this.tracker.generations[key] = generation;
    const instanceId = `${key}#${generation}`;
    const start = document.createComment(`citry:i18n-slot:start:${key}`);
    const end = document.createComment(`citry:i18n-slot:end:${key}`);
    const instance = {
      cleaned: false,
      end,
      input: null,
      instanceId,
      key,
      name,
      nodes: [],
      start,
      state: { clicks: 0 },
    };
    if (name === "terms_link") {
      const opening = document.createTextNode("[");
      const label = document.createElement("label");
      label.dataset.slotKey = key;
      label.append("Terms ");
      const input = document.createElement("input");
      input.dataset.slotInput = key;
      input.value = `initial:${key}`;
      label.append(input);
      const closing = document.createTextNode("]");
      instance.input = input;
      instance.nodes = [opening, label, closing];
    } else if (name === "help_link") {
      const button = document.createElement("button");
      button.dataset.slotKey = key;
      button.lang = "he";
      button.dir = "rtl";
      button.textContent = "עזרה";
      button.addEventListener("click", () => {
        instance.state.clicks += 1;
      });
      instance.nodes = [button];
    } else {
      throw new Error(`unknown Slot factory ${name}`);
    }
    this.tracker.created.push(instanceId);
    return instance;
  }

  cleanup(instance) {
    require(!instance.cleaned, `Slot instance cleaned twice: ${instance.instanceId}`);
    instance.cleaned = true;
    this.tracker.cleaned.push(instance.instanceId);
    this.tracker.cleanupWasConnected.push(nodesInclusive(instance.start, instance.end).every((node) => node.isConnected));
  }

  commit(prepared, context) {
    const plannedKeys = prepared.tokens
      .filter((token) => token.kind === "slot")
      .map((token) => `rich:${token.name}:${token.occurrence}`);
    require(plannedKeys.length === new Set(plannedKeys).size, "duplicate rich Slot occurrence key");

    const active = captureFocus(document.activeElement);
    const activeOwner = active === null
      ? null
      : [...this.instances.values()].find((instance) => nodeInside(instance, active.element)) ?? null;
    const nextInstances = new Map();
    const fragment = document.createDocumentFragment();
    for (const token of prepared.tokens) {
      if (token.kind === "text") {
        fragment.append(document.createTextNode(token.value));
        continue;
      }
      const key = `rich:${token.name}:${token.occurrence}`;
      const instance = this.instances.get(key) ?? this.createInstance(token.name, key);
      nextInstances.set(key, instance);
      if (instance.start.parentNode === null) {
        fragment.append(instance.start, ...instance.nodes, instance.end);
      } else {
        moveInstance(instance, fragment);
      }
    }

    const removed = [...this.instances.values()].filter((instance) => !nextInstances.has(instance.key));
    const activeWasRemoved = activeOwner !== null && removed.includes(activeOwner);
    for (const instance of removed) this.cleanup(instance);
    clearBetween(this.start, this.end);
    this.provider.lang = context.locale;
    this.provider.dir = context.direction;
    this.provider.insertBefore(fragment, this.end);
    this.instances = nextInstances;

    if (activeWasRemoved) {
      this.provider.focus({ preventScroll: true });
    } else if (activeOwner !== null) {
      require(restoreFocus(active), "focus did not return to the surviving Slot occurrence");
    }
    this.provider.dispatchEvent(new CustomEvent("citry:i18n-committed", { detail: context }));
  }

  keysInDomOrder() {
    const keys = [];
    let current = this.start.nextSibling;
    while (current !== null && current !== this.end) {
      if (current.nodeType === Node.COMMENT_NODE && current.data.startsWith("citry:i18n-slot:start:")) {
        keys.push(current.data.slice("citry:i18n-slot:start:".length));
      }
      current = current.nextSibling;
    }
    return keys;
  }

  destroy() {
    const active = document.activeElement;
    const ownedFocus = active instanceof HTMLElement
      && [...this.instances.values()].some((instance) => nodeInside(instance, active));
    for (const instance of this.instances.values()) this.cleanup(instance);
    clearBetween(this.start, this.end);
    this.start.remove();
    this.end.remove();
    this.instances.clear();
    if (ownedFocus) this.provider.focus({ preventScroll: true });
  }
}


class RichService {
  constructor(region, sources) {
    this.region = region;
    this.sources = sources;
  }

  switchLocale(targetLocale, options = {}) {
    const resolvedLocale = options.resolvedLocale ?? targetLocale;
    if (resolvedLocale !== targetLocale) {
      throw new ProbeError(
        "I18N_RICH_LANGUAGE_MISMATCH",
        `wrapperless rich output for ${targetLocale} resolved from ${resolvedLocale}`,
      );
    }
    const source = options.source ?? this.sources[resolvedLocale];
    if (source === undefined) throw new ProbeError("I18N_BROWSER_ARTIFACT", `missing ${resolvedLocale}`);
    const prepared = formatRich(resolvedLocale, source);
    this.region.commit(prepared, { direction: DIRECTIONS[targetLocale], locale: targetLocale });
    return prepared;
  }
}


function snapshot(provider, tracker) {
  return JSON.stringify({
    cleaned: tracker.cleaned,
    created: tracker.created,
    dir: provider.dir,
    html: provider.innerHTML,
    lang: provider.lang,
  });
}


function expectProbeError(code, operation) {
  try {
    operation();
  } catch (error) {
    require(error instanceof ProbeError, `expected ProbeError, got ${error}`);
    require(error.code === code, `expected ${code}, got ${error.code}`);
    return error.code;
  }
  throw new Error(`operation did not raise ${code}`);
}


function allTrue(record) {
  return Object.values(record).every((value) => value === true);
}


async function runLifecycleProbe(sources) {
  document.body.replaceChildren();
  const provider = document.createElement("section");
  provider.id = "provider";
  provider.tabIndex = -1;
  document.body.append(provider);
  const tracker = { cleaned: [], cleanupWasConnected: [], created: [], generations: {} };
  const region = new RichRegion(provider, tracker);
  const service = new RichService(region, sources);
  const commitSnapshots = [];
  provider.addEventListener("citry:i18n-committed", () => {
    commitSnapshots.push({ dir: provider.dir, keys: region.keysInDomOrder(), lang: provider.lang });
  });

  const initial = service.switchLocale("en-US");
  const terms0 = region.instances.get("rich:terms_link:0");
  const terms1 = region.instances.get("rich:terms_link:1");
  const help0 = region.instances.get("rich:help_link:0");
  require(terms0?.input instanceof HTMLInputElement, "first terms Slot did not render an input");
  require(terms1?.input instanceof HTMLInputElement, "second terms Slot did not render an input");
  require(help0 !== undefined, "help Slot did not render");
  terms0.input.value = "draft-zero";
  terms1.input.value = "draft-one";
  terms1.input.focus();
  terms1.input.setSelectionRange(1, 4);
  help0.nodes[0].click();
  help0.nodes[0].click();

  const observedStates = [];
  const observer = new MutationObserver(() => {
    observedStates.push({ dir: provider.dir, keys: region.keysInDomOrder(), lang: provider.lang });
  });
  observer.observe(provider, { attributes: true, childList: true, subtree: true });
  const arabic = service.switchLocale("ar");
  await Promise.resolve();
  const terms2First = region.instances.get("rich:terms_link:2");
  require(terms2First?.input instanceof HTMLInputElement, "third terms Slot was not created");
  help0.nodes[0].click();

  const expectedArabicOrder = [
    "rich:help_link:0",
    "rich:terms_link:0",
    "rich:terms_link:1",
    "rich:terms_link:2",
  ];
  const arabicObserverWasComplete = observedStates.length > 0 && observedStates.every(
    (state) => state.lang === "ar" && state.dir === "rtl"
      && JSON.stringify(state.keys) === JSON.stringify(expectedArabicOrder),
  );
  const focusAndSelectionSurvivedMove = document.activeElement === terms1.input
    && terms1.input.selectionStart === 1
    && terms1.input.selectionEnd === 4;

  terms2First.input.focus();
  const beforeRemovalCleanup = tracker.cleaned.length;
  service.switchLocale("en-US");
  await Promise.resolve();
  const removedFocusedSlotCleaned = !terms2First.input.isConnected
    && tracker.cleaned.length === beforeRemovalCleanup + 1
    && document.activeElement === provider;

  service.switchLocale("ar");
  const terms2Second = region.instances.get("rich:terms_link:2");
  require(terms2Second?.input instanceof HTMLInputElement, "third terms Slot was not recreated");
  service.switchLocale("en-US");

  const beforeFailure = snapshot(provider, tracker);
  const missingCode = expectProbeError(
    "I18N_SLOT_MISSING",
    () => service.switchLocale("ar", { source: sources.missing }),
  );
  const missingWasAtomic = snapshot(provider, tracker) === beforeFailure;
  const fallbackCode = expectProbeError(
    "I18N_RICH_LANGUAGE_MISMATCH",
    () => service.switchLocale("ar", { resolvedLocale: "en-US" }),
  );
  const fallbackWasAtomic = snapshot(provider, tracker) === beforeFailure;

  const freshA = formatRich("en-US", sources["en-US"]);
  const freshB = formatRich("en-US", sources["en-US"]);
  const freshMarkerSets = new Set(Object.values(freshA.markers));
  const markersAreFresh = Object.values(freshB.markers).every((marker) => !freshMarkerSets.has(marker));

  const zero = "00".repeat(16);
  const one = "11".repeat(16);
  const sequence = [zero, one, "22".repeat(16), "33".repeat(16)];
  const forced = allocateMarkers(
    `${sources["en-US"]}\n# ${markerFor(zero, "help_link")}`,
    [markerFor(one, "help_link")],
    SLOT_NAMES,
    () => sequence.shift(),
  );

  const helpButton = help0.nodes[0];
  const plainArabicTextWasDirect = [...provider.childNodes].some(
    (node) => node.nodeType === Node.TEXT_NODE && node.textContent.includes("Before"),
  );
  const gates = {
    application_language_on_slot_survived: helpButton.lang === "he" && helpButton.dir === "rtl",
    catalog_markup_stayed_text: provider.querySelector("unsafe, img, script") === null
      && provider.textContent.includes("<unsafe>"),
    collision_retry_worked: forced.attempts === 4,
    commit_event_saw_complete_state: commitSnapshots.some(
      (state) => state.lang === "ar" && state.dir === "rtl"
        && JSON.stringify(state.keys) === JSON.stringify(expectedArabicOrder),
    ),
    existing_occurrences_kept_dom_identity: region.instances.get("rich:terms_link:0") === terms0
      && region.instances.get("rich:terms_link:1") === terms1
      && region.instances.get("rich:help_link:0") === help0,
    focus_and_selection_survived_move: focusAndSelectionSurvivedMove,
    focus_was_rehomed_when_occurrence_disappeared: removedFocusedSlotCleaned,
    inherited_slot_followed_provider: terms0.input.closest("[lang]") === provider,
    marker_per_fill_was_distinct: new Set(Object.values(initial.markers)).size === SLOT_NAMES.length,
    markers_changed_per_resolution: markersAreFresh,
    markers_never_reached_dom: !provider.innerHTML.includes(MARKER_PREFIX),
    missing_slot_failed_before_commit: missingCode === "I18N_SLOT_MISSING" && missingWasAtomic,
    moved_slot_kept_application_state: terms0.input.value === "draft-zero"
      && terms1.input.value === "draft-one" && help0.state.clicks === 3,
    mutation_observer_saw_complete_commit: arabicObserverWasComplete,
    new_occurrence_got_new_instance: terms2Second !== terms2First,
    repeated_slots_became_distinct_instances: initial.counts.terms_link === 2
      && arabic.counts.terms_link === 3 && terms0 !== terms1,
    rootless_multi_node_slot_was_supported: terms0.nodes.length === 3
      && terms0.nodes.some((node) => node.nodeType === Node.TEXT_NODE),
    translated_text_used_no_private_wrapper: plainArabicTextWasDirect,
    wrapper_carried_active_language_and_direction: provider.lang === "en-US" && provider.dir === "ltr",
    wrapperless_cross_language_fallback_rejected: fallbackCode === "I18N_RICH_LANGUAGE_MISMATCH"
      && fallbackWasAtomic,
  };
  require(allTrue(gates), `lifecycle gates failed: ${JSON.stringify(gates)}`);

  observer.disconnect();
  region.destroy();
  const cleanupCounts = Object.fromEntries(
    tracker.created.map((instanceId) => [instanceId, tracker.cleaned.filter((item) => item === instanceId).length]),
  );
  gates.cleanup_ran_once_per_created_instance = tracker.created.length === tracker.cleaned.length
    && Object.values(cleanupCounts).every((count) => count === 1)
    && tracker.cleanupWasConnected.every(Boolean);
  require(gates.cleanup_ran_once_per_created_instance, `cleanup gates failed: ${JSON.stringify(tracker)}`);

  return {
    counts: { arabic_terms: arabic.counts.terms_link, english_terms: initial.counts.terms_link },
    gates,
    orders: {
      arabic: expectedArabicOrder,
      english: ["rich:terms_link:0", "rich:terms_link:1", "rich:help_link:0"],
    },
    rejection_codes: [fallbackCode, missingCode].sort(),
  };
}


async function runPerformanceProbe(sources) {
  const provider = document.createElement("section");
  provider.tabIndex = -1;
  document.body.append(provider);
  const tracker = { cleaned: [], cleanupWasConnected: [], created: [], generations: {} };
  const region = new RichRegion(provider, tracker);
  const service = new RichService(region, sources);
  service.switchLocale("en-US");
  const samples = [];
  for (let index = 0; index < 30; index += 1) {
    const start = performance.now();
    service.switchLocale(index % 2 === 0 ? "ar" : "en-US");
    samples.push(performance.now() - start);
  }
  samples.sort((left, right) => left - right);
  const p95 = samples[Math.ceil(samples.length * 0.95) - 1];
  region.destroy();
  provider.remove();
  return { commit_p95_under_50_ms: p95 <= 50 };
}


globalThis.runCitryRichClientProbe = async function runCitryRichClientProbe(sources) {
  const lifecycle = await runLifecycleProbe(sources);
  const performance = await runPerformanceProbe(sources);
  require(allTrue(performance), `performance gates failed: ${JSON.stringify(performance)}`);
  return { ...lifecycle, performance };
};
