try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DisclosureFormsAndFocus_ad26c9", "b2e3effafc0f9ad29cae8f88ea8c45efb6786b3097a6d6c33364f378d5a281bf")({
  data() {
    return {
      notificationOpen:true, escalationOpen:false, invalidTarget:null
    };
  },
  methods: {
    handleInvalid(event) {
      if (event.target.name === 'notification-email') {
        event.preventDefault();
        this.notificationOpen = true;
      } else if (event.target.name === 'escalation-contact') {
        event.preventDefault();
        this.escalationOpen = true;
      } else {
        return;
      }
      if (this.invalidTarget === null) {
        this.invalidTarget = event.target;
        // A submit fires `invalid` for each control, and queued
        // microtasks run between those events. Clearing
        // `invalidTarget` in `$nextTick` would let each later control
        // schedule its own focus, so the last one would win. A timer
        // runs once, after every event and after Vue opens the panel,
        // so the first invalid control keeps focus.
        setTimeout(() => {
          this.invalidTarget?.focus();
          this.invalidTarget = null;
        }, 0);
      }
    },
  },
});

})();
__citryRuntime.finishScript("a5ad2667be374f3a8e8037ef2dadcb0391b5cb997f66fc19e4b623b1070dc1c3");
} catch (error) {
__citryRuntime.finishScript("a5ad2667be374f3a8e8037ef2dadcb0391b5cb997f66fc19e4b623b1070dc1c3", error);
}