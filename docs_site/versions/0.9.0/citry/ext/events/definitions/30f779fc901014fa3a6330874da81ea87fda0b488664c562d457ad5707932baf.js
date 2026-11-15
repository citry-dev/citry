try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "TagsInputMorphAndCleanup_afc0e6", "c4d313f15d88c74d800a702784040dc5bb0d1892b3b363e3fda7c0eadff8d63c")({
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
__citryRuntime.finishScript("c75dd427211e26c0821a6fbf120b6a74309cd39b3e0f37a83b2ee165b0f4889a");
} catch (error) {
__citryRuntime.finishScript("c75dd427211e26c0821a6fbf120b6a74309cd39b3e0f37a83b2ee165b0f4889a", error);
}