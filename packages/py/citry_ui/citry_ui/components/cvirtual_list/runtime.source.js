$component({
  props: {overscan: {}, itemSize: {}, onRangeChange: {}},
  init: ({els, data, props, effect}) => {
    const root = els[0];
    const before = root.querySelector('[data-citry-virtual-list-spacer="before"]');
    const after = root.querySelector('[data-citry-virtual-list-spacer="after"]');
    const handoffKey = Symbol.for("citry-ui:virtual-list-handoff");
    const previous = root[handoffKey];
    const handoff = previous?.kind === "virtual-list" ? previous : {kind: "virtual-list", scrollTop: null};
    root[handoffKey] = handoff;
    const invalid = new Set();
    let alive = true;
    let frame = 0;
    let requestId = 0;
    let lastRequest = "";
    let sourceEvent = null;
    let reason = "initial";
    let effectiveOverscan = data.overscan;
    let effectiveItemSize = data.itemSize;
    let callback = null;
    const committedStart = data.startIndex;
    const committedEnd = data.startIndex
      + root.querySelectorAll(':scope > [data-citry-ui-part="track"] > [data-citry-ui-part="item"]').length;
    const report = (name, value) => {
      if (invalid.has(name)) return;
      invalid.add(name);
      console.error(`[citry-ui] CVirtualList ${name} received invalid client value.`, value, root);
    };
    const resolveInteger = (name, fallback, minimum, maximum = Number.MAX_SAFE_INTEGER) => {
      const value = props[name];
      if (value === undefined) { invalid.delete(name); return fallback; }
      if (Number.isInteger(value) && value >= minimum && value <= maximum) {
        invalid.delete(name);
        return value;
      }
      report(name, value);
      return fallback;
    };
    const resolveCallback = () => {
      const value = props.onRangeChange;
      if (value === undefined || value === null) {
        invalid.delete("onRangeChange");
        callback = null;
      } else if (typeof value === "function") {
        invalid.delete("onRangeChange");
        callback = value;
      } else {
        report("onRangeChange", value);
      }
    };
    const setPending = (pending) => {
      root.toggleAttribute("data-pending", pending);
      if (pending) root.setAttribute("aria-busy", "true");
      else root.removeAttribute("aria-busy");
    };
    const updateGeometry = () => {
      root.style.setProperty("--cui-virtual-list-item-size", `${effectiveItemSize}px`);
      before.style.blockSize = `${committedStart * effectiveItemSize}px`;
      after.style.blockSize = `${Math.max(0, data.totalCount - committedEnd) * effectiveItemSize}px`;
    };
    const desiredRange = () => {
      const size = Math.max(1, effectiveItemSize);
      const visibleStart = Math.max(0, Math.min(data.totalCount, Math.floor(root.scrollTop / size)));
      const visibleEnd = Math.max(
        visibleStart,
        Math.min(data.totalCount, Math.ceil((root.scrollTop + root.clientHeight) / size)),
      );
      let start = Math.max(0, visibleStart - effectiveOverscan);
      let end = Math.min(data.totalCount, visibleEnd + effectiveOverscan);
      const focused = root.contains(document.activeElement)
        ? document.activeElement?.closest?.('[data-citry-ui-part="item"]')
        : null;
      if (focused && root.contains(focused)) {
        const focusedIndex = Number(focused.getAttribute("data-index"));
        if (Number.isInteger(focusedIndex)) {
          start = Math.min(start, focusedIndex);
          end = Math.max(end, focusedIndex + 1);
        }
      }
      return {start, end, visibleStart, visibleEnd};
    };
    const calculate = () => {
      frame = 0;
      if (!alive) return;
      const range = desiredRange();
      const covered = committedStart <= range.start && committedEnd >= range.end;
      setPending(!covered);
      if (covered) {
        lastRequest = "";
        return;
      }
      const key = `${range.start}:${range.end}`;
      if (key === lastRequest) return;
      lastRequest = key;
      requestId += 1;
      if (callback) {
        try {
          callback({
            startIndex: range.start,
            endIndex: range.end,
            visibleStartIndex: range.visibleStart,
            visibleEndIndex: range.visibleEnd,
            requestId,
            reason,
            sourceEvent,
          });
        } catch (error) {
          console.error("[citry-ui] CVirtualList onRangeChange callback failed.", error, root);
        }
      }
      sourceEvent = null;
    };
    const schedule = (nextReason, event = null) => {
      reason = nextReason;
      sourceEvent = event;
      if (!frame) frame = requestAnimationFrame(calculate);
    };
    const onScroll = (event) => {
      handoff.scrollTop = root.scrollTop;
      schedule("scroll", event);
    };
    root.addEventListener("scroll", onScroll, {passive: true});
    const observer = new ResizeObserver(() => schedule("resize"));
    observer.observe(root);
    const firstOffset = Number.isFinite(handoff.scrollTop)
      ? handoff.scrollTop
      : data.initialIndex * effectiveItemSize;
    root.scrollTop = Math.min(
      Math.max(0, firstOffset),
      Math.max(0, data.totalCount * effectiveItemSize - root.clientHeight),
    );
    handoff.scrollTop = root.scrollTop;
    effect(() => {
      effectiveOverscan = resolveInteger("overscan", data.overscan, 0, 100);
      const maximumItemSize = Math.max(1, Math.floor(16000000 / Math.max(1, data.totalCount)));
      effectiveItemSize = resolveInteger("itemSize", data.itemSize, 1, maximumItemSize);
      resolveCallback();
      updateGeometry();
      schedule("configuration");
    });
    schedule("initial");
    root.setAttribute("data-citry-virtual-window-initialized", "");
    return () => {
      alive = false;
      handoff.scrollTop = root.scrollTop;
      root.removeEventListener("scroll", onScroll);
      observer.disconnect();
      if (frame) cancelAnimationFrame(frame);
      root.removeAttribute("data-citry-virtual-window-initialized");
    };
  },
});
