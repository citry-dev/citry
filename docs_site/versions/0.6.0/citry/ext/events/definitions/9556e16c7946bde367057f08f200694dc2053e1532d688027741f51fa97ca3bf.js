(function() {

__citryRuntime.registerTypeOptions.bind(null, "BasicContextMenu_c8a1dd", "bd6dd87562a1bb7fa6ebe7a8ae1ea1ef8024f9e9c34aa9a478cec716bd43ba74")({
  data() { return {lastActionLabel: "Last action: No action yet"}; },
  methods: {
    onAction(value) { this.lastActionLabel = `Last action: ${value}`; },
  },
});

})();