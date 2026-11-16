try {
(function() {

const publish = () => {
  const height = Math.ceil(document.documentElement.scrollHeight);
  parent.postMessage({ type: "citry-ui-preview-height", height }, "*");
};
addEventListener("message", (event) => {
  if (event.source !== parent) return;
  if (
    event.data?.type === "citry-ui-preview-theme"
    && ["light", "dark"].includes(event.data.theme)
  ) {
    document.documentElement.style.colorScheme = event.data.theme;
    document.body.style.colorScheme = event.data.theme;
    publish();
    return;
  }
  if (
    event.data?.type === "citry-ui-preview-controls"
    && event.data.values
    && typeof event.data.values === "object"
    && !Array.isArray(event.data.values)
  ) {
    dispatchEvent(new CustomEvent("citry-ui-preview-controls", {
      detail: event.data.values,
    }));
    publish();
  }
});
addEventListener("load", publish);
new ResizeObserver(publish).observe(document.documentElement);
publish();

})();
__citryRuntime.finishScript("f8e6345dd117fe97e965d1056af4ff580d80bf2a10efd878c057f32ed5410287");
} catch (error) {
__citryRuntime.finishScript("f8e6345dd117fe97e965d1056af4ff580d80bf2a10efd878c057f32ed5410287", error);
}