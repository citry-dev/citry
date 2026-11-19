try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonAtAGlance_1d6608", "512849f5fdfc35dc59acd465a55a3bfc190b241478510070871b6cc1141755fc")({
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
__citryRuntime.finishScript("74b64f6cc915f6f5300f9c7ee3461d87a3ee0e35ea1ea911584c31aa9aaa6505");
} catch (error) {
__citryRuntime.finishScript("74b64f6cc915f6f5300f9c7ee3461d87a3ee0e35ea1ea911584c31aa9aaa6505", error);
}