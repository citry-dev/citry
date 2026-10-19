(function() {

__citryRuntime.registerTypeOptions.bind(null, "CSplitter_bff85e", "6147643d028c7653d5bf00f4b3a11d5499a3572aaf5ea3790326d178aab8fce6")({
  props: {
    sizes: {}, orientation: {}, disabled: {}, keyboardStep: {}, variant: {}, size: {},
    onResizeStart: {}, onResize: {}, onResizeEnd: {},
  },
  onServerRender: ({component}) => {
    const root = component.$refs.splitterRoot.$el;
    const data = component.serverDefaults;
    const props = component.$props;
    const effect = Citry.vue.watchEffect;
    const invalidEpisodes = new Set();
    const panels = () => [...root.querySelectorAll(':scope > [data-citry-ui-part="panel"]')];
    const handles = () => [...root.querySelectorAll(':scope > [data-citry-ui-part="handle"]')];
    const initial = panels().map((panel) => Number(panel.dataset.sizePercent));
    const panelIds = panels().map((panel) => panel.dataset.panelId);
    const fingerprint = JSON.stringify(data.sizes ?? initial);
    const prior = root.__citryUiSplitterRuntime;
    let committed = prior && prior.serverFingerprint === fingerprint
      && JSON.stringify(prior.panelIds) === JSON.stringify(panelIds)
      ? [...prior.committed]
      : [...initial];
    let current = [...committed];
    let controlled = false;
    let callbackStart = null;
    let callbackResize = null;
    let callbackEnd = null;
    let configuration = {
      orientation: data.orientation,
      disabled: data.disabled,
      keyboardStep: data.keyboardStep,
      variant: data.variant,
      size: data.size,
    };
    let drag = null;
    let task = null;
    let generation = 0;
    let structureValid = false;

    const report = (name, value) => {
      if (invalidEpisodes.has(name)) return;
      invalidEpisodes.add(name);
      console.error(`[citry-ui] CSplitter ${name} received invalid client value`, value);
    };
    const resolveBoolean = (name, fallback) => {
      const supplied = props[name];
      if (supplied === undefined) { invalidEpisodes.delete(name); return fallback; }
      if (typeof supplied === 'boolean') { invalidEpisodes.delete(name); return supplied; }
      report(name, supplied); return fallback;
    };
    const resolveNumber = (name, fallback, minimum, maximum) => {
      const supplied = props[name];
      if (supplied === undefined) { invalidEpisodes.delete(name); return fallback; }
      if (typeof supplied === 'number' && Number.isFinite(supplied)
          && supplied >= minimum && supplied <= maximum) {
        invalidEpisodes.delete(name); return supplied;
      }
      report(name, supplied); return fallback;
    };
    const resolveChoice = (name, fallback, allowed) => {
      const supplied = props[name];
      if (supplied === undefined) { invalidEpisodes.delete(name); return fallback; }
      if (typeof supplied === 'string' && allowed.includes(supplied)) {
        invalidEpisodes.delete(name); return supplied;
      }
      report(name, supplied); return fallback;
    };
    const effectivelyDisabled = () => {
      if (configuration.disabled) return true;
      for (let node = root.parentElement; node; node = node.parentElement) {
        if (!(node instanceof HTMLFieldSetElement) || !node.disabled) continue;
        const legend = [...node.children].find((child) => child instanceof HTMLLegendElement);
        if (!(legend instanceof Element) || !legend.contains(root)) return true;
      }
      return false;
    };
    const limits = (index, sizes = current) => {
      const entries = panels();
      const before = entries[index];
      const after = entries[index + 1];
      const total = sizes[index] + sizes[index + 1];
      return {
        minimum: Math.max(Number(before.dataset.minSize), total - Number(after.dataset.maxSize)),
        maximum: Math.min(Number(before.dataset.maxSize), total - Number(after.dataset.minSize)),
      };
    };
    const validSizes = (value) => {
      const entries = panels();
      if (!Array.isArray(value) || value.length !== entries.length) return false;
      if (!value.every((item) => typeof item === 'number' && Number.isFinite(item))) return false;
      if (Math.abs(value.reduce((sum, item) => sum + item, 0) - 100) > 0.01) return false;
      return value.every((item, index) => item >= Number(entries[index].dataset.minSize)
        && item <= Number(entries[index].dataset.maxSize));
    };
    const invalidStructure = () => {
      const children = [...root.children];
      const entries = panels();
      const bars = handles();
      if (entries.length < 2 || bars.length !== entries.length - 1) return 'requires two or more panels';
      if (children.length !== entries.length + bars.length) return 'contains an unknown direct child';
      for (let index = 0; index < children.length; index += 1) {
        const expected = index % 2 === 0 ? 'panel' : 'handle';
        if (children[index].dataset.citryUiPart !== expected) return 'panel and handle order is invalid';
      }
      return null;
    };
    const sync = () => {
      const problem = invalidStructure();
      if (problem) {
        structureValid = false;
        report('structure', problem);
        root.removeAttribute('data-citry-splitter-initialized');
        handles().forEach((handle) => { handle.tabIndex = -1; handle.setAttribute('aria-disabled', 'true'); });
        return;
      }
      invalidEpisodes.delete('structure');
      structureValid = true;
      let supplied = props.sizes;
      if (supplied === null) supplied = undefined;
      if (supplied === undefined) {
        invalidEpisodes.delete('sizes');
        if (controlled) committed = [...current];
        controlled = false;
        current = [...committed];
      } else if (validSizes(supplied)) {
        invalidEpisodes.delete('sizes');
        controlled = true;
        current = [...supplied];
      } else {
        report('sizes', supplied);
        controlled = true;
        current = [...committed];
      }
      const disabled = effectivelyDisabled();
      if (disabled && drag) endDrag(drag.lastEvent, true);
      root.dataset.orientation = configuration.orientation;
      root.dataset.variant = configuration.variant;
      root.dataset.size = configuration.size;
      root.toggleAttribute('data-disabled', disabled);
      panels().forEach((panel, index) => {
        const value = Math.round(current[index] * 10000) / 10000;
        panel.dataset.sizePercent = String(value);
        panel.style.flex = `${value} 1 0px`;
      });
      handles().forEach((handle, index) => {
        const range = limits(index);
        handle.setAttribute(
          'aria-orientation', configuration.orientation === 'horizontal' ? 'vertical' : 'horizontal'
        );
        handle.setAttribute('aria-valuemin', String(Math.round(range.minimum * 100) / 100));
        handle.setAttribute('aria-valuemax', String(Math.round(range.maximum * 100) / 100));
        handle.setAttribute('aria-valuenow', String(Math.round(current[index] * 100) / 100));
        handle.setAttribute('aria-disabled', disabled ? 'true' : 'false');
        handle.tabIndex = disabled ? -1 : 0;
        handle.toggleAttribute('data-disabled', disabled);
      });
      root.__citryUiSplitterRuntime = {
        serverFingerprint: fingerprint, panelIds, committed: [...committed],
      };
      root.setAttribute('data-citry-splitter-initialized', '');
    };
    const schedule = () => {
      if (task !== null) return;
      const scheduled = generation;
      task = setTimeout(() => { task = null; if (scheduled === generation) sync(); }, 0);
    };
    const detail = (sizes, previous, index, source, event) => ({
      sizes: [...sizes], previousSizes: [...previous], handleIndex: index,
      controlled, source, sourceEvent: event,
    });
    const request = (next, previous, index, source, event) => {
      callbackResize?.([...next], detail(next, previous, index, source, event));
      if (!controlled) { committed = [...next]; current = [...next]; sync(); }
      else schedule();
    };
    const handleForEvent = (event) => event.composedPath().find(
      (node) => node instanceof Element && node.matches?.('[data-citry-ui-part="handle"]')
        && node.closest('[data-citry-ui-part="splitter"]') === root
    );
    const coordinate = (event) => configuration.orientation === 'horizontal' ? event.clientX : event.clientY;
    const onPointerDown = (event) => {
      const handle = handleForEvent(event);
      if (!(handle instanceof HTMLElement) || event.button !== 0
          || effectivelyDisabled() || !structureValid) return;
      event.preventDefault();
      const index = Number(handle.dataset.handleIndex);
      const startSizes = [...current];
      drag = {
        handle, index, pointerId: event.pointerId, start: coordinate(event),
        startSizes, lastSizes: startSizes, lastEvent: event,
      };
      handle.setPointerCapture(event.pointerId);
      handle.setAttribute('data-active', '');
      root.setAttribute('data-resizing', '');
      callbackStart?.(detail(startSizes, startSizes, index, 'pointer', event));
    };
    const onPointerMove = (event) => {
      if (!drag || event.pointerId !== drag.pointerId) return;
      const rect = root.getBoundingClientRect();
      const dimension = configuration.orientation === 'horizontal' ? rect.width : rect.height;
      if (!(dimension > 0)) return;
      let delta = (coordinate(event) - drag.start) / dimension * 100;
      if (configuration.orientation === 'horizontal' && getComputedStyle(root).direction === 'rtl') delta *= -1;
      const range = limits(drag.index, drag.startSizes);
      const before = Math.max(range.minimum, Math.min(range.maximum, drag.startSizes[drag.index] + delta));
      const next = [...drag.startSizes];
      const total = drag.startSizes[drag.index] + drag.startSizes[drag.index + 1];
      next[drag.index] = before;
      next[drag.index + 1] = total - before;
      drag.lastSizes = next;
      drag.lastEvent = event;
      request(next, drag.startSizes, drag.index, 'pointer', event);
    };
    function endDrag(event, cancelled = false) {
      if (!drag) return;
      const transaction = drag;
      drag = null;
      if (transaction.handle.hasPointerCapture?.(transaction.pointerId)) {
        transaction.handle.releasePointerCapture(transaction.pointerId);
      }
      transaction.handle.removeAttribute('data-active');
      root.removeAttribute('data-resizing');
      const finalSizes = cancelled ? current : transaction.lastSizes;
      callbackEnd?.([...finalSizes], detail(
        finalSizes, transaction.startSizes, transaction.index, 'pointer', event ?? transaction.lastEvent
      ));
    }
    const onPointerEnd = (event) => {
      if (drag && event.pointerId === drag.pointerId) endDrag(event);
    };
    const onKeyDown = (event) => {
      const handle = handleForEvent(event);
      if (!(handle instanceof HTMLElement) || effectivelyDisabled() || !structureValid) return;
      const index = Number(handle.dataset.handleIndex);
      const range = limits(index);
      let nextBefore = null;
      const multiplier = event.shiftKey ? 4 : 1;
      const amount = configuration.keyboardStep * multiplier;
      if (event.key === 'Home') nextBefore = range.minimum;
      else if (event.key === 'End') nextBefore = range.maximum;
      else if (configuration.orientation === 'horizontal' && ['ArrowLeft', 'ArrowRight'].includes(event.key)) {
        const physical = event.key === 'ArrowRight' ? amount : -amount;
        nextBefore = current[index] + (getComputedStyle(root).direction === 'rtl' ? -physical : physical);
      } else if (configuration.orientation === 'vertical' && ['ArrowUp', 'ArrowDown'].includes(event.key)) {
        nextBefore = current[index] + (event.key === 'ArrowDown' ? amount : -amount);
      }
      if (nextBefore === null) return;
      event.preventDefault();
      nextBefore = Math.max(range.minimum, Math.min(range.maximum, nextBefore));
      if (Math.abs(nextBefore - current[index]) < 0.0001) return;
      const previous = [...current];
      const total = current[index] + current[index + 1];
      const next = [...current];
      next[index] = nextBefore;
      next[index + 1] = total - nextBefore;
      callbackStart?.(detail(previous, previous, index, 'keyboard', event));
      request(next, previous, index, 'keyboard', event);
      callbackEnd?.([...next], detail(next, previous, index, 'keyboard', event));
    };
    root.addEventListener('pointerdown', onPointerDown);
    root.addEventListener('pointermove', onPointerMove);
    root.addEventListener('pointerup', onPointerEnd);
    root.addEventListener('pointercancel', onPointerEnd);
    root.addEventListener('keydown', onKeyDown);
    const observer = new MutationObserver(schedule);
    observer.observe(root, {childList: true});
    const fieldsets = [];
    for (let ancestor = root.parentElement; ancestor; ancestor = ancestor.parentElement) {
      if (!(ancestor instanceof HTMLFieldSetElement)) continue;
      const item = new MutationObserver(schedule);
      item.observe(ancestor, {childList: true, attributes: true, attributeFilter: ['disabled']});
      fieldsets.push(item);
    }
    const stop = effect(() => {
      callbackStart = typeof props.onResizeStart === 'function' ? props.onResizeStart : null;
      callbackResize = typeof props.onResize === 'function' ? props.onResize : null;
      callbackEnd = typeof props.onResizeEnd === 'function' ? props.onResizeEnd : null;
      configuration = {
        orientation: resolveChoice('orientation', data.orientation, ['horizontal', 'vertical']),
        disabled: resolveBoolean('disabled', data.disabled),
        keyboardStep: resolveNumber('keyboardStep', data.keyboardStep, 0.1, 25),
        variant: resolveChoice('variant', data.variant, ['plain', 'soft', 'outline']),
        size: resolveChoice('size', data.size, ['sm', 'md', 'lg']),
      };
      schedule();
    });
    schedule();
    return () => {
      generation += 1;
      if (task !== null) clearTimeout(task);
      if (drag) endDrag(drag.lastEvent, true);
      root.__citryUiSplitterRuntime = {serverFingerprint: fingerprint, panelIds, committed: [...committed]};
      stop?.(); observer.disconnect(); fieldsets.forEach((item) => item.disconnect());
      root.removeEventListener('pointerdown', onPointerDown);
      root.removeEventListener('pointermove', onPointerMove);
      root.removeEventListener('pointerup', onPointerEnd);
      root.removeEventListener('pointercancel', onPointerEnd);
      root.removeEventListener('keydown', onKeyDown);
      root.removeAttribute('data-resizing');
      root.removeAttribute('data-citry-splitter-initialized');
    };
  },
})

})();