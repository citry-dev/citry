try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormConfiguration_558fc9", "15f209712e42d54b702e92057ac78aeaa37ccf9c09cedff9c84a539a199716b7")({
  data() {
    return {
      disabled: false,
      readonly: false,
      submitting: false,
      gap: '1rem',
    };
  },
  methods: {
    applyPreviewControls(event) {
      Object.assign(this, event.detail);
    },
  },
  mounted() {
    window.addEventListener("citry-ui-preview-controls", this.applyPreviewControls);
  },
  beforeUnmount() {
    window.removeEventListener("citry-ui-preview-controls", this.applyPreviewControls);
  },
});

})();
__citryRuntime.finishScript("e8a4467bfd84b1de36adf4c5de273e0e233404226033e83b18b6db1094c90e34");
} catch (error) {
__citryRuntime.finishScript("e8a4467bfd84b1de36adf4c5de273e0e233404226033e83b18b6db1094c90e34", error);
}