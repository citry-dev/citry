try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ContextMenuNativeContent_b1fc14", "336f05e28c5376ab03cc6dcd6ae193f56895a74d35779849abfff6e4c24cfba8")({
  data(){return {last:'No custom request yet'};},
  mounted() {
    this.$refs.closedShadowHost.attachShadow({mode:'closed'}).textContent =
      'Closed shadow fixture';
    this.$refs.openShadowHost.attachShadow({mode:'open'}).textContent =
      'Select open-shadow text';
  },
});

})();
__citryRuntime.finishScript("bda0ae940f98be2674dadb899d2f3a7c063fc2a3dd46d90bf9be069c0dffe1d5");
} catch (error) {
__citryRuntime.finishScript("bda0ae940f98be2674dadb899d2f3a7c063fc2a3dd46d90bf9be069c0dffe1d5", error);
}