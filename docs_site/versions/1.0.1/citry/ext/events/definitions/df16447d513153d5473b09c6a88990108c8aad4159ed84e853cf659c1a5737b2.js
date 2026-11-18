try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormSafePalette_b4093e", "ae27fb33fab7a717abb81f814fab44d3973b6a726ee7ae5723dcef0d531ae6c3")({
  data() {
    return {
      open:false,submits:0,actions:0,query:''
    };
  },
  methods: {
    // Only an explicit action submits the form; Enter in the palette
    // never does.
    runAction(value) {
      this.actions++;
      if (value === 'focus-name') this.$refs.nameInput.focus();
      if (value === 'submit-profile') this.$refs.form.requestSubmit();
    },
  },
});

})();
__citryRuntime.finishScript("690fd5f9b34ac9bf0af6c39398cf2d93ee1e7ad10a8ad66103ca35cab53f9cc5");
} catch (error) {
__citryRuntime.finishScript("690fd5f9b34ac9bf0af6c39398cf2d93ee1e7ad10a8ad66103ca35cab53f9cc5", error);
}