try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ImageLifecycle_3ddd62", "52f3c06638ff4b6797f1f3b0c53278bd2d837aec780ce1dbe8d24199d51d59d5")({
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
__citryRuntime.finishScript("3b9e449cfbc3ab9855ddb794c0dcb906d33dba6e1f2749a4ef8929402325e45b");
} catch (error) {
__citryRuntime.finishScript("3b9e449cfbc3ab9855ddb794c0dcb906d33dba6e1f2749a4ef8929402325e45b", error);
}