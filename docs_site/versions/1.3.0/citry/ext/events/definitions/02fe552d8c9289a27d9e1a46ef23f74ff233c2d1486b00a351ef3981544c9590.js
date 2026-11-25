try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "PaletteLayers_bea2e3", "f0342e24864ce32f4ed0882950699d7c4ac3f46c314bcf71e4b6751e3e5958fc")({
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
__citryRuntime.finishScript("f7654dbdfa59561cbb8f10abd58aa3aa8b2ecf4e54a0aca4e1664c901b3ddca5");
} catch (error) {
__citryRuntime.finishScript("f7654dbdfa59561cbb8f10abd58aa3aa8b2ecf4e54a0aca4e1664c901b3ddca5", error);
}