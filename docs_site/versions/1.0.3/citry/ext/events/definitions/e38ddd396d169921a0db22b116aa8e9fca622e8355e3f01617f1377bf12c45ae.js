try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SwitchForm_a45992", "28a67f261d7a205e42a97905b6c79fc5c50bb282109e77e6458be3520d5ba679")({
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
__citryRuntime.finishScript("a2007ca2243f6fb75f1179d30ac570cff08d9521e795c4758b0f3afc23e2ed52");
} catch (error) {
__citryRuntime.finishScript("a2007ca2243f6fb75f1179d30ac570cff08d9521e795c4758b0f3afc23e2ed52", error);
}