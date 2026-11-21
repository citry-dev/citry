try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ResponsiveImageSources_0d3122", "fca8f2f1f6970d6657e18366ba1aa7a3687558bea68d28c7c018d8323e2da6a4")({
  data() {
    return {
      selected:'Waiting for native selection'
    };
  },
  methods: {
    // The browser picks the candidate, so show the filename it
    // settled on, which changes across the 48rem and 64rem widths.
    showSelectedSource(detail) {
      const value = detail.current_src || detail.src;
      this.selected = value.split('/').pop().split('?')[0];
    },
  },
});

})();
__citryRuntime.finishScript("d573cccea5db06426e7b9b91d46d06d1681f965ca1f426e7814c2b3b1e680bb7");
} catch (error) {
__citryRuntime.finishScript("d573cccea5db06426e7b9b91d46d06d1681f965ca1f426e7814c2b3b1e680bb7", error);
}