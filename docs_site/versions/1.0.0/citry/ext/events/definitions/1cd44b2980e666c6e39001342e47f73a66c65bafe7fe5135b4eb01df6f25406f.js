try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonDisabledAndLoading_86b3df", "5bda49e702acab35fec89072c569288e32ca744dc5dc394eba12737889874665")({data(){return {
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
__citryRuntime.finishScript("f1144fda2ba23a409cd891c8cd525288f50dd138179c35ff58d724cf49ffcd30");
} catch (error) {
__citryRuntime.finishScript("f1144fda2ba23a409cd891c8cd525288f50dd138179c35ff58d724cf49ffcd30", error);
}