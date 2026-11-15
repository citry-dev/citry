try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "CheckboxConfiguration_c50db1", "fb2a1aadc3000d34d0d288e8d55ae3049f52f9f64ecf878a78b7225cb6b8ec20")({
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
__citryRuntime.finishScript("7f3e13d134a442bb7d01018559d5fc8b16a4e35790b1b74183d1c0efa1b28bb9");
} catch (error) {
__citryRuntime.finishScript("7f3e13d134a442bb7d01018559d5fc8b16a4e35790b1b74183d1c0efa1b28bb9", error);
}