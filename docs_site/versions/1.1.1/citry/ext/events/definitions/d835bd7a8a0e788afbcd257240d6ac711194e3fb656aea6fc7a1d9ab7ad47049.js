try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ReactiveImage_aee0b9", "8deb0e61358b89b9ed98b899735c9b0031e2ef3fa40d7e0882e82fc52e39a628")({
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
    // Count every status report and show only the filename, so the
    // output never exposes a full image path.
    recordStatus(detail) {
      this.callbacks++;
      this.status = detail.status;
      this.selected = this.redact(detail.current_src || detail.src);
      if (detail.status === 'loaded') this.nativeLoads++;
      if (detail.status === 'error') this.nativeErrors++;
    },
  },
});

})();
__citryRuntime.finishScript("b47b116c2c1fb4116a32bd093a897ef2a59fc8474410a22b44f7e5b4964d4532");
} catch (error) {
__citryRuntime.finishScript("b47b116c2c1fb4116a32bd093a897ef2a59fc8474410a22b44f7e5b4964d4532", error);
}