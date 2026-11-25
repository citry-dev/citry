try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonDisabledAndLoading_a140ef", "5bda49e702acab35fec89072c569288e32ca744dc5dc394eba12737889874665")({data(){return {
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
__citryRuntime.finishScript("0b8abaed91c31ae63f0e20a998f2f9116d2914b3391d482a3efd099859a19fa0");
} catch (error) {
__citryRuntime.finishScript("0b8abaed91c31ae63f0e20a998f2f9116d2914b3391d482a3efd099859a19fa0", error);
}