try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledDrawer_6b03a3", "3f9a2f344eaa2625b6ab60c788b6dc79781ae5616370f2289ba69b114c9c5934")({
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
__citryRuntime.finishScript("4085519c2893102f6a1abc06a1e255bd5819b9087804e0357f693f4d7e3be4ed");
} catch (error) {
__citryRuntime.finishScript("4085519c2893102f6a1abc06a1e255bd5819b9087804e0357f693f4d7e3be4ed", error);
}