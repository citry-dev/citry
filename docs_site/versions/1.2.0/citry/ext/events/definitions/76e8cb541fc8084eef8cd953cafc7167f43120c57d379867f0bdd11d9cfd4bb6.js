try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TooltipPlacements_d7446a", "94804b8020bc1fd27d9910268a971b7620f02dc67c35872cc0e2f5378396563c")({
  data() {
    return {
      placement: 'top'
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
__citryRuntime.finishScript("fea8d6a394d06d9d099bff83b7eaa57c5f1fc40ad46ed513bc91722b9f18258c");
} catch (error) {
__citryRuntime.finishScript("fea8d6a394d06d9d099bff83b7eaa57c5f1fc40ad46ed513bc91722b9f18258c", error);
}