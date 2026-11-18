try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "CommandActions_56ae8e", "ed3a5ee2b4c4838662e8274ca3fbefb9f0ec40273b61c9b1f433098baec05afd")({
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
__citryRuntime.finishScript("b5e25986f1a489db9da4af6a9d72b70e22f5b95d690eb17b77eea5a303d1e91e");
} catch (error) {
__citryRuntime.finishScript("b5e25986f1a489db9da4af6a9d72b70e22f5b95d690eb17b77eea5a303d1e91e", error);
}