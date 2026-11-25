try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonVariantsAndSizes_e46edf", "f24510a95ac4684598c2fc3842cb1db081ff79ffa48bae66f8d39ce13bae07d9")({
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
__citryRuntime.finishScript("14e388ce76b1338e3813340eaaecb06b1167f95fadfb7091df48cb5649f2ed63");
} catch (error) {
__citryRuntime.finishScript("14e388ce76b1338e3813340eaaecb06b1167f95fadfb7091df48cb5649f2ed63", error);
}