try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "CheckboxConfiguration_a1504d", "fb2a1aadc3000d34d0d288e8d55ae3049f52f9f64ecf878a78b7225cb6b8ec20")({
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
__citryRuntime.finishScript("afe5d70bfe19a026240acf478d6d7ceca24aa5bff8bb664582114834b87ceb03");
} catch (error) {
__citryRuntime.finishScript("afe5d70bfe19a026240acf478d6d7ceca24aa5bff8bb664582114834b87ceb03", error);
}