(function() {

__citryRuntime.registerTypeOptions.bind(null, "CProgress_dbddf8", "1abde4c0caaa60e3592e55c8c6ec16301908416b982eb7b6ac7eb587909ac014")({
  props: {
    value: {},
    label: {},
    valueText: {},
    intent: {},
    size: {},
    shape: {},
  },
  onServerRender: ({component}) => {
    const progress = component.$el;
    const data = component;
    const defaults = component.serverDefaults;
    const props = component.$props;
    const i18n = component.$i18n;
    const allowedValues = {
      intent: ["neutral", "primary", "success", "warn", "danger"],
      size: ["sm", "md", "lg"],
      shape: ["square", "rounded", "pill"],
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
      console.error(
        `[citry-ui] CProgress ${name} received invalid client value ${describeValue(value)}; `
          + "using the server-rendered fallback.",
        progress,
      );
    };
    const sourceValue = (name) => props[name] === undefined ? defaults[name] : props[name];
    const resolveChoice = (name) => {
      const value = sourceValue(name);
      if (allowedValues[name].includes(value)) {
        invalidEpisodes.delete(name);
        return value;
      }
      reportInvalid(name, value);
      return defaults[name];
    };
    const resolveLabel = () => {
      const value = sourceValue("label");
      if (typeof value === "string" && value.length > 0) {
        invalidEpisodes.delete("label");
        return value;
      }
      reportInvalid("label", value);
      return defaults.label;
    };
    const resolveValueText = () => {
      const value = sourceValue("valueText");
      if (value === null || (typeof value === "string" && value.length > 0)) {
        invalidEpisodes.delete("valueText");
        return value;
      }
      reportInvalid("valueText", value);
      return defaults.valueText;
    };
    const resolveValue = () => {
      const value = sourceValue("value");
      if (
        value === null
        || (
          typeof value === "number"
          && Number.isFinite(value)
          && value >= 0
          && value <= data.max
        )
      ) {
        invalidEpisodes.delete("value");
        return value;
      }
      reportInvalid("value", value);
      return defaults.value;
    };
    const setAttribute = (name, value) => {
      if (value === null) {
        progress.removeAttribute(name);
      } else if (progress.getAttribute(name) !== String(value)) {
        progress.setAttribute(name, String(value));
      }
    };
    const setData = (name, value) => {
      if (progress.dataset[name] !== value) {
        progress.dataset[name] = value;
      }
    };

    const fallbackBinding = i18n && data.catalogFallbackText
      ? i18n.bind({
          message: "citry-ui-progress-value-text",
          values: () => {
            const value = resolveValue();
            return {
              label: resolveLabel(),
              value: i18n.format.number(value ?? 0, {format: "citry-ui-progress-value"}),
              max: i18n.format.number(data.max, {format: "citry-ui-progress-value"}),
            };
          },
          onChange: (text) => {
            progress.textContent = resolveValue() === null ? resolveLabel() : text;
          },
        })
      : null;

    Citry.vue.watchEffect(() => {
      const value = resolveValue();
      setAttribute("value", value);
      setAttribute("aria-label", resolveLabel());
      setAttribute("aria-valuetext", resolveValueText());
      setData("state", value === null ? "indeterminate" : "determinate");
      setData("intent", resolveChoice("intent"));
      setData("size", resolveChoice("size"));
      setData("shape", resolveChoice("shape"));
    });

    progress.setAttribute("data-citry-progress-initialized", "");
    return () => {
      fallbackBinding?.dispose();
      progress.removeAttribute("data-citry-progress-initialized");
    };
  },
});

})();