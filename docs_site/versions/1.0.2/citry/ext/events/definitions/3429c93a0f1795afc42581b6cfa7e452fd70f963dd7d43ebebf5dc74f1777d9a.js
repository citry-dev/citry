try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "IndeterminateCheckbox_465b74", "2ef09127dbbd36a559415d9a0aeb7ecf8381eca4cb82ed1ede54a45d018a2008")({
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
__citryRuntime.finishScript("96c41174cfe0a7832a99161d4b923d6d87786c206c135f313321e9240b923d5d");
} catch (error) {
__citryRuntime.finishScript("96c41174cfe0a7832a99161d4b923d6d87786c206c135f313321e9240b923d5d", error);
}