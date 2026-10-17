/* Observe native Tetra morph completion; never replace its request transport. */
(() => {
  const pending = new Set();
  function ready(phase) {
    window.Alpine.nextTick(() => {
      const board = document.getElementById("board");
      if (!board || pending.size !== 0) return;
      window.__citryBench?.ready({
        revision: Number(board.dataset.revision), session: board.dataset.session,
        operation: board.dataset.operation, phase, pending: pending.size,
      });
    });
  }
  document.addEventListener("alpine:initialized", () => ready("initial"), {once: true});
  document.addEventListener("tetra:before-request", event => pending.add(event.detail.requestId));
  document.addEventListener("tetra:after-request", event => pending.delete(event.detail.requestId));
  document.addEventListener("tetra:component-updated", () => ready("update"));
})();
