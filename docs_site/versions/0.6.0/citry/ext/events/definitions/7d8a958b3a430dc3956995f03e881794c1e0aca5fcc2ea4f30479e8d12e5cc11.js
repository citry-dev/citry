(function() {

__citryRuntime.registerTypeOptions.bind(null, "TabsConfiguration_caed96", "469a7945cab34168ff498b636ea5db09ce168afb205bc59645bafa5126d171f6")({
  data() {
    return {
      selected: 'mercury',
      accent: 'violet',
      accents: {
        violet: 'light-dark(#6d28d9, #c4b5fd)',
        coral: 'light-dark(#c2410c, #fdba74)',
        teal: 'light-dark(#0f766e, #5eead4)',
        pink: 'light-dark(#be185d, #f9a8d4)',
      },
      variant: 'underline',
      density: 'default',
      orientation: 'horizontal',
      align: 'start',
      grow: false,
      loop: true,
      disabled: false,
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