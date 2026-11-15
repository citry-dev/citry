try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ContextMenuNativeContent_268125", "336f05e28c5376ab03cc6dcd6ae193f56895a74d35779849abfff6e4c24cfba8")({
  data(){return {last:'No custom request yet'};},
  mounted() {
    this.$refs.closedShadowHost.attachShadow({mode:'closed'}).textContent =
      'Closed shadow fixture';
    this.$refs.openShadowHost.attachShadow({mode:'open'}).textContent =
      'Select open-shadow text';
  },
});

})();
__citryRuntime.finishScript("6be8f4dae0abbeff37a0a5c920523bdcf6f157e602d779d385bf7d48d7fa40ad");
} catch (error) {
__citryRuntime.finishScript("6be8f4dae0abbeff37a0a5c920523bdcf6f157e602d779d385bf7d48d7fa40ad", error);
}