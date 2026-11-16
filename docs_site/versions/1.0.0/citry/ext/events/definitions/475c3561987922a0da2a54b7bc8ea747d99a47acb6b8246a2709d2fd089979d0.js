try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsDisabledStates_49c06e", "62fe6a46f825ec69927710b7db1cbfdbeea2ad4f870e15fb89464b2b0d154bff")({
  data() {
    return {
      group_disabled: false
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
__citryRuntime.finishScript("22d9ca225d91b8646e63bbf77db59ee9c18304bb9128ae2cb5cf35fd8045933d");
} catch (error) {
__citryRuntime.finishScript("22d9ca225d91b8646e63bbf77db59ee9c18304bb9128ae2cb5cf35fd8045933d", error);
}