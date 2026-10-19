(function() {

__citryRuntime.registerTypeOptions.bind(null, "ScrollAreaNativeCallback_74c6d2", "91d0da677367261f1968737fee62c3d7c941bd83843ce89eccb5af41339bb4b2")({
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