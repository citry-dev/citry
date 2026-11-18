try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "MenuPlacement_0fb9be", "ee5f47e1f911a7a3082a18a027f37e0ac18b230ddceac9364311046150a9153b")({
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
__citryRuntime.finishScript("a824224b17606bfbc171289b170c5ee917564ae9b775a78aa6c3a5b6eaccc7b3");
} catch (error) {
__citryRuntime.finishScript("a824224b17606bfbc171289b170c5ee917564ae9b775a78aa6c3a5b6eaccc7b3", error);
}