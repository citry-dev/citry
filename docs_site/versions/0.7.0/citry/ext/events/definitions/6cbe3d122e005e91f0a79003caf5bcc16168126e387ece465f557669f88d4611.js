(function() {

__citryRuntime.registerTypeOptions.bind(null, "MenuKeyboard_5f0d68", "756c1490a2694523ca6ccb53edd916d7f91512de22b02d9951ce8a97ad53d8df")({
  data(){return {loop: true, close: false};},
  methods: {
    applyPreviewControls(event) {
      Object.assign(this, event.detail);
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