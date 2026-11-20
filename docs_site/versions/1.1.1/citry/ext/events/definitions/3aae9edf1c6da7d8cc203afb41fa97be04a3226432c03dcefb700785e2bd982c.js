try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TagsInputMorphAndCleanup_014be4", "c4d313f15d88c74d800a702784040dc5bb0d1892b3b363e3fda7c0eadff8d63c")({
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
__citryRuntime.finishScript("398d3127bbe6a260b87ad031e261b77d81150ece25a71dbe1e7a56701707b771");
} catch (error) {
__citryRuntime.finishScript("398d3127bbe6a260b87ad031e261b77d81150ece25a71dbe1e7a56701707b771", error);
}