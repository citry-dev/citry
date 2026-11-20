try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DrawerForm_1c1c86", "019e594f039c5dccf56606269cd2ef75e1e1232f788d7b17dd393c9c3d7e282c")({
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
__citryRuntime.finishScript("5bb024acaf25ba51211d76b4167bcd7d58dbf2e1c0f5e07d3b612f5ef678fb42");
} catch (error) {
__citryRuntime.finishScript("5bb024acaf25ba51211d76b4167bcd7d58dbf2e1c0f5e07d3b612f5ef678fb42", error);
}