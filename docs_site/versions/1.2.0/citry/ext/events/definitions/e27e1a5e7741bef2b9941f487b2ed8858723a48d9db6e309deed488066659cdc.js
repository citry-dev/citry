try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "PaletteLayers_8c6e42", "f0342e24864ce32f4ed0882950699d7c4ac3f46c314bcf71e4b6751e3e5958fc")({
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
__citryRuntime.finishScript("e56b0b0e1be81f51052bf4f33693da9e9d14b6d67602cb5e2ef5c79e1d024817");
} catch (error) {
__citryRuntime.finishScript("e56b0b0e1be81f51052bf4f33693da9e9d14b6d67602cb5e2ef5c79e1d024817", error);
}