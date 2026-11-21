try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormSafePalette_833421", "ae27fb33fab7a717abb81f814fab44d3973b6a726ee7ae5723dcef0d531ae6c3")({
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
__citryRuntime.finishScript("7178aa3a449377bcb11cad37ef0e632be5e98a509808063e5ed765dba894acaf");
} catch (error) {
__citryRuntime.finishScript("7178aa3a449377bcb11cad37ef0e632be5e98a509808063e5ed765dba894acaf", error);
}