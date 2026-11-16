try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ImageLifecycle_8249d8", "52f3c06638ff4b6797f1f3b0c53278bd2d837aec780ce1dbe8d24199d51d59d5")({
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
__citryRuntime.finishScript("f7108139b5f186f592364aa36240c482f17bde33e5cca96e87833d852f3962cb");
} catch (error) {
__citryRuntime.finishScript("f7108139b5f186f592364aa36240c482f17bde33e5cca96e87833d852f3962cb", error);
}