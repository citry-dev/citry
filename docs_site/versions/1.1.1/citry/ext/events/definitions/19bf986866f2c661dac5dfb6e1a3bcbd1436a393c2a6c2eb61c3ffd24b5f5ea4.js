try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonForms_8f7313", "f8e8f48050e7a1f836adcfc9fac0d7839e4fd26d548a910591a24356e250fa9e")({
  data(){return {result:'No Form action yet',owner:'accession-form'};},
  onServerRender({component}) {
    const primary=component.$refs.externalSplit.$el.querySelector(
      '[data-citry-ui-part="split-button-primary"]'
    );
    Citry.vue.watchEffect(()=>primary.setAttribute('form',component.owner));
  },
});

})();
__citryRuntime.finishScript("a99b1e1a21b8c5ffa26bf6970e4b929e203c9838ceb1fa6c5db8e53243cf8080");
} catch (error) {
__citryRuntime.finishScript("a99b1e1a21b8c5ffa26bf6970e4b929e203c9838ceb1fa6c5db8e53243cf8080", error);
}