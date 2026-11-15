try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledMenu_b5a2d7", "14923b1aa3b9cdfd1650fb1b97520f2e6a45f6cc9f32df818757fba6c65ce9ac")({
  data(){return {open: false, disabled: false, locked: false, size: 'md', lastReason: 'none'};},
  methods: {
    // Show every request's reason, but change `open` only while
    // requests are not locked, so a declined request leaves the Menu
    // as is.
    applyOpenRequest(nextOpen, detail) {
      this.lastReason = detail.reason;
      if (!this.locked) this.open = nextOpen;
    },
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
__citryRuntime.finishScript("65e3db6b033369f53b8836e0ba8bebcc066d1ae0f8ba04679ac33a8a5b359cc8");
} catch (error) {
__citryRuntime.finishScript("65e3db6b033369f53b8836e0ba8bebcc066d1ae0f8ba04679ac33a8a5b359cc8", error);
}