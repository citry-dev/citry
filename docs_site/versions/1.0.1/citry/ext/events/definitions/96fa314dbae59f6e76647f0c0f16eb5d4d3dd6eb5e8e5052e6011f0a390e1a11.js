try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "CustomizeAccordion_79520e", "a17e4b7ed465b184d103dd467449d89ab26d67189fd3720c8ba3ce7f46fe35f8")({
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
__citryRuntime.finishScript("47ed4d626148cade28bf5a10b2e92626e54acbf4eb04eb95f4aef025943db7bf");
} catch (error) {
__citryRuntime.finishScript("47ed4d626148cade28bf5a10b2e92626e54acbf4eb04eb95f4aef025943db7bf", error);
}