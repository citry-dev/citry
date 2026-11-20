try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DataGridSortingSelection_d4815c", "e42c2f94851c4ec2f5a187fec139da27e1cffaca99a026ac20e04199016a0b27")({
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
__citryRuntime.finishScript("e28dcd83c870f01782a8851611366fc143e30cfe84cb40e5ee4d8bcf531140b9");
} catch (error) {
__citryRuntime.finishScript("e28dcd83c870f01782a8851611366fc143e30cfe84cb40e5ee4d8bcf531140b9", error);
}