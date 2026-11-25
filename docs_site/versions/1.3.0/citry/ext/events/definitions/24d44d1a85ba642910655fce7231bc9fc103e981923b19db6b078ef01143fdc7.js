try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "CustomizeAccordion_8dae70", "a17e4b7ed465b184d103dd467449d89ab26d67189fd3720c8ba3ce7f46fe35f8")({
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
__citryRuntime.finishScript("b235109b450832701502ce3b4f2de38b6d73dc114c89a7b56e3ab2e0aaca2541");
} catch (error) {
__citryRuntime.finishScript("b235109b450832701502ce3b4f2de38b6d73dc114c89a7b56e3ab2e0aaca2541", error);
}