try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonDisabledAndLoading_3f1262", "5bda49e702acab35fec89072c569288e32ca744dc5dc394eba12737889874665")({data(){return {
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
__citryRuntime.finishScript("87516ea514dca7e0b17529fedd0e1c76786ac71c85e387f1f6c3a01d9891c54b");
} catch (error) {
__citryRuntime.finishScript("87516ea514dca7e0b17529fedd0e1c76786ac71c85e387f1f6c3a01d9891c54b", error);
}