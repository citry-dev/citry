try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ContextMenuNativeContent_89effb", "336f05e28c5376ab03cc6dcd6ae193f56895a74d35779849abfff6e4c24cfba8")({
  data(){return {last:'No custom request yet'};},
  mounted() {
    this.$refs.closedShadowHost.attachShadow({mode:'closed'}).textContent =
      'Closed shadow fixture';
    this.$refs.openShadowHost.attachShadow({mode:'open'}).textContent =
      'Select open-shadow text';
  },
});

})();
__citryRuntime.finishScript("a746bd42e4e6098007e56d8c8e2a58ec9d583e311bc2568cd2e72f300131c234");
} catch (error) {
__citryRuntime.finishScript("a746bd42e4e6098007e56d8c8e2a58ec9d583e311bc2568cd2e72f300131c234", error);
}