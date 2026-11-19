try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "InfiniteScrollVirtualList_c3d025", "3ccd6c68dd607b19b779c795433e36c736ee8ed0d48006a73c8c0c277180ef0c")({
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
__citryRuntime.finishScript("cdba677d693a1e4b9e0c6636bd32373f695fb6701b5fc55df4399722cfab6546");
} catch (error) {
__citryRuntime.finishScript("cdba677d693a1e4b9e0c6636bd32373f695fb6701b5fc55df4399722cfab6546", error);
}