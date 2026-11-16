try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "InfiniteScrollVirtualList_8d5b7c", "3ccd6c68dd607b19b779c795433e36c736ee8ed0d48006a73c8c0c277180ef0c")({
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
__citryRuntime.finishScript("84c2c3bf7b0abbaf84e068bf6d33ff8ec2b60c90cf984f6b2645ef6160f13473");
} catch (error) {
__citryRuntime.finishScript("84c2c3bf7b0abbaf84e068bf6d33ff8ec2b60c90cf984f6b2645ef6160f13473", error);
}