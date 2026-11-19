try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureDrawer_916f4e", "9be70bc424d319fcab84660c283a174860ff2b7ee587044dfd4fc0c9cb1518eb")({
  data() {
    return {
      placement:'inline-end', size:'md', scroll:'body'
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
__citryRuntime.finishScript("fd24f3c1b056144f1e98178966df65c7e65987e15523e2f54f0ef24b296c1b60");
} catch (error) {
__citryRuntime.finishScript("fd24f3c1b056144f1e98178966df65c7e65987e15523e2f54f0ef24b296c1b60", error);
}