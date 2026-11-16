try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledDisclosure_e855d0", "d733e202eb3b2e2f7d89b1defaafdfd7c501d80c47ced77acde41961848658d7")({
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
__citryRuntime.finishScript("50e284a81292f31f24cd09b125374e506fedf534476e996192be91ab3c7ffe42");
} catch (error) {
__citryRuntime.finishScript("50e284a81292f31f24cd09b125374e506fedf534476e996192be91ab3c7ffe42", error);
}