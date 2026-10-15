/* Observe completed framework updates; application events stay in Citry. */
(() => {
  let pending = 0;
  function ready(phase) {
    window.Alpine.nextTick(() => {
      const board = document.getElementById("board");
      if (!board || pending !== 0 || !Citry.events._internal.alpineStarted) return;
      const observerStart = performance.now();
      const work = Citry.events._internal.debug();
      const observerMs = performance.now() - observerStart;
      if (work.queuedCalls !== 0 || work.pendingFlushes !== 0) return;
      window.__citryBench?.ready({
        revision: Number(board.dataset.revision),
        session: board.dataset.session,
        operation: board.dataset.operation,
        phase,
        pending,
        observer_ms: observerMs,
      });
    });
  }
  document.addEventListener("alpine:initialized", () => ready("initial"), { once: true });
  document.addEventListener("citry:events:before", () => { pending += 1; });
  document.addEventListener("citry:events:after", (event) => {
    pending -= 1;
    if (event.detail.ok) ready("update");
  });
})();
