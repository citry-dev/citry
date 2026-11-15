try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "CustomizeAccordion_d5cf73", "a17e4b7ed465b184d103dd467449d89ab26d67189fd3720c8ba3ce7f46fe35f8")({
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
__citryRuntime.finishScript("f0a2563de7984ee1ca358327b25f8cf045fab46370547054ca10b2c1c10c7d3f");
} catch (error) {
__citryRuntime.finishScript("f0a2563de7984ee1ca358327b25f8cf045fab46370547054ca10b2c1c10c7d3f", error);
}