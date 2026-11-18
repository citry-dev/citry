try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FieldInputConfiguration_771830", "06a4752c27a29092e5046b6e36537be80f9b6f6890d7c1ef203b8870e38b245c")({
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
__citryRuntime.finishScript("cb945b18962d46a8878493a4ce35df3223e3d5a189694a74884dcb46577948a8");
} catch (error) {
__citryRuntime.finishScript("cb945b18962d46a8878493a4ce35df3223e3d5a189694a74884dcb46577948a8", error);
}