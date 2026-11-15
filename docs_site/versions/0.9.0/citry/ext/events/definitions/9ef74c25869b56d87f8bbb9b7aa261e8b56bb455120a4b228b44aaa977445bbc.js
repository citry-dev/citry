try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ResponsiveImageSources_50f6a6", "fca8f2f1f6970d6657e18366ba1aa7a3687558bea68d28c7c018d8323e2da6a4")({
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
__citryRuntime.finishScript("97e3be145c8e81d4e0b41e970e07472734e0eb3f1456ecf3149d0f37987b3ba6");
} catch (error) {
__citryRuntime.finishScript("97e3be145c8e81d4e0b41e970e07472734e0eb3f1456ecf3149d0f37987b3ba6", error);
}