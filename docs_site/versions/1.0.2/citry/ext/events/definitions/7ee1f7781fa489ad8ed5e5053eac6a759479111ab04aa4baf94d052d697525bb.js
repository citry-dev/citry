try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureCombobox_f3233e", "86b2c068f0ec9828902474913cca8edbe50fd7587cf98f7ae322327ddb7be3b8")({
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
__citryRuntime.finishScript("707644dde9d5e612ea3138f1585a4b5cd57e6160e4e856db5f5ddbef7727fbbf");
} catch (error) {
__citryRuntime.finishScript("707644dde9d5e612ea3138f1585a4b5cd57e6160e4e856db5f5ddbef7727fbbf", error);
}