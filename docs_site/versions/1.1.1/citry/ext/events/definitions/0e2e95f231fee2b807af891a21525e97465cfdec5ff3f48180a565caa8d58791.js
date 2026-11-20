try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ConfigureCombobox_8b43b2", "86b2c068f0ec9828902474913cca8edbe50fd7587cf98f7ae322327ddb7be3b8")({
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
__citryRuntime.finishScript("a68a2dcf2ef8ac40692a133e1129ccc3420c6b38e64816bec71188e981a4f2bb");
} catch (error) {
__citryRuntime.finishScript("a68a2dcf2ef8ac40692a133e1129ccc3420c6b38e64816bec71188e981a4f2bb", error);
}