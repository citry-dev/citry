try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "InfiniteScrollAtAGlance_be2c30", "aab21c547912c75bedeef7beeb52bea612286b04e984f0ff226f867b7e057f91")({
  data() {
    return { moreActivities: [], loading: false, hasMore: true, page: 0 };
  },
  methods: {
    loadNextPage(detail) {
      // This static preview handles the named action locally. A server page
      // lets the submit continue and returns the next keyed result page.
      detail.sourceEvent?.preventDefault();
      const pages = [
        [
          { id: 4, label: 'Received legal approval' },
          { id: 5, label: 'Scheduled the launch' },
        ],
        [
          { id: 6, label: 'Opened early access' },
          { id: 7, label: 'Collected the first responses' },
        ],
      ];
      if (this.loading || !this.hasMore) return;
      this.loading = true;
      return new Promise(resolve => setTimeout(() => {
        this.moreActivities.push(...pages[this.page]);
        this.page += 1;
        this.hasMore = this.page < pages.length;
        this.loading = false;
        resolve();
      }, 220));
    },
  },
});

})();
__citryRuntime.finishScript("04aac8d62b95cbba27d85f5831aecbf23a1617fa45682f33301031540e3300c8");
} catch (error) {
__citryRuntime.finishScript("04aac8d62b95cbba27d85f5831aecbf23a1617fa45682f33301031540e3300c8", error);
}