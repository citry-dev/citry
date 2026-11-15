try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DrawerForm_18d74f", "019e594f039c5dccf56606269cd2ef75e1e1232f788d7b17dd393c9c3d7e282c")({
  data() {
    return {
      result:'No chart selected'
    };
  },
  methods: {
    // Only a close from a button with a `value` carries a return
    // value, so other closes keep the last selection on screen.
    showSelectedChart(open, detail) {
      if (!open && detail.returnValue) this.result = `Selected: ${detail.returnValue}`;
    },
  },
});

})();
__citryRuntime.finishScript("ba2bdb81eb51f7d807b185c52bd0c7145e589f36eac794a1312f01e7b7cac053");
} catch (error) {
__citryRuntime.finishScript("ba2bdb81eb51f7d807b185c52bd0c7145e589f36eac794a1312f01e7b7cac053", error);
}