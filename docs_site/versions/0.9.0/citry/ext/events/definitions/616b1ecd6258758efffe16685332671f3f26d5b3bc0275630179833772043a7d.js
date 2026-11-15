try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FieldInputConfiguration_382f1d", "06a4752c27a29092e5046b6e36537be80f9b6f6890d7c1ef203b8870e38b245c")({
  data() {
    return {
      orientation: 'vertical',
      density: 'default',
      variant: 'outline',
      size: 'md',
      required: true,
      disabled: false,
      readonly: false,
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
__citryRuntime.finishScript("5282059e16d6d3b859322dbac5a88474c91cb91bebcb69ec3f2f251976c13b7b");
} catch (error) {
__citryRuntime.finishScript("5282059e16d6d3b859322dbac5a88474c91cb91bebcb69ec3f2f251976c13b7b", error);
}