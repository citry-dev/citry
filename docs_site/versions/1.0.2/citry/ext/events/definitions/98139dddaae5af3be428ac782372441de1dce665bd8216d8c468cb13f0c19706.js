try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TooltipPlacements_818f01", "94804b8020bc1fd27d9910268a971b7620f02dc67c35872cc0e2f5378396563c")({
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
__citryRuntime.finishScript("7f68a34f956fbc02040cd70436ec7519c2446f8ece31f69ff96030fe5066e1ca");
} catch (error) {
__citryRuntime.finishScript("7f68a34f956fbc02040cd70436ec7519c2446f8ece31f69ff96030fe5066e1ca", error);
}