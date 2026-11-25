try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsDisabledStates_786dae", "62fe6a46f825ec69927710b7db1cbfdbeea2ad4f870e15fb89464b2b0d154bff")({
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
__citryRuntime.finishScript("83a36a671026d3abc67274b6690503c78b22523bccef917da48a57da5ba32285");
} catch (error) {
__citryRuntime.finishScript("83a36a671026d3abc67274b6690503c78b22523bccef917da48a57da5ba32285", error);
}