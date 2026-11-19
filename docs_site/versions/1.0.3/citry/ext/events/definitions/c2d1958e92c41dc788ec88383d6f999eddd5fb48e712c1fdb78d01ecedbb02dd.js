try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "MenuKeyboard_6924ad", "756c1490a2694523ca6ccb53edd916d7f91512de22b02d9951ce8a97ad53d8df")({
  data(){return {loop: true, close: false};},
  methods: {
    applyPreviewControls(event) {
      Object.assign(this, event.detail);
    },
  },
  mounted() {
    window.addEventListener("citry-ui-preview-controls", this.applyPreviewControls);
  },
  beforeUnmount() {
    window.removeEventListener("citry-ui-preview-controls", this.applyPreviewControls);
  },
});

})();
__citryRuntime.finishScript("a1b590e87518538b2d5a67c82f7cfdeab6794180590479cff9259433ed5bed31");
} catch (error) {
__citryRuntime.finishScript("a1b590e87518538b2d5a67c82f7cfdeab6794180590479cff9259433ed5bed31", error);
}