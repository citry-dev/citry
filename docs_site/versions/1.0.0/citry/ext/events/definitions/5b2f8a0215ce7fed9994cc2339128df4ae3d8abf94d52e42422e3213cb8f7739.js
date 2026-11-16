try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TagsInputMorphAndCleanup_4ae8d2", "c4d313f15d88c74d800a702784040dc5bb0d1892b3b363e3fda7c0eadff8d63c")({
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
__citryRuntime.finishScript("434e68e79ea123f4c8c27c1e3d396da7cff10b123fe626b4494b211d561d5f77");
} catch (error) {
__citryRuntime.finishScript("434e68e79ea123f4c8c27c1e3d396da7cff10b123fe626b4494b211d561d5f77", error);
}