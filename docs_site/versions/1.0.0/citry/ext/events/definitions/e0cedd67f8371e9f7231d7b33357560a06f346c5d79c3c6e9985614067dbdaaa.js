try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ContextMenuNativeContent_9d5412", "336f05e28c5376ab03cc6dcd6ae193f56895a74d35779849abfff6e4c24cfba8")({
  data(){return {last:'No custom request yet'};},
  mounted() {
    this.$refs.closedShadowHost.attachShadow({mode:'closed'}).textContent =
      'Closed shadow fixture';
    this.$refs.openShadowHost.attachShadow({mode:'open'}).textContent =
      'Select open-shadow text';
  },
});

})();
__citryRuntime.finishScript("95b5ea84bbab2085294f1301848261907cfd15eca465f7b84240cb8e263adfbd");
} catch (error) {
__citryRuntime.finishScript("95b5ea84bbab2085294f1301848261907cfd15eca465f7b84240cb8e263adfbd", error);
}