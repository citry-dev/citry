try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureAlert_8c1ccd", "0783867deefad4dea1bca638f2c6892d91fad1f06ffb71ccbcd6b2688540bc48")({
  data() {
    return {
      intent: 'info',
      variant: 'soft',
      size: 'md',
      announce: 'off',
      icon: true,
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
__citryRuntime.finishScript("cf5ecea1d244d6168e805304aab693abb7e9bf4934673b6bf7c2bd462bb0aef8");
} catch (error) {
__citryRuntime.finishScript("cf5ecea1d244d6168e805304aab693abb7e9bf4934673b6bf7c2bd462bb0aef8", error);
}