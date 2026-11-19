try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DataGridSortingSelection_cc8c8f", "e42c2f94851c4ec2f5a187fec139da27e1cffaca99a026ac20e04199016a0b27")({
  data() {
    return {
      sort:[{key:'name',direction:'asc'}],notice:'Activate a sortable header or select a row'
    };
  },
  methods: {
    // The grid reorders only after the owner accepts the requested sort.
    applySort(next) {
      this.sort = next;
      const order = next
        .map((item, index) => `${index + 1}. ${item.key} ${item.direction}`)
        .join(', ');
      this.notice = next.length ? `Sorted: ${order}` : 'Server row order restored';
    },
  },
});

})();
__citryRuntime.finishScript("33564105463d863c2ad3537b3794cb3aa011215d8595bf2ade80bc10aa1e2743");
} catch (error) {
__citryRuntime.finishScript("33564105463d863c2ad3537b3794cb3aa011215d8595bf2ade80bc10aa1e2743", error);
}