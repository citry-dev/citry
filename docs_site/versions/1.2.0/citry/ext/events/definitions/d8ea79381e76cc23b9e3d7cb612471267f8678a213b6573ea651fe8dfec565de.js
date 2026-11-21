try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "CustomizeAccordion_7a30aa", "a17e4b7ed465b184d103dd467449d89ab26d67189fd3720c8ba3ce7f46fe35f8")({
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
__citryRuntime.finishScript("d2540a8056465daa56616f2c81f9caebf74ab7cfc1519dd3e9c79380ae20a8f8");
} catch (error) {
__citryRuntime.finishScript("d2540a8056465daa56616f2c81f9caebf74ab7cfc1519dd3e9c79380ae20a8f8", error);
}