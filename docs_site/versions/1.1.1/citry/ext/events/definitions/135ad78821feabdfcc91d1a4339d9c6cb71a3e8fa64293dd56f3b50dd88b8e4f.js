try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonLayersAndDialog_91a47c", "87702bc6a0765c8969a984c27425c3f5e8603e48324ab393ee74725ae3178bbe")({
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
__citryRuntime.finishScript("8d65e3dbcbcc8a1b4a479df4a81372f418d68e66413468561c9059f8aa612da8");
} catch (error) {
__citryRuntime.finishScript("8d65e3dbcbcc8a1b4a479df4a81372f418d68e66413468561c9059f8aa612da8", error);
}