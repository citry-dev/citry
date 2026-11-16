try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledDrawer_89a0ea", "3f9a2f344eaa2625b6ab60c788b6dc79781ae5616370f2289ba69b114c9c5934")({
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
__citryRuntime.finishScript("6ca0c2ada6d89e3aea13db02442ad281da343cf1dbc3be899a78a0cc3db48247");
} catch (error) {
__citryRuntime.finishScript("6ca0c2ada6d89e3aea13db02442ad281da343cf1dbc3be899a78a0cc3db48247", error);
}