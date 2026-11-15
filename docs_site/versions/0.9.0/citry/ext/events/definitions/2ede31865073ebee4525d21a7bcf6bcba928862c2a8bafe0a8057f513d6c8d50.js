try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DialogForm_11fccc", "1afecaabd5e5246881f8fd6852ab65a3255482a3e16d78ed5a484110297945a0")({
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
__citryRuntime.finishScript("5c8c8227ebe83d23217f82bf0b83d3d68fc3310863701c2c0f6a84fd6ff63a28");
} catch (error) {
__citryRuntime.finishScript("5c8c8227ebe83d23217f82bf0b83d3d68fc3310863701c2c0f6a84fd6ff63a28", error);
}