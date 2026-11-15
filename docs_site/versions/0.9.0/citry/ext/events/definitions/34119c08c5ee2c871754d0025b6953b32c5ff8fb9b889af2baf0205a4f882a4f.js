try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SwitchForm_4b0ab1", "28a67f261d7a205e42a97905b6c79fc5c50bb282109e77e6458be3520d5ba679")({
  data() {
    return {
      result: ''
    };
  },
  methods: {
    // An unchecked switch leaves its name out of the form data.
    save(form) {
      const enabled = new window.FormData(form).has('quiet_hours');
      this.result = enabled ? 'Saved' : 'Enable quiet hours';
    },
  },
});

})();
__citryRuntime.finishScript("caa30497cf7b32c7bd647b1ddd2b60561c077bc3449c4a5bc9ac890e1d3b27fc");
} catch (error) {
__citryRuntime.finishScript("caa30497cf7b32c7bd647b1ddd2b60561c077bc3449c4a5bc9ac890e1d3b27fc", error);
}