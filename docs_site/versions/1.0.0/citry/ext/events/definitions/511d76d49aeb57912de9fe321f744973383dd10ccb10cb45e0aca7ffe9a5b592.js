try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "CustomizeAccordion_3da1e9", "a17e4b7ed465b184d103dd467449d89ab26d67189fd3720c8ba3ce7f46fe35f8")({
  data() {
    return {
      variant: 'separated',
      size: 'md',
      indicator: true,
      indicator_position: 'end',
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
__citryRuntime.finishScript("06ef58180094961511ca7ca368156da39796d0926a540b1b5e756862d09a0790");
} catch (error) {
__citryRuntime.finishScript("06ef58180094961511ca7ca368156da39796d0926a540b1b5e756862d09a0790", error);
}