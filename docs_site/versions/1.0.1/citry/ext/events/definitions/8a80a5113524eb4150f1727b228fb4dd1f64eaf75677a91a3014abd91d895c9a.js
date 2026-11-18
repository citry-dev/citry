try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "InfiniteScrollVirtualList_128496", "3ccd6c68dd607b19b779c795433e36c736ee8ed0d48006a73c8c0c277180ef0c")({
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
__citryRuntime.finishScript("14cda8a6f9c3f6dd663d0494d68aca42b082c5b632fb1f33ffe7390a59ce18e4");
} catch (error) {
__citryRuntime.finishScript("14cda8a6f9c3f6dd663d0494d68aca42b082c5b632fb1f33ffe7390a59ce18e4", error);
}