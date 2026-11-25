try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DrawerForm_9f6579", "019e594f039c5dccf56606269cd2ef75e1e1232f788d7b17dd393c9c3d7e282c")({
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
__citryRuntime.finishScript("dab70e6165d05ce6c12db768667b62bb32805f0c5f014fe2c5b03269e0f9cd47");
} catch (error) {
__citryRuntime.finishScript("dab70e6165d05ce6c12db768667b62bb32805f0c5f014fe2c5b03269e0f9cd47", error);
}