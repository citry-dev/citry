try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ApplicationShortcut_b79a4d", "b39935dabdcb91d3f4effc007af66e22d242d9f3c8d1f053c5130655eb66fd90")({
  data() {
    return {
      workspaceOpen:false,helpOpen:false,enabled:true,target:'workspace',opens:0
    };
  },
  methods: {
    handleShortcut(event) {
      if (
        !this.enabled
        || (!event.metaKey && !event.ctrlKey)
        || event.key.toLowerCase() !== 'k'
        || event.isComposing
        || ['INPUT', 'TEXTAREA', 'SELECT'].includes(event.target.tagName)
        || event.target.isContentEditable
      ) return;
      event.preventDefault();
      this.opens++;
      if (this.target === 'workspace') this.workspaceOpen = true;
      else this.helpOpen = true;
    },
  },
  mounted() {
    window.addEventListener("keydown", this.handleShortcut);
  },
  beforeUnmount() {
    window.removeEventListener("keydown", this.handleShortcut);
  },
});

})();
__citryRuntime.finishScript("abed2ac0b3af064b839d335bfc549536fa874aa9b29964ba428bb8b09daacc15");
} catch (error) {
__citryRuntime.finishScript("abed2ac0b3af064b839d335bfc549536fa874aa9b29964ba428bb8b09daacc15", error);
}