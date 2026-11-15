try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsAlignmentAndOrientation_5fe614", "acec645729d9f3b61f941dc5b8558216e9bfb399b878e4e1ca87f8d587013b2f")({
  data() {
    return {
      align: 'start', orientation: 'horizontal'
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
__citryRuntime.finishScript("74a7a580f9c3db4eb10ac0776dbbaf02da2feeb7c5e97494f03d706e3a740880");
} catch (error) {
__citryRuntime.finishScript("74a7a580f9c3db4eb10ac0776dbbaf02da2feeb7c5e97494f03d706e3a740880", error);
}