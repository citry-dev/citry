try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureDrawer_d910bf", "9be70bc424d319fcab84660c283a174860ff2b7ee587044dfd4fc0c9cb1518eb")({
  data() {
    return {
      placement:'inline-end', size:'md', scroll:'body'
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
__citryRuntime.finishScript("fc922b8ec3325fbc66d25fec578cdb237c642ed489d87a9eb01feb4ecbc46790");
} catch (error) {
__citryRuntime.finishScript("fc922b8ec3325fbc66d25fec578cdb237c642ed489d87a9eb01feb4ecbc46790", error);
}