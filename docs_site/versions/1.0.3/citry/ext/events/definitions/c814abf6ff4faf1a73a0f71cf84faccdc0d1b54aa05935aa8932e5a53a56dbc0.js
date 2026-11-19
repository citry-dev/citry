try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "IndeterminateCheckbox_869640", "2ef09127dbbd36a559415d9a0aeb7ecf8381eca4cb82ed1ede54a45d018a2008")({
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
__citryRuntime.finishScript("6d74c25ebf38ea5311995f0b738d8b60cd6fc0f17f3df110c6cbc1931649c4ec");
} catch (error) {
__citryRuntime.finishScript("6d74c25ebf38ea5311995f0b738d8b60cd6fc0f17f3df110c6cbc1931649c4ec", error);
}