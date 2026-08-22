$component({
  props: {
    open: {}, active: {}, dismissible: {}, closeOnEscape: {}, closeOnOutside: {},
    skippable: {}, scroll: {}, missingTarget: {}, size: {}, onOpenChange: {}, onActiveChange: {},
  },
  init: ({els, data, props, effect}) => {
    const host = els[0];
    const dialog = host?.querySelector(':scope > [data-citry-tour-dialog]');
    const surface = dialog?.querySelector(':scope > [data-citry-ui-part="surface"]');
    const spotlight = dialog?.querySelector(':scope > [data-citry-ui-part="spotlight"]');
    const panels = [...(surface?.querySelectorAll(':scope > [data-citry-tour-panel]') ?? [])];
    if (!(host instanceof HTMLElement) || !(dialog instanceof HTMLDialogElement)
        || !(surface instanceof HTMLElement) || !(spotlight instanceof HTMLElement)
        || panels.length === 0) {
      throw new Error('[citry-ui] CTour requires its owned anatomy.');
    }

    const invalid = new Map();
    const handoffKey = Symbol.for('citry-ui:tour-handoff');
    const previousHandoff = host[handoffKey];
    const handoff = previousHandoff?.kind === 'tour'
      ? previousHandoff : {kind: 'tour', restoreFocus: null};
    host[handoffKey] = handoff;
    let internalOpen = Boolean(data.open);
    let internalActive = data.active;
    let controlledOpen = false;
    let controlledActive = false;
    let appliedOpen = dialog.open;
    let active = data.active;
    let onOpenChange = null;
    let onActiveChange = null;
    let target = null;
    let resizeObserver = null;
    let mutationObserver = null;
    let frame = 0;
    let listening = false;
    let firstReconcile = true;
    let internalClose = false;
    let configuration = {
      dismissible: data.dismissible,
      closeOnEscape: data.closeOnEscape,
      closeOnOutside: data.closeOnOutside,
      skippable: data.skippable,
      scroll: data.scroll,
      missingTarget: data.missingTarget,
      size: data.size,
    };

    const report = (name, value) => {
      let shown;
      try { shown = JSON.stringify(value) ?? String(value); } catch { shown = String(value); }
      const fingerprint = `${typeof value}:${shown}`;
      if (invalid.get(name) === fingerprint) return;
      invalid.set(name, fingerprint);
      console.error(`[citry-ui] CTour ${name} received invalid client value ${shown}.`, host);
    };
    const boolean = name => {
      const value = props[name] === undefined ? data[name] : props[name];
      if (typeof value === 'boolean') { invalid.delete(name); return value; }
      report(name, value);
      return data[name];
    };
    const choice = (name, allowed) => {
      const value = props[name] === undefined ? data[name] : props[name];
      if (allowed.includes(value)) { invalid.delete(name); return value; }
      report(name, value);
      return data[name];
    };
    const callback = name => {
      const value = props[name];
      if (value === undefined || value === null || typeof value === 'function') {
        invalid.delete(name);
        return value ?? null;
      }
      report(name, value);
      return null;
    };
    const activators = () => [...host.querySelectorAll('[data-citry-tour-trigger]')]
      .filter(element => element.closest('[data-citry-tour-host]') === host);
    const panelTarget = index => {
      const id = panels[index]?.dataset.targetId;
      return id ? host.ownerDocument.getElementById(id) : null;
    };
    const targetExists = index => !panels[index]?.dataset.targetId || panelTarget(index)?.isConnected;
    const resolveIndex = (requested, direction = 1) => {
      if (!Number.isInteger(requested) || requested < 0 || requested >= panels.length) return null;
      if (targetExists(requested)) return requested;
      if (configuration.missingTarget === 'close') return null;
      for (let index = requested + direction; index >= 0 && index < panels.length; index += direction) {
        if (targetExists(index)) return index;
      }
      return null;
    };
    const updateActivators = open => {
      for (const activator of activators()) activator.setAttribute('aria-expanded', String(open));
    };
    const notifyOpen = (open, reason, source) => onOpenChange?.(open, {
      reason, active, value: panels[active].dataset.value, controlled: controlledOpen, source,
    });
    const notifyActive = (next, previous, reason, source) => onActiveChange?.(next, {
      previousActive: previous,
      value: panels[next].dataset.value,
      previousValue: panels[previous].dataset.value,
      reason,
      controlled: controlledActive,
      source,
    });
    const focusTitle = index => queueMicrotask(() => {
      if (appliedOpen && active === index) {
        panels[index].querySelector('[data-citry-ui-part="title"]')?.focus({preventScroll: true});
      }
    });

    const stopGeometry = () => {
      if (!listening) return;
      listening = false;
      globalThis.removeEventListener('resize', queueGeometry);
      host.ownerDocument.removeEventListener('scroll', queueGeometry, true);
      resizeObserver?.disconnect();
      mutationObserver?.disconnect();
      resizeObserver = null;
      mutationObserver = null;
      if (frame) cancelAnimationFrame(frame);
      frame = 0;
    };
    const clamp = (value, minimum, maximum) => Math.max(minimum, Math.min(value, maximum));
    const cssLength = (value, fallback) => {
      const raw = value.trim();
      const number = Number.parseFloat(raw);
      if (!Number.isFinite(number)) return fallback;
      if (raw.endsWith('rem')) {
        return number * Number.parseFloat(getComputedStyle(host.ownerDocument.documentElement).fontSize);
      }
      if (raw.endsWith('em')) return number * Number.parseFloat(getComputedStyle(host).fontSize);
      if (raw.endsWith('dvi') || raw.endsWith('vw')) return number * innerWidth / 100;
      if (raw.endsWith('dvb') || raw.endsWith('vh')) return number * innerHeight / 100;
      return number;
    };
    const intersectArea = (left, top, width, height, rect) => {
      const overlapWidth = Math.max(0, Math.min(left + width, rect.right) - Math.max(left, rect.left));
      const overlapHeight = Math.max(0, Math.min(top + height, rect.bottom) - Math.max(top, rect.top));
      return overlapWidth * overlapHeight;
    };
    const place = () => {
      frame = 0;
      if (!appliedOpen) return;
      const panel = panels[active];
      target = panelTarget(active);
      const targeted = Boolean(panel.dataset.targetId && target?.isConnected);
      host.toggleAttribute('data-targeted', targeted);
      if (!targeted) {
        spotlight.hidden = false;
        spotlight.dataset.mode = 'backdrop';
        for (const name of ['inset-inline-start', 'inset-block-start', 'inline-size', 'block-size']) {
          spotlight.style.removeProperty(name);
        }
        surface.style.removeProperty('inset-inline-start');
        surface.style.removeProperty('inset-block-start');
        surface.style.removeProperty('--_cui-tour-arrow-inline');
        surface.style.removeProperty('--_cui-tour-arrow-block');
        surface.dataset.placement = 'center';
        return;
      }

      spotlight.hidden = false;
      spotlight.dataset.mode = 'target';
      const rect = target.getBoundingClientRect();
      const hostStyle = getComputedStyle(host);
      const pad = cssLength(hostStyle.getPropertyValue('--_cui-tour-spotlight-padding'), 8);
      const gap = cssLength(hostStyle.getPropertyValue('--_cui-tour-offset'), 12);
      const protectedRect = {
        left: rect.left - pad,
        top: rect.top - pad,
        right: rect.right + pad,
        bottom: rect.bottom + pad,
      };
      spotlight.style.insetInlineStart = `${protectedRect.left}px`;
      spotlight.style.insetBlockStart = `${protectedRect.top}px`;
      spotlight.style.inlineSize = `${protectedRect.right - protectedRect.left}px`;
      spotlight.style.blockSize = `${protectedRect.bottom - protectedRect.top}px`;

      const box = surface.getBoundingClientRect();
      const margin = 8;
      const rtl = hostStyle.direction === 'rtl';
      const requested = panel.dataset.placement;
      const physical = requested === 'inline-start' ? (rtl ? 'right' : 'left')
        : requested === 'inline-end' ? (rtl ? 'left' : 'right') : requested;
      const opposite = physical.startsWith('top') ? physical.replace('top', 'bottom')
        : physical.startsWith('bottom') ? physical.replace('bottom', 'top')
        : physical === 'left' ? 'right' : physical === 'right' ? 'left' : 'bottom';
      const placements = [...new Set([physical, opposite, 'bottom', 'top', 'right', 'left'])];
      const rawPosition = placement => {
        let x = rect.left + (rect.width - box.width) / 2;
        let y = rect.bottom + gap + pad;
        if (placement.startsWith('top')) y = rect.top - box.height - gap - pad;
        if (placement === 'left') {
          x = rect.left - box.width - gap - pad;
          y = rect.top + (rect.height - box.height) / 2;
        }
        if (placement === 'right') {
          x = rect.right + gap + pad;
          y = rect.top + (rect.height - box.height) / 2;
        }
        if (placement.endsWith('-start')) x = rtl ? rect.right - box.width : rect.left;
        if (placement.endsWith('-end')) x = rtl ? rect.left : rect.right - box.width;
        return {x, y};
      };
      const candidates = placements.map((placement, order) => {
        const raw = rawPosition(placement);
        const x = clamp(raw.x, margin, Math.max(margin, innerWidth - box.width - margin));
        const y = clamp(raw.y, margin, Math.max(margin, innerHeight - box.height - margin));
        const overflow = Math.abs(x - raw.x) + Math.abs(y - raw.y);
        const overlap = intersectArea(x, y, box.width, box.height, protectedRect);
        return {placement, x, y, score: overlap * 1_000_000 + overflow * 100 + order};
      });
      const best = candidates.reduce((winner, candidate) => candidate.score < winner.score ? candidate : winner);
      surface.style.insetInlineStart = `${best.x}px`;
      surface.style.insetBlockStart = `${best.y}px`;
      surface.dataset.placement = best.placement;
      surface.style.setProperty(
        '--_cui-tour-arrow-inline',
        `${clamp(rect.left + rect.width / 2 - best.x, 18, Math.max(18, box.width - 18))}px`,
      );
      surface.style.setProperty(
        '--_cui-tour-arrow-block',
        `${clamp(rect.top + rect.height / 2 - best.y, 18, Math.max(18, box.height - 18))}px`,
      );
    };
    function queueGeometry() {
      if (!frame) frame = requestAnimationFrame(place);
    }
    const startGeometry = () => {
      stopGeometry();
      if (!appliedOpen) return;
      listening = true;
      globalThis.addEventListener('resize', queueGeometry);
      host.ownerDocument.addEventListener('scroll', queueGeometry, true);
      target = panelTarget(active);
      if (target && 'ResizeObserver' in globalThis) {
        resizeObserver = new ResizeObserver(queueGeometry);
        resizeObserver.observe(target);
      }
      mutationObserver = new MutationObserver(() => {
        if (panels[active].dataset.targetId && !panelTarget(active)?.isConnected) {
          const next = resolveIndex(active + 1, 1) ?? resolveIndex(active - 1, -1);
          if (next === null) requestOpen(false, 'missing-target', target);
          else requestActive(next, 'missing-target', target);
        }
      });
      mutationObserver.observe(host.ownerDocument.documentElement, {subtree: true, childList: true});
      queueGeometry();
    };

    const showPanel = (index, source = null) => {
      const previous = active;
      active = index;
      const panel = panels[index];
      panels.forEach((candidate, candidateIndex) => {
        const current = candidateIndex === index;
        candidate.hidden = !current;
        candidate.toggleAttribute('data-current', current);
        candidate.inert = !current;
      });
      host.dataset.active = String(index);
      host.dataset.value = panel.dataset.value;
      dialog.setAttribute('aria-labelledby', panel.dataset.titleId);
      if (panel.dataset.describe === 'true') dialog.setAttribute('aria-describedby', panel.dataset.descriptionId);
      else dialog.removeAttribute('aria-describedby');
      if (appliedOpen && configuration.scroll !== 'none') {
        panelTarget(index)?.scrollIntoView({behavior: configuration.scroll, block: 'nearest', inline: 'nearest'});
      }
      if (appliedOpen) {
        startGeometry();
        focusTitle(index);
      }
      return previous;
    };
    const applyOpen = (next, source = null) => {
      if (next) {
        if (!appliedOpen && source instanceof HTMLElement) handoff.restoreFocus = source;
        if (!dialog.open) dialog.show();
        appliedOpen = true;
        host.toggleAttribute('data-open', true);
        dialog.toggleAttribute('data-open', true);
        updateActivators(true);
        if (configuration.scroll !== 'none') {
          panelTarget(active)?.scrollIntoView({behavior: configuration.scroll, block: 'nearest', inline: 'nearest'});
        }
        startGeometry();
        focusTitle(active);
        return;
      }
      if (!appliedOpen && !dialog.open) return;
      appliedOpen = false;
      host.removeAttribute('data-open');
      dialog.removeAttribute('data-open');
      updateActivators(false);
      stopGeometry();
      if (dialog.open) {
        internalClose = true;
        dialog.close();
      }
      const restore = handoff.restoreFocus;
      handoff.restoreFocus = null;
      if (restore?.isConnected) queueMicrotask(() => restore.focus({preventScroll: true}));
    };
    const requestOpen = (next, reason, source) => {
      if (next === appliedOpen) return;
      if (next) {
        if (source instanceof HTMLElement) handoff.restoreFocus = source;
        const resolved = resolveIndex(active, 1);
        if (resolved === null) { notifyOpen(false, 'missing-target', source); return; }
        if (resolved !== active) showPanel(resolved, source);
      }
      if (controlledOpen) notifyOpen(next, reason, source);
      else {
        internalOpen = next;
        applyOpen(next, source);
        notifyOpen(next, reason, source);
      }
    };
    const requestActive = (next, reason, source) => {
      const direction = next >= active ? 1 : -1;
      const resolved = resolveIndex(next, direction);
      if (resolved === null) { requestOpen(false, 'missing-target', source); return; }
      if (resolved === active) return;
      const previous = active;
      if (controlledActive) notifyActive(resolved, previous, reason, source);
      else {
        internalActive = resolved;
        showPanel(resolved, source);
        notifyActive(resolved, previous, reason, source);
      }
    };
    const onClick = event => {
      const trigger = event.target.closest?.('[data-citry-tour-trigger]');
      if (trigger && trigger.closest('[data-citry-tour-host]') === host) {
        requestOpen(true, 'activator', trigger);
        return;
      }
      const action = event.target.closest?.('[data-citry-tour-action]');
      if (!action || !dialog.contains(action)) return;
      const kind = action.dataset.citryTourAction;
      if (kind === 'previous') requestActive(active - 1, 'previous', action);
      else if (kind === 'next') requestActive(active + 1, 'next', action);
      else if (kind === 'finish') requestOpen(false, 'finish', action);
      else if (kind === 'skip' && configuration.skippable) requestOpen(false, 'skip', action);
      else if (kind === 'close' && configuration.dismissible) requestOpen(false, 'close', action);
    };
    const onKeyDown = event => {
      if (!appliedOpen || event.defaultPrevented || event.key !== 'Escape'
          || !configuration.dismissible || !configuration.closeOnEscape) return;
      event.preventDefault();
      requestOpen(false, 'escape', event.target);
    };
    const onPointerDown = event => {
      if (!appliedOpen || !configuration.dismissible || !configuration.closeOnOutside
          || surface.contains(event.target)) return;
      requestOpen(false, 'outside', event.target);
    };
    const onNativeClose = event => {
      if (internalClose) { internalClose = false; return; }
      if (!appliedOpen) return;
      appliedOpen = false;
      internalOpen = false;
      host.removeAttribute('data-open');
      dialog.removeAttribute('data-open');
      updateActivators(false);
      stopGeometry();
      notifyOpen(false, 'native', event.target);
    };

    host.addEventListener('click', onClick);
    host.ownerDocument.addEventListener('keydown', onKeyDown, true);
    host.ownerDocument.addEventListener('pointerdown', onPointerDown, true);
    dialog.addEventListener('close', onNativeClose);
    effect(() => {
      configuration = {
        dismissible: boolean('dismissible'),
        closeOnEscape: boolean('closeOnEscape'),
        closeOnOutside: boolean('closeOnOutside'),
        skippable: boolean('skippable'),
        scroll: choice('scroll', ['auto', 'smooth', 'none']),
        missingTarget: choice('missingTarget', ['skip', 'close']),
        size: choice('size', ['sm', 'md', 'lg']),
      };
      onOpenChange = callback('onOpenChange');
      onActiveChange = callback('onActiveChange');
      const suppliedActive = props.active;
      let nextActive = internalActive;
      if (suppliedActive === undefined || suppliedActive === null) {
        controlledActive = false;
        invalid.delete('active');
      } else if (Number.isInteger(suppliedActive) && suppliedActive >= 0 && suppliedActive < panels.length) {
        controlledActive = true;
        nextActive = suppliedActive;
        invalid.delete('active');
      } else {
        controlledActive = false;
        report('active', suppliedActive);
      }
      const resolved = resolveIndex(nextActive, nextActive >= active ? 1 : -1);
      if (resolved !== null && resolved !== active) showPanel(resolved);
      const suppliedOpen = props.open;
      let nextOpen = internalOpen;
      if (suppliedOpen === undefined || suppliedOpen === null) {
        controlledOpen = false;
        invalid.delete('open');
      } else if (typeof suppliedOpen === 'boolean') {
        controlledOpen = true;
        nextOpen = suppliedOpen;
        invalid.delete('open');
      } else {
        controlledOpen = false;
        report('open', suppliedOpen);
      }
      host.dataset.size = configuration.size;
      surface.dataset.size = configuration.size;
      surface.querySelector('[data-citry-tour-action="close"]').hidden = !configuration.dismissible;
      for (const panel of panels) {
        const skip = panel.querySelector('[data-citry-tour-action="skip"]');
        if (skip) skip.hidden = !configuration.skippable;
      }
      if (nextOpen && resolveIndex(active, 1) === null) {
        if (appliedOpen) requestOpen(false, 'missing-target', null);
      } else if (nextOpen !== appliedOpen || firstReconcile) {
        applyOpen(nextOpen);
      }
      firstReconcile = false;
    });
    host.setAttribute('data-citry-tour-initialized', '');
    return () => {
      host.removeEventListener('click', onClick);
      host.ownerDocument.removeEventListener('keydown', onKeyDown, true);
      host.ownerDocument.removeEventListener('pointerdown', onPointerDown, true);
      dialog.removeEventListener('close', onNativeClose);
      stopGeometry();
      host.removeAttribute('data-citry-tour-initialized');
    };
  },
});
