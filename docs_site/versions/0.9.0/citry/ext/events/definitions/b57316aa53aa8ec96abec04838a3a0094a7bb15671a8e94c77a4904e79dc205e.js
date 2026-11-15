try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ButtonConfiguration_89bb3e", "31a922ae0cbbfec64a9e9c8e3bb117011480d22169d2c2c15c211010764be2a7")({
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
__citryRuntime.finishScript("96331a8dfbd586fa6367be736bb595d35665bbdeb46b61a6abc6476c563d33c4");
} catch (error) {
__citryRuntime.finishScript("96331a8dfbd586fa6367be736bb595d35665bbdeb46b61a6abc6476c563d33c4", error);
}