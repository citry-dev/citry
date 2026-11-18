try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ContextMenuNativeContent_598fa1", "336f05e28c5376ab03cc6dcd6ae193f56895a74d35779849abfff6e4c24cfba8")({
  data(){return {last:'No custom request yet'};},
  mounted() {
    this.$refs.closedShadowHost.attachShadow({mode:'closed'}).textContent =
      'Closed shadow fixture';
    this.$refs.openShadowHost.attachShadow({mode:'open'}).textContent =
      'Select open-shadow text';
  },
});

})();
__citryRuntime.finishScript("54756b40ca74ae3828f753c1ddde0f645cb29315c70da0e798bce65ea6bbad12");
} catch (error) {
__citryRuntime.finishScript("54756b40ca74ae3828f753c1ddde0f645cb29315c70da0e798bce65ea6bbad12", error);
}