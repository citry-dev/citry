try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DialogForm_16aa2d", "1afecaabd5e5246881f8fd6852ab65a3255482a3e16d78ed5a484110297945a0")({
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
__citryRuntime.finishScript("c75b1d3f95a2ba316798408c7412a53868880ebba5802bf6e05394292ae58463");
} catch (error) {
__citryRuntime.finishScript("c75b1d3f95a2ba316798408c7412a53868880ebba5802bf6e05394292ae58463", error);
}