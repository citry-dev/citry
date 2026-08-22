"""Private active-descendant collection runtime shared by Citry UI families."""

from citry.ext.dependencies import Script

ACTIVE_DESCENDANT_RUNTIME_KEY = "citry-ui:active-descendant-runtime"
ACTIVE_DESCENDANT_RUNTIME_GENERATION = 1

ACTIVE_DESCENDANT_RUNTIME_JS = r"""
  (() => {
    const key = Symbol.for("citry-ui:active-descendant-runtime");
    const installed = globalThis[key];
    if (installed !== undefined) {
      if (installed.generation !== 1) {
        throw new Error(
          "[citry-ui] cannot replace an incompatible active-descendant runtime; "
            + "a full page reload is required.",
        );
      }
      return;
    }

    const ownerKey = Symbol.for("citry-ui:active-descendant-owner");
    const canonicalizeText = (
      value,
      { compatibility = false, collapseWhitespace = false, trim = false } = {},
    ) => {
      let text = String(value);
      if (compatibility) text = text.normalize("NFKC");
      if (collapseWhitespace) text = text.replace(/\s+/gu, " ");
      if (trim) text = text.trim();
      return text.toLowerCase();
    };
    const canonicalText = (value) => canonicalizeText(value, {
      compatibility: true,
      collapseWhitespace: true,
      trim: true,
    });

    const create = ({ input, listbox, idPrefix }) => {
      if (!(input instanceof HTMLElement) || !(listbox instanceof HTMLElement)) {
        throw new TypeError("[citry-ui] active-descendant requires an input and listbox.");
      }
      const previous = listbox[ownerKey] ?? null;
      const retained = Boolean(previous
        && previous.input === input
        && previous.listbox === listbox
        && previous.idPrefix === idPrefix);
      if (previous && !retained) previous.abort();
      const owner = {
        active: true,
        input,
        listbox,
        idPrefix,
        ids: retained ? previous.ids : new Map(),
        nextId: retained ? previous.nextId : 1,
        lastScrolled: retained ? previous.lastScrolled : null,
        abort() {
          input.removeAttribute("aria-activedescendant");
          owner.ids.clear();
          owner.lastScrolled = null;
          owner.active = false;
        },
      };
      listbox[ownerKey] = owner;

      const idFor = (value) => {
        if (!owner.ids.has(value)) {
          owner.ids.set(value, `${idPrefix}-${owner.nextId}`);
          owner.nextId += 1;
        }
        return owner.ids.get(value);
      };
      const retain = (values) => {
        const current = new Set(values);
        for (const value of owner.ids.keys()) {
          if (!current.has(value)) owner.ids.delete(value);
        }
      };
      const eligible = (items) => items.filter((item) => !item.disabled && item.visible !== false);
      const edge = (items, direction = 1) => {
        const available = eligible(items);
        return direction < 0 ? available.at(-1)?.value ?? null : available[0]?.value ?? null;
      };
      const move = (items, activeValue, delta, loop = true) => {
        const available = eligible(items);
        if (!available.length) return null;
        const current = available.findIndex((item) => item.value === activeValue);
        if (current < 0) return delta < 0 ? available.at(-1).value : available[0].value;
        const candidate = current + delta;
        if (candidate >= 0 && candidate < available.length) return available[candidate].value;
        if (!loop) return activeValue;
        return candidate < 0 ? available.at(-1).value : available[0].value;
      };
      const nearest = (items, activeValue, previousOrder = []) => {
        const available = eligible(items);
        if (available.some((item) => item.value === activeValue)) return activeValue;
        const availableValues = new Set(available.map((item) => item.value));
        const index = previousOrder.indexOf(activeValue);
        if (index >= 0) {
          for (let offset = 1; offset < previousOrder.length; offset += 1) {
            const following = previousOrder[index + offset];
            if (following !== undefined && availableValues.has(following)) return following;
            const preceding = previousOrder[index - offset];
            if (preceding !== undefined && availableValues.has(preceding)) return preceding;
          }
        }
        return available[0]?.value ?? null;
      };
      const sync = ({
        items,
        activeValue,
        selectedValue = null,
        open = true,
        unavailable = false,
        optionFor,
        selectedAttribute = "data-selected",
        activeAttribute = "data-active",
        scroll = true,
      }) => {
        let activeElement = null;
        for (const item of items) {
          const option = optionFor(item.value);
          if (
            !(option instanceof HTMLElement)
            || !option.isConnected
            || option.getRootNode() !== listbox.getRootNode()
            || !listbox.contains(option)
          ) continue;
          const active = open && !unavailable && !item.disabled && item.value === activeValue;
          const selected = item.value === selectedValue;
          const selectedWithoutActive = selected && (!open || activeValue === null);
          option.setAttribute("aria-selected", active || selectedWithoutActive ? "true" : "false");
          option.toggleAttribute(selectedAttribute, selected);
          option.toggleAttribute(activeAttribute, active);
          if (active) activeElement = option;
        }
        if (activeElement) {
          input.setAttribute("aria-activedescendant", activeElement.id);
          if (scroll && owner.lastScrolled !== activeValue) {
            activeElement.scrollIntoView({ block: "nearest" });
            owner.lastScrolled = activeValue;
          }
        } else {
          input.removeAttribute("aria-activedescendant");
          owner.lastScrolled = null;
        }
        return activeElement;
      };
      const resetScroll = () => {
        owner.lastScrolled = null;
      };
      const cleanup = () => {
        owner.active = false;
        if (listbox[ownerKey] !== owner) return;
        owner.abort();
        delete listbox[ownerKey];
      };
      return { idFor, retain, edge, move, nearest, sync, resetScroll, cleanup, retained };
    };

    globalThis[key] = { generation: 1, canonicalizeText, canonicalText, create };
  })();
"""

ACTIVE_DESCENDANT_RUNTIME_DEPENDENCY = Script(content=ACTIVE_DESCENDANT_RUNTIME_JS)


__all__: list[str] = []
