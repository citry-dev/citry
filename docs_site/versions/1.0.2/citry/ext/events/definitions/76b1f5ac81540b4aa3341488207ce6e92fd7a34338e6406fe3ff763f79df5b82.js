try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "InfiniteScrollErrorRetry_5bd765", "25b3e8ba7ac4275134b999ad10aece4c0c5d98ed37dcb96e4a07aa97325ac9b2")({
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
__citryRuntime.finishScript("e05a92b8bd4f68a6fd1bb2e995ea9b16c9e50229efbb6bd9152c0882d322b815");
} catch (error) {
__citryRuntime.finishScript("e05a92b8bd4f68a6fd1bb2e995ea9b16c9e50229efbb6bd9152c0882d322b815", error);
}