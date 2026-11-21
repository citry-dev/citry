try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DisclosureVariantsAndSizes_a17c8e", "c1df605a32c44c83837c947b330327c3a2101cd7009283ea35fd2fe2fae46e0a")({
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
__citryRuntime.finishScript("575ff53f40cde1df250e985be770b9db159ed7057af083e63afa69eff1284a78");
} catch (error) {
__citryRuntime.finishScript("575ff53f40cde1df250e985be770b9db159ed7057af083e63afa69eff1284a78", error);
}