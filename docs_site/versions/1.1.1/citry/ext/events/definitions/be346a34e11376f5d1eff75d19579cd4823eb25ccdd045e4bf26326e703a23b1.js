try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonAtAGlance_57b6ac", "512849f5fdfc35dc59acd465a55a3bfc190b241478510070871b6cc1141755fc")({
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
__citryRuntime.finishScript("3731200e9879990c8e2f68f58a53cd947fe388f393ca778f5741e0a9d1710c57");
} catch (error) {
__citryRuntime.finishScript("3731200e9879990c8e2f68f58a53cd947fe388f393ca778f5741e0a9d1710c57", error);
}