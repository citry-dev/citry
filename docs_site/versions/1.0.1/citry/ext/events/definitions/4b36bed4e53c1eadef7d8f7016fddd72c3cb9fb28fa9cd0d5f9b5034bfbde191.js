try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DrawerForm_7dfb51", "019e594f039c5dccf56606269cd2ef75e1e1232f788d7b17dd393c9c3d7e282c")({
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
__citryRuntime.finishScript("645fe03e7649a0c6d6edde20395af38ca914d116300da7a8891bdb70156fdd06");
} catch (error) {
__citryRuntime.finishScript("645fe03e7649a0c6d6edde20395af38ca914d116300da7a8891bdb70156fdd06", error);
}