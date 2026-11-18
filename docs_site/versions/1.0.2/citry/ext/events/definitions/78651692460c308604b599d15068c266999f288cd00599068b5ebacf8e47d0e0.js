try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TagsInputMorphAndCleanup_1e4db6", "c4d313f15d88c74d800a702784040dc5bb0d1892b3b363e3fda7c0eadff8d63c")({
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
__citryRuntime.finishScript("9344d2da4b62a182fdf0a8eb251a3335c988816394d6ed8373584f2710ab0dee");
} catch (error) {
__citryRuntime.finishScript("9344d2da4b62a182fdf0a8eb251a3335c988816394d6ed8373584f2710ab0dee", error);
}