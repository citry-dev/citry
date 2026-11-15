try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureCombobox_5fb856", "86b2c068f0ec9828902474913cca8edbe50fd7587cf98f7ae322327ddb7be3b8")({
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
__citryRuntime.finishScript("ed1c3c335a98edaf8a50df705974754572f328cd44f1c38c365c808ce83cede4");
} catch (error) {
__citryRuntime.finishScript("ed1c3c335a98edaf8a50df705974754572f328cd44f1c38c365c808ce83cede4", error);
}