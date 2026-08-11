function requireSwitchBenchmark(condition, message) {
  if (!condition) throw new Error(message);
}

function switchStateIsComplete(locale) {
  const wrappers = Object.fromEntries(Array.from(document.querySelectorAll("[data-provider]")).map(
    (element) => [element.dataset.provider, { dir: element.dir, lang: element.lang }],
  ));
  const outputs = Object.fromEntries(Array.from(document.querySelectorAll("[data-reader]")).map(
    (element) => [element.dataset.reader, element.textContent],
  ));
  const labels = locale === "ar-EG"
    ? { direction: "rtl", inherited: "مرحبا", outer: "مرحبا" }
    : { direction: "ltr", inherited: "Hello", outer: "Hello" };
  const benchmarkReadersComplete = Object.entries(outputs)
    .filter(([name]) => name.startsWith("benchmark_reader_"))
    .every(([, value]) => value === labels.outer);
  return wrappers.outer?.lang === locale
    && wrappers.outer?.dir === labels.direction
    && wrappers.inherited?.lang === locale
    && wrappers.inherited?.dir === labels.direction
    && wrappers.explicit?.lang === "cs-CZ"
    && wrappers.explicit?.dir === "ltr"
    && wrappers.independent?.lang === "ja-JP"
    && wrappers.independent?.dir === "ltr"
    && outputs.outer_reader === labels.outer
    && outputs.inherited_reader === labels.inherited
    && outputs.explicit_reader === "Ahoj"
    && outputs.independent_reader === "こんにちは"
    && outputs.blocked_reader === "blocked"
    && benchmarkReadersComplete;
}

function percentile(values, fraction) {
  const ordered = [...values].sort((left, right) => left - right);
  return ordered[Math.ceil(ordered.length * fraction) - 1];
}

async function runSwitchBenchmark() {
  const service = window.__providerProbe.services.outer;
  requireSwitchBenchmark(service?.context?.locale === "en-US", "the benchmark did not start in English");
  const samples = [];
  let sampledFrames = 0;
  let mixedFrames = 0;
  for (let index = 0; index < 30; index += 1) {
    const target = index % 2 === 0 ? "ar-EG" : "en-US";
    let active = true;
    const sampleFrame = () => {
      if (!active) return;
      sampledFrames += 1;
      if (!switchStateIsComplete("en-US") && !switchStateIsComplete("ar-EG")) mixedFrames += 1;
      requestAnimationFrame(sampleFrame);
    };
    requestAnimationFrame(sampleFrame);
    const started = performance.now();
    const result = await service.switchLocale(target);
    samples.push(performance.now() - started);
    await new Promise((resolve) => requestAnimationFrame(() => requestAnimationFrame(resolve)));
    active = false;
    requireSwitchBenchmark(result.status === "committed", `switch ${index} did not commit`);
    requireSwitchBenchmark(switchStateIsComplete(target), `switch ${index} exposed an incomplete target state`);
  }
  requireSwitchBenchmark(mixedFrames === 0, `the browser exposed ${mixedFrames} mixed-locale frames`);
  return {
    max_ms: Math.max(...samples),
    median_ms: percentile(samples, 0.5),
    min_ms: Math.min(...samples),
    mixed_frames: mixedFrames,
    p95_ms: percentile(samples, 0.95),
    sample_count: samples.length,
    sampled_frames: sampledFrames,
  };
}

globalThis.CitryI18nSwitchBenchmark = Object.freeze({ runSwitchBenchmark });
