try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "InfiniteScrollVirtualList_b5a2eb", "3ccd6c68dd607b19b779c795433e36c736ee8ed0d48006a73c8c0c277180ef0c")({
  data() {
    return { expanded: false, loading: false, hasMore: true };
  },
  methods: {
    loadSnapshot() {
      if (this.loading || !this.hasMore) return;
      this.loading = true;
      return new Promise(resolve => setTimeout(() => {
        this.expanded = true;
        this.hasMore = false;
        this.loading = false;
        resolve();
      }, 220));
    },
  },
});

})();
__citryRuntime.finishScript("0c732f4b3a4a813a73cc8147a145e9481ebfb38f0e0eace921e79216facf9c4a");
} catch (error) {
__citryRuntime.finishScript("0c732f4b3a4a813a73cc8147a145e9481ebfb38f0e0eace921e79216facf9c4a", error);
}