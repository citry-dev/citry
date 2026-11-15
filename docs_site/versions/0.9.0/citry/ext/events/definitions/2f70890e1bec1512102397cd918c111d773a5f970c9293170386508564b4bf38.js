try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureDrawer_b73b6b", "9be70bc424d319fcab84660c283a174860ff2b7ee587044dfd4fc0c9cb1518eb")({
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
__citryRuntime.finishScript("9ffd17087fb9d27647fe78ca84d302386518629edd189dbff658e7e47cca8862");
} catch (error) {
__citryRuntime.finishScript("9ffd17087fb9d27647fe78ca84d302386518629edd189dbff658e7e47cca8862", error);
}