try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledDisclosure_94b4b9", "d733e202eb3b2e2f7d89b1defaafdfd7c501d80c47ced77acde41961848658d7")({
  data() {
    return {
      open:false, controlled:true, accept:true, last:'none'
    };
  },
  methods: {
    // Show every request. Change `open` only while this owner controls
    // the Disclosure and accepts requests; after release the
    // Disclosure applies requests itself.
    applyOpenRequest(next, detail) {
      this.last = `${detail.source}: ${next ? 'open' : 'closed'}`;
      if (this.controlled && this.accept) this.open = next;
    },
  },
});

})();
__citryRuntime.finishScript("3c2f991c342088874f3bfaf978152e1ef94dfbcb10676caa3e236360874eccef");
} catch (error) {
__citryRuntime.finishScript("3c2f991c342088874f3bfaf978152e1ef94dfbcb10676caa3e236360874eccef", error);
}