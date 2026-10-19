(function() {

__citryRuntime.registerTypeOptions.bind(null, "CAvatar_516550", "6c44e65c0f977cdb37bf23cc96a926ceec84e5a96b15dd60229354fa046d5ba2")({
  props: {
    src: {},
    alt: {},
    variant: {},
    size: {},
    shape: {},
    onStatusChange: {},
  },
  onServerRender: ({component}) => {
    const root = component.$el;
    // Server-rendered values, used while the matching prop is absent.
    const data = component.serverDefaults;
    const props = component.$props;
    let image = root.querySelector('[data-citry-ui-part="image"]');
    if (!(image instanceof HTMLImageElement)) {
      image = document.createElement("img");
      for (const [name, value] of Object.entries(data.imgAttrs)) {
        image.setAttribute(name, value);
      }
      image.classList.add("cui-avatar__image");
      image.dataset.citryUiPart = "image";
      image.alt = "";
      image.hidden = true;
      root.append(image);
    }
    const allowedValues = {
      variant: ["soft", "solid", "outline"],
      size: ["sm", "md", "lg"],
      shape: ["circle", "rounded", "square"],
    };
    const invalidEpisodes = new Set();
    let currentSource = data.src;
    let currentStatus = root.dataset.status;
    let sourceGeneration = 0;

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
        `[citry-ui] CAvatar ${name} received invalid client value `
          + `${describeValue(value)}; using the server-rendered fallback.`,
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
    const resolveText = (name) => {
      const value = props[name] === undefined ? data[name] : props[name];
      if (typeof value === "string" && !value.includes("\u0000")) {
        invalidEpisodes.delete(name);
        return value;
      }
      reportInvalid(name, value);
      return data[name];
    };
    const resolveSource = () => {
      const value = props.src === undefined ? data.src : props.src;
      if (value === null || (typeof value === "string" && value && !value.includes("\u0000"))) {
        invalidEpisodes.delete("src");
        return value;
      }
      reportInvalid("src", value);
      return data.src;
    };
    const notifyStatus = (status, source) => {
      const callback = props.onStatusChange;
      if (callback === undefined || callback === null) {
        invalidEpisodes.delete("onStatusChange");
        return;
      }
      if (typeof callback !== "function") {
        reportInvalid("onStatusChange", callback);
        return;
      }
      invalidEpisodes.delete("onStatusChange");
      callback({status, src: source});
    };
    const setStatus = (status, source, notify = true) => {
      if (currentStatus === status && root.dataset.status === status) {
        return;
      }
      currentStatus = status;
      root.dataset.status = status;
      if (notify) {
        notifyStatus(status, source);
      }
    };
    const settleCurrentImage = (generation) => {
      if (generation !== sourceGeneration || currentSource === null) {
        return;
      }
      if (!image.complete) {
        return;
      }
      if (image.naturalWidth > 0) {
        image.hidden = false;
        setStatus("loaded", currentSource);
      } else {
        image.hidden = true;
        setStatus("error", currentSource);
      }
    };
    const onLoad = () => {
      if (currentSource === null) {
        return;
      }
      image.hidden = false;
      setStatus("loaded", currentSource);
    };
    const onError = () => {
      if (currentSource === null) {
        return;
      }
      image.hidden = true;
      setStatus("error", currentSource);
    };

    image.addEventListener("load", onLoad);
    image.addEventListener("error", onError);

    Citry.vue.watchEffect(() => {
      const source = resolveSource();
      const alt = resolveText("alt");
      const variant = resolveChoice("variant");
      const size = resolveChoice("size");
      const shape = resolveChoice("shape");

      root.dataset.variant = variant;
      root.dataset.size = size;
      root.dataset.shape = shape;
      if (alt) {
        root.setAttribute("role", "img");
        root.setAttribute("aria-label", alt);
      } else {
        root.removeAttribute("role");
        root.removeAttribute("aria-label");
      }

      if (source !== currentSource) {
        currentSource = source;
        sourceGeneration += 1;
        if (source === null) {
          image.removeAttribute("src");
          image.hidden = true;
          setStatus("fallback", null);
        } else {
          image.hidden = false;
          image.setAttribute("src", source);
          setStatus("loading", source);
          const generation = sourceGeneration;
          queueMicrotask(() => settleCurrentImage(generation));
        }
      } else {
        settleCurrentImage(sourceGeneration);
      }
    });

    root.dataset.citryAvatarInitialized = "";
    return () => {
      sourceGeneration += 1;
      image.removeEventListener("load", onLoad);
      image.removeEventListener("error", onError);
      delete root.dataset.citryAvatarInitialized;
    };
  },
});

})();