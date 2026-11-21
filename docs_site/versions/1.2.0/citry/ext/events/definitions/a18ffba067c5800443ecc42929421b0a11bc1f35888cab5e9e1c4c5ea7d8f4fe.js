try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "CheckboxConfiguration_264e69", "fb2a1aadc3000d34d0d288e8d55ae3049f52f9f64ecf878a78b7225cb6b8ec20")({
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
__citryRuntime.finishScript("2e0d013d2070d341803f877058b2f955337f4bf7ea3786902df937a8c1dbc6e2");
} catch (error) {
__citryRuntime.finishScript("2e0d013d2070d341803f877058b2f955337f4bf7ea3786902df937a8c1dbc6e2", error);
}