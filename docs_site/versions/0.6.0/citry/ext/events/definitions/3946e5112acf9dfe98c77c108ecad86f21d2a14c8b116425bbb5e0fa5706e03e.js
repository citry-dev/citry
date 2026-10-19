(function() {

__citryRuntime.registerTypeOptions.bind(null, "MenuPlacement_0e73a5", "ee5f47e1f911a7a3082a18a027f37e0ac18b230ddceac9364311046150a9153b")({
  data(){return {placement: 'bottom-start', rtl: false, match: true};},
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