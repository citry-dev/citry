try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureDrawer_e94d80", "9be70bc424d319fcab84660c283a174860ff2b7ee587044dfd4fc0c9cb1518eb")({
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
__citryRuntime.finishScript("ae9b76a0f577c968516cb03f59700473714fa1e5a27fee122982ce99323e620f");
} catch (error) {
__citryRuntime.finishScript("ae9b76a0f577c968516cb03f59700473714fa1e5a27fee122982ce99323e620f", error);
}