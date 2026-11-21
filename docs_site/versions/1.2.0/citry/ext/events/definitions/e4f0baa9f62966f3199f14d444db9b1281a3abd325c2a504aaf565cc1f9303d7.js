try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonAtAGlance_5cbd1a", "512849f5fdfc35dc59acd465a55a3bfc190b241478510070871b6cc1141755fc")({
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
__citryRuntime.finishScript("fcea9c1bb5163b3c487726df89466a6e4408dbb953b8fc3442785dfa53d111fc");
} catch (error) {
__citryRuntime.finishScript("fcea9c1bb5163b3c487726df89466a6e4408dbb953b8fc3442785dfa53d111fc", error);
}