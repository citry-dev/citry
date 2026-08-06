import {
  beginCitryCanvasRender,
  mountCitryCanvasHtml,
} from "./citry-lifecycle.js";

function buildStoryArgs(args, argTypes) {
  const result = { ...args };
  for (const [name, argType] of Object.entries(argTypes)) {
    const control = argType.control;
    const kind =
      control && typeof control === "object" && "type" in control
        ? control.type?.toLowerCase()
        : undefined;
    if (kind === "date") {
      result[name] = new Date(result[name]).toISOString();
    } else if (kind === "object") {
      result[name] = JSON.stringify(result[name]);
    }
  }
  return result;
}

async function fetchStoryHtml(url, storyId, args, signal) {
  const query = new URLSearchParams();
  for (const [name, value] of Object.entries(args)) {
    if (value !== undefined) {
      query.set(name, String(value));
    }
  }
  const response = await fetch(`${url}/${storyId}?${query}`, { signal });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(
      `Citry scenario ${storyId} failed with ${response.status}: ${detail}`,
    );
  }
  return response.text();
}

export async function renderCitryServerToCanvas(context, canvas) {
  context.storyFn();
  const token = beginCitryCanvasRender(context, canvas);
  const { args, argTypes, parameters } = context.storyContext;
  const server = parameters.server;
  const storyId = server.id ?? context.id;
  const storyArgs = {
    ...server.params,
    ...buildStoryArgs(args, argTypes),
  };
  const html = await fetchStoryHtml(
    server.url,
    storyId,
    storyArgs,
    token.signal,
  );
  return mountCitryCanvasHtml(context, token, html);
}
