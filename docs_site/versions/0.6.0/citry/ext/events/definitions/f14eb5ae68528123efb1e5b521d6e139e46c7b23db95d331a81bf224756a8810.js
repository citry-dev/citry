(function() {

__citryRuntime.registerTypeOptions.bind(null, "CSpinner_c40717", "98b446b9d4f55347c2a7436c2d7e6701db860bb4a6fd843b2eb0ce3b36919abf")({
  props: {
    label: {},
    intent: {},
    size: {},
  },
  onServerRender: ({component}) => {
    const spinner = component.$el;
    const data = component.serverDefaults;
    const props = component.$props;
    const allowedValues = {
      intent: ["neutral", "primary", "success", "warn", "danger"],
      size: ["sm", "md", "lg"],
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
        `[citry-ui] CSpinner ${name} received invalid client value ${describeValue(value)}; `
          + "using the server-rendered fallback.",
        spinner,
      );
    };
    const sourceValue = (name) => props[name] === undefined ? data[name] : props[name];
    const resolveChoice = (name) => {
      const value = sourceValue(name);
      if (allowedValues[name].includes(value)) {
        invalidEpisodes.delete(name);
        return value;
      }
      reportInvalid(name, value);
      return data[name];
    };
    const resolveLabel = () => {
      const value = sourceValue("label");
      if (typeof value === "string" && value.length > 0) {
        invalidEpisodes.delete("label");
        return value;
      }
      reportInvalid("label", value);
      return data.label;
    };
    const setAttribute = (name, value) => {
      if (spinner.getAttribute(name) !== value) {
        spinner.setAttribute(name, value);
      }
    };
    const setData = (name, value) => {
      if (spinner.dataset[name] !== value) {
        spinner.dataset[name] = value;
      }
    };

    Citry.vue.watchEffect(() => {
      setAttribute("aria-label", resolveLabel());
      setData("intent", resolveChoice("intent"));
      setData("size", resolveChoice("size"));
    });

    spinner.setAttribute("data-citry-spinner-initialized", "");
    return () => {
      spinner.removeAttribute("data-citry-spinner-initialized");
    };
  },
});

})();