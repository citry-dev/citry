try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "IndeterminateCheckbox_be5c8d", "2ef09127dbbd36a559415d9a0aeb7ecf8381eca4cb82ed1ede54a45d018a2008")({
  data() {
    return {
      meadow: true,
      woodland: false,
      wetland: true,
      get count() { return [this.meadow, this.woodland, this.wetland].filter(Boolean).length },
      get all() { return this.count === 3 },
      get mixed() { return this.count > 0 && this.count < 3 },
      setAll(value) { this.meadow = value; this.woodland = value; this.wetland = value },
    };
  },
});

})();
__citryRuntime.finishScript("fbf964877b9e0aadf5581d995bb6a568d318b0be323185e767163251e78f061b");
} catch (error) {
__citryRuntime.finishScript("fbf964877b9e0aadf5581d995bb6a568d318b0be323185e767163251e78f061b", error);
}