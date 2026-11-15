try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "InfiniteScrollAutomatic_e7f01f", "9c8ff2e39ec851f1002ecbb02a192cb4c659b9250c27f3573d8a62810d7d82cb")({
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
__citryRuntime.finishScript("e4e37525bf3cd3233a51787d20537bca2e0bc7bdc27990dba8dcb3cbd4a7c228");
} catch (error) {
__citryRuntime.finishScript("e4e37525bf3cd3233a51787d20537bca2e0bc7bdc27990dba8dcb3cbd4a7c228", error);
}