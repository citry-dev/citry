try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ButtonConfiguration_e794c1", "31a922ae0cbbfec64a9e9c8e3bb117011480d22169d2c2c15c211010764be2a7")({
  data() {
    return {
      variant: 'solid',
      intent: 'primary',
      size: 'md',
      loading_pos: 'center',
      loading: false,
      disabled: false,
      block: false,
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
__citryRuntime.finishScript("c9170b5f419f4658265a6583d63af64da25952fdca38b85d84ea1e26036cf5d3");
} catch (error) {
__citryRuntime.finishScript("c9170b5f419f4658265a6583d63af64da25952fdca38b85d84ea1e26036cf5d3", error);
}