try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TagsInputMorphAndCleanup_8fe4f0", "c4d313f15d88c74d800a702784040dc5bb0d1892b3b363e3fda7c0eadff8d63c")({
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
__citryRuntime.finishScript("0a51604758ea40a641c4042e84c8d89b6f6e60dd7e4f685762cba010f2f92a2c");
} catch (error) {
__citryRuntime.finishScript("0a51604758ea40a641c4042e84c8d89b6f6e60dd7e4f685762cba010f2f92a2c", error);
}