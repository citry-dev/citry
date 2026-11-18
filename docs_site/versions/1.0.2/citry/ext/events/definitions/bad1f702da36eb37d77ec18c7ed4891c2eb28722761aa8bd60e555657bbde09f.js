try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "CheckboxConfiguration_d6a2a7", "fb2a1aadc3000d34d0d288e8d55ae3049f52f9f64ecf878a78b7225cb6b8ec20")({
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
__citryRuntime.finishScript("176da1cca51c660b02337aaec6f2d9897aa75b128b2a3b9809a92204349bf964");
} catch (error) {
__citryRuntime.finishScript("176da1cca51c660b02337aaec6f2d9897aa75b128b2a3b9809a92204349bf964", error);
}