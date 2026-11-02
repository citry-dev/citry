(function() {

__citryRuntime.registerTypeOptions.bind(null, "CAlert_0cc501", "f19d408b4fec0ec1b6817c1c784c81e61024558eeb2df579d6f10cf248390606")({
  props: {
    intent: {},
    variant: {},
    size: {},
    announce: {},
    icon: {},
  },
  onServerRender: ({component}) => {
    const root = component.$el;
    const data = component.serverDefaults;
    const props = component.$props;
    const indicator = root.querySelector('[data-citry-ui-part="indicator"]');
    const content = root.querySelector('[data-citry-ui-part="content"]');
    const automaticGlyphs = Array.from(
      indicator.querySelectorAll("[data-cui-alert-intent]"),
    );
    const allowedValues = {
      intent: ["info", "success", "warn", "error"],
      variant: ["soft", "solid", "outline"],
      size: ["sm", "md", "lg"],
      announce: ["off", "polite", "assertive"],
    };
    const invalidEpisodes = new Set();

    const describeValue = (value) => {
      try {
        return JSON.stringify(value) ?? String(value);
      } catch {
        return String(value);
      }
    };
    const reportInvalid = (name, value) => {
      if (invalidEpisodes.has(name)) {
        return;
      }
      invalidEpisodes.add(name);
      const describedValue = describeValue(value);
      console.error(
        `[citry-ui] CAlert ${name} received invalid client value ${describedValue}; `
          + "using the server-rendered fallback.",
        root,
      );
    };
    const resolveChoice = (name) => {
      const value = props[name] === undefined ? data[name] : props[name];
      if (allowedValues[name].includes(value)) {
        invalidEpisodes.delete(name);
        return value;
      }
      reportInvalid(name, value);
      return data[name];
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
    const setData = (name, value) => {
      if (root.dataset[name] !== value) {
        root.dataset[name] = value;
      }
    };
    const setRole = (announce) => {
      const role = announce === "polite"
        ? "status"
        : announce === "assertive"
          ? "alert"
          : null;
      if (role === null) {
        content.removeAttribute("role");
      } else if (content.getAttribute("role") !== role) {
        content.setAttribute("role", role);
      }
    };

    Citry.vue.watchEffect(() => {
      const next = {
        intent: resolveChoice("intent"),
        variant: resolveChoice("variant"),
        size: resolveChoice("size"),
        announce: resolveChoice("announce"),
        icon: resolveBoolean("icon"),
      };
      setData("intent", next.intent);
      setData("variant", next.variant);
      setData("size", next.size);
      setData("announce", next.announce);
      root.toggleAttribute("data-icon", next.icon);
      if (indicator.hidden === next.icon) {
        indicator.hidden = !next.icon;
      }
      for (const glyph of automaticGlyphs) {
        const hidden = glyph.dataset.cuiAlertIntent !== next.intent;
        if (glyph.hasAttribute("data-cui-alert-hidden") !== hidden) {
          glyph.toggleAttribute("data-cui-alert-hidden", hidden);
        }
      }
      setRole(next.announce);
    });
    root.setAttribute("data-citry-alert-initialized", "");

    return () => {
      root.removeAttribute("data-citry-alert-initialized");
    };
  },
});

})();