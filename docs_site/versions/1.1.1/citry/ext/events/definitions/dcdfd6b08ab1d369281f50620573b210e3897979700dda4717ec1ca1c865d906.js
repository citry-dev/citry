try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "MenuKeyboard_2d5bde", "756c1490a2694523ca6ccb53edd916d7f91512de22b02d9951ce8a97ad53d8df")({
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
__citryRuntime.finishScript("d05b85e5ca98b673af82260e5ff62fdeebf0fb68fec1ec08b03b32141e5db411");
} catch (error) {
__citryRuntime.finishScript("d05b85e5ca98b673af82260e5ff62fdeebf0fb68fec1ec08b03b32141e5db411", error);
}