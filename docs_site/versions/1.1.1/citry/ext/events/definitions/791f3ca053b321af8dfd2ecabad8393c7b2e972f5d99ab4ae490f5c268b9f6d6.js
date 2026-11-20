try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "PaletteLayers_2bd33f", "f0342e24864ce32f4ed0882950699d7c4ac3f46c314bcf71e4b6751e3e5958fc")({
  data() {
    return {
      removed: false,
      paletteOpen: false,
      popoverOpen: false,
    };
  },
  methods: {
    handlePaletteAction(value) {
      if (value === 'show-details') this.popoverOpen = true;
    },
    removePaletteOwner() {
      this.$refs.paletteOwner.remove();
      this.removed = true;
    },
  },
  mounted() {
    this.$nextTick(() => {
      const host = this.$refs.shadowHost;
      const fixture = this.$refs.shadowFixture;
      if (!host.shadowRoot && fixture) {
        host.attachShadow({ mode: 'open' }).append(fixture);
      }
    });
  },
});

})();
__citryRuntime.finishScript("18128549047eec251711fda4a6f662bc6565f7b34375ccca9e262055cff4a7ef");
} catch (error) {
__citryRuntime.finishScript("18128549047eec251711fda4a6f662bc6565f7b34375ccca9e262055cff4a7ef", error);
}