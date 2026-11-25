try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DisclosureVariantsAndSizes_a73faf", "c1df605a32c44c83837c947b330327c3a2101cd7009283ea35fd2fe2fae46e0a")({
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
__citryRuntime.finishScript("d4065d7dca72c679e56edb16d97203fed25f57c0b04fc5abed0dacaa408f8a28");
} catch (error) {
__citryRuntime.finishScript("d4065d7dca72c679e56edb16d97203fed25f57c0b04fc5abed0dacaa408f8a28", error);
}