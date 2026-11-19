try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsDisabledStates_a877c3", "62fe6a46f825ec69927710b7db1cbfdbeea2ad4f870e15fb89464b2b0d154bff")({
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
__citryRuntime.finishScript("0f0f0d233ddf50eb6b170c9ca308dd756260e84d44d5c2e252e61fe177e6bd91");
} catch (error) {
__citryRuntime.finishScript("0f0f0d233ddf50eb6b170c9ca308dd756260e84d44d5c2e252e61fe177e6bd91", error);
}