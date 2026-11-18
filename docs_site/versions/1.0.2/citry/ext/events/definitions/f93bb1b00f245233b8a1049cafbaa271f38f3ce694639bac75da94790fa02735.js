try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SwitchForm_1ed5da", "28a67f261d7a205e42a97905b6c79fc5c50bb282109e77e6458be3520d5ba679")({
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
__citryRuntime.finishScript("0806a67e07f2d1ce6425e2a559fd3187c4d38af4591ece413e212352b739483d");
} catch (error) {
__citryRuntime.finishScript("0806a67e07f2d1ce6425e2a559fd3187c4d38af4591ece413e212352b739483d", error);
}