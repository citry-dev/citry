$component({
  props: {order: {}, layout: {}, disabled: {}, onOrderChange: {}},
  init: ({els, data, props, effect, i18n}) => {
    const root = els[0];
    const list = root?.querySelector(':scope > [data-citry-sortable-items]');
    const status = root?.querySelector(':scope > [data-citry-ui-part="status"]');
    const instructions = root?.querySelector(':scope > [data-citry-sortable-instructions]');
    if (!(root instanceof HTMLElement) || !(list instanceof HTMLOListElement)
        || !(status instanceof HTMLElement) || !(instructions instanceof HTMLElement)) {
      throw new Error('[citry-ui] CSortable settled anatomy is invalid.');
    }
    const initial = [...list.querySelectorAll(':scope > [data-citry-sortable-item]')]
      .map(item => item.dataset.value);
    const byValue = new Map([...list.querySelectorAll(':scope > [data-citry-sortable-item]')]
      .map(item => [item.dataset.value, item]));
    const invalid = new Set();
    let accepted = data.order === null ? [...initial] : [...data.order];
    let controlled = false;
    let disabled = data.disabled;
    let layout = data.layout;
    let callback = null;
    let move = null;
    let pending = null;
    let pendingTouch = null;
    let alive = true;
    const report = (name, value) => {
      if (invalid.has(name)) return;
      invalid.add(name);
      console.error(`[citry-ui] CSortable ${name} received invalid client value.`, value, root);
    };
    const same = (left, right) => left.length === right.length
      && left.every((value, index) => value === right[index]);
    const validOrder = value => Array.isArray(value) && value.length === initial.length
      && value.every(item => typeof item === 'string' && byValue.has(item))
      && new Set(value).size === value.length;
    const values = () => [...list.querySelectorAll(':scope > [data-citry-sortable-item]')]
      .map(item => item.dataset.value);
    const format = (pattern, args) => Object.entries(args).reduce(
      (text, [name, value]) => text.replaceAll(`{${name}}`, String(value)), pattern,
    );
    const message = (kind, item, position) => {
      const args = {item, position: String(position), total: String(initial.length)};
      if (i18n && data.catalog[kind]) {
        try { return i18n.tr(`citry-ui-sortable-${kind.replace('_', '-')}`, args); }
        catch (error) { console.error('[citry-ui] CSortable translation failed.', error, root); }
      }
      return format(data.labels[kind], args);
    };
    const announce = (kind, activeMove) => {
      const item = byValue.get(activeMove.value);
      const position = values().indexOf(activeMove.value) + 1;
      status.textContent = message(kind, item.dataset.label, position);
    };
    const syncInputs = () => {
      for (const value of values()) {
        const item = byValue.get(value);
        const input = item.querySelector(':scope > [data-citry-sortable-input]');
        if (input) {
          input.disabled = disabled;
        }
      }
    };
    const syncOrder = order => {
      for (const value of order) list.append(byValue.get(value));
      accepted = [...order];
      syncInputs();
    };
    const moveItemTo = (item, nextIndex) => {
      const ordered = [...list.querySelectorAll(':scope > [data-citry-sortable-item]')];
      const without = ordered.filter(candidate => candidate !== item);
      const index = Math.max(0, Math.min(without.length, nextIndex));
      if (index === without.length) list.append(item);
      else list.insertBefore(item, without[index]);
    };
    const notify = (activeMove, sourceEvent) => {
      const next = values();
      const toIndex = next.indexOf(activeMove.value);
      if (same(next, activeMove.originOrder)) return;
      const detail = {
        order: [...next], previousOrder: [...activeMove.originOrder], value: activeMove.value,
        fromIndex: activeMove.originIndex, toIndex, source: activeMove.source,
        controlled, sourceEvent,
      };
      if (controlled) {
        pending = {next: [...next], activeMove};
        syncOrder(accepted);
      }
      else {
        accepted = [...next];
        syncInputs();
        root.dispatchEvent(new Event('input', {bubbles: true}));
        root.dispatchEvent(new Event('change', {bubbles: true}));
      }
      if (callback) {
        try { callback([...next], detail); }
        catch (error) { console.error('[citry-ui] CSortable onOrderChange callback failed.', error, root); }
      }
      if (!controlled) announce('dropped', activeMove);
    };
    const clearMoving = activeMove => {
      activeMove.item.removeAttribute('data-moving');
      activeMove.handle.removeAttribute('aria-pressed');
      root.removeAttribute('data-dragging');
      activeMove.item.style.removeProperty('position');
      activeMove.item.style.removeProperty('inset');
      activeMove.item.style.removeProperty('inline-size');
      activeMove.item.style.removeProperty('block-size');
      activeMove.item.style.removeProperty('z-index');
      activeMove.item.style.removeProperty('pointer-events');
      activeMove.item.style.removeProperty('transform');
      activeMove.placeholder?.remove();
      if (activeMove.source === 'pointer') {
        window.removeEventListener('pointermove', pointerMove);
        window.removeEventListener('pointerup', pointerEnd);
        window.removeEventListener('pointercancel', pointerEnd);
      }
    };
    const cancel = (event, announceCancel = true) => {
      if (!move) return;
      const activeMove = move;
      move = null;
      clearMoving(activeMove);
      syncOrder(activeMove.originOrder);
      if (announceCancel) announce('cancelled', activeMove);
      activeMove.handle.focus({preventScroll: true});
      if (event?.pointerId !== undefined && activeMove.handle.hasPointerCapture?.(event.pointerId)) {
        activeMove.handle.releasePointerCapture(event.pointerId);
      }
    };
    const beginKeyboard = (item, handle, event) => {
      const order = values();
      move = {
        source: 'keyboard', item, handle, value: item.dataset.value,
        originOrder: order, originIndex: order.indexOf(item.dataset.value), placeholder: null,
      };
      item.setAttribute('data-moving', '');
      handle.setAttribute('aria-pressed', 'true');
      root.setAttribute('data-dragging', '');
      announce('picked_up', move);
      event.preventDefault();
    };
    const beginPointer = (item, handle, event) => {
      if (move || disabled || item.hasAttribute('data-disabled')) return;
      const order = values();
      const rect = item.getBoundingClientRect();
      const placeholder = document.createElement('li');
      placeholder.setAttribute('data-placeholder', '');
      placeholder.setAttribute('data-citry-ui-part', 'placeholder');
      placeholder.style.blockSize = `${rect.height}px`;
      placeholder.style.inlineSize = `${rect.width}px`;
      item.before(placeholder);
      move = {
        source: 'pointer', item, handle, value: item.dataset.value,
        originOrder: order, originIndex: order.indexOf(item.dataset.value), placeholder,
        pointerId: event.pointerId, offsetX: event.clientX - rect.left, offsetY: event.clientY - rect.top,
      };
      item.setAttribute('data-moving', '');
      handle.setAttribute('aria-pressed', 'true');
      root.setAttribute('data-dragging', '');
      Object.assign(item.style, {
        position: 'fixed', inset: '0 auto auto 0', inlineSize: `${rect.width}px`,
        blockSize: `${rect.height}px`, zIndex: '1', pointerEvents: 'none',
      });
      item.style.transform = `translate(${event.clientX - move.offsetX}px, ${event.clientY - move.offsetY}px)`;
      handle.setPointerCapture?.(event.pointerId);
      window.addEventListener('pointermove', pointerMove, {passive: false});
      window.addEventListener('pointerup', pointerEnd);
      window.addEventListener('pointercancel', pointerEnd);
      announce('picked_up', move);
    };
    const pointerMove = event => {
      if (pendingTouch && event.pointerId === pendingTouch.event.pointerId) {
        const distance = Math.hypot(event.clientX - pendingTouch.x, event.clientY - pendingTouch.y);
        if (distance > 8) {
          clearTimeout(pendingTouch.timer);
          pendingTouch = null;
        }
      }
      if (!move || move.source !== 'pointer' || move.pointerId !== event.pointerId) return;
      event.preventDefault();
      move.item.style.transform = `translate(${event.clientX - move.offsetX}px, ${event.clientY - move.offsetY}px)`;
      const candidates = [...list.querySelectorAll(':scope > [data-citry-sortable-item]')]
        .filter(item => item !== move.item);
      if (!candidates.length) return;
      const nearest = candidates.map(item => {
        const rect = item.getBoundingClientRect();
        const dx = event.clientX - (rect.left + rect.width / 2);
        const dy = event.clientY - (rect.top + rect.height / 2);
        const distance = layout === 'vertical' ? Math.abs(dy)
          : layout === 'horizontal' ? Math.abs(dx) : Math.hypot(dx, dy);
        return {item, rect, distance, dx, dy};
      }).sort((left, right) => left.distance - right.distance)[0];
      const after = layout === 'vertical' ? nearest.dy > 0
        : layout === 'horizontal' ? nearest.dx > 0
        : event.clientY > nearest.rect.top + nearest.rect.height / 2
          || (Math.abs(event.clientY - (nearest.rect.top + nearest.rect.height / 2)) < nearest.rect.height / 3
            && event.clientX > nearest.rect.left + nearest.rect.width / 2);
      if (after) nearest.item.after(move.placeholder);
      else nearest.item.before(move.placeholder);
      if (event.clientY < 48) window.scrollBy({top: -16, behavior: 'instant'});
      else if (event.clientY > window.innerHeight - 48) window.scrollBy({top: 16, behavior: 'instant'});
    };
    const pointerEnd = event => {
      if (pendingTouch && event.pointerId === pendingTouch.event.pointerId) {
        clearTimeout(pendingTouch.timer);
        pendingTouch = null;
      }
      if (!move || move.source !== 'pointer' || move.pointerId !== event.pointerId) return;
      const activeMove = move;
      move = null;
      activeMove.placeholder.before(activeMove.item);
      clearMoving(activeMove);
      notify(activeMove, event);
      activeMove.handle.focus({preventScroll: true});
      if (activeMove.handle.hasPointerCapture?.(event.pointerId)) activeMove.handle.releasePointerCapture(event.pointerId);
    };
    const onPointerDown = event => {
      if (event.button !== 0 || disabled) return;
      const handle = event.target.closest('[data-citry-sortable-handle]');
      const item = handle?.closest('[data-citry-sortable-item]');
      if (!handle || !item || !list.contains(item) || item.hasAttribute('data-disabled')) return;
      if (event.pointerType === 'touch') {
        const pending = {event, item, handle, x: event.clientX, y: event.clientY, timer: 0};
        pending.timer = setTimeout(() => {
          if (pendingTouch !== pending) return;
          pendingTouch = null;
          beginPointer(item, handle, event);
        }, 180);
        pendingTouch = pending;
      } else {
        event.preventDefault();
        beginPointer(item, handle, event);
      }
    };
    const onKeyDown = event => {
      const handle = event.target.closest('[data-citry-sortable-handle]');
      const item = handle?.closest('[data-citry-sortable-item]');
      if (!handle || !item || !list.contains(item) || disabled || item.hasAttribute('data-disabled')) return;
      if (!move && (event.key === ' ' || event.key === 'Enter')) {
        beginKeyboard(item, handle, event);
        return;
      }
      if (!move || move.source !== 'keyboard' || move.item !== item) return;
      if (event.key === 'Escape') {
        event.preventDefault();
        cancel(event);
        return;
      }
      if (event.key === ' ' || event.key === 'Enter') {
        event.preventDefault();
        const activeMove = move;
        move = null;
        clearMoving(activeMove);
        notify(activeMove, event);
        activeMove.handle.focus({preventScroll: true});
        return;
      }
      const forwardKey = layout === 'vertical' ? 'ArrowDown'
        : getComputedStyle(root).direction === 'rtl' ? 'ArrowLeft' : 'ArrowRight';
      const backwardKey = layout === 'vertical' ? 'ArrowUp'
        : getComputedStyle(root).direction === 'rtl' ? 'ArrowRight' : 'ArrowLeft';
      let nextIndex = values().indexOf(move.value);
      if (event.key === 'Home') nextIndex = 0;
      else if (event.key === 'End') nextIndex = initial.length - 1;
      else if (event.key === forwardKey || (layout === 'grid' && event.key === 'ArrowDown')) nextIndex += 1;
      else if (event.key === backwardKey || (layout === 'grid' && event.key === 'ArrowUp')) nextIndex -= 1;
      else return;
      event.preventDefault();
      const before = values().indexOf(move.value);
      moveItemTo(item, nextIndex);
      if (values().indexOf(move.value) !== before) announce('moved', move);
    };
    const onReset = event => setTimeout(() => {
      if (!alive || event.defaultPrevented) return;
      if (same(initial, accepted)) return;
      const previous = [...accepted];
      const detail = {
        order: [...initial], previousOrder: previous, value: initial[0],
        fromIndex: previous.indexOf(initial[0]), toIndex: 0, source: 'reset', controlled, sourceEvent: event,
      };
      if (controlled) pending = {
        next: [...initial],
        activeMove: {source: 'reset', value: initial[0], originOrder: previous, originIndex: detail.fromIndex},
      };
      else {
        syncOrder(initial);
        root.dispatchEvent(new Event('input', {bubbles: true}));
        root.dispatchEvent(new Event('change', {bubbles: true}));
      }
      if (callback) {
        try { callback([...initial], detail); }
        catch (error) { console.error('[citry-ui] CSortable onOrderChange callback failed.', error, root); }
      }
    }, 0);
    const form = data.form ? document.getElementById(data.form) : root.closest('form');
    form?.addEventListener('reset', onReset);
    list.addEventListener('pointerdown', onPointerDown);
    list.addEventListener('keydown', onKeyDown);
    root.setAttribute('data-enhanced', '');
    root.setAttribute('data-citry-sortable-initialized', '');
    instructions.hidden = false;
    syncOrder(accepted);
    effect(() => {
      const nextCallback = props.onOrderChange;
      if (nextCallback === undefined || nextCallback === null) { callback = null; invalid.delete('onOrderChange'); }
      else if (typeof nextCallback === 'function') { callback = nextCallback; invalid.delete('onOrderChange'); }
      else report('onOrderChange', nextCallback);
      if (props.disabled !== undefined && typeof props.disabled !== 'boolean') report('disabled', props.disabled);
      else invalid.delete('disabled');
      disabled = typeof props.disabled === 'boolean' ? props.disabled : data.disabled;
      root.toggleAttribute('data-disabled', disabled);
      root.setAttribute('aria-disabled', String(disabled));
      root.querySelectorAll('[data-citry-sortable-handle]').forEach(handle => {
        handle.disabled = disabled || handle.closest('[data-citry-sortable-item]').hasAttribute('data-disabled');
      });
      syncInputs();
      const nextLayout = props.layout;
      if (nextLayout !== undefined && !['vertical', 'horizontal', 'grid'].includes(nextLayout)) report('layout', nextLayout);
      else {
        invalid.delete('layout');
        layout = nextLayout ?? data.layout;
        root.dataset.layout = layout;
      }
      const next = props.order;
      if (next === undefined || next === null) controlled = false;
      else if (validOrder(next)) {
        invalid.delete('order');
        controlled = true;
        if (move) cancel(null, false);
        const changed = !same(next, accepted);
        if (changed) syncOrder(next);
        if (pending && same(next, pending.next)) {
          const acceptedMove = pending.activeMove;
          byValue.get(acceptedMove.value)?.querySelector('[data-citry-sortable-handle]')?.focus({preventScroll: true});
          if (acceptedMove.source !== 'reset') announce('dropped', acceptedMove);
          pending = null;
        }
        else if (pending && changed) pending = null;
      } else report('order', next);
    });
    return () => {
      alive = false;
      if (pendingTouch) clearTimeout(pendingTouch.timer);
      cancel(null, false);
      form?.removeEventListener('reset', onReset);
      list.removeEventListener('pointerdown', onPointerDown);
      list.removeEventListener('keydown', onKeyDown);
      window.removeEventListener('pointermove', pointerMove);
      window.removeEventListener('pointerup', pointerEnd);
      window.removeEventListener('pointercancel', pointerEnd);
      root.removeAttribute('data-enhanced');
      root.removeAttribute('data-citry-sortable-initialized');
    };
  },
});
