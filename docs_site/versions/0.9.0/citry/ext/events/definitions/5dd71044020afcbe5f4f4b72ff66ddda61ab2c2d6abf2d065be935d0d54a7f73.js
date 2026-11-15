try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ImageLifecycle_9176a6", "52f3c06638ff4b6797f1f3b0c53278bd2d837aec780ce1dbe8d24199d51d59d5")({
  data() {
    return {
      status:'waiting',selected:'none'
    };
  },
  methods: {
    // Show the reported status and the bare filename, without the
    // path or the `?plate=` query.
    recordStatus(detail) {
      this.status = detail.status;
      this.selected = (detail.current_src || detail.src).split('/').pop().split('?')[0];
    },
  },
});

})();
__citryRuntime.finishScript("ce048462ae010559cb2a9dff9a4d50382359bb4a640a2a825e94d2a334179f1c");
} catch (error) {
__citryRuntime.finishScript("ce048462ae010559cb2a9dff9a4d50382359bb4a640a2a825e94d2a334179f1c", error);
}