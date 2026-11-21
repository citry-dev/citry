try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "IndeterminateCheckbox_aee6ca", "2ef09127dbbd36a559415d9a0aeb7ecf8381eca4cb82ed1ede54a45d018a2008")({
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
__citryRuntime.finishScript("63f4a6210a7a4990b24b6e126157a24aff5ec761f99040921e227550ff304878");
} catch (error) {
__citryRuntime.finishScript("63f4a6210a7a4990b24b6e126157a24aff5ec761f99040921e227550ff304878", error);
}