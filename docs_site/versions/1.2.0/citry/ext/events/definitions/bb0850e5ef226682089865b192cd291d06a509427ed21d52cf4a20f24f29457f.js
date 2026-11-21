try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "InfiniteScrollAtAGlance_26ecbe", "aab21c547912c75bedeef7beeb52bea612286b04e984f0ff226f867b7e057f91")({
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
__citryRuntime.finishScript("b0415f082925b89e1ffbfb6a168b87554522888db9b32e4008451a5caf01386a");
} catch (error) {
__citryRuntime.finishScript("b0415f082925b89e1ffbfb6a168b87554522888db9b32e4008451a5caf01386a", error);
}