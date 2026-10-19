(function() {

__citryRuntime.registerTypeOptions.bind(null, "InfiniteScrollAutomatic_44ed91", "9c8ff2e39ec851f1002ecbb02a192cb4c659b9250c27f3573d8a62810d7d82cb")({
  data() {
    return { moreResults: [], loading: false, hasMore: true, nextResult: 9 };
  },
  methods: {
    loadNextPage() {
      if (this.loading) return;
      this.loading = true;
      return new Promise(resolve => setTimeout(() => {
        const page = Array.from({ length: 4 }, () => {
          const id = this.nextResult++;
          return { id, label: `Search result ${id}` };
        });
        this.moreResults.push(...page);
        this.loading = false;
        resolve();
      }, 260));
    },
  },
});

})();