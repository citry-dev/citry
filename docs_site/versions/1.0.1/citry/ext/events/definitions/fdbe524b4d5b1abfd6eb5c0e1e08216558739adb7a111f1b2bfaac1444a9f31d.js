try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "MenuKeyboard_3cb827", "756c1490a2694523ca6ccb53edd916d7f91512de22b02d9951ce8a97ad53d8df")({
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
__citryRuntime.finishScript("ca57d8c7b8802d80372901243c80bad61474b45b98edc93d8ba5d8f4d5f56288");
} catch (error) {
__citryRuntime.finishScript("ca57d8c7b8802d80372901243c80bad61474b45b98edc93d8ba5d8f4d5f56288", error);
}