try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledMissionTarget_a10d8f", "887b0bf2d4cb1b74603de9f3a63fc2a322dfe29fae17f008fc2c2e15293d758f")({
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
__citryRuntime.finishScript("c7e39d3216692d295b39f64f85828b34858b4de77105605212ec54fa60526daf");
} catch (error) {
__citryRuntime.finishScript("c7e39d3216692d295b39f64f85828b34858b4de77105605212ec54fa60526daf", error);
}