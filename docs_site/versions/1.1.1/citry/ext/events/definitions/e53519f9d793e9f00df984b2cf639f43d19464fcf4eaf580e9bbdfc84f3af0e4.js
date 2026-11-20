try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledSplitButtonMenu_fa5ce2", "826c5ace4d7e6bb593117196ed460b099196b62423c6f86c31d7eebfd1440934")({
  data(){return {
    open:false,
    controlled:true,
    accept:true,
    lastReason:'none'
  };},
  methods: {
    // Show every request's reason. Change `open` only while this owner controls
    // the Menu and accepts requests; after release the Menu applies
    // requests itself.
    applyOpenRequest(nextOpen, detail) {
      this.lastReason = detail.reason;
      if (this.controlled && this.accept) this.open = nextOpen;
    },
  },
});

})();
__citryRuntime.finishScript("0b5d7539232b1a87a95c2fdbeed1a1a87dd447492b39c10ab61d28bd8fdc305d");
} catch (error) {
__citryRuntime.finishScript("0b5d7539232b1a87a95c2fdbeed1a1a87dd447492b39c10ab61d28bd8fdc305d", error);
}