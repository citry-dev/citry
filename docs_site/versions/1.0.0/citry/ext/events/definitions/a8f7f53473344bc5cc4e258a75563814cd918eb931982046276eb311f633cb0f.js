try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "MenuPlacement_97fd18", "ee5f47e1f911a7a3082a18a027f37e0ac18b230ddceac9364311046150a9153b")({
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
__citryRuntime.finishScript("826bd3e2e2206d08636c3c126ad9acccb2c6f070a3c4e755dd2e80d8c72cdbc6");
} catch (error) {
__citryRuntime.finishScript("826bd3e2e2206d08636c3c126ad9acccb2c6f070a3c4e755dd2e80d8c72cdbc6", error);
}