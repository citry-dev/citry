try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureCombobox_ceeba7", "86b2c068f0ec9828902474913cca8edbe50fd7587cf98f7ae322327ddb7be3b8")({
  data() {
    return {
      variant: 'outline',
      size: 'md',
      filter: 'contains',
      clearable: true,
      open_on_focus: false,
      auto_highlight: false,
    };
  },
  methods: {
    applyPreviewControls(event) {
      Object.assign(this, event.detail);
    },
  },
  mounted() {
    window.addEventListener("citry-ui-preview-controls", this.applyPreviewControls);
  },
  beforeUnmount() {
    window.removeEventListener("citry-ui-preview-controls", this.applyPreviewControls);
  },
});

})();
__citryRuntime.finishScript("4ac99c0af8de923db8408fc82756e34d4ae6ffb9391b6096f5988fa76bdd321f");
} catch (error) {
__citryRuntime.finishScript("4ac99c0af8de923db8408fc82756e34d4ae6ffb9391b6096f5988fa76bdd321f", error);
}