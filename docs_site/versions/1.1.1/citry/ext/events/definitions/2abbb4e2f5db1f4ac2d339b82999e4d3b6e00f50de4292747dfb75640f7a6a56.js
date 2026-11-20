try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsDisabledStates_d9a356", "62fe6a46f825ec69927710b7db1cbfdbeea2ad4f870e15fb89464b2b0d154bff")({
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
__citryRuntime.finishScript("4f1fe5cd7769280d2a38b8ff761d52e1bd70052117b0a3704c703cf4efc06bfd");
} catch (error) {
__citryRuntime.finishScript("4f1fe5cd7769280d2a38b8ff761d52e1bd70052117b0a3704c703cf4efc06bfd", error);
}