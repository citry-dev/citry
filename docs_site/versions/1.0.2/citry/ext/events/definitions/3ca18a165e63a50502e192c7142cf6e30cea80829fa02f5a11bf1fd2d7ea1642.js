try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsDisabledStates_b1b6ba", "62fe6a46f825ec69927710b7db1cbfdbeea2ad4f870e15fb89464b2b0d154bff")({
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
__citryRuntime.finishScript("b8e7543ae6545fb764ad8e39480338e69136d59a571c1c05ce7eb160e2e7e77c");
} catch (error) {
__citryRuntime.finishScript("b8e7543ae6545fb764ad8e39480338e69136d59a571c1c05ce7eb160e2e7e77c", error);
}