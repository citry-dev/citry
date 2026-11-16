try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ContextMenuLayersAndRoots_4f664d", "01765be893324f4a36f65979fc6bfcfe5b15565fa31b33a72f652ab5a69ecf88")({data(){return {
    last:'No layer request yet',
    counterTick:0,
    nestedRemoved:false,
  };},
  methods: {
    // The layer runtime is not reactive, so the tick argument makes
    // the output re-read it when the refresh button is pressed.
    layerSummary(tick) {
      const runtime=globalThis[Symbol.for('citry-ui:anchored-layer-runtime')];
      const layers=tick >= 0 ? (runtime?.layers.length ?? 0) : 0;
      const registrations=runtime?.stats?.activeCoordinators ?? 0;
      return `${this.last}; layers ${layers}; registrations ${registrations}`;
    },
  },
  mounted() {
    const shadow=this.$refs.shadowHost.attachShadow({mode:'open'});
    document.querySelectorAll('style').forEach(
      (style)=>shadow.append(style.cloneNode(true))
    );
    shadow.append(this.$refs.shadowFixture);
  },
});

})();
__citryRuntime.finishScript("8c49fce146b14d75b61b7e2a0a1b76991900046a6842211befa85af7591dde77");
} catch (error) {
__citryRuntime.finishScript("8c49fce146b14d75b61b7e2a0a1b76991900046a6842211befa85af7591dde77", error);
}