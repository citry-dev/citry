try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DisclosureFormsAndFocus_4e0118", "b2e3effafc0f9ad29cae8f88ea8c45efb6786b3097a6d6c33364f378d5a281bf")({
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
__citryRuntime.finishScript("dc3bc1b22af7026968892f73a40728732a84e445ff1f24ec352d429f1ebc3dc5");
} catch (error) {
__citryRuntime.finishScript("dc3bc1b22af7026968892f73a40728732a84e445ff1f24ec352d429f1ebc3dc5", error);
}