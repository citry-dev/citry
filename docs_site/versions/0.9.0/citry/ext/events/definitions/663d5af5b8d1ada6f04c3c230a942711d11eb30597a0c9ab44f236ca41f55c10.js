try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "MenuPlacement_272f56", "ee5f47e1f911a7a3082a18a027f37e0ac18b230ddceac9364311046150a9153b")({
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
__citryRuntime.finishScript("e2bd52dd6bd1514f8a1dea2d6d16169760909d2dea08a10e1d8a641917283f73");
} catch (error) {
__citryRuntime.finishScript("e2bd52dd6bd1514f8a1dea2d6d16169760909d2dea08a10e1d8a641917283f73", error);
}