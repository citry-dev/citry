(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureDrawer_eef390", "9be70bc424d319fcab84660c283a174860ff2b7ee587044dfd4fc0c9cb1518eb")({
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