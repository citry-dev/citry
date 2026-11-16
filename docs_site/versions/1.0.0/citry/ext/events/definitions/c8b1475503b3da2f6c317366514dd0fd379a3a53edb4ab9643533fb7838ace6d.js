try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledMenu_af3fe3", "14923b1aa3b9cdfd1650fb1b97520f2e6a45f6cc9f32df818757fba6c65ce9ac")({
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
__citryRuntime.finishScript("dc1d7272e7dd48c26f67b09fab28cf5c40ebd23c73b65f9fdc3b00392c37895e");
} catch (error) {
__citryRuntime.finishScript("dc1d7272e7dd48c26f67b09fab28cf5c40ebd23c73b65f9fdc3b00392c37895e", error);
}