try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FormSafePalette_743de2", "ae27fb33fab7a717abb81f814fab44d3973b6a726ee7ae5723dcef0d531ae6c3")({
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
__citryRuntime.finishScript("28f0d6c22dba9612d2d2257580071d757023be89fd4de98519d1f88c6ba78da6");
} catch (error) {
__citryRuntime.finishScript("28f0d6c22dba9612d2d2257580071d757023be89fd4de98519d1f88c6ba78da6", error);
}