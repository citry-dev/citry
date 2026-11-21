try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ContextMenuNativeContent_722a91", "336f05e28c5376ab03cc6dcd6ae193f56895a74d35779849abfff6e4c24cfba8")({
  data(){return {last:'No custom request yet'};},
  mounted() {
    this.$refs.closedShadowHost.attachShadow({mode:'closed'}).textContent =
      'Closed shadow fixture';
    this.$refs.openShadowHost.attachShadow({mode:'open'}).textContent =
      'Select open-shadow text';
  },
});

})();
__citryRuntime.finishScript("e74c2b0e61e18e39e15903494a6ce9baa190dbc27751365991603ce1128a9209");
} catch (error) {
__citryRuntime.finishScript("e74c2b0e61e18e39e15903494a6ce9baa190dbc27751365991603ce1128a9209", error);
}