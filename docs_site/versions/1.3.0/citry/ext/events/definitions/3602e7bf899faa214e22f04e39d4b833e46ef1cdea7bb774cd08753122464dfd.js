try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonForms_b11cd5", "f8e8f48050e7a1f836adcfc9fac0d7839e4fd26d548a910591a24356e250fa9e")({
  data(){return {result:'No Form action yet',owner:'accession-form'};},
  onServerRender({component}) {
    const primary=component.$refs.externalSplit.$el.querySelector(
      '[data-citry-ui-part="split-button-primary"]'
    );
    Citry.vue.watchEffect(()=>primary.setAttribute('form',component.owner));
  },
});

})();
__citryRuntime.finishScript("19e897237e728a19ab04a866710c49a706b03b227d1d837e4bc86fe4762eb99f");
} catch (error) {
__citryRuntime.finishScript("19e897237e728a19ab04a866710c49a706b03b227d1d837e4bc86fe4762eb99f", error);
}