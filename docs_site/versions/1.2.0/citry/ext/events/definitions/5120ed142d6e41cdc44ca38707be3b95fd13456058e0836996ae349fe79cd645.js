try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledDisclosure_c0b842", "d733e202eb3b2e2f7d89b1defaafdfd7c501d80c47ced77acde41961848658d7")({
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
__citryRuntime.finishScript("ac1992bd881dcf65a3e38783aa5d5e78d51f0b7f78c78dd409fb77ccdf4b163f");
} catch (error) {
__citryRuntime.finishScript("ac1992bd881dcf65a3e38783aa5d5e78d51f0b7f78c78dd409fb77ccdf4b163f", error);
}