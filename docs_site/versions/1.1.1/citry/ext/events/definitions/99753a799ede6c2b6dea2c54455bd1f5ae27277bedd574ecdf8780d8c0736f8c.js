try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ContextMenuNativeContent_806872", "336f05e28c5376ab03cc6dcd6ae193f56895a74d35779849abfff6e4c24cfba8")({
  data(){return {last:'No custom request yet'};},
  mounted() {
    this.$refs.closedShadowHost.attachShadow({mode:'closed'}).textContent =
      'Closed shadow fixture';
    this.$refs.openShadowHost.attachShadow({mode:'open'}).textContent =
      'Select open-shadow text';
  },
});

})();
__citryRuntime.finishScript("e94d68583423d4d6ee4baf3073b221cbe31445176a6c9a1be708628560c5c1f5");
} catch (error) {
__citryRuntime.finishScript("e94d68583423d4d6ee4baf3073b221cbe31445176a6c9a1be708628560c5c1f5", error);
}