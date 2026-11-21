try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureCombobox_99f885", "86b2c068f0ec9828902474913cca8edbe50fd7587cf98f7ae322327ddb7be3b8")({
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
__citryRuntime.finishScript("9a9bc01bf6f09a50968a255ee5c0f213bb5d60e9cd1ef499195c13f20985b517");
} catch (error) {
__citryRuntime.finishScript("9a9bc01bf6f09a50968a255ee5c0f213bb5d60e9cd1ef499195c13f20985b517", error);
}