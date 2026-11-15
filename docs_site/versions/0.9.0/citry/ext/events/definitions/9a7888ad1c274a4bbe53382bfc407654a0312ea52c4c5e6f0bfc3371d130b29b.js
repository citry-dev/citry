try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "PaletteLayers_817d1f", "f0342e24864ce32f4ed0882950699d7c4ac3f46c314bcf71e4b6751e3e5958fc")({
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
__citryRuntime.finishScript("37b2710a6ae762594d4803cb4b2d8051c14d6f86d39c7bcb6261a58f9682fe25");
} catch (error) {
__citryRuntime.finishScript("37b2710a6ae762594d4803cb4b2d8051c14d6f86d39c7bcb6261a58f9682fe25", error);
}