function requireProbe(condition, message) {
  if (!condition) throw new Error(message);
}


function pause() {
  return new Promise((resolve) => setTimeout(resolve, 60));
}


function componentId(element) {
  return element.getAttribute("data-cid").trim().split(/\s+/).at(-1);
}


function occurrenceRecord(classId, morphKey) {
  const ownership = Citry.manager.ownership;
  for (const revision of ownership.revisions()) {
    const graph = ownership.get(revision);
    const invocation = Array.from(graph.registry.nestedComponents.values()).find(
      (candidate) => candidate.targetClassId === classId && candidate.morphKey === morphKey,
    );
    const instance = invocation === undefined ? undefined : graph.registry.renderIds.get(invocation.targetRenderId);
    if (instance === undefined) continue;
    const route = ownership.forRender(revision, instance.renderId);
    if (route === null) continue;
    const physical = graph.registry.physicalPlacements.get(route.instance.key)?.[0];
    if (route?.logicalInstance?.active && physical !== undefined) {
      return { anchor: route.anchor, graph, instance, logical: route.logicalInstance, physical, revision, route };
    }
  }
  throw new Error(`missing live occurrence ${morphKey}`);
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
  throw new Error("ownership range lost its closing cap");
}


function inputFor(occurrence) {
  return document.querySelector(`.terms-input[data-occurrence="${occurrence}"]`);
}


function providerSnapshot() {
  const provider = document.querySelector(".i18n-runtime-provider");
  return JSON.stringify({
    cleanups: window.__richRuntime.cleanups,
    dir: provider.dir,
    html: provider.innerHTML,
    lang: provider.lang,
  });
}


async function applyFragment(html) {
  const provider = document.querySelector(".i18n-runtime-provider");
  const id = componentId(provider);
  const anchor = Citry.events._internal.getAnchor(id);
  const sequence = anchor.epoch + 1;
  anchor.epoch = sequence;
  await Citry.events._internal.applyResult(
    {
      ok: true,
      sendSequence: sequence,
      actions: [{ action: "render", target: `render:${id}`, swap: "morph", html }],
    },
    { anchor, instance: id, event: "refresh" },
  );
  await pause();
}


function slotRegionCount() {
  return Citry.manager.ownership.revisions().reduce(
    (count, revision) => count + Citry.manager.ownership.get(revision).registry.slotRegions.size,
    0,
  );
}


async function runServerBackedProbe(growthFragment, backFragment, classIds) {
  await pause();
  const provider = document.querySelector(".i18n-runtime-provider");
  const input0 = inputFor("rich:terms_link:0");
  const input1 = inputFor("rich:terms_link:1");
  const help = document.querySelector(".help-slot");
  requireProbe(input0 instanceof HTMLInputElement && input1 instanceof HTMLInputElement, "initial inputs missing");
  requireProbe(help instanceof HTMLButtonElement, "initial teleported help missing");
  const beforeRecords = Object.fromEntries(
    ["rich:terms_link:0", "rich:terms_link:1", "rich:help_link:0"].map(
      (key) => [key, occurrenceRecord(classIds.occurrence, key)],
    ),
  );
  const beforeRevisionCount = Citry.manager.ownership.revisions().length;
  const initialSlotRegionCount = slotRegionCount();
  const sourceProjectionMissing = Array.from(document.querySelectorAll(".term-owner")).every(
    (element) => element.textContent === "missing",
  );
  input0.value = "draft-zero";
  input1.value = "draft-one";
  input1.focus();
  input1.setSelectionRange(1, 4);
  help.click();
  await pause();
  requireProbe(help.textContent === "help:1", "teleported local state did not update");

  await applyFragment(growthFragment);
  const growthInput2 = inputFor("rich:terms_link:2");
  const afterGrowthRecords = Object.fromEntries(
    ["rich:terms_link:0", "rich:terms_link:1", "rich:help_link:0"].map(
      (key) => [key, occurrenceRecord(classIds.occurrence, key)],
    ),
  );
  const helpAfterGrowth = document.querySelector(".help-slot");
  helpAfterGrowth.click();
  await pause();
  const growthObservations = {
    added_occurrence_initialized: growthInput2 instanceof HTMLInputElement
      && window.__richRuntime.inits.includes("rich:terms_link:2"),
    existing_component_ranges_kept_logical_identity: Object.keys(beforeRecords).every(
      (key) => beforeRecords[key].logical === afterGrowthRecords[key].logical
        && beforeRecords[key].anchor === afterGrowthRecords[key].anchor,
    ),
    existing_inputs_kept_dom_identity: inputFor("rich:terms_link:0") === input0
      && inputFor("rich:terms_link:1") === input1,
    focus_and_selection_survived: document.activeElement === input1
      && input1.selectionStart === 1 && input1.selectionEnd === 4,
    input_state_survived: input0.value === "draft-zero" && input1.value === "draft-one",
    provider_switched: document.querySelector(".i18n-runtime-provider").lang === "ar"
      && document.querySelector(".i18n-runtime-provider").dir === "rtl",
    retained_inner_ranges_were_not_recreated: !window.__richRuntime.cleanups.includes("rich:terms_link:0")
      && !window.__richRuntime.cleanups.includes("rich:terms_link:1"),
    slot_region_records_grew_with_occurrence: slotRegionCount() > initialSlotRegionCount,
    teleport_dom_identity_survived: helpAfterGrowth === help,
    teleport_kept_native_placement: helpAfterGrowth.parentElement.id === "portal",
    teleport_kept_local_state: helpAfterGrowth.textContent === "help:2",
  };
  requireProbe(
    growthObservations.added_occurrence_initialized
      && growthObservations.existing_component_ranges_kept_logical_identity
      && growthObservations.input_state_survived
      && growthObservations.provider_switched
      && growthObservations.slot_region_records_grew_with_occurrence
      && growthObservations.teleport_kept_native_placement,
    `server-backed structural gates failed: ${JSON.stringify(growthObservations)}`,
  );
  requireProbe(
    !growthObservations.existing_inputs_kept_dom_identity
      && !growthObservations.focus_and_selection_survived
      && !growthObservations.retained_inner_ranges_were_not_recreated
      && !growthObservations.teleport_dom_identity_survived
      && !growthObservations.teleport_kept_local_state,
    `server-backed lifecycle limitation changed: ${JSON.stringify(growthObservations)}`,
  );

  growthInput2.focus();
  const cleanupBeforeRemoval = window.__richRuntime.cleanups.length;
  await applyFragment(backFragment);
  const activeAfterRemoval = document.activeElement;
  const finalRecords = Object.fromEntries(
    ["rich:terms_link:0", "rich:terms_link:1", "rich:help_link:0"].map(
      (key) => [key, occurrenceRecord(classIds.occurrence, key)],
    ),
  );
  const finalObservations = {
    added_occurrence_cleaned_once: !growthInput2.isConnected
      && window.__richRuntime.cleanups.length === cleanupBeforeRemoval + 1
      && window.__richRuntime.cleanups.filter((item) => item === "rich:terms_link:2").length === 1,
    existing_ranges_survived_round_trip: Object.keys(beforeRecords).every(
      (key) => beforeRecords[key].logical === finalRecords[key].logical,
    ),
    focus_did_not_remain_on_removed_dom: activeAfterRemoval !== growthInput2,
    generic_runtime_did_not_choose_provider_focus: activeAfterRemoval !== document.querySelector(".i18n-runtime-provider"),
    provider_returned_to_english: document.querySelector(".i18n-runtime-provider").lang === "en-US"
      && document.querySelector(".i18n-runtime-provider").dir === "ltr",
    revisions_pruned: Citry.manager.ownership.revisions().length === beforeRevisionCount,
    surviving_state_remained: inputFor("rich:terms_link:0") === input0
      && inputFor("rich:terms_link:1") === input1
      && input0.value === "draft-zero" && input1.value === "draft-one",
  };
  requireProbe(
    finalObservations.existing_ranges_survived_round_trip
      && finalObservations.focus_did_not_remain_on_removed_dom
      && finalObservations.provider_returned_to_english,
    `return structural gates failed: ${JSON.stringify(finalObservations)}`,
  );
  return {
    final_observations: finalObservations,
    growth_observations: growthObservations,
    integration_findings: {
      repeated_slot_source_projection_missing: sourceProjectionMissing,
    },
    lifecycle_counts: {
      cleanups: [...window.__richRuntime.cleanups],
      inits: [...window.__richRuntime.inits],
      revision_count_after_return: Citry.manager.ownership.revisions().length,
    },
    occurrence_counts: { after_growth: 4, initial: 3, after_return: 3 },
  };
}


function moveOccurrence(record, fragment) {
  for (const node of nodesInclusive(record.physical.start, record.physical.end)) fragment.append(node);
}


function captureFocus() {
  const element = document.activeElement;
  if (!(element instanceof HTMLInputElement)) return null;
  return {
    element,
    end: element.selectionEnd,
    start: element.selectionStart,
  };
}


function restoreFocus(snapshot) {
  if (snapshot === null || !snapshot.element.isConnected) return;
  snapshot.element.focus({ preventScroll: true });
  snapshot.element.setSelectionRange(snapshot.start, snapshot.end);
}


function clientOnlyCommit(classId, locale, order) {
  const provider = document.querySelector(".i18n-runtime-provider");
  const output = document.querySelector(".rich-output");
  let records;
  try {
    records = order.map((entry) => ({ ...entry, record: occurrenceRecord(classId, entry.key) }));
  } catch {
    throw new Error("I18N_RICH_OCCURRENCE_MISSING");
  }
  requireProbe(
    records.every(({ record }) => record.physical.start.parentNode === output && record.physical.end.parentNode === output),
    "I18N_RICH_OCCURRENCE_MISSING",
  );
  const focus = captureFocus();
  const fragment = document.createDocumentFragment();
  for (const entry of records) {
    fragment.append(document.createTextNode(entry.before));
    moveOccurrence(entry.record, fragment);
  }
  fragment.append(document.createTextNode(order.at(-1).after));
  provider.lang = locale;
  provider.dir = locale === "ar" ? "rtl" : "ltr";
  output.replaceChildren(fragment);
  restoreFocus(focus);
}


async function runClientOnlyProbe(classIds) {
  await pause();
  const provider = document.querySelector(".i18n-runtime-provider");
  const input0 = inputFor("rich:terms_link:0");
  const input1 = inputFor("rich:terms_link:1");
  const help = document.querySelector(".help-slot");
  const records = Object.fromEntries(
    ["rich:terms_link:0", "rich:terms_link:1", "rich:help_link:0"].map(
      (key) => [key, occurrenceRecord(classIds.occurrence, key)],
    ),
  );
  const revision = records["rich:terms_link:0"].revision;
  const initialSlotRegionCount = slotRegionCount();
  const sourceProjectionMissing = Array.from(document.querySelectorAll(".term-owner")).every(
    (element) => element.textContent === "missing",
  );
  input0.value = "client-zero";
  input1.value = "client-one";
  input1.focus();
  input1.setSelectionRange(2, 5);
  help.click();
  await pause();

  const beforeFailure = providerSnapshot();
  let preflightCode = null;
  try {
    clientOnlyCommit(classIds.occurrence, "ar", [
      { after: "", before: "", key: "rich:terms_link:99" },
    ]);
  } catch (error) {
    preflightCode = error.message;
  }
  const failedCommitWasAtomic = providerSnapshot() === beforeFailure;

  const observed = [];
  const observer = new MutationObserver(() => {
    observed.push({ dir: provider.dir, lang: provider.lang });
  });
  observer.observe(provider, { attributes: true, childList: true, subtree: true });
  clientOnlyCommit(classIds.occurrence, "ar", [
    { before: "أولًا ", key: "rich:help_link:0" },
    { before: " ثم ", key: "rich:terms_link:0" },
    { after: ".", before: " وبعدها ", key: "rich:terms_link:1" },
  ]);
  await pause();
  help.click();
  await pause();
  const afterRecords = Object.fromEntries(
    Object.keys(records).map((key) => [key, occurrenceRecord(classIds.occurrence, key)]),
  );
  const gates = {
    all_ranges_remained_live: Object.values(afterRecords).every((record) => record.route.logicalInstance.active),
    client_only_failure_was_atomic: preflightCode === "I18N_RICH_OCCURRENCE_MISSING" && failedCommitWasAtomic,
    dom_identity_survived: inputFor("rich:terms_link:0") === input0
      && inputFor("rich:terms_link:1") === input1 && document.querySelector(".help-slot") === help,
    focus_and_selection_survived: document.activeElement === input1
      && input1.selectionStart === 2 && input1.selectionEnd === 5,
    logical_identity_survived: Object.keys(records).every(
      (key) => records[key].logical === afterRecords[key].logical,
    ),
    mutation_observer_saw_complete_context: observed.length > 0
      && observed.every((state) => state.lang === "ar" && state.dir === "rtl"),
    no_component_cleanup_ran: window.__richRuntime.cleanups.length === 0,
    one_graph_revision_remained: Citry.manager.ownership.revisions().length === 1
      && Citry.manager.ownership.revisions()[0] === revision,
    retained_state_survived: input0.value === "client-zero" && input1.value === "client-one",
    slot_region_records_survived: slotRegionCount() === initialSlotRegionCount,
    teleport_dom_and_state_survived: document.querySelector(".help-slot") === help
      && help.parentElement.id === "portal" && help.textContent === "help:2",
  };
  requireProbe(Object.values(gates).every(Boolean), `client-only gates failed: ${JSON.stringify(gates)}`);
  observer.disconnect();

  clientOnlyCommit(classIds.occurrence, "en-US", [
    { before: "Before <unsafe> ", key: "rich:terms_link:0" },
    { before: ", again ", key: "rich:terms_link:1" },
    { after: ".", before: ", and finally ", key: "rich:help_link:0" },
  ]);
  await pause();
  requireProbe(provider.lang === "en-US" && provider.dir === "ltr", "English context did not return");
  requireProbe(window.__richRuntime.cleanups.length === 0, "round-trip move cleaned a live range");

  const ownershipMethods = Object.keys(Citry.manager.ownership).sort();
  return {
    gates,
    integration_findings: {
      repeated_slot_source_projection_missing: sourceProjectionMissing,
    },
    ownership_surface: {
      has_browser_slot_instantiation: ownershipMethods.some(
        (name) => /instantiate|blueprint|clone/i.test(name),
      ),
      has_range_relocation: ownershipMethods.some((name) => /move|relocate/i.test(name)),
    },
  };
}


globalThis.CitryRichRuntimeProbe = {
  runClientOnlyProbe,
  runServerBackedProbe,
};
