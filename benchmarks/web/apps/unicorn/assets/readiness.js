/* Unicorn finishes handler refresh synchronously after its updated callback. */
(() => {
  let initialized = false;
  function ready(phase) {
    window.Alpine.nextTick(() => {
      const observerStart = performance.now();
      const component = window.Unicorn.getComponent("board");
      const board = document.getElementById("board");
      const pending = component.actionQueue.length + (component.currentActionQueue ? 1 : 0);
      if (!board || pending || component.debounceTimer) return;
      window.__citryBench?.ready({
        revision: Number(board.dataset.revision), session: board.dataset.session,
        operation: board.dataset.operation, phase, pending,
        observer_ms: performance.now() - observerStart,
      });
    });
  }
  window.unicornBenchStart = () => {
    initialized = true;
    window.Unicorn.addEventListener("updated", () => ready("update"));
  };
  document.addEventListener("alpine:initialized", () => {
    if (initialized) ready("initial");
  }, { once: true });
  // The runner writes the correlation value directly; defer its normal model event
  // into the same native Unicorn action request as the submitted form.
  document.addEventListener("submit", event => {
    if (event.target.closest("#board")) window.Unicorn.trigger("board", "operation");
  }, true);
})();
