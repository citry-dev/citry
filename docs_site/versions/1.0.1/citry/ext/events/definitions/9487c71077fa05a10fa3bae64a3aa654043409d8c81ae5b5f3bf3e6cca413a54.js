try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ResponsiveImageSources_ca2148", "fca8f2f1f6970d6657e18366ba1aa7a3687558bea68d28c7c018d8323e2da6a4")({
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
__citryRuntime.finishScript("96437c4d4f5d4c68dd864c161ddb0aaadc10c1a02f72c94c0fd46d15b2050319");
} catch (error) {
__citryRuntime.finishScript("96437c4d4f5d4c68dd864c161ddb0aaadc10c1a02f72c94c0fd46d15b2050319", error);
}