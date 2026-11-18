try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DisclosureVariantsAndSizes_af9fa2", "c1df605a32c44c83837c947b330327c3a2101cd7009283ea35fd2fe2fae46e0a")({
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
__citryRuntime.finishScript("47a509c06a65d0c382761fa1248175b21626732e73cd3d81862ae510e5f69420");
} catch (error) {
__citryRuntime.finishScript("47a509c06a65d0c382761fa1248175b21626732e73cd3d81862ae510e5f69420", error);
}