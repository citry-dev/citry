try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledMissionTarget_290233", "887b0bf2d4cb1b74603de9f3a63fc2a322dfe29fae17f008fc2c2e15293d758f")({
  data() {
    return {
      value: null,
      query: '',
      open: false,
      lastReason: 'none',
    };
  },
  methods: {
    handleValueChange(next, detail) {
      this.value = next;
      this.lastReason = `value: ${detail.reason}`;
    },
    handleInputValueChange(next, detail) {
      this.query = next;
      this.lastReason = `query: ${detail.reason}`;
    },
    handleOpenChange(next, detail) {
      this.open = next;
      this.lastReason = `popup: ${detail.reason}`;
    },
  },
});

})();
__citryRuntime.finishScript("0941e544101694dd0de52d4992d041c01c73873d57a004173c0a3a78cbf61b43");
} catch (error) {
__citryRuntime.finishScript("0941e544101694dd0de52d4992d041c01c73873d57a004173c0a3a78cbf61b43", error);
}