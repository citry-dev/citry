try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureDrawer_dccf7e", "9be70bc424d319fcab84660c283a174860ff2b7ee587044dfd4fc0c9cb1518eb")({
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
__citryRuntime.finishScript("6d3969bbd1e3667c5c6181f6098a934eccf69d8a8a1eeb31f084a180777eefb6");
} catch (error) {
__citryRuntime.finishScript("6d3969bbd1e3667c5c6181f6098a934eccf69d8a8a1eeb31f084a180777eefb6", error);
}