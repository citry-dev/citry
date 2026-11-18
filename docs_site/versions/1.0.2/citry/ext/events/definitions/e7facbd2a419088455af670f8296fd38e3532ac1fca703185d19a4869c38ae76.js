try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonDisabledAndLoading_826fc1", "5bda49e702acab35fec89072c569288e32ca744dc5dc394eba12737889874665")({data(){return {
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
__citryRuntime.finishScript("f892dc94b100527f175a96042c5bb53b9546b2a4e8c214318338d430654f6961");
} catch (error) {
__citryRuntime.finishScript("f892dc94b100527f175a96042c5bb53b9546b2a4e8c214318338d430654f6961", error);
}