try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ContextMenuFocusAndKeyboard_64d9ed", "e998b9d45199372f1f9b235f44ac65c8138d29c0c357a28d4c95ac398320dc4d")({
  data(){return {disableInvoker:false,invokerRemoved:false,last:'No close yet'};},
  methods: {
    // Two commands disable or remove the nested Button, so the reader
    // can try the menu's focus return without it. Other commands leave
    // the Button as it is.
    changeReturnTarget(value) {
      if (value === 'disable-invoker') this.disableInvoker = true;
      if (value === 'remove-invoker') this.invokerRemoved = true;
    },
  },
});

})();
__citryRuntime.finishScript("28b8e732830c46cbaf985f409bf880295dca2ecb976d964650b49282b7eb39fd");
} catch (error) {
__citryRuntime.finishScript("28b8e732830c46cbaf985f409bf880295dca2ecb976d964650b49282b7eb39fd", error);
}