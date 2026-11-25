try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureAlert_8c4d35", "0783867deefad4dea1bca638f2c6892d91fad1f06ffb71ccbcd6b2688540bc48")({
  data() {
    return {
      intent: 'info',
      variant: 'soft',
      size: 'md',
      announce: 'off',
      icon: true,
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
__citryRuntime.finishScript("253f11d6cbd450bbc35633a70d0ca5613f053e1d45f7918c946a9097fbd137bb");
} catch (error) {
__citryRuntime.finishScript("253f11d6cbd450bbc35633a70d0ca5613f053e1d45f7918c946a9097fbd137bb", error);
}