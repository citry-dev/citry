try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormSafePalette_f8fae2", "ae27fb33fab7a717abb81f814fab44d3973b6a726ee7ae5723dcef0d531ae6c3")({
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
__citryRuntime.finishScript("b1e72deaa5cd63cabb5637e686e3fe8883644963f38f45273245ef91b4ac99ed");
} catch (error) {
__citryRuntime.finishScript("b1e72deaa5cd63cabb5637e686e3fe8883644963f38f45273245ef91b4ac99ed", error);
}