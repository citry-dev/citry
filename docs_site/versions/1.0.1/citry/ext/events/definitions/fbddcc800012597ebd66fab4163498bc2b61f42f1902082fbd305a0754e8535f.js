try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SwitchForm_8bccd0", "28a67f261d7a205e42a97905b6c79fc5c50bb282109e77e6458be3520d5ba679")({
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
__citryRuntime.finishScript("063d20e7fc66970af62c5093fe1af04f36d45026497e57e157eae0d635400fc6");
} catch (error) {
__citryRuntime.finishScript("063d20e7fc66970af62c5093fe1af04f36d45026497e57e157eae0d635400fc6", error);
}