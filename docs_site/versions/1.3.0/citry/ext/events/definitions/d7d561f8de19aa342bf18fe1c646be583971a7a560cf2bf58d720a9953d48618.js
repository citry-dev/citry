try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureCombobox_9d86b2", "86b2c068f0ec9828902474913cca8edbe50fd7587cf98f7ae322327ddb7be3b8")({
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
__citryRuntime.finishScript("df2e30a25b12ff23b54efee8d86d956e00b496667d1062ffe1c60ca5043fada3");
} catch (error) {
__citryRuntime.finishScript("df2e30a25b12ff23b54efee8d86d956e00b496667d1062ffe1c60ca5043fada3", error);
}