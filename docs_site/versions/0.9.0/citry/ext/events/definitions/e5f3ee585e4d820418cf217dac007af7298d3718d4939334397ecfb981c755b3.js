try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "IndeterminateCheckbox_9624f5", "2ef09127dbbd36a559415d9a0aeb7ecf8381eca4cb82ed1ede54a45d018a2008")({
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
__citryRuntime.finishScript("ffee1551c32e8889e76712298cae47da89f7f7e74caa76958a6590018dbeb418");
} catch (error) {
__citryRuntime.finishScript("ffee1551c32e8889e76712298cae47da89f7f7e74caa76958a6590018dbeb418", error);
}