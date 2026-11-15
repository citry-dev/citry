try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledDisclosure_90888f", "d733e202eb3b2e2f7d89b1defaafdfd7c501d80c47ced77acde41961848658d7")({
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
__citryRuntime.finishScript("6759e41c30d4568c347e15d78e11e23b4b917a0f7cad6604b190170b3c129f7d");
} catch (error) {
__citryRuntime.finishScript("6759e41c30d4568c347e15d78e11e23b4b917a0f7cad6604b190170b3c129f7d", error);
}