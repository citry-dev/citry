import {defineNitroPlugin} from "nitropack/runtime";

import {appendServerTiming} from "../utils/benchmark-timing.mjs";

export default defineNitroPlugin(nitro => {
  nitro.hooks.hook("request", event => {
    event.context.benchStarted = performance.now();
  });
  nitro.hooks.hook("beforeResponse", event => {
    const response = event.node.res;
    if (!response.getHeader("cache-control")) response.setHeader("cache-control", "no-store");
    if (event.context.benchStarted !== undefined) {
      const duration = (performance.now() - event.context.benchStarted).toFixed(3);
      const pathname = (event.node.req.url || "/").split("?", 1)[0];
      const metric = pathname === "/" ? "render" : pathname === "/api/action" ? "prepare" : null;
      const existing = response.getHeader("server-timing");
      const hasExisting = Array.isArray(existing) ? existing.length > 0 : Boolean(existing);
      if (metric) {
        const spans = hasExisting
          ? [`application;dur=${duration}`]
          : [`application;dur=${duration}`, `${metric};dur=${duration}`];
        response.setHeader("server-timing", appendServerTiming(existing, spans));
      }
    }
  });
});
