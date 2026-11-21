try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "MenuKeyboard_4770bf", "756c1490a2694523ca6ccb53edd916d7f91512de22b02d9951ce8a97ad53d8df")({
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
__citryRuntime.finishScript("2ce3a2f27c9f129af59e717011c02049f94588aea7712b04a871d0070c3795f6");
} catch (error) {
__citryRuntime.finishScript("2ce3a2f27c9f129af59e717011c02049f94588aea7712b04a871d0070c3795f6", error);
}