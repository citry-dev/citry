try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "FragmentWidget_9ba611", "1b5068182486f98a149253374ed17caf4737f41d1f477345e47e61670b736412")({
  data() {
    return { scriptRan: false };
  },
  mounted() {
    // The label appears only once the widget's own script has
    // run in the page that inserted the fragment.
    this.scriptRan = true;
  },
});

})();
__citryRuntime.finishScript("dc6b8f3013af2abe51d5032e4f23c6dfc46b3fc50067ad3b59d3fa21ef258fde");
} catch (error) {
__citryRuntime.finishScript("dc6b8f3013af2abe51d5032e4f23c6dfc46b3fc50067ad3b59d3fa21ef258fde", error);
}