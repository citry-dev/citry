try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ReactiveImage_e8a785", "8deb0e61358b89b9ed98b899735c9b0031e2ef3fa40d7e0882e82fc52e39a628")({
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
__citryRuntime.finishScript("2d4c16bf9a069f6c4700f851bc50df22e45b09d03c3dadc5489294f1e23d4b58");
} catch (error) {
__citryRuntime.finishScript("2d4c16bf9a069f6c4700f851bc50df22e45b09d03c3dadc5489294f1e23d4b58", error);
}