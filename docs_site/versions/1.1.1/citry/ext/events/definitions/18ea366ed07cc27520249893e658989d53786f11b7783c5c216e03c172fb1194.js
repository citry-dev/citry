try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DialogForm_894891", "1afecaabd5e5246881f8fd6852ab65a3255482a3e16d78ed5a484110297945a0")({
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
__citryRuntime.finishScript("b6d117c645ac5309bbe036397080833b0245b02864db05086cd09601ce6cf575");
} catch (error) {
__citryRuntime.finishScript("b6d117c645ac5309bbe036397080833b0245b02864db05086cd09601ce6cf575", error);
}