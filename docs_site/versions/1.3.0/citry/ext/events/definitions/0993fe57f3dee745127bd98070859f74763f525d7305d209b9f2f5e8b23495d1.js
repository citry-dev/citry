try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "InfiniteScrollVirtualList_f6ec23", "3ccd6c68dd607b19b779c795433e36c736ee8ed0d48006a73c8c0c277180ef0c")({
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
__citryRuntime.finishScript("9c20e92041942e7600390b506818b0edb650a4d7902a8930945ce433bc0f27da");
} catch (error) {
__citryRuntime.finishScript("9c20e92041942e7600390b506818b0edb650a4d7902a8930945ce433bc0f27da", error);
}