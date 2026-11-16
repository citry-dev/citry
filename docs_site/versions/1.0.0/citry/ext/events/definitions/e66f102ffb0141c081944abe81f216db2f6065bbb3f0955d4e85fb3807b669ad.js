try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "InfiniteScrollErrorRetry_21ea0f", "25b3e8ba7ac4275134b999ad10aece4c0c5d98ed37dcb96e4a07aa97325ac9b2")({
  data() {
    return {
      recoveredOrders: [], loading: false, error: true, hasMore: true, recovered: false,
    };
  },
  methods: {
    retryPage() {
      if (this.loading || !this.hasMore) return;
      this.error = false;
      this.loading = true;
      return new Promise(resolve => setTimeout(() => {
        this.recoveredOrders.push(
          { id: 1040, label: 'Order #1040' },
          { id: 1039, label: 'Order #1039' },
        );
        this.recovered = true;
        this.hasMore = false;
        this.loading = false;
        resolve();
      }, 260));
    },
  },
});

})();
__citryRuntime.finishScript("fdb8798078afe6c7483c98753d3a1f48f53fd5442f60b53ea6089ee951006c58");
} catch (error) {
__citryRuntime.finishScript("fdb8798078afe6c7483c98753d3a1f48f53fd5442f60b53ea6089ee951006c58", error);
}