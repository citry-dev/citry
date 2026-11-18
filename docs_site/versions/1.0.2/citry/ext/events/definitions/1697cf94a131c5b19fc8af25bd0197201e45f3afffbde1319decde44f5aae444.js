try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ButtonConfiguration_a1a4ab", "31a922ae0cbbfec64a9e9c8e3bb117011480d22169d2c2c15c211010764be2a7")({
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
__citryRuntime.finishScript("6512eec7e98412d9f1338a83bacd80ebc38783c3fed69304979fa2a2a562f718");
} catch (error) {
__citryRuntime.finishScript("6512eec7e98412d9f1338a83bacd80ebc38783c3fed69304979fa2a2a562f718", error);
}