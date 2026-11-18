try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "PaletteLayers_6b9385", "f0342e24864ce32f4ed0882950699d7c4ac3f46c314bcf71e4b6751e3e5958fc")({
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
__citryRuntime.finishScript("0a3ae58fa988b9b1d72ce62f87ebb385417b065ba17848f922b9d435debb2a82");
} catch (error) {
__citryRuntime.finishScript("0a3ae58fa988b9b1d72ce62f87ebb385417b065ba17848f922b9d435debb2a82", error);
}