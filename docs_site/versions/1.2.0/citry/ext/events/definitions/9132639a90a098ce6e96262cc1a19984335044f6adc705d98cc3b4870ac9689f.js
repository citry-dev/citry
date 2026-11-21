try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TagsInputMorphAndCleanup_755a01", "c4d313f15d88c74d800a702784040dc5bb0d1892b3b363e3fda7c0eadff8d63c")({
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
__citryRuntime.finishScript("c66a6db777a5cdceac17f22fc3ec7aac0b43f43c97232f8863925476e3c17260");
} catch (error) {
__citryRuntime.finishScript("c66a6db777a5cdceac17f22fc3ec7aac0b43f43c97232f8863925476e3c17260", error);
}