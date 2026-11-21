try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ContextMenuFocusAndKeyboard_2a1596", "e998b9d45199372f1f9b235f44ac65c8138d29c0c357a28d4c95ac398320dc4d")({
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
__citryRuntime.finishScript("9cbf764cee6f2dc96d2adacb15af362178d5de3d93a7ee258c3fb1920409cb06");
} catch (error) {
__citryRuntime.finishScript("9cbf764cee6f2dc96d2adacb15af362178d5de3d93a7ee258c3fb1920409cb06", error);
}