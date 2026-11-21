try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsDisabledStates_289eba", "62fe6a46f825ec69927710b7db1cbfdbeea2ad4f870e15fb89464b2b0d154bff")({
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
__citryRuntime.finishScript("0c34e15ab864916c96c0d1fcaedd03ded17638a96e3956b4df71eb5e166037b3");
} catch (error) {
__citryRuntime.finishScript("0c34e15ab864916c96c0d1fcaedd03ded17638a96e3956b4df71eb5e166037b3", error);
}