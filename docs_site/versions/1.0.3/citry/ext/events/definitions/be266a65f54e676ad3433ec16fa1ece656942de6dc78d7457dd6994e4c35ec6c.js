try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonVariantsAndSizes_23ce81", "f24510a95ac4684598c2fc3842cb1db081ff79ffa48bae66f8d39ce13bae07d9")({
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
__citryRuntime.finishScript("c05702356d6c2fa3e36750c6751e4ec946905b8d64acfc50d83cda7589d05ac3");
} catch (error) {
__citryRuntime.finishScript("c05702356d6c2fa3e36750c6751e4ec946905b8d64acfc50d83cda7589d05ac3", error);
}