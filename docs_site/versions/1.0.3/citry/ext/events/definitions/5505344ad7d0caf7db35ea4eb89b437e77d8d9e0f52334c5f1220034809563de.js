try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureCombobox_afc26f", "86b2c068f0ec9828902474913cca8edbe50fd7587cf98f7ae322327ddb7be3b8")({
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
__citryRuntime.finishScript("f7dfee2d4d18b269ea26a8f763eb7d481a392bd8df93931f6bc81f0dee56f930");
} catch (error) {
__citryRuntime.finishScript("f7dfee2d4d18b269ea26a8f763eb7d481a392bd8df93931f6bc81f0dee56f930", error);
}