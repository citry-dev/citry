try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureDrawer_e29332", "9be70bc424d319fcab84660c283a174860ff2b7ee587044dfd4fc0c9cb1518eb")({
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
__citryRuntime.finishScript("f1e8b0a24b65be4a56677128f52bc0bcc5d1214d777b007a5d801073ec7d639c");
} catch (error) {
__citryRuntime.finishScript("f1e8b0a24b65be4a56677128f52bc0bcc5d1214d777b007a5d801073ec7d639c", error);
}