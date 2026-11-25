try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledMissionTarget_b4ff84", "887b0bf2d4cb1b74603de9f3a63fc2a322dfe29fae17f008fc2c2e15293d758f")({
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
__citryRuntime.finishScript("8243c4702adeefd26d2cf50c5bdaee6ea1243093bf6d4c1b71900f78de355d84");
} catch (error) {
__citryRuntime.finishScript("8243c4702adeefd26d2cf50c5bdaee6ea1243093bf6d4c1b71900f78de355d84", error);
}