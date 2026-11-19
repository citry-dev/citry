try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DialogForm_143a7a", "1afecaabd5e5246881f8fd6852ab65a3255482a3e16d78ed5a484110297945a0")({
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
__citryRuntime.finishScript("f6208d4b8818b048ee66ddc47f1ddb249a3e531483365a5474b66a41ca4d1011");
} catch (error) {
__citryRuntime.finishScript("f6208d4b8818b048ee66ddc47f1ddb249a3e531483365a5474b66a41ca4d1011", error);
}