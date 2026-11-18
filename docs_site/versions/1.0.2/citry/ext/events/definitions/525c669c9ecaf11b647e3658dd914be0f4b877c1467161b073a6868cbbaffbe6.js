try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormReset_0e6e5e", "34cc8131b3362bb8b970d8a13823023b1faa3b35c1a1ed5f777aab3cfc8e6879")({
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
__citryRuntime.finishScript("5eaad7c23ffa029c172d8839290c1901be44fd57e3aeaaefe45ffc4b21c4c7b4");
} catch (error) {
__citryRuntime.finishScript("5eaad7c23ffa029c172d8839290c1901be44fd57e3aeaaefe45ffc4b21c4c7b4", error);
}