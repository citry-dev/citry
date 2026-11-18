try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsDisabledStates_3e9030", "62fe6a46f825ec69927710b7db1cbfdbeea2ad4f870e15fb89464b2b0d154bff")({
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
__citryRuntime.finishScript("5af27937955b4c203be337a707bd75166cf5725762e3466ca8310057e93e3fda");
} catch (error) {
__citryRuntime.finishScript("5af27937955b4c203be337a707bd75166cf5725762e3466ca8310057e93e3fda", error);
}