try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SwitchForm_6f367b", "28a67f261d7a205e42a97905b6c79fc5c50bb282109e77e6458be3520d5ba679")({
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
__citryRuntime.finishScript("f74dd8fb3ce959ad5644f3c1c306374f784ffd7e085b6d7339caeb24058dadb8");
} catch (error) {
__citryRuntime.finishScript("f74dd8fb3ce959ad5644f3c1c306374f784ffd7e085b6d7339caeb24058dadb8", error);
}