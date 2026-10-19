/* The normal ReactPy script component calls this after its commit effect. */
(() => {
  let localReady = false;
  let pending = 0;
  let candidate = null;
  function finish() {
    if (!localReady || !candidate || pending !== 0) return;
    const board = document.querySelector("#board");
    if (!board || Number(board.dataset.revision) !== candidate.revision ||
        board.dataset.operation !== candidate.operation || board.dataset.session !== candidate.session) return;
    const detail = candidate;
    candidate = null;
    window.__citryBench?.ready({ ...detail, pending });
  }
  document.addEventListener("submit", (event) => {
    if (event.target.closest("#board")) pending += 1;
  }, true);
  window.__reactpyBoardObserver = {
    localReady() { localReady = true; finish(); },
    committed(detail) {
      if (detail.phase === "update") pending -= 1;
      candidate = detail;
      queueMicrotask(finish);
    },
  };
})();
