try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormReset_c17107", "34cc8131b3362bb8b970d8a13823023b1faa3b35c1a1ed5f777aab3cfc8e6879")({
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
__citryRuntime.finishScript("cade7e666c262ca6a22e4c6f5ad2963a08f54db654c20571f272de5ddd3d7be0");
} catch (error) {
__citryRuntime.finishScript("cade7e666c262ca6a22e4c6f5ad2963a08f54db654c20571f272de5ddd3d7be0", error);
}