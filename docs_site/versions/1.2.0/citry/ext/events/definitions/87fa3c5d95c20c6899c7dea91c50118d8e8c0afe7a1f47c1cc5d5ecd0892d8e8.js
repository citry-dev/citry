try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "RowsAndResize_8fe66c", "2e746cdde83e899fda5cdd6c08a88af1141efc45f1387d57153fe073ffb86d38")({
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
__citryRuntime.finishScript("f924ddbb7901129fafa5ca0d7d3386ed81ed692e51271c3b86292ffc2220e081");
} catch (error) {
__citryRuntime.finishScript("f924ddbb7901129fafa5ca0d7d3386ed81ed692e51271c3b86292ffc2220e081", error);
}