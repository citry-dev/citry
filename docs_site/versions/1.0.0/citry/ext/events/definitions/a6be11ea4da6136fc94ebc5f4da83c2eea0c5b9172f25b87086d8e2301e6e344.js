try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DrawerForm_89a3b4", "019e594f039c5dccf56606269cd2ef75e1e1232f788d7b17dd393c9c3d7e282c")({
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
__citryRuntime.finishScript("3cd45b5266449493f946aef38c412a446631d6111fe4965262a4b3e0e7331cc3");
} catch (error) {
__citryRuntime.finishScript("3cd45b5266449493f946aef38c412a446631d6111fe4965262a4b3e0e7331cc3", error);
}