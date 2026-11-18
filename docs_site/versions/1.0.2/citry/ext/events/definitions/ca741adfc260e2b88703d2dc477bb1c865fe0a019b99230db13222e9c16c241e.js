try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonForms_28eacc", "f8e8f48050e7a1f836adcfc9fac0d7839e4fd26d548a910591a24356e250fa9e")({
  data(){return {result:'No Form action yet',owner:'accession-form'};},
  onServerRender({component}) {
    const primary=component.$refs.externalSplit.$el.querySelector(
      '[data-citry-ui-part="split-button-primary"]'
    );
    Citry.vue.watchEffect(()=>primary.setAttribute('form',component.owner));
  },
});

})();
__citryRuntime.finishScript("38d46e139aa99a35474ecdaeaaccfa76011ca17469870af349e552102ba35566");
} catch (error) {
__citryRuntime.finishScript("38d46e139aa99a35474ecdaeaaccfa76011ca17469870af349e552102ba35566", error);
}