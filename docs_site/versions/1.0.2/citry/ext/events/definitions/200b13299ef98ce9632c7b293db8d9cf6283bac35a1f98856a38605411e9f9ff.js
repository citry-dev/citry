try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DialogForm_bc3bb0", "1afecaabd5e5246881f8fd6852ab65a3255482a3e16d78ed5a484110297945a0")({
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
__citryRuntime.finishScript("3d04b1787e92b47fb188dc36f970eb7083d17367d5ff15f29ed16cd922bcc18f");
} catch (error) {
__citryRuntime.finishScript("3d04b1787e92b47fb188dc36f970eb7083d17367d5ff15f29ed16cd922bcc18f", error);
}