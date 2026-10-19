(function() {

__citryRuntime.registerTypeOptions.bind(null, "FieldInputConfiguration_a7439d", "06a4752c27a29092e5046b6e36537be80f9b6f6890d7c1ef203b8870e38b245c")({
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