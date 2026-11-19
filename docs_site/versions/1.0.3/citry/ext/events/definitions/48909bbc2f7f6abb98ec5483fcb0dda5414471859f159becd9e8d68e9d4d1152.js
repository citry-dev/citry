try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DisclosureVariantsAndSizes_b50a87", "c1df605a32c44c83837c947b330327c3a2101cd7009283ea35fd2fe2fae46e0a")({
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
__citryRuntime.finishScript("cadd9d19ff52b0b1e4cf09c2ff7f9da280bee5be227ba2a2daa498679b09c7a8");
} catch (error) {
__citryRuntime.finishScript("cadd9d19ff52b0b1e4cf09c2ff7f9da280bee5be227ba2a2daa498679b09c7a8", error);
}