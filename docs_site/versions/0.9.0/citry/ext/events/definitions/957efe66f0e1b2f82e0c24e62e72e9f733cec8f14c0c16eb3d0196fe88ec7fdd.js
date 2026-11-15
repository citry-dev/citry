try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledContextMenu_d6a95b", "a32b365e1ac670c18b0e03d59fd1aace9dc6e199f8f40543d9487293590fb810")({
  data(){return {
    open:false,
    controlled:true,
    accept:true,
    breakClaim:false,
    lastReason:'none',
    candidate:'none',
  };},
  methods: {
    // Returning true tells the menu that the owner opened it, so the
    // menu blocks the browser's own menu. Any other return lets the
    // browser's menu show. "Break the claim" returns true without
    // opening, which the menu reports as a broken claim.
    claimOpenRequest(nextOpen, detail) {
      this.lastReason = detail.reason;
      this.candidate = `${Math.round(detail.clientX)}, ${Math.round(detail.clientY)}`;
      // After release the menu opens and closes by itself and ignores
      // what this returns.
      if (!this.controlled) return;
      // The owner always accepts a close.
      if (!nextOpen) {
        this.open = false;
        return;
      }
      if (!this.accept) return false;
      if (!this.breakClaim) this.open = true;
      return true;
    },
  },
});

})();
__citryRuntime.finishScript("5f76dbb8df9ed396d3a03f1bd219bd564229979cc2ca862633b5d367c7adc964");
} catch (error) {
__citryRuntime.finishScript("5f76dbb8df9ed396d3a03f1bd219bd564229979cc2ca862633b5d367c7adc964", error);
}