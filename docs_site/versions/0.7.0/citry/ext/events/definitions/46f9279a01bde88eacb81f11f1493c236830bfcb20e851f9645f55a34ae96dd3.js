(function() {

// Page markup can hide a document's members behind named elements. The core runtime's helper
// reads the built-in ones; Citry before 0.7.0 have no helper, so the fallback reads members directly.
const builtIn = globalThis[Symbol.for("citry:built-in-members")] ?? (target => target);

__citryRuntime.registerTypeOptions.bind(null, "CAvatar_516550", "95e6d638fbf2d3c873872d212e17470a9d18357ccf2f2f8e16d2f1181d5ca963")({
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
      image = builtIn(document).createElement("img");
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
    // This repeats the image URL rule from _url.py in the browser, so a
    // client prop cannot load a URL the server would refuse.
    const isImageUrlAllowed = (value) => {
      // Strip C0 controls and spaces from both ends with loops: a regex
      // anchored only at the end slows down on a long run of spaces.
      let start = 0;
      let end = value.length;
      while (start < end && value.charCodeAt(start) <= 0x20) start += 1;
      while (end > start && value.charCodeAt(end - 1) <= 0x20) end -= 1;
      const text = value.slice(start, end).replace(/[\t\n\r]/g, "");
      const match = /^([a-z][a-z0-9+.-]*):/i.exec(text);
      if (match === null) return true;
      const scheme = match[1].toLowerCase();
      if (scheme === "data") {
        return /^[\t\n\f\r ]*image\//i.test(text.slice(match[0].length));
      }
      return ["http", "https", "blob"].includes(scheme);
    };
    const resolveSource = () => {
      const value = props.src === undefined ? data.src : props.src;
      if (
        value === null
        || (typeof value === "string" && value && !value.includes("\u0000") && isImageUrlAllowed(value))
      ) {
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