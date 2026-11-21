try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonDisabledAndLoading_a1d0f6", "5bda49e702acab35fec89072c569288e32ca744dc5dc394eba12737889874665")({data(){return {
    disabled: false,
    primaryDisabled: false,
    menuDisabled: false,
    loading: false,
    saves: 0,
    last: 'Ready',
  };},
  onServerRender({component}) {
    const primary=component.$refs.split.$el.querySelector(
      '[data-citry-ui-part="split-button-primary"]'
    );
    const save=()=>{component.saves += 1; component.last=`Saved ${component.saves} times`;};
    primary.addEventListener('click',save);
    return ()=>primary.removeEventListener('click',save);
  },
});

})();
__citryRuntime.finishScript("650ac5a672e8d43d45070443164b74ae0b18d6f8065e5543e9d5e9bbba936542");
} catch (error) {
__citryRuntime.finishScript("650ac5a672e8d43d45070443164b74ae0b18d6f8065e5543e9d5e9bbba936542", error);
}