try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonForms_0b6cc5", "f8e8f48050e7a1f836adcfc9fac0d7839e4fd26d548a910591a24356e250fa9e")({
  data(){return {result:'No Form action yet',owner:'accession-form'};},
  onServerRender({component}) {
    const primary=component.$refs.externalSplit.$el.querySelector(
      '[data-citry-ui-part="split-button-primary"]'
    );
    Citry.vue.watchEffect(()=>primary.setAttribute('form',component.owner));
  },
});

})();
__citryRuntime.finishScript("6320f31cfd47b1bcda99fa4552b11b40ab74591a8a942ea62ada8e5c97d70390");
} catch (error) {
__citryRuntime.finishScript("6320f31cfd47b1bcda99fa4552b11b40ab74591a8a942ea62ada8e5c97d70390", error);
}