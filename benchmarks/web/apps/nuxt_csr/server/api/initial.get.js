import {getQuery, setHeader} from "h3";
import {browserSnapshot, csrfFor, reset, snapshot} from "../model.mjs";

export default defineEventHandler(event => {
  const query = getQuery(event);
  const session = String(query.session || "manual");
  const count = Number(query.count || 14);
  const started = performance.now();
  reset(session, count);
  const value = browserSnapshot(snapshot(session));
  setHeader(event, "server-timing", `prepare;dur=${(performance.now() - started).toFixed(3)}`);
  return {board: value, csrf: csrfFor(session)};
});
