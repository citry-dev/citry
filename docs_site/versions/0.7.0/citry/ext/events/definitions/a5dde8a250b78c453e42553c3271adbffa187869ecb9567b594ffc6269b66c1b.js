(function() {

__citryRuntime.registerTypeOptions.bind(null, "Tabs_118635", "cae579f775e7f984bfa3199f808852b77a19b225691ec60441048d671f086465")({
  created() {
    // Vue does not promise that refs collected inside v-for
    // keep the list order, so each button is stored under its
    // index. A plain Map, set up here rather than in data(),
    // keeps Vue from tracking the elements as state.
    this.tabButtons = new Map();
  },
  methods: {
    keepTabButton(index, el) {
      // Vue calls this with null when the button unmounts, so
      // the Map drops it instead of holding a detached element.
      if (el) {
        this.tabButtons.set(index, el);
      } else {
        this.tabButtons.delete(index);
      }
    },
    moveWithKeys(event, index) {
      // The arrow keys wrap around, and Home and End jump to
      // the ends, as the WAI-ARIA tabs pattern expects.
      const count = this.tabs.length;
      const nextIndex = {
        ArrowRight: (index + 1) % count,
        ArrowLeft: (index - 1 + count) % count,
        Home: 0,
        End: count - 1,
      }[event.key];
      // Other keys, such as Tab, keep their usual meaning.
      if (nextIndex === undefined) return;
      event.preventDefault();
      this.activeIndex = nextIndex;
      // Only the open tab is in the Tab order, so focus
      // follows it.
      this.tabButtons.get(nextIndex)?.focus();
    },
  },
});

})();