(function() {

__citryRuntime.registerTypeOptions.bind(null, "ReactiveImage_e60e1d", "22fed9eb8c350f14d6160904b0cc3a86ad3669b708d1166d70bf1b78ccf0c773")({
  data() {
    return {
      source:'/static/img/ui/image/horsehead-nebula-1280.jpg?frame=slow-red',
      status:'waiting',
      selected:'none',
      callbacks:0,
      nativeLoads:0,
      nativeErrors:0,
      redact:(value)=>value ? value.split('/').pop().split('?')[0] : 'none',
    };
  },
  methods: {
    // Replace the source twice in one task; only the second
    // image may settle the status.
    rapidAThenB() {
      this.source = '/static/img/ui/image/horsehead-nebula-1280.jpg?frame=rapid-a';
      queueMicrotask(() => {
        this.source = '/static/img/ui/image/orion-nebula-640.jpg?frame=rapid-b';
      });
    },
  },
});

})();