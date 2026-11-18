try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "RowsAndResize_553973", "2e746cdde83e899fda5cdd6c08a88af1141efc45f1387d57153fe073ffb86d38")({
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
__citryRuntime.finishScript("84c4994fa168a14136e6ab424b0279fc0bbf87bcf9757e2a8e70b51848a2a393");
} catch (error) {
__citryRuntime.finishScript("84c4994fa168a14136e6ab424b0279fc0bbf87bcf9757e2a8e70b51848a2a393", error);
}