try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DrawerForm_372005", "019e594f039c5dccf56606269cd2ef75e1e1232f788d7b17dd393c9c3d7e282c")({
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
__citryRuntime.finishScript("6fa9eb227417eb3aab5b07675c41dcb66e10ec32b70ae61d4e603062b79a0cf8");
} catch (error) {
__citryRuntime.finishScript("6fa9eb227417eb3aab5b07675c41dcb66e10ec32b70ae61d4e603062b79a0cf8", error);
}