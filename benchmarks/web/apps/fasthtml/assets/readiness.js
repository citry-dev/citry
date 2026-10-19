/* Wait for HTMX settlement and Alpine's queued DOM updates. */
(() => {
  let pending = 0;
  function ready(phase) {
    window.Alpine.nextTick(() => {
      const board = document.getElementById("board");
      if (!board || pending !== 0) return;
      window.__citryBench?.ready({
        revision: Number(board.dataset.revision),
        session: board.dataset.session,
        operation: board.dataset.operation,
        phase,
        pending,
      });
    });
  }
  document.addEventListener("alpine:initialized", () => ready("initial"), { once: true });
  document.addEventListener("htmx:beforeRequest", () => { pending += 1; });
  document.addEventListener("htmx:afterRequest", () => { pending -= 1; });
  document.addEventListener("htmx:afterSettle", () => ready("update"));
})();
