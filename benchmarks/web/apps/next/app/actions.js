"use server";

import {cookies} from "next/headers";
import {apply, browserSnapshot, csrfFor, ensure} from "../scenario/node_model.mjs";

export async function submitAction(formData) {
  const values = Object.fromEntries(formData.entries());
  const session = String(values.session || "");
  if (String(values.csrf || "") !== csrfFor(session)) throw new Error("CSRF verification failed");
  // Next can place the page and Server Action in separate server bundles.  The
  // count lets a fresh action bundle reconstruct the same canonical session
  // before applying the first mutation; subsequent actions use its in-memory
  // state.  Inserted rows are rounded back to their supported canonical size.
  const observedCount = Number(values.count || 14);
  const count = observedCount >= 1400 ? 1400 : observedCount >= 140 ? 140 : 14;
  ensure(session, count);
  const board = apply(session, {
    action: String(values.action || ""),
    operation: String(values.operation || ""),
    row_id: String(values.row_id || "0"),
    query: String(values.query || ""),
    title: String(values.title || ""),
  });
  const store = await cookies();
  store.set("citry-bench-ack", encodeURIComponent(JSON.stringify({
    operation: board.operation,
    revision: board.revision,
  })), {httpOnly: false, sameSite: "lax", path: "/"});
  return {board: browserSnapshot(board)};
}
