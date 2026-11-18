try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledDisclosure_eb0a04", "d733e202eb3b2e2f7d89b1defaafdfd7c501d80c47ced77acde41961848658d7")({
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
__citryRuntime.finishScript("de9cc8cd7c2e8dc868d7108710822cc845b6a26f11466c9b7f48e18628b2400f");
} catch (error) {
__citryRuntime.finishScript("de9cc8cd7c2e8dc868d7108710822cc845b6a26f11466c9b7f48e18628b2400f", error);
}