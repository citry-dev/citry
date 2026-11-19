try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "MenuPlacement_c975a1", "ee5f47e1f911a7a3082a18a027f37e0ac18b230ddceac9364311046150a9153b")({
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
__citryRuntime.finishScript("76958fa678e7d8edb70ff14151190220239e850520e93e787e8c29ac405ddfd5");
} catch (error) {
__citryRuntime.finishScript("76958fa678e7d8edb70ff14151190220239e850520e93e787e8c29ac405ddfd5", error);
}