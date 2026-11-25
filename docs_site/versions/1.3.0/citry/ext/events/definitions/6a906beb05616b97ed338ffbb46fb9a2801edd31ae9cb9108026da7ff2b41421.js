try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ContextMenuNativeContent_aa27f7", "336f05e28c5376ab03cc6dcd6ae193f56895a74d35779849abfff6e4c24cfba8")({
  data(){return {last:'No custom request yet'};},
  mounted() {
    this.$refs.closedShadowHost.attachShadow({mode:'closed'}).textContent =
      'Closed shadow fixture';
    this.$refs.openShadowHost.attachShadow({mode:'open'}).textContent =
      'Select open-shadow text';
  },
});

})();
__citryRuntime.finishScript("9d4e3127ab10ba2492bfc610dd079eb8de2fae0c5c0988c6d766e0c1d395aee8");
} catch (error) {
__citryRuntime.finishScript("9d4e3127ab10ba2492bfc610dd079eb8de2fae0c5c0988c6d766e0c1d395aee8", error);
}