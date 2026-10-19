(function() {

__citryRuntime.registerTypeOptions.bind(null, "InfiniteScrollServerAction_af0caf", "2b0c177a4bfe55c5c0321ff8e1db921b22002c2fc2c73b969946bd63649185cf")({
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