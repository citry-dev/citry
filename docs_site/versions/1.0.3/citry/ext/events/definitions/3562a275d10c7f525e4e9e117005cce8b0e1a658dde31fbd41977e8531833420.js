try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DrawerForm_6ea27b", "019e594f039c5dccf56606269cd2ef75e1e1232f788d7b17dd393c9c3d7e282c")({
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
__citryRuntime.finishScript("35584467a38338e918c9c6af8aeba5c71ec6d2846997f357b92baf6d9944ed4e");
} catch (error) {
__citryRuntime.finishScript("35584467a38338e918c9c6af8aeba5c71ec6d2846997f357b92baf6d9944ed4e", error);
}