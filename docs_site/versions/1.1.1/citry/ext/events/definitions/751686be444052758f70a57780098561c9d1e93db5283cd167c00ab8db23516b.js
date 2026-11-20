try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "SwitchForm_cf16a8", "28a67f261d7a205e42a97905b6c79fc5c50bb282109e77e6458be3520d5ba679")({
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
__citryRuntime.finishScript("36043bb91af9e017551ca37ab0dd3a0ea517b1a2dad5ecddf5cbf31ee289705f");
} catch (error) {
__citryRuntime.finishScript("36043bb91af9e017551ca37ab0dd3a0ea517b1a2dad5ecddf5cbf31ee289705f", error);
}