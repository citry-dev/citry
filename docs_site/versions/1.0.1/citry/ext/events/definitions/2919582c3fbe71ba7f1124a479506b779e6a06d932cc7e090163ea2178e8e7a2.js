try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonForms_88befe", "f8e8f48050e7a1f836adcfc9fac0d7839e4fd26d548a910591a24356e250fa9e")({
  data(){return {result:'No Form action yet',owner:'accession-form'};},
  onServerRender({component}) {
    const primary=component.$refs.externalSplit.$el.querySelector(
      '[data-citry-ui-part="split-button-primary"]'
    );
    Citry.vue.watchEffect(()=>primary.setAttribute('form',component.owner));
  },
});

})();
__citryRuntime.finishScript("7174626b8f4cd114dee04be0d60c15606d3256fa347d341b16efa8ba9000f4ad");
} catch (error) {
__citryRuntime.finishScript("7174626b8f4cd114dee04be0d60c15606d3256fa347d341b16efa8ba9000f4ad", error);
}