try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonAtAGlance_9e9a0e", "512849f5fdfc35dc59acd465a55a3bfc190b241478510070871b6cc1141755fc")({
  data(){return {saved:0,last:'No action yet'};},
  onServerRender({component}) {
    const primary=component.$refs.split.$el.querySelector(
      '[data-citry-ui-part="split-button-primary"]'
    );
    const save=()=>{component.saved += 1; component.last=`Saved specimen ${component.saved}`;};
    primary.addEventListener('click',save);
    return ()=>primary.removeEventListener('click',save);
  },
});

})();
__citryRuntime.finishScript("6a666edae1ce5b4222ceb1d95fb19c335ff4c78aa2bba3cc1dc70c8c70a94a89");
} catch (error) {
__citryRuntime.finishScript("6a666edae1ce5b4222ceb1d95fb19c335ff4c78aa2bba3cc1dc70c8c70a94a89", error);
}