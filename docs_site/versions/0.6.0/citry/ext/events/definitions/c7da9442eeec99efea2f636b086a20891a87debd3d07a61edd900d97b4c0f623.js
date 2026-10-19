(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledMenu_20da5f", "3f718c0682110d20fabf436d9cd98adc187d37669cd754e21f9ddc396fd5ea37")({
  data(){return {open: false, disabled: false, locked: false, size: 'md', lastReason: 'none'};},
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