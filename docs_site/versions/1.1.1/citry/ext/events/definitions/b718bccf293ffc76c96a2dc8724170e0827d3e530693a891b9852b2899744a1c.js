try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledCommandPalette_a8cd07", "cc78eb8673eab7a24ec4f0b788730116eab0a385a441c59679032ca3d302177b")({
  data() {
    return {
      open:true,
      query:'work',
      controlOpen:true,
      controlQuery:true,
      acceptClose:false,
      acceptQuery:false,
      requests:[],
    };
  },
  methods: {
    // A controlled palette opens on request but closes only once the
    // owner ticks Accept close.
    applyOpenRequest(value, detail) {
      this.requests.push(`open:${value}:${detail.reason}`);
      if (!this.controlOpen || value || this.acceptClose) this.open = value;
    },
    // The reset that comes with a close is always taken, so the next
    // open starts with an empty query.
    applyQueryRequest(value, detail) {
      this.requests.push(`query:${value}:${detail.reason}`);
      if (!this.controlQuery || this.acceptQuery || detail.reason === 'close') {
        this.query = value;
      }
    },
  },
});

})();
__citryRuntime.finishScript("0a83be6e7e37692f1d7fb195f81868c91bc4dd42e432fb3bcf6e889b7da0b95d");
} catch (error) {
__citryRuntime.finishScript("0a83be6e7e37692f1d7fb195f81868c91bc4dd42e432fb3bcf6e889b7da0b95d", error);
}