try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureDrawer_f237c0", "9be70bc424d319fcab84660c283a174860ff2b7ee587044dfd4fc0c9cb1518eb")({
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
__citryRuntime.finishScript("424f2d729b7cba43c5462c6ad508ca5c23b522b161238c45ffa3f43cf00a5c44");
} catch (error) {
__citryRuntime.finishScript("424f2d729b7cba43c5462c6ad508ca5c23b522b161238c45ffa3f43cf00a5c44", error);
}