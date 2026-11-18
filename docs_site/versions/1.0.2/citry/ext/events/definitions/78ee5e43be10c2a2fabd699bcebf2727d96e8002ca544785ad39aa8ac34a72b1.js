try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ImageLifecycle_4019be", "52f3c06638ff4b6797f1f3b0c53278bd2d837aec780ce1dbe8d24199d51d59d5")({
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
__citryRuntime.finishScript("7e16a836eb824caa839493a71d4be0ebe7db49a48df63674f32dd3a59cfd8f32");
} catch (error) {
__citryRuntime.finishScript("7e16a836eb824caa839493a71d4be0ebe7db49a48df63674f32dd3a59cfd8f32", error);
}