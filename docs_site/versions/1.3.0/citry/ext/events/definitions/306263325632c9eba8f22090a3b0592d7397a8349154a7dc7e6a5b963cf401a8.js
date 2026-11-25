try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonLayersAndDialog_152e15", "87702bc6a0765c8969a984c27425c3f5e8603e48324ab393ee74725ae3178bbe")({
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
__citryRuntime.finishScript("0d9bc8f939e575ae47abea0b1718f77a3db5aa56f41cdf4bd559e2efd6db4def");
} catch (error) {
__citryRuntime.finishScript("0d9bc8f939e575ae47abea0b1718f77a3db5aa56f41cdf4bd559e2efd6db4def", error);
}