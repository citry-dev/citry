try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledArchive_a86bd4", "71126af3723347b7e75ebabb6f5fa2b2a01fb669282af323777613de5b02b99e")({
  data() {
    return {
      open: false, pending: false, result: 'No decision yet'
    };
  },
  methods: {
    applyArchiveDecision(next, detail) {
      // When Archive is chosen, keep the dialog open while the work
      // runs and close it once the record is archived.
      if (detail.returnValue === 'action') {
        this.pending = true;
        this.result = 'Archiving...';
        window.setTimeout(() => {
          this.pending = false;
          this.open = false;
          this.result = 'Record archived';
        }, 500);
      } else {
        // While the record is archiving, decline Escape and every other
        // close request, as the disabled Cancel button does, so the
        // dialog cannot report a cancel for work that still finishes.
        if (this.pending) return;
        // Apply every other request as it comes, and note a cancel
        // when the dialog closes.
        this.open = next;
        if (!next) this.result = 'Archive cancelled';
      }
    },
  },
});

})();
__citryRuntime.finishScript("5e0db33accd6998be71fb5e60c6bc240ec20aff5537ae3960493630940591788");
} catch (error) {
__citryRuntime.finishScript("5e0db33accd6998be71fb5e60c6bc240ec20aff5537ae3960493630940591788", error);
}