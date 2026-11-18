try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonAtAGlance_388118", "512849f5fdfc35dc59acd465a55a3bfc190b241478510070871b6cc1141755fc")({
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
__citryRuntime.finishScript("9b01d5efabe0caca984488d84c9a9b9c9b2be91816c851982677c20ad63caa14");
} catch (error) {
__citryRuntime.finishScript("9b01d5efabe0caca984488d84c9a9b9c9b2be91816c851982677c20ad63caa14", error);
}