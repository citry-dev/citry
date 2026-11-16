try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DisclosureVariantsAndSizes_9bea3d", "c1df605a32c44c83837c947b330327c3a2101cd7009283ea35fd2fe2fae46e0a")({
  data() {
    return {
      variant:'outline',size:'md',indicator:true,indicator_position:'end'
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
__citryRuntime.finishScript("a77df221f1171126eb81e628727e779ee3abc0e2ca43b9da39d759e07da175df");
} catch (error) {
__citryRuntime.finishScript("a77df221f1171126eb81e628727e779ee3abc0e2ca43b9da39d759e07da175df", error);
}