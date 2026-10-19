(function() {

__citryRuntime.registerTypeOptions.bind(null, "InfiniteScrollErrorRetry_a78069", "25b3e8ba7ac4275134b999ad10aece4c0c5d98ed37dcb96e4a07aa97325ac9b2")({
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