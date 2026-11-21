try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ScrollAreaNativeCallback_924c5d", "91d0da677367261f1968737fee62c3d7c941bd83843ce89eccb5af41339bb4b2")({
  data() {
    return {
      rows: 6,
      sentinelTop: 150,
      imageVisible: false,
      expanded: false,
      nativeCount: 0,
      settled: 0,
      callbackCount: 0,
      lastInline: 0,
      lastBlock: 0,
    };
  },
  methods: {
    handleScrollChange(detail) {
      this.callbackCount += 1;
      this.lastInline = Math.round(detail.inlineOffset);
      this.lastBlock = Math.round(detail.blockOffset);
    },
    // Simulate an image that finishes loading after the area settled.
    showImageLater() {
      setTimeout(() => { this.imageVisible = true; }, 350);
    },
  },
  mounted() {
    this.$nextTick(() => {
      const host = this.$refs.shadowHost;
      const fixture = this.$refs.shadowFixture;
      if (!host.shadowRoot && fixture) host.attachShadow({ mode: 'open' }).append(fixture);
    });
  },
});

})();
__citryRuntime.finishScript("24925a302a19f57136796563fdfabb0361236f1ccd3f27604753d8cf1ed0bed4");
} catch (error) {
__citryRuntime.finishScript("24925a302a19f57136796563fdfabb0361236f1ccd3f27604753d8cf1ed0bed4", error);
}