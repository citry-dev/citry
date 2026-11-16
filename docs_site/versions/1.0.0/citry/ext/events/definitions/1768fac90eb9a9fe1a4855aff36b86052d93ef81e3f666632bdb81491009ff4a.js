try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormReset_f27788", "34cc8131b3362bb8b970d8a13823023b1faa3b35c1a1ed5f777aab3cfc8e6879")({
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
__citryRuntime.finishScript("c5725fe2230de63d346f5cd7d66637b02ee40938ddea612217bcc4166973599e");
} catch (error) {
__citryRuntime.finishScript("c5725fe2230de63d346f5cd7d66637b02ee40938ddea612217bcc4166973599e", error);
}