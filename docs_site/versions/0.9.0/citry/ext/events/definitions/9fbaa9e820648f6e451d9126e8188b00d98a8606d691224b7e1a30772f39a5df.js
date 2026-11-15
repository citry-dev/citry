try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsDisabledStates_b2f920", "62fe6a46f825ec69927710b7db1cbfdbeea2ad4f870e15fb89464b2b0d154bff")({
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
__citryRuntime.finishScript("953b60d039bb92b5ec151f8f432de0f42c8920487e0f0a3bd4fa04a5dffc2b07");
} catch (error) {
__citryRuntime.finishScript("953b60d039bb92b5ec151f8f432de0f42c8920487e0f0a3bd4fa04a5dffc2b07", error);
}