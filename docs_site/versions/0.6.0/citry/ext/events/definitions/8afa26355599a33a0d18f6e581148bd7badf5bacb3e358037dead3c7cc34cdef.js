(function() {

__citryRuntime.registerTypeOptions.bind(null, "RowsAndResize_34e891", "2e746cdde83e899fda5cdd6c08a88af1141efc45f1387d57153fe073ffb86d38")({
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