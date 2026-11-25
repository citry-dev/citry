try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormSafePalette_9c30dd", "ae27fb33fab7a717abb81f814fab44d3973b6a726ee7ae5723dcef0d531ae6c3")({
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
__citryRuntime.finishScript("b7aefa20878309551d0a2bfb17844d4a024ee5bff24586f52bf55a6da3c40af0");
} catch (error) {
__citryRuntime.finishScript("b7aefa20878309551d0a2bfb17844d4a024ee5bff24586f52bf55a6da3c40af0", error);
}