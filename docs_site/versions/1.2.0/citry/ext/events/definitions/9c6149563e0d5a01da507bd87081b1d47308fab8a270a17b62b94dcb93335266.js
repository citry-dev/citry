try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DialogForm_ac53bb", "1afecaabd5e5246881f8fd6852ab65a3255482a3e16d78ed5a484110297945a0")({
  data() {
    return {
      result: 'No constellation selected'
    };
  },
  methods: {
    // Only a close from a button with a `value` carries a return
    // value, so other closes keep the last selection on screen.
    showSelectedConstellation(open, detail) {
      if (!open && detail.returnValue) this.result = detail.returnValue;
    },
  },
});

})();
__citryRuntime.finishScript("0c72648795579618490822a9652686c44b0012c94605682443158d8816741331");
} catch (error) {
__citryRuntime.finishScript("0c72648795579618490822a9652686c44b0012c94605682443158d8816741331", error);
}