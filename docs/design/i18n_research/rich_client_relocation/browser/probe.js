function requireProbe(condition, message) {
  if (!condition) throw new Error(message);
}


function pause() {
  return new Promise((resolve) => setTimeout(resolve, 60));
}


function componentId(element) {
  return element.getAttribute("data-cid").trim().split(/\s+/).at(-1);
}


function occurrencePhysicals(registration) {
  const state = Citry.manager.ownership.get(registration.graph.revision);
  const graphId = registration.graph.instance.graphId;
  return Object.fromEntries(registration.data.occurrences.map((occurrence) => {
    const region = state.registry.slotRegions.get(`g${graphId}:r:${occurrence.regionId}`);
    const physical = state.registry.physicalPlacements.get(region.key)[0];
    return [occurrence.key, { physical, region }];
  }));
}


function pageSnapshot(provider, output) {
  return JSON.stringify({
    cleanups: window.__richRelocation.cleanups,
    dir: provider.dir,
    html: output.innerHTML,
    lang: provider.lang,
    registrations: window.__richRelocation.registrations.length,
  });
}


function runFailure(registration, output, provider, segments, mutateRegistration, options) {
  const before = pageSnapshot(provider, output);
  let code = null;
  try {
    const selected = mutateRegistration === null ? registration : mutateRegistration(registration);
    const plan = CitryRichRelocationCandidate.prepare(selected, output, segments);
    if (options !== null) plan.commit(options);
  } catch (error) {
    code = error.code || error.message;
  }
  return { atomic: pageSnapshot(provider, output) === before, code };
}


function runSyntheticRangeFailure(provider, kind) {
  const output = document.createElement("div");
  provider.append(output);
  const boundary0 = document.createElement("bdi");
  const boundary1 = kind === "overlap" ? boundary0 : document.createElement("bdi");
  boundary0.dir = "auto";
  boundary1.dir = "auto";
  const start0 = document.createComment("synthetic:0:start");
  const end0 = document.createComment("synthetic:0:end");
  const start1 = document.createComment("synthetic:1:start");
  const end1 = document.createComment("synthetic:1:end");
  if (kind === "overlap") {
    boundary0.append(start0, start1, document.createTextNode("overlap"), end0, end1);
    output.append(boundary0);
  } else {
    boundary0.append(start0, document.createTextNode("zero"), end0);
    boundary1.append(start1, document.createTextNode("one"), end1);
    output.append(boundary0, boundary1);
  }
  const physical0 = {
    end: end0,
    endMarker: end0.data,
    key: "g9:r:1",
    start: start0,
    startMarker: start0.data,
  };
  const physical1 = kind === "overlap"
    ? {
        end: end1,
        endMarker: end1.data,
        key: "g9:r:2",
        start: start1,
        startMarker: start1.data,
      }
    : {
        end: end1,
        endMarker: `${end1.data}:corrupt`,
        key: "g9:r:2",
        start: start1,
        startMarker: start1.data,
      };
  const fakeState = {
    registry: {
      fills: new Map([
        ["g9:f:1", { ownerRenderId: "owner", policy: "template", receiverRenderId: "fake", slot: "terms" }],
      ]),
      physicalPlacements: new Map([
        ["g9:r:1", [physical0]],
        ["g9:r:2", [physical1]],
      ]),
      slotRegions: new Map([
        ["g9:r:1", { fillId: 1, key: "g9:r:1", receiverRenderId: "fake" }],
        ["g9:r:2", { fillId: 1, key: "g9:r:2", receiverRenderId: "fake" }],
      ]),
    },
  };
  const registration = {
    data: {
      occurrences: [
        { key: "fake:0", regionId: 1, slot: "terms" },
        { key: "fake:1", regionId: 2, slot: "terms" },
      ],
    },
    els: [output],
    graph: {
      instance: { active: true, graphId: 9 },
      logicalInstance: { active: true },
      revision: "f".repeat(64),
    },
    id: "fake",
  };
  const segments = [
    { type: "occurrence", key: "fake:0" },
    { type: "occurrence", key: "fake:1" },
  ];
  const before = output.innerHTML;
  const ownership = Citry.manager.ownership;
  const realGet = ownership.get;
  let code = null;
  try {
    ownership.get = (revision) => (revision === registration.graph.revision ? fakeState : realGet(revision));
    CitryRichRelocationCandidate.prepare(registration, output, segments);
  } catch (error) {
    code = error.code || error.message;
  } finally {
    ownership.get = realGet;
  }
  const atomic = output.innerHTML === before;
  output.remove();
  return { atomic, code };
}


async function runProbe() {
  await pause();
  const registration = window.__richRelocation.registrations[0];
  const provider = document.querySelector(".i18n-relocation-provider");
  const output = document.querySelector(".rich-relocation-output");
  const input0 = document.querySelector('.terms-input[data-occurrence="message:terms_link:0"]');
  const input1 = document.querySelector('.terms-input[data-occurrence="message:terms_link:1"]');
  const ownerButtons = Array.from(document.querySelectorAll(".term-owner"));
  const help = document.querySelector(".help-slot");
  requireProbe(registration !== undefined, "the rich component did not register its occurrence map");
  requireProbe(provider instanceof HTMLElement && output instanceof HTMLElement, "the provider or output is missing");
  requireProbe(input0 instanceof HTMLInputElement && input1 instanceof HTMLInputElement, "the initial inputs are missing");
  requireProbe(help instanceof HTMLButtonElement, "the teleported help Slot is missing");

  const initialPhysicals = occurrencePhysicals(registration);
  const initialBoundaries = Object.fromEntries(registration.data.occurrences.map((occurrence) => [
    occurrence.key,
    initialPhysicals[occurrence.key].physical.start.parentElement,
  ]));
  const initialIdentities = Object.fromEntries(Object.entries(window.__richRelocation.scopes).map(
    ([key, scope]) => [key, scope.identity],
  ));
  const initialRevision = registration.graph.revision;
  const providerRenderId = componentId(provider);
  const initialGates = {
    component_js_received_graph_route: registration.graph.revision === Citry.manager.ownership.revisions()[0]
      && registration.graph.instance.renderId === registration.id,
    direct_slot_regions_are_distinct: new Set(
      registration.data.occurrences.map((occurrence) => occurrence.regionId),
    ).size === 3,
    occurrence_map_came_from_js_data: JSON.stringify(
      registration.data.occurrences.map((occurrence) => occurrence.key),
    ) === JSON.stringify([
      "message:terms_link:0",
      "message:terms_link:1",
      "message:help_link:0",
    ]),
    original_fill_scope_is_live: ownerButtons.every(
      (button) => button.textContent.startsWith("caller:")
        && Alpine.evaluate(button, "owner") === "caller"
        && Citry.manager.ownership._ownerForElement(button) === providerRenderId,
    ),
    slot_boundaries_are_structural_isolates: Object.values(initialBoundaries).every(
      (boundary) => boundary.tagName === "BDI"
        && boundary.getAttribute("dir") === "auto"
        && !boundary.hasAttribute("lang")
        && getComputedStyle(boundary).unicodeBidi.includes("isolate"),
    ),
    slot_owned_language_is_explicit: ownerButtons.every(
      (button) => button.lang === "en" && button.closest("[lang]") === button,
    ) && help.lang === "en",
  };
  requireProbe(Object.values(initialGates).every(Boolean), `initial gates failed: ${JSON.stringify(initialGates)}`);

  input0.value = "draft-zero";
  input1.value = "draft-one";
  input1.focus();
  input1.setSelectionRange(1, 4);
  ownerButtons[0].click();
  help.click();
  await pause();
  requireProbe(document.querySelector(".caller-clicks").textContent === "1", "the caller-owned event did not run");
  requireProbe(help.textContent === "help:1", "the teleported local state did not update");

  const englishSegments = [
    { type: "text", value: "Before <unsafe> " },
    { type: "occurrence", key: "message:terms_link:0" },
    { type: "text", value: ", again " },
    { type: "occurrence", key: "message:terms_link:1" },
    { type: "text", value: ", and finally " },
    { type: "occurrence", key: "message:help_link:0" },
    { type: "text", value: "." },
  ];
  const arabicSegments = [
    { type: "text", value: "المساعدة <unsafe> " },
    { type: "occurrence", key: "message:help_link:0" },
    { type: "text", value: " ثم الشروط " },
    { type: "occurrence", key: "message:terms_link:0" },
    { type: "text", value: " ومرة أخرى " },
    { type: "occurrence", key: "message:terms_link:1" },
    { type: "text", value: "." },
  ];

  const failures = {
    duplicate: runFailure(
      registration,
      output,
      provider,
      [arabicSegments[1], arabicSegments[1], ...arabicSegments.slice(2)],
      null,
      null,
    ),
    foreign_region: runFailure(
      registration,
      output,
      provider,
      arabicSegments,
      (current) => {
        const state = Citry.manager.ownership.get(current.graph.revision);
        const foreign = Array.from(state.registry.slotRegions.values()).find(
          (region) => region.receiverRenderId !== current.id,
        );
        return {
          ...current,
          data: {
            occurrences: current.data.occurrences.map((occurrence, index) => (
              index === 0 ? { ...occurrence, regionId: foreign.regionId } : occurrence
            )),
          },
        };
      },
      null,
    ),
    invalid_destination: runFailure(
      registration,
      ownerButtons[0],
      provider,
      arabicSegments,
      null,
      null,
    ),
    missing: runFailure(
      registration,
      output,
      provider,
      arabicSegments.filter((segment) => segment.key !== "message:help_link:0"),
      null,
      null,
    ),
    stale_revision: runFailure(
      registration,
      output,
      provider,
      arabicSegments,
      (current) => ({ ...current, graph: { ...current.graph, revision: "0".repeat(64) } }),
      null,
    ),
  };
  initialBoundaries["message:terms_link:0"].setAttribute("lang", "en");
  failures.invalid_boundary = runFailure(
    registration,
    output,
    provider,
    arabicSegments,
    null,
    null,
  );
  initialBoundaries["message:terms_link:0"].removeAttribute("lang");
  failures.corrupt_range = runSyntheticRangeFailure(provider, "corrupt");
  failures.overlapping_ranges = runSyntheticRangeFailure(provider, "overlap");
  requireProbe(
    failures.corrupt_range.code === "I18N_RICH_RANGE_CORRUPT"
      && failures.duplicate.code === "I18N_RICH_OCCURRENCE_DUPLICATE"
      && failures.foreign_region.code === "I18N_RICH_OCCURRENCE_MISSING"
      && failures.invalid_destination.code === "I18N_RICH_DESTINATION_INVALID"
      && failures.invalid_boundary.code === "I18N_RICH_BOUNDARY_INVALID"
      && failures.missing.code === "I18N_RICH_OCCURRENCE_MISSING"
      && failures.overlapping_ranges.code === "I18N_RICH_RANGE_OVERLAP"
      && failures.stale_revision.code === "I18N_RICH_REGISTRATION_STALE"
      && Object.values(failures).every((failure) => failure.atomic),
    `preflight failure changed: ${JSON.stringify(failures)}`,
  );

  failures.invalid_context = runFailure(
    registration,
    output,
    provider,
    arabicSegments,
    null,
    { direction: "sideways", lang: "ar", provider },
  );
  requireProbe(
    failures.invalid_context.atomic && failures.invalid_context.code === "I18N_RICH_CONTEXT_INVALID",
    `context failure changed: ${JSON.stringify(failures.invalid_context)}`,
  );

  const observed = [];
  const observer = new MutationObserver(() => {
    observed.push({
      dir: provider.dir,
      hasArabic: output.textContent.includes("المساعدة"),
      lang: provider.lang,
    });
  });
  observer.observe(provider, { attributes: true, childList: true, subtree: true });
  const arabicPlan = CitryRichRelocationCandidate.prepare(registration, output, arabicSegments);
  const commitResult = arabicPlan.commit({ direction: "rtl", focusFallback: provider, lang: "ar", provider });
  await pause();
  help.click();
  ownerButtons[1].click();
  await pause();
  const afterPhysicals = occurrencePhysicals(registration);
  const moveGates = {
    caller_events_still_use_source_scope: document.querySelector(".caller-clicks").textContent === "2",
    caller_scope_survived: Array.from(document.querySelectorAll(".term-owner")).every(
      (button) => button.textContent.startsWith("caller:")
        && Alpine.evaluate(button, "owner") === "caller"
        && Citry.manager.ownership._ownerForElement(button) === providerRenderId,
    ),
    component_identity_survived: Object.entries(initialIdentities).every(
      ([key, identity]) => window.__richRelocation.scopes[key].identity === identity,
    ),
    component_ranges_survived: Object.keys(initialPhysicals).every(
      (key) => initialPhysicals[key].physical === afterPhysicals[key].physical,
    ),
    structural_boundaries_survived: Object.entries(initialBoundaries).every(
      ([key, boundary]) => boundary === afterPhysicals[key].physical.start.parentElement
        && getComputedStyle(boundary).unicodeBidi.includes("isolate"),
    ),
    context_and_content_committed: provider.lang === "ar" && provider.dir === "rtl"
      && output.textContent.includes("المساعدة") && commitResult.moved === 3,
    focus_and_selection_survived: document.activeElement === input1
      && input1.selectionStart === 1 && input1.selectionEnd === 4,
    input_dom_and_state_survived: document.querySelector(
      '.terms-input[data-occurrence="message:terms_link:0"]',
    ) === input0
      && document.querySelector('.terms-input[data-occurrence="message:terms_link:1"]') === input1
      && input0.value === "draft-zero" && input1.value === "draft-one",
    no_cleanup_or_reinitialization: window.__richRelocation.cleanups.length === 0
      && window.__richRelocation.inits.length === 2,
    observer_saw_only_complete_state: observed.length > 0 && observed.every(
      (state) => state.lang === "ar" && state.dir === "rtl" && state.hasArabic,
    ),
    one_graph_revision_remained: Citry.manager.ownership.revisions().length === 1
      && Citry.manager.ownership.revisions()[0] === initialRevision,
    teleport_dom_placement_and_state_survived: document.querySelector(".help-slot") === help
      && help.parentElement.id === "portal" && help.textContent === "help:2"
      && help.lang === "en" && help.dir === "auto",
    hostile_slot_controls_remained_inside_isolates: Array.from(
      document.querySelectorAll(".hostile-slot-text"),
    ).every((element) => element.closest("bdi")?.classList.contains("rich-slot-boundary")),
    slot_language_was_not_relabelled: ownerButtons.every(
      (button) => button.lang === "en" && button.closest("[lang]") === button,
    ),
    unsafe_catalog_text_stayed_text: output.textContent.includes("<unsafe>")
      && output.querySelector("unsafe") === null,
  };
  requireProbe(Object.values(moveGates).every(Boolean), `move gates failed: ${JSON.stringify(moveGates)}`);

  const afterCommit = pageSnapshot(provider, output);
  let consumedCode = null;
  try {
    arabicPlan.commit({ direction: "rtl", focusFallback: provider, lang: "ar", provider });
  } catch (error) {
    consumedCode = error.code;
  }
  failures.consumed_plan = {
    atomic: pageSnapshot(provider, output) === afterCommit,
    code: consumedCode,
  };
  requireProbe(
    failures.consumed_plan.code === "I18N_RICH_PLAN_CONSUMED" && failures.consumed_plan.atomic,
    "a consumed plan did not fail atomically",
  );
  const englishPlan = CitryRichRelocationCandidate.prepare(registration, output, englishSegments);
  englishPlan.commit({ direction: "ltr", focusFallback: provider, lang: "en-US", provider });
  await pause();
  observer.disconnect();
  const roundTripGates = {
    caller_scope_remained_after_round_trip: Array.from(document.querySelectorAll(".term-owner")).every(
      (button) => Alpine.evaluate(button, "owner") === "caller",
    ),
    context_returned: provider.lang === "en-US" && provider.dir === "ltr",
    focus_and_state_remained: document.activeElement === input1
      && input0.value === "draft-zero" && input1.value === "draft-one",
    no_cleanup_ran: window.__richRelocation.cleanups.length === 0,
    structural_boundaries_remained: Object.entries(initialBoundaries).every(
      ([key, boundary]) => boundary === occurrencePhysicals(registration)[key].physical.start.parentElement
        && getComputedStyle(boundary).unicodeBidi.includes("isolate"),
    ),
    teleport_remained: document.querySelector(".help-slot") === help
      && help.parentElement.id === "portal" && help.textContent === "help:2",
    unsafe_catalog_text_is_literal: output.textContent.includes("Before <unsafe>")
      && output.querySelector("unsafe") === null,
  };
  requireProbe(
    Object.values(roundTripGates).every(Boolean),
    `round-trip gates failed: ${JSON.stringify(roundTripGates)}`,
  );
  return {
    candidate_format: CitryRichRelocationCandidate.FORMAT,
    failures,
    initial_gates: initialGates,
    move_gates: moveGates,
    round_trip_gates: roundTripGates,
    server_occurrence_declarations: registration.data.occurrences,
  };
}


globalThis.CitryRichRelocationProbe = { runProbe };
