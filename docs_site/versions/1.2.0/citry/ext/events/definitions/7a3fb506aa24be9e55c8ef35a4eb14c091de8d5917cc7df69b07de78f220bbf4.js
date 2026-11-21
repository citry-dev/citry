try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ImageLifecycle_39d33c", "52f3c06638ff4b6797f1f3b0c53278bd2d837aec780ce1dbe8d24199d51d59d5")({
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
__citryRuntime.finishScript("928946f8ad7656e061390d40675943b58fe280132118fc50ad6900cec3d37b4f");
} catch (error) {
__citryRuntime.finishScript("928946f8ad7656e061390d40675943b58fe280132118fc50ad6900cec3d37b4f", error);
}