try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonAtAGlance_7ec56f", "512849f5fdfc35dc59acd465a55a3bfc190b241478510070871b6cc1141755fc")({
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
__citryRuntime.finishScript("15e018f4548e17314d6e9a86c70f931d3cb378a2c3ee2309d9fdf27ee4d5ada0");
} catch (error) {
__citryRuntime.finishScript("15e018f4548e17314d6e9a86c70f931d3cb378a2c3ee2309d9fdf27ee4d5ada0", error);
}