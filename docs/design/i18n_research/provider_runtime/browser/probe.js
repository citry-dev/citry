function requireProviderProbe(condition, message) {
  if (!condition) throw new Error(message);
}


function providerSnapshot() {
  return JSON.stringify({
    contexts: Object.fromEntries(Object.entries(window.__providerProbe.services).map(
      ([name, service]) => [name, service.context],
    )),
    outputs: Object.fromEntries(Array.from(document.querySelectorAll("[data-reader]")).map(
      (element) => [element.dataset.reader, element.textContent],
    )),
    wrappers: Object.fromEntries(Array.from(document.querySelectorAll("[data-provider]")).map(
      (element) => [element.dataset.provider, { dir: element.dir, lang: element.lang }],
    )),
  });
}


function completeArabicState() {
  const wrappers = Object.fromEntries(Array.from(document.querySelectorAll("[data-provider]")).map(
    (element) => [element.dataset.provider, { dir: element.dir, lang: element.lang }],
  ));
  const outputs = Object.fromEntries(Array.from(document.querySelectorAll("[data-reader]")).map(
    (element) => [element.dataset.reader, element.textContent],
  ));
  return wrappers.outer?.lang === "ar-EG"
    && wrappers.outer?.dir === "rtl"
    && wrappers.inherited?.lang === "ar-EG"
    && wrappers.inherited?.dir === "rtl"
    && wrappers.explicit?.lang === "cs-CZ"
    && wrappers.explicit?.dir === "ltr"
    && wrappers.independent?.lang === "ja-JP"
    && wrappers.independent?.dir === "ltr"
    && outputs.outer_reader === "مرحبا"
    && outputs.inherited_reader === "مرحبا"
    && outputs.explicit_reader === "Ahoj"
    && outputs.independent_reader === "こんにちは"
    && outputs.blocked_reader === "blocked";
}


async function runProviderProbe() {
  const tracker = window.__providerProbe;
  const services = tracker.services;
  const outer = services.outer;
  const inherited = services.inherited;
  const explicit = services.explicit;
  const independent = services.independent;
  requireProviderProbe(outer && inherited && explicit && independent, "the provider services did not mount");

  const initial = providerSnapshot();
  const initialGates = {
    blocked_reader_has_no_service: tracker.readers.blocked_reader.service === null,
    browser_context_matches_server_context: Array.from(document.querySelectorAll("[data-reader]"))
      .filter((element) => element.dataset.reader !== "blocked_reader")
      .every((element) => element.dataset.serverLocale === tracker.readers[element.dataset.reader].service.context.locale),
    explicit_child_is_fixed: explicit.context.locale === "cs-CZ" && explicit.context.timeZone === null,
    false_then_true_is_independent: independent.context.locale === "ja-JP",
    inherited_child_merged_fields: inherited.context.locale === "en-US"
      && inherited.context.timeZone === "Europe/Prague",
    readonly_service: Object.isFrozen(outer)
      && Object.isFrozen(outer.context)
      && Reflect.set(outer, "context", { locale: "forged" }) === false
      && outer.context.locale === "en-US",
    server_values_visible: Array.from(document.querySelectorAll("[data-reader]"))
      .every((element) => element.dataset.serverLocale !== ""),
  };
  requireProviderProbe(Object.values(initialGates).every(Boolean), `initial gates failed: ${JSON.stringify(initialGates)}`);

  const loadsBeforeInvalid = tracker.loads.length;
  let invalidAliasCode = null;
  try {
    await outer.switchLocale("en_US");
  } catch (error) {
    invalidAliasCode = error.code;
  }
  const invalidAlias = {
    atomic: providerSnapshot() === initial,
    code: invalidAliasCode,
    skippedLoad: tracker.loads.length === loadsBeforeInvalid,
  };

  tracker.failures.add("pl-PL");
  let failedChunkCode = null;
  try {
    await outer.switchLocale("pl-PL");
  } catch (error) {
    failedChunkCode = error.code || "CHUNK_FAILED";
  }
  tracker.failures.delete("pl-PL");
  const failedChunk = {
    atomic: providerSnapshot() === initial,
    code: failedChunkCode,
  };

  tracker.corrupt.add("ar-EG");
  let badRevisionCode = null;
  try {
    await outer.switchLocale("ar-EG");
  } catch (error) {
    badRevisionCode = error.code;
  }
  tracker.corrupt.delete("ar-EG");
  const badRevision = {
    atomic: providerSnapshot() === initial,
    code: badRevisionCode,
  };

  tracker.delays.set("ar-EG", 80);
  tracker.delays.set("en-US", 1);
  const oldRequest = outer.switchLocale("ar-EG");
  await new Promise((resolve) => setTimeout(resolve, 5));
  const newRequest = outer.switchLocale("en-US");
  const [oldResult, newResult] = await Promise.all([oldRequest, newRequest]);
  const staleGeneration = {
    latestCommitted: newResult.status === "committed" && outer.context.locale === "en-US",
    oldIgnored: oldResult.status === "stale",
    stateStayedComplete: providerSnapshot() === initial,
  };
  tracker.delays.clear();

  const observations = [];
  const observer = new MutationObserver(() => observations.push(completeArabicState()));
  observer.observe(document.querySelector('[data-provider="outer"]'), {
    attributes: true,
    childList: true,
    subtree: true,
  });
  const switchResult = await outer.switchLocale("ar-EG");
  await new Promise((resolve) => setTimeout(resolve, 20));
  observer.disconnect();

  let unknownMessageCode = null;
  try {
    outer.bindMessage("unknown", document.querySelector('[data-reader="outer_reader"]'));
  } catch (error) {
    unknownMessageCode = error.code;
  }

  const switchGates = {
    atomic_observer_state: observations.length > 0 && observations.every(Boolean),
    blocked_subtree_stayed_fixed: tracker.readers.blocked_reader.service === null
      && document.querySelector('[data-reader="blocked_reader"]').textContent === "blocked",
    committed: switchResult.status === "committed" && completeArabicState(),
    explicit_child_stayed_fixed: explicit.context.locale === "cs-CZ" && explicit.context.direction === "ltr",
    inherited_child_recomputed: inherited.context.locale === "ar-EG"
      && inherited.context.direction === "rtl"
      && inherited.context.timeZone === "Europe/Prague",
    independent_child_stayed_fixed: independent.context.locale === "ja-JP",
    outer_context_changed: outer.context.locale === "ar-EG" && outer.context.direction === "rtl",
    unknown_message_rejected: unknownMessageCode === "I18N_PROVIDER_MESSAGE_INVALID",
  };
  requireProviderProbe(Object.values(switchGates).every(Boolean), `switch gates failed: ${JSON.stringify(switchGates)}`);
  requireProviderProbe(
    invalidAlias.atomic && invalidAlias.skippedLoad && invalidAlias.code === "I18N_PROVIDER_LOCALE_INVALID",
    `invalid alias gate failed: ${JSON.stringify(invalidAlias)}`,
  );
  requireProviderProbe(failedChunk.atomic, `failed chunk changed the page: ${JSON.stringify(failedChunk)}`);
  requireProviderProbe(
    badRevision.atomic && badRevision.code === "I18N_PROVIDER_ARTIFACT_INVALID",
    `bad revision gate failed: ${JSON.stringify(badRevision)}`,
  );
  requireProviderProbe(
    Object.values(staleGeneration).every(Boolean),
    `stale generation gate failed: ${JSON.stringify(staleGeneration)}`,
  );

  return {
    candidate_format: CitryI18nProviderCandidate.FORMAT,
    failures: {
      bad_revision: badRevision,
      failed_chunk: failedChunk,
      invalid_alias: invalidAlias,
    },
    initial_gates: initialGates,
    load_calls: tracker.loads,
    stale_generation: staleGeneration,
    switch_gates: switchGates,
  };
}


globalThis.CitryI18nProviderProbe = Object.freeze({ runProviderProbe });
