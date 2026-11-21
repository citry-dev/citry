try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "ControlledMissionTarget_0c80e8", "887b0bf2d4cb1b74603de9f3a63fc2a322dfe29fae17f008fc2c2e15293d758f")({
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
__citryRuntime.finishScript("da938a9e1e3c472bc13bdbc33fbb3d7941b15d264e18e42eba0a14ca6f1a9a7f");
} catch (error) {
__citryRuntime.finishScript("da938a9e1e3c472bc13bdbc33fbb3d7941b15d264e18e42eba0a14ca6f1a9a7f", error);
}