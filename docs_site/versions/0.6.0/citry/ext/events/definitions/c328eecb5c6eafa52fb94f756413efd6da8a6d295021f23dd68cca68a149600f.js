(function() {

__citryRuntime.registerTypeOptions.bind(null, "SplitButtonLayersAndDialog_c2f695", "c2c33b1e6dde0f2e4575f1b11c5886cfb34fd98f8a831b020a50e3a4da4c46ad")({
  data(){return {dialogOpen:false,last:'No layer action yet'};},
  mounted() {
    if (!this.$refs.shadowHost.shadowRoot) {
      this.$refs.shadowHost.attachShadow({mode:'open'}).append(this.$refs.shadowFixture);
    }
  },
});

})();