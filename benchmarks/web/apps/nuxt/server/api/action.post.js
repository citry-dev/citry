import {getHeader, readBody, setHeader} from "h3";
import {apply, browserSnapshot, csrfFor} from "../model.mjs";

export default defineEventHandler(async event => {
  const values = await readBody(event);
  const session = String(values?.session || "");
  if (getHeader(event, "x-csrf-token") !== csrfFor(session) || values?.csrf !== csrfFor(session)) {
    throw createError({statusCode: 403, statusMessage: "CSRF verification failed"});
  }
  const board = apply(session, {
    action: String(values.action || ""),
    operation: String(values.operation || ""),
    row_id: String(values.row_id || "0"),
    query: String(values.query || ""),
    title: String(values.title || ""),
  });
  setHeader(event, "x-bench-operation", board.operation);
  setHeader(event, "x-bench-revision", String(board.revision));
  const started = performance.now();
  const payload = JSON.stringify({board: browserSnapshot(board)});
  const duration = (performance.now() - started).toFixed(3);
  setHeader(event, "content-type", "application/json; charset=utf-8");
  setHeader(event, "server-timing", `prepare;dur=${duration}`);
  return payload;
});
