try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonVariantsAndSizes_49fffa", "f24510a95ac4684598c2fc3842cb1db081ff79ffa48bae66f8d39ce13bae07d9")({
  data(){return {
      variant:'solid',
      intent:'primary',
      size:'md',
      block:false,
      placement:'bottom-end',
      match_width:false
    };},
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
__citryRuntime.finishScript("3a6c2e8643e7f79ada75a562e9563036da0e6d5c79efdda72ba73e610c230362");
} catch (error) {
__citryRuntime.finishScript("3a6c2e8643e7f79ada75a562e9563036da0e6d5c79efdda72ba73e610c230362", error);
}