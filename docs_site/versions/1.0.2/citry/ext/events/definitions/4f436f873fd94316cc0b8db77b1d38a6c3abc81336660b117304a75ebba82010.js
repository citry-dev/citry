try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "InfiniteScrollVirtualList_a51b5a", "3ccd6c68dd607b19b779c795433e36c736ee8ed0d48006a73c8c0c277180ef0c")({
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
__citryRuntime.finishScript("f50b262c2f7e106fb10ee1980cc99de363b6c200820d86416fe9881df5661557");
} catch (error) {
__citryRuntime.finishScript("f50b262c2f7e106fb10ee1980cc99de363b6c200820d86416fe9881df5661557", error);
}