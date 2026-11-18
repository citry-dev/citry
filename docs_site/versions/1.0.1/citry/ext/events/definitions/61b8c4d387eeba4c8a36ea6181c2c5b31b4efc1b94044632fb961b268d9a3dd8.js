try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonLayersAndDialog_0f6d79", "87702bc6a0765c8969a984c27425c3f5e8603e48324ab393ee74725ae3178bbe")({
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
__citryRuntime.finishScript("6ad095a1e6e6b66f2e03ebddd5e30fc283381774b91a52db362c74671b87d872");
} catch (error) {
__citryRuntime.finishScript("6ad095a1e6e6b66f2e03ebddd5e30fc283381774b91a52db362c74671b87d872", error);
}