try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonLayersAndDialog_4a09e0", "87702bc6a0765c8969a984c27425c3f5e8603e48324ab393ee74725ae3178bbe")({
  data(){return {dialogOpen:false,last:'No layer action yet'};},
  methods: {
    // Show every chosen value. The provenance command also opens
    // the Dialog.
    applyLayerAction(value) {
      this.last = value;
      if (value === 'open-provenance') this.dialogOpen = true;
    },
  },
  mounted() {
    if (!this.$refs.shadowHost.shadowRoot) {
      this.$refs.shadowHost.attachShadow({mode:'open'}).append(this.$refs.shadowFixture);
    }
  },
});

})();
__citryRuntime.finishScript("10c1c1f4f41e5b6204fd8a94e56ecc332dba50ed56f619269eda1191eb4b79e4");
} catch (error) {
__citryRuntime.finishScript("10c1c1f4f41e5b6204fd8a94e56ecc332dba50ed56f619269eda1191eb4b79e4", error);
}