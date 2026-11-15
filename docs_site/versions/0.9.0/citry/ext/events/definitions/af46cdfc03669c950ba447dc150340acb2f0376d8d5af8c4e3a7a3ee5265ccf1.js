try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledDrawer_eac62d", "3f9a2f344eaa2625b6ab60c788b6dc79781ae5616370f2289ba69b114c9c5934")({
  data() {
    return {
      open:false, accept:true, log:'No request yet'
    };
  },
  methods: {
    // Show every request's reason, but change `open` only while the
    // owner accepts requests, so a declined request leaves the Drawer
    // as is.
    applyOpenRequest(next, detail) {
      this.log = `${detail.reason}: ${next ? 'open' : 'closed'}`;
      if (this.accept) this.open = next;
    },
  },
});

})();
__citryRuntime.finishScript("1c73148ddf908db432943945183ac36e1a213d465db9b140e1fad92ec7becbe3");
} catch (error) {
__citryRuntime.finishScript("1c73148ddf908db432943945183ac36e1a213d465db9b140e1fad92ec7becbe3", error);
}