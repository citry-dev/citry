try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormReset_6f7cac", "34cc8131b3362bb8b970d8a13823023b1faa3b35c1a1ed5f777aab3cfc8e6879")({
  data() {
    return {
      cancel_reset: false, status: 'Edit either value, then reset.'
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
__citryRuntime.finishScript("e0c370b7966398024fdd4bf30b6e9241ed6f7f6f75bebce709bb06ff5cc9c5a6");
} catch (error) {
__citryRuntime.finishScript("e0c370b7966398024fdd4bf30b6e9241ed6f7f6f75bebce709bb06ff5cc9c5a6", error);
}