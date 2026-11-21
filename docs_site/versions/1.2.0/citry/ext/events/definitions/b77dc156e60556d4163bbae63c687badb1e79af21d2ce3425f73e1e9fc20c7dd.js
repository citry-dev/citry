try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "MenuPlacement_faecda", "ee5f47e1f911a7a3082a18a027f37e0ac18b230ddceac9364311046150a9153b")({
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
__citryRuntime.finishScript("dc5dfa7413ec23a4b3cd21848b94715c14a7451d5009e9220d1b9d7e3da43080");
} catch (error) {
__citryRuntime.finishScript("dc5dfa7413ec23a4b3cd21848b94715c14a7451d5009e9220d1b9d7e3da43080", error);
}