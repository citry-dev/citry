try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "IndeterminateCheckbox_9ca130", "2ef09127dbbd36a559415d9a0aeb7ecf8381eca4cb82ed1ede54a45d018a2008")({
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
__citryRuntime.finishScript("36255315716041baad68426fb2f6cbe71720b0506df52345df58af6f608b936f");
} catch (error) {
__citryRuntime.finishScript("36255315716041baad68426fb2f6cbe71720b0506df52345df58af6f608b936f", error);
}