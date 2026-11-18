try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledMissionTarget_8ad70c", "887b0bf2d4cb1b74603de9f3a63fc2a322dfe29fae17f008fc2c2e15293d758f")({
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
__citryRuntime.finishScript("cb30207f4fb5f6d448c268485c2521fdae88b7fe7a84e0694ed22ffbfccbf72e");
} catch (error) {
__citryRuntime.finishScript("cb30207f4fb5f6d448c268485c2521fdae88b7fe7a84e0694ed22ffbfccbf72e", error);
}