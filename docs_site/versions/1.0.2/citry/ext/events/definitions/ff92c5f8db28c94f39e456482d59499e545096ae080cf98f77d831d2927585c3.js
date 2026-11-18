try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DrawerForm_fd56b4", "019e594f039c5dccf56606269cd2ef75e1e1232f788d7b17dd393c9c3d7e282c")({
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
__citryRuntime.finishScript("ec185ae013d45d2d984fcd964f5fceba979bf68bc3b61ae2c418266e13587589");
} catch (error) {
__citryRuntime.finishScript("ec185ae013d45d2d984fcd964f5fceba979bf68bc3b61ae2c418266e13587589", error);
}