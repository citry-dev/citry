try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TagsInputMorphAndCleanup_9f52f3", "c4d313f15d88c74d800a702784040dc5bb0d1892b3b363e3fda7c0eadff8d63c")({
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
__citryRuntime.finishScript("f626d6e5a4c20b00a7d807936fa39c83ac19b40ef4ea8a371c380aeeb509c61b");
} catch (error) {
__citryRuntime.finishScript("f626d6e5a4c20b00a7d807936fa39c83ac19b40ef4ea8a371c380aeeb509c61b", error);
}