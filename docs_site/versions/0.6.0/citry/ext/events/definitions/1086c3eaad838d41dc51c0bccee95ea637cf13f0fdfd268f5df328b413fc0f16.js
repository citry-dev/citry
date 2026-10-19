(function() {

__citryRuntime.registerTypeOptions.bind(null, "IndeterminateCheckbox_d4fd78", "2ef09127dbbd36a559415d9a0aeb7ecf8381eca4cb82ed1ede54a45d018a2008")({
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