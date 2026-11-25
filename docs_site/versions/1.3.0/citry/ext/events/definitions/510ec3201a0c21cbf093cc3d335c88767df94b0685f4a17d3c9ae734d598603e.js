try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "MenuPlacement_910d7b", "ee5f47e1f911a7a3082a18a027f37e0ac18b230ddceac9364311046150a9153b")({
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
__citryRuntime.finishScript("afc589872a8adc0674ee65acd621c0a3d094ae5b18af9136864451a57388f3d7");
} catch (error) {
__citryRuntime.finishScript("afc589872a8adc0674ee65acd621c0a3d094ae5b18af9136864451a57388f3d7", error);
}