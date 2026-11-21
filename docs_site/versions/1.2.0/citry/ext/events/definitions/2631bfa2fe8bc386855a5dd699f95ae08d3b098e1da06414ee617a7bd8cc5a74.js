try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonForms_1de9d4", "f8e8f48050e7a1f836adcfc9fac0d7839e4fd26d548a910591a24356e250fa9e")({
  data(){return {result:'No Form action yet',owner:'accession-form'};},
  onServerRender({component}) {
    const primary=component.$refs.externalSplit.$el.querySelector(
      '[data-citry-ui-part="split-button-primary"]'
    );
    Citry.vue.watchEffect(()=>primary.setAttribute('form',component.owner));
  },
});

})();
__citryRuntime.finishScript("6ca302fe15e3cdf6639f4d868e4573acc5adaf60082c3df8d12121472641fdb4");
} catch (error) {
__citryRuntime.finishScript("6ca302fe15e3cdf6639f4d868e4573acc5adaf60082c3df8d12121472641fdb4", error);
}