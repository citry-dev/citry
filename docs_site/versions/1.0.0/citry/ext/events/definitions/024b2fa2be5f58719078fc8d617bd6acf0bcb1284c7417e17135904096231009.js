try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "CommandActions_24a8df", "ed3a5ee2b4c4838662e8274ca3fbefb9f0ec40273b61c9b1f433098baec05afd")({
  data() {
    return {
      open:true,events:[],throwNext:false,moveFocus:false
    };
  },
  methods: {
    logOpenChange(value, detail) {
      this.events.push(`open:${value}:${detail.reason}`);
      this.open = value;
    },
    runAction(value, detail) {
      this.events.push(`action:${value}:${detail.source}:${detail.closeOnAction}`);
      if (this.moveFocus) this.$refs.focusTarget.focus();
      // Throw once, so the console shows the reported error.
      if (this.throwNext) {
        this.throwNext = false;
        throw new Error('Application action failed');
      }
    },
  },
});

})();
__citryRuntime.finishScript("4b89df07b5b2db16d8e47c00bc1b21957dd0503b5ba1d1b21851e0a12325244a");
} catch (error) {
__citryRuntime.finishScript("4b89df07b5b2db16d8e47c00bc1b21957dd0503b5ba1d1b21851e0a12325244a", error);
}