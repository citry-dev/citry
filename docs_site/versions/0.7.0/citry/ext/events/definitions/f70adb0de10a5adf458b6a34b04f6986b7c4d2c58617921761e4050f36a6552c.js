(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledCommandPalette_7f64f9", "cc78eb8673eab7a24ec4f0b788730116eab0a385a441c59679032ca3d302177b")({
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