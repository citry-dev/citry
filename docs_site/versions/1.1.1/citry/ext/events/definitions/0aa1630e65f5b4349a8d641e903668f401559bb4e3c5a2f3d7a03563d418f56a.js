try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "InfiniteScrollVirtualList_7c8d4d", "3ccd6c68dd607b19b779c795433e36c736ee8ed0d48006a73c8c0c277180ef0c")({
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
__citryRuntime.finishScript("e45ec55c587cf77516d3438dbd916bfbb151d8d4f2965b2beabd713802229550");
} catch (error) {
__citryRuntime.finishScript("e45ec55c587cf77516d3438dbd916bfbb151d8d4f2965b2beabd713802229550", error);
}