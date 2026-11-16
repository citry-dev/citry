try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonVariantsAndSizes_0c86b8", "f24510a95ac4684598c2fc3842cb1db081ff79ffa48bae66f8d39ce13bae07d9")({
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
__citryRuntime.finishScript("f615323cb40c9fa19213a3b881bda1769859b8b1cf6f9bcd5b1a476763500e34");
} catch (error) {
__citryRuntime.finishScript("f615323cb40c9fa19213a3b881bda1769859b8b1cf6f9bcd5b1a476763500e34", error);
}