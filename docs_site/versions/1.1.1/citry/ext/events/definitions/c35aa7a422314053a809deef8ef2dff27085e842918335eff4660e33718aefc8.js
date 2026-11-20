try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormReset_578c53", "34cc8131b3362bb8b970d8a13823023b1faa3b35c1a1ed5f777aab3cfc8e6879")({
  data() {
    return {
      cancel_reset: false, status: 'Edit either value, then reset.'
    };
  },
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
__citryRuntime.finishScript("9d606cc68833bef238dbd5fd0670c278bee2861dacdbce1fc0b5997b05b71829");
} catch (error) {
__citryRuntime.finishScript("9d606cc68833bef238dbd5fd0670c278bee2861dacdbce1fc0b5997b05b71829", error);
}