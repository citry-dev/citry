(function() {

__citryRuntime.registerTypeOptions.bind(null, "CCarousel_f351c4", "212c8701a1cf6c448d4a88d02cd1957e4db1d6f93307d3dc5f773af4ec91998a")({
  props: {
    index: {},
    orientation: {},
    loop: {},
    disabled: {},
    controls: {},
    indicators: {},
    draggable: {},
    variant: {},
    size: {},
    onIndexChange: {},
  },
  onServerRender: ({component}) => {
    const root = component.$el;
    const data = component.serverDefaults;
    const props = component.$props;
    const effect = Citry.vue.watchEffect;
    const geometry = globalThis[Symbol.for("citry-ui:scroll-geometry")];
    if (geometry?.generation !== 1) {
      throw new Error("[citry-ui] CCarousel scroll geometry dependency did not load.");
    }
    const viewport = root.querySelector("[data-citry-carousel-viewport]");
    const track = viewport?.querySelector(':scope > [data-citry-ui-part="track"]');
    const previousButton = root.querySelector("[data-citry-carousel-previous]");
    const nextButton = root.querySelector("[data-citry-carousel-next]");
    const controls = root.querySelector(':scope > [data-citry-ui-part="controls"]');
    const indicators = root.querySelector("[data-citry-carousel-indicators]");
    if (!viewport || !track || !previousButton || !nextButton || !controls || !indicators) {
      throw new Error("[citry-ui] CCarousel requires its owned controls, viewport, track, and indicators.");
    }
    const handoffKey = Symbol.for("citry-ui:carousel-handoff");
    const previous = root[handoffKey];
    delete root[handoffKey];
    let active = true;
    let controlled = false;
    let internalIndex = previous?.serverIndex === data.index ? previous.index : data.index;
    let effectiveIndex = -1;
    let onIndexChange = null;
    let slides = [];
    let invalidStructure = false;
    let scrollFrame = null;
    let scrollTimer = null;
    let suppressionTimer = null;
    let reconcileFrame = null;
    let suppressScroll = false;
    let drag = null;
    let configuration = {
      orientation: data.orientation,
      loop: data.loop,
      disabled: data.disabled,
      controls: data.controls,
      indicators: data.indicators,
      draggable: data.draggable,
      variant: data.variant,
      size: data.size,
    };
    const invalidEpisodes = new Set();

    const reportInvalid = (name, value) => {
      if (invalidEpisodes.has(name)) return;
      invalidEpisodes.add(name);
      console.error(`[citry-ui] CCarousel ${name} received invalid client value.`, value, root);
    };
    const resolveBoolean = (name) => {
      const value = props[name] === undefined ? data[name] : props[name];
      if (typeof value === "boolean") {
        invalidEpisodes.delete(name);
        return value;
      }
      reportInvalid(name, value);
      return data[name];
    };
    const resolveChoice = (name, allowed) => {
      const value = props[name] === undefined ? data[name] : props[name];
      if (allowed.includes(value)) {
        invalidEpisodes.delete(name);
        return value;
      }
      reportInvalid(name, value);
      return data[name];
    };
    const resolveCallback = () => {
      const value = props.onIndexChange;
      if (value === undefined || value === null || typeof value === "function") {
        invalidEpisodes.delete("onIndexChange");
        return value ?? null;
      }
      reportInvalid("onIndexChange", value);
      return null;
    };
    const collect = () => {
      const children = [...track.children];
      const next = children.filter((element) => element.matches("[data-citry-carousel-slide]"));
      const values = new Set();
      let valid = next.length > 0 && next.length === children.length;
      next.forEach((slide, index) => {
        const value = slide.dataset.value;
        if (!value || values.has(value)) valid = false;
        values.add(value);
        slide.dataset.index = String(index);
      });
      slides = next;
      invalidStructure = !valid;
      if (!valid) reportInvalid("structure", children.length);
      else invalidEpisodes.delete("structure");
    };
    const reducedMotion = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
    const horizontalMaximum = () => geometry.maximum(viewport.scrollWidth, viewport.clientWidth);
    const horizontalRtl = () => getComputedStyle(viewport).direction === "rtl";
    const horizontalPosition = () => geometry.horizontalFromRaw(
      viewport.scrollLeft,
      horizontalMaximum(),
      horizontalRtl(),
    );
    const horizontalRaw = (position) => geometry.horizontalToRaw(
      position,
      horizontalMaximum(),
      horizontalRtl(),
    );
    const horizontalSlidePosition = (slide) => Math.abs(slide.offsetLeft - track.offsetLeft);
    const scrollPosition = (index) => {
      const slide = slides[index];
      if (!slide) return 0;
      return configuration.orientation === "horizontal"
        ? horizontalSlidePosition(slide)
        : slide.offsetTop - track.offsetTop;
    };
    const scrollToIndex = (index, instant = false) => {
      const position = scrollPosition(index);
      const currentPosition = configuration.orientation === "horizontal"
        ? horizontalPosition()
        : viewport.scrollTop;
      if (Math.abs(currentPosition - position) <= 1) {
        suppressScroll = false;
        return;
      }
      suppressScroll = true;
      viewport.scrollTo({
        left: configuration.orientation === "horizontal" ? horizontalRaw(position) : 0,
        top: configuration.orientation === "vertical" ? position : 0,
        behavior: instant || reducedMotion() ? "instant" : "smooth",
      });
      clearTimeout(suppressionTimer);
      suppressionTimer = setTimeout(() => { suppressScroll = false; }, instant ? 0 : 350);
    };
    const syncIndicators = () => {
      indicators.replaceChildren();
      slides.forEach((slide, index) => {
        const button = document.createElement("button");
        button.type = "button";
        button.dataset.citryUiPart = "indicator";
        button.dataset.index = String(index);
        button.setAttribute(
          "aria-label",
          slide.getAttribute("aria-label") ?? slide.dataset.value ?? String(index + 1),
        );
        indicators.append(button);
      });
    };
    const apply = (index, { scroll = false, instant = false } = {}) => {
      const next = invalidStructure || slides.length === 0
        ? -1
        : Math.min(Math.max(index, 0), slides.length - 1);
      effectiveIndex = next;
      root.dataset.orientation = configuration.orientation;
      root.dataset.variant = configuration.variant;
      root.dataset.size = configuration.size;
      root.toggleAttribute("data-loop", configuration.loop);
      root.toggleAttribute("data-disabled", configuration.disabled);
      root.toggleAttribute("data-draggable", configuration.draggable);
      if (next < 0) delete root.dataset.index;
      else root.dataset.index = String(next);
      controls.hidden = !configuration.controls;
      indicators.hidden = !configuration.indicators;
      previousButton.disabled = configuration.disabled || (!configuration.loop && next <= 0);
      nextButton.disabled = configuration.disabled || (!configuration.loop && next >= slides.length - 1);
      slides.forEach((slide, slideIndex) => slide.toggleAttribute("data-active", slideIndex === next));
      [...indicators.children].forEach((button, buttonIndex) => {
        button.toggleAttribute("aria-current", buttonIndex === next);
        button.disabled = configuration.disabled;
      });
      if (scroll && next >= 0) scrollToIndex(next, instant);
    };
    const notify = (index, previousIndex, reason, source, forced = false) => {
      onIndexChange?.(index, {
        index,
        previousIndex,
        value: slides[index]?.dataset.value ?? "",
        reason,
        controlled,
        forced,
        source,
      });
    };
    const request = (requested, reason, source, forced = false) => {
      if (!slides.length || configuration.disabled) return;
      let next = requested;
      if (configuration.loop) next = (next + slides.length) % slides.length;
      else next = Math.min(Math.max(next, 0), slides.length - 1);
      const previousIndex = effectiveIndex;
      if (next === previousIndex) return;
      if (!controlled || forced) {
        internalIndex = next;
        apply(next, { scroll: true });
      }
      notify(next, previousIndex, reason, source, forced);
    };
    const nearestIndex = () => {
      const position = configuration.orientation === "horizontal" ? horizontalPosition() : viewport.scrollTop;
      let best = 0;
      let distance = Number.POSITIVE_INFINITY;
      slides.forEach((slide, index) => {
        const candidate = configuration.orientation === "horizontal"
          ? horizontalSlidePosition(slide)
          : slide.offsetTop - track.offsetTop;
        const currentDistance = Math.abs(position - candidate);
        if (currentDistance < distance) {
          best = index;
          distance = currentDistance;
        }
      });
      return best;
    };
    const settleScroll = () => {
      scrollFrame = null;
      if (!active || suppressScroll || drag) return;
      const next = nearestIndex();
      if (next === effectiveIndex) return;
      const previousIndex = effectiveIndex;
      if (controlled) scrollToIndex(effectiveIndex);
      else {
        internalIndex = next;
        apply(next);
      }
      notify(next, previousIndex, "scroll", viewport);
    };
    const onScroll = () => {
      if (scrollFrame !== null) cancelAnimationFrame(scrollFrame);
      clearTimeout(scrollTimer);
      scrollTimer = setTimeout(() => {
        scrollFrame = requestAnimationFrame(settleScroll);
      }, 90);
    };
    const onClick = (event) => {
      if (configuration.disabled) return;
      const path = event.composedPath();
      if (path.includes(previousButton)) request(effectiveIndex - 1, "previous", previousButton);
      else if (path.includes(nextButton)) request(effectiveIndex + 1, "next", nextButton);
      else {
        const picker = path.find((element) => element?.matches?.('[data-citry-ui-part="indicator"]'));
        if (picker && indicators.contains(picker)) request(Number(picker.dataset.index), "picker", picker);
      }
    };
    const axisPosition = (event) => configuration.orientation === "horizontal" ? event.clientX : event.clientY;
    const axisScroll = () => configuration.orientation === "horizontal"
      ? horizontalPosition()
      : viewport.scrollTop;
    const onPointerDown = (event) => {
      if (
        !configuration.draggable
        || configuration.disabled
        || event.button !== 0
        || event.pointerType === "touch"
      ) return;
      drag = { id: event.pointerId, start: axisPosition(event), scroll: axisScroll() };
      viewport.setPointerCapture(event.pointerId);
      viewport.toggleAttribute("data-dragging", true);
    };
    const onPointerMove = (event) => {
      if (!drag || drag.id !== event.pointerId) return;
      const position = drag.scroll + drag.start - axisPosition(event);
      if (configuration.orientation === "horizontal") viewport.scrollLeft = horizontalRaw(position);
      else viewport.scrollTop = position;
      event.preventDefault();
    };
    const onPointerEnd = (event) => {
      if (!drag || drag.id !== event.pointerId) return;
      drag = null;
      viewport.toggleAttribute("data-dragging", false);
      if (viewport.hasPointerCapture(event.pointerId)) viewport.releasePointerCapture(event.pointerId);
      requestAnimationFrame(settleScroll);
    };
    const reconcile = () => {
      reconcileFrame = null;
      const previousSlides = slides;
      const previousValue = previousSlides[effectiveIndex]?.dataset.value ?? null;
      const previousIndex = effectiveIndex;
      collect();
      syncIndicators();
      if (invalidStructure) {
        apply(-1);
        return;
      }
      let next = previousValue === null
        ? internalIndex
        : slides.findIndex((slide) => slide.dataset.value === previousValue);
      let forced = false;
      if (next < 0) {
        next = Math.min(previousIndex, slides.length - 1);
        forced = previousIndex >= 0;
      }
      if (!controlled) internalIndex = next;
      apply(controlled ? effectiveIndex : next, { scroll: true, instant: true });
      if (forced) notify(next, previousIndex, "structure", root, true);
    };
    const scheduleReconcile = () => {
      if (reconcileFrame !== null) return;
      reconcileFrame = requestAnimationFrame(reconcile);
    };
    const observer = new MutationObserver(scheduleReconcile);
    observer.observe(track, { childList: true });
    const resizeObserver = new ResizeObserver(() => {
      if (effectiveIndex >= 0) scrollToIndex(effectiveIndex, true);
    });
    resizeObserver.observe(viewport);
    root.addEventListener("click", onClick, true);
    viewport.addEventListener("scroll", onScroll, { passive: true });
    viewport.addEventListener("pointerdown", onPointerDown);
    viewport.addEventListener("pointermove", onPointerMove);
    viewport.addEventListener("pointerup", onPointerEnd);
    viewport.addEventListener("pointercancel", onPointerEnd);
    collect();
    syncIndicators();

    effect(() => {
      configuration = {
        orientation: resolveChoice("orientation", ["horizontal", "vertical"]),
        loop: resolveBoolean("loop"),
        disabled: resolveBoolean("disabled"),
        controls: resolveBoolean("controls"),
        indicators: resolveBoolean("indicators"),
        draggable: resolveBoolean("draggable"),
        variant: resolveChoice("variant", ["plain", "surface"]),
        size: resolveChoice("size", ["sm", "md", "lg"]),
      };
      onIndexChange = resolveCallback();
      const supplied = props.index !== undefined;
      let next = internalIndex;
      if (supplied) {
        if (Number.isInteger(props.index) && props.index >= 0 && props.index < slides.length) {
          controlled = true;
          invalidEpisodes.delete("index");
          next = props.index;
          internalIndex = props.index;
        } else {
          controlled = false;
          reportInvalid("index", props.index);
        }
      } else {
        controlled = false;
        invalidEpisodes.delete("index");
      }
      apply(next, { scroll: true, instant: effectiveIndex < 0 });
      root.setAttribute("data-citry-carousel-initialized", "");
    });

    return () => {
      active = false;
      clearTimeout(scrollTimer);
      clearTimeout(suppressionTimer);
      cancelAnimationFrame(scrollFrame);
      cancelAnimationFrame(reconcileFrame);
      observer.disconnect();
      resizeObserver.disconnect();
      root.removeEventListener("click", onClick, true);
      viewport.removeEventListener("scroll", onScroll);
      viewport.removeEventListener("pointerdown", onPointerDown);
      viewport.removeEventListener("pointermove", onPointerMove);
      viewport.removeEventListener("pointerup", onPointerEnd);
      viewport.removeEventListener("pointercancel", onPointerEnd);
      root[handoffKey] = { index: internalIndex, serverIndex: data.index };
      root.removeAttribute("data-citry-carousel-initialized");
    };
  },
});

})();