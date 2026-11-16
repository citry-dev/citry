try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonLayersAndDialog_2a2b4c", "87702bc6a0765c8969a984c27425c3f5e8603e48324ab393ee74725ae3178bbe")({
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
__citryRuntime.finishScript("34707fd9ec2605f95d2ae8fc3209d615cd70054498d0b840a6cfa9016cb4390e");
} catch (error) {
__citryRuntime.finishScript("34707fd9ec2605f95d2ae8fc3209d615cd70054498d0b840a6cfa9016cb4390e", error);
}