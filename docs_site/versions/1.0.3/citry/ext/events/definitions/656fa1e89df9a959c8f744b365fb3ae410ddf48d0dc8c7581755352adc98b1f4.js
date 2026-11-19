try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FieldInputConfiguration_cd0943", "06a4752c27a29092e5046b6e36537be80f9b6f6890d7c1ef203b8870e38b245c")({
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
__citryRuntime.finishScript("a34fc39b77e866216146ef412a91092b050e188cc5ca71d2910577a0d8cd291e");
} catch (error) {
__citryRuntime.finishScript("a34fc39b77e866216146ef412a91092b050e188cc5ca71d2910577a0d8cd291e", error);
}