import {
  beginCitryCanvasRender,
  mountCitryCanvasHtml,
} from "./citry-lifecycle.js";

const RENDER_BASE_URL = "/citry/ext/storybook_scenarios/render";

function encodeArg(value) {
  if (value !== null && typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}

export async function loadCitryScenario({ args, parameters, abortSignal }) {
  const scenarioId = parameters.citry?.scenarioId;
  if (!scenarioId) {
    throw new Error("Citry story is missing parameters.citry.scenarioId.");
  }

  const query = new URLSearchParams();
  for (const [name, value] of Object.entries(args)) {
    if (value !== undefined) {
      query.set(name, encodeArg(value));
    }
  }

  const response = await fetch(`${RENDER_BASE_URL}/${scenarioId}?${query}`, {
    signal: abortSignal,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      `Citry scenario ${scenarioId} failed with ${response.status}: ${detail}`,
    );
  }
  return { citryHtml: await response.text() };
}

export function renderCitryScenario(_args, { loaded }) {
  return loaded.citryHtml;
}

export async function renderCitryHtmlToCanvas(context, canvas) {
  const token = beginCitryCanvasRender(context, canvas);
  const html = await context.storyFn();
  return mountCitryCanvasHtml(context, token, html);
}
