try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "CustomizeAccordion_39a169", "a17e4b7ed465b184d103dd467449d89ab26d67189fd3720c8ba3ce7f46fe35f8")({
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
__citryRuntime.finishScript("e29b82b17ccc7689bfbfc416f7d6f766e359c28d923c5791e8af87a2b5ccfdab");
} catch (error) {
__citryRuntime.finishScript("e29b82b17ccc7689bfbfc416f7d6f766e359c28d923c5791e8af87a2b5ccfdab", error);
}