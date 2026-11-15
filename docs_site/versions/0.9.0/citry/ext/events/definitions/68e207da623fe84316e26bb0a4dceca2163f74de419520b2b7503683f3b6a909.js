try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledMissionTarget_9b2f89", "887b0bf2d4cb1b74603de9f3a63fc2a322dfe29fae17f008fc2c2e15293d758f")({
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
__citryRuntime.finishScript("6764e4881ac070fd2da2a3375c2ef7929f45975b14e758c40ce15123e56a176a");
} catch (error) {
__citryRuntime.finishScript("6764e4881ac070fd2da2a3375c2ef7929f45975b14e758c40ce15123e56a176a", error);
}