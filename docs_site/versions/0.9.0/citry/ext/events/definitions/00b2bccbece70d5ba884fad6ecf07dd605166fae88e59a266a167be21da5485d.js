try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "MenuKeyboard_d55ca9", "756c1490a2694523ca6ccb53edd916d7f91512de22b02d9951ce8a97ad53d8df")({
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
__citryRuntime.finishScript("7bb56360288d5da75155277e94b8b0b69d33e06adbf23717497f55ba563db857");
} catch (error) {
__citryRuntime.finishScript("7bb56360288d5da75155277e94b8b0b69d33e06adbf23717497f55ba563db857", error);
}