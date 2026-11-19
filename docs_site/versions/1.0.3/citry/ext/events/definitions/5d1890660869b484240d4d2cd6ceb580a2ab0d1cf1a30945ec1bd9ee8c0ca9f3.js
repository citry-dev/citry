try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledDisclosure_2ada57", "d733e202eb3b2e2f7d89b1defaafdfd7c501d80c47ced77acde41961848658d7")({
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
__citryRuntime.finishScript("770cea87fae033390a39c650a85b364f0bafc983cac6c66fba4f014b96e5bf6c");
} catch (error) {
__citryRuntime.finishScript("770cea87fae033390a39c650a85b364f0bafc983cac6c66fba4f014b96e5bf6c", error);
}