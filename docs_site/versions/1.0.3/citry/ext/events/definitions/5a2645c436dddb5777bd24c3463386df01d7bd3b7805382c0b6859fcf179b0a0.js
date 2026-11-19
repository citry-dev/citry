try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormSafePalette_178851", "ae27fb33fab7a717abb81f814fab44d3973b6a726ee7ae5723dcef0d531ae6c3")({
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
__citryRuntime.finishScript("3be5944db4f8be903b9cc009f9f59f96e8984e9dbfde032d0153de9b6d13c22d");
} catch (error) {
__citryRuntime.finishScript("3be5944db4f8be903b9cc009f9f59f96e8984e9dbfde032d0153de9b6d13c22d", error);
}