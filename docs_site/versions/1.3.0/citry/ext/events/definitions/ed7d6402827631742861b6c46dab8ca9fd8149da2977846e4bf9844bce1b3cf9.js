try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledPopover_6dfa83", "6ced216940fd74aa82af40e75b20d2887570331febbb455314f1d42ab607e01d")({
  data() {
    return {
      open: false, locked: false, lastReason: 'none'
    };
  },
  methods: {
    // Show every request's reason, but change `open` only while
    // requests are not locked, so a declined request leaves the
    // Popover as is.
    applyOpenRequest(nextOpen, detail) {
      this.lastReason = detail.reason;
      if (!this.locked) this.open = nextOpen;
    },
  },
});

})();
__citryRuntime.finishScript("b5fc038519cfca36e12fa00bee5d36de767946e42639c374a442c772216c8072");
} catch (error) {
__citryRuntime.finishScript("b5fc038519cfca36e12fa00bee5d36de767946e42639c374a442c772216c8072", error);
}