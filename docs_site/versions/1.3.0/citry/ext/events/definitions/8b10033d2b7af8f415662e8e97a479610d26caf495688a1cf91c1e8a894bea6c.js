try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "InfiniteScrollServerAction_d5b07a", "2b0c177a4bfe55c5c0321ff8e1db921b22002c2fc2c73b969946bd63649185cf")({
  data() {
    return {
      moreResults: [], loading: false, hasMore: true,
      acceptedAction: 'Waiting for a named action',
    };
  },
  methods: {
    loadServerPage(event) {
      const submitter = event.submitter;
      if (!submitter || this.loading || !this.hasMore) return;
      this.acceptedAction = `${submitter.name}=${submitter.value}`;
      this.loading = true;
      setTimeout(() => {
        this.moreResults.push(
          { id: 3, label: 'Mirrorless travel kit' },
          { id: 4, label: 'Low-light autofocus test' },
        );
        this.hasMore = false;
        this.loading = false;
      }, 240);
    },
  },
});

})();
__citryRuntime.finishScript("6babcea329d05d53a8a1ce8c33da088687403ced089d3146f516286d656ba201");
} catch (error) {
__citryRuntime.finishScript("6babcea329d05d53a8a1ce8c33da088687403ced089d3146f516286d656ba201", error);
}