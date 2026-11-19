try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonForms_3cbb1c", "f8e8f48050e7a1f836adcfc9fac0d7839e4fd26d548a910591a24356e250fa9e")({
  data(){return {result:'No Form action yet',owner:'accession-form'};},
  onServerRender({component}) {
    const primary=component.$refs.externalSplit.$el.querySelector(
      '[data-citry-ui-part="split-button-primary"]'
    );
    Citry.vue.watchEffect(()=>primary.setAttribute('form',component.owner));
  },
});

})();
__citryRuntime.finishScript("3bebd0039a9136a6c32b6a0938f17bb7556234ce6da9b41d59f02427f3e54157");
} catch (error) {
__citryRuntime.finishScript("3bebd0039a9136a6c32b6a0938f17bb7556234ce6da9b41d59f02427f3e54157", error);
}