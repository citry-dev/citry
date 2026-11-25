try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ResponsiveImageSources_98f81c", "fca8f2f1f6970d6657e18366ba1aa7a3687558bea68d28c7c018d8323e2da6a4")({
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
__citryRuntime.finishScript("cbcc4182887b7f4ce81f524dfc8d87f1248f96ff6169052e6e3b95124b7b8f84");
} catch (error) {
__citryRuntime.finishScript("cbcc4182887b7f4ce81f524dfc8d87f1248f96ff6169052e6e3b95124b7b8f84", error);
}