try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "InfiniteScrollAutomatic_13fa4a", "9c8ff2e39ec851f1002ecbb02a192cb4c659b9250c27f3573d8a62810d7d82cb")({
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
__citryRuntime.finishScript("f47442e745fdbf5c0bfc704558a9648fd8e8eed4e65b0ff1b44a60eb5309f37c");
} catch (error) {
__citryRuntime.finishScript("f47442e745fdbf5c0bfc704558a9648fd8e8eed4e65b0ff1b44a60eb5309f37c", error);
}