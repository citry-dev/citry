try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "RowsAndResize_ec63c3", "2e746cdde83e899fda5cdd6c08a88af1141efc45f1387d57153fe073ffb86d38")({
  data() {
    return {
      rows: 4, resize: 'vertical'
    };
  },
  methods: {
    applyPreviewControls(event) {
      // A select reports its choice as text, and a bound `rows`
      // must be a number, so convert it before passing it on.
      const { rows, resize } = event.detail;
      Object.assign(this, { rows: Number(rows), resize });
    },
  },
  mounted() {
    window.addEventListener("citry-ui-preview-controls", this.applyPreviewControls);
  },
  beforeUnmount() {
    window.removeEventListener("citry-ui-preview-controls", this.applyPreviewControls);
  },
});

})();
__citryRuntime.finishScript("a05824368259fb6e7f899218e30072f5578ff15e70f9311775a579d6a6c3dfee");
} catch (error) {
__citryRuntime.finishScript("a05824368259fb6e7f899218e30072f5578ff15e70f9311775a579d6a6c3dfee", error);
}