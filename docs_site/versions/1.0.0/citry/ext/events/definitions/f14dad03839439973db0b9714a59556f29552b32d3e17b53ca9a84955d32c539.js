try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "CheckboxConfiguration_65afbb", "fb2a1aadc3000d34d0d288e8d55ae3049f52f9f64ecf878a78b7225cb6b8ec20")({
  data() {
    return {
      variant: 'solid',
      size: 'md',
      label_pos: 'end',
      checked: true,
      indeterminate: false,
      required: false,
      disabled: false,
      invalid: false,
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
__citryRuntime.finishScript("7505fc1f413c99c1d8d055a8fe70db858fd251e93a4b96a6f007a4481d3b420d");
} catch (error) {
__citryRuntime.finishScript("7505fc1f413c99c1d8d055a8fe70db858fd251e93a4b96a6f007a4481d3b420d", error);
}