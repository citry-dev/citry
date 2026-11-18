try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "CommandActions_f6974c", "ed3a5ee2b4c4838662e8274ca3fbefb9f0ec40273b61c9b1f433098baec05afd")({
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
__citryRuntime.finishScript("c5e2062b701ba3878435f3a72830a195fb4a41ab6793e4aea500ea9474b7a4c8");
} catch (error) {
__citryRuntime.finishScript("c5e2062b701ba3878435f3a72830a195fb4a41ab6793e4aea500ea9474b7a4c8", error);
}