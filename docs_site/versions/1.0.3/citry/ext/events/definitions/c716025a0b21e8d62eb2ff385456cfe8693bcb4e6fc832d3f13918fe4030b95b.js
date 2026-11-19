try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TagsInputMorphAndCleanup_74a40c", "c4d313f15d88c74d800a702784040dc5bb0d1892b3b363e3fda7c0eadff8d63c")({
  data() {
    return {
      controlled:false,
      tags:['owner-one'],
      mounted:true,
    };
  },
  methods: {
    // Store the requested tags only while the page owns them.
    applyControlledTags(next) {
      if (this.controlled) this.tags = next;
    },
  },
});

})();
__citryRuntime.finishScript("c75d04f1fec83172a85bf2332bd16f4bdff4e12039ebd8dafd4240652b2c830e");
} catch (error) {
__citryRuntime.finishScript("c75d04f1fec83172a85bf2332bd16f4bdff4e12039ebd8dafd4240652b2c830e", error);
}