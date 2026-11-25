try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SwitchForm_3923dc", "28a67f261d7a205e42a97905b6c79fc5c50bb282109e77e6458be3520d5ba679")({
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
__citryRuntime.finishScript("a1acd89b7b8ef60dc1bf682f182146011db2e7bfb8e85971e0c70384df36d444");
} catch (error) {
__citryRuntime.finishScript("a1acd89b7b8ef60dc1bf682f182146011db2e7bfb8e85971e0c70384df36d444", error);
}