try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonForms_b63c5f", "f8e8f48050e7a1f836adcfc9fac0d7839e4fd26d548a910591a24356e250fa9e")({
  data(){return {result:'No Form action yet',owner:'accession-form'};},
  onServerRender({component}) {
    const primary=component.$refs.externalSplit.$el.querySelector(
      '[data-citry-ui-part="split-button-primary"]'
    );
    Citry.vue.watchEffect(()=>primary.setAttribute('form',component.owner));
  },
});

})();
__citryRuntime.finishScript("d46bff7ce8212b1b17b2ae035d9817a023cefb1a626e5334ca9b8a5e4ebc2aa8");
} catch (error) {
__citryRuntime.finishScript("d46bff7ce8212b1b17b2ae035d9817a023cefb1a626e5334ca9b8a5e4ebc2aa8", error);
}