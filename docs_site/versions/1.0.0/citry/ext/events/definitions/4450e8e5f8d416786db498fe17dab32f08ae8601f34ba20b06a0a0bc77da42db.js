try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FieldInputConfiguration_2e741d", "06a4752c27a29092e5046b6e36537be80f9b6f6890d7c1ef203b8870e38b245c")({
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
__citryRuntime.finishScript("2b136c9cee4b8e8fb9be345ee6ec427fc5c19090dd9de5dee7dece3b7895fa7f");
} catch (error) {
__citryRuntime.finishScript("2b136c9cee4b8e8fb9be345ee6ec427fc5c19090dd9de5dee7dece3b7895fa7f", error);
}