try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ApplicationShortcut_c5cfef", "b39935dabdcb91d3f4effc007af66e22d242d9f3c8d1f053c5130655eb66fd90")({
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
__citryRuntime.finishScript("b6769f7443af529e6dc23082b4aeece960786c79621c0502025d8b257f8441fe");
} catch (error) {
__citryRuntime.finishScript("b6769f7443af529e6dc23082b4aeece960786c79621c0502025d8b257f8441fe", error);
}