try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "MenuPlacement_c7ffe8", "ee5f47e1f911a7a3082a18a027f37e0ac18b230ddceac9364311046150a9153b")({
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
__citryRuntime.finishScript("f25c59464e7294d1f809e117577dcd5f7572fc78943bacf50c1ee3eec92312bd");
} catch (error) {
__citryRuntime.finishScript("f25c59464e7294d1f809e117577dcd5f7572fc78943bacf50c1ee3eec92312bd", error);
}