try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonVariantsAndSizes_64dad2", "f24510a95ac4684598c2fc3842cb1db081ff79ffa48bae66f8d39ce13bae07d9")({
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
__citryRuntime.finishScript("49670780e94c8f8a37b88c8817da5daa0d229180b4bcfb093ddf71ecc4c147d9");
} catch (error) {
__citryRuntime.finishScript("49670780e94c8f8a37b88c8817da5daa0d229180b4bcfb093ddf71ecc4c147d9", error);
}