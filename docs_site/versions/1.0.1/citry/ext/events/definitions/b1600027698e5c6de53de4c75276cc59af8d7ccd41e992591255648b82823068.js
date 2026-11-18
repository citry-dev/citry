try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "PaletteLayers_4efa02", "f0342e24864ce32f4ed0882950699d7c4ac3f46c314bcf71e4b6751e3e5958fc")({
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
__citryRuntime.finishScript("778944e42ae4a6b8abaed17214db7df6628b6ff6f183da972e994bc056f79b09");
} catch (error) {
__citryRuntime.finishScript("778944e42ae4a6b8abaed17214db7df6628b6ff6f183da972e994bc056f79b09", error);
}