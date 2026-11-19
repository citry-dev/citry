try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledDrawer_647b32", "3f9a2f344eaa2625b6ab60c788b6dc79781ae5616370f2289ba69b114c9c5934")({
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
__citryRuntime.finishScript("633e5496b04cde5a237475328b7ddf13c8564170f38cbf17d25204758eb7d773");
} catch (error) {
__citryRuntime.finishScript("633e5496b04cde5a237475328b7ddf13c8564170f38cbf17d25204758eb7d773", error);
}