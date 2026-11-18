try {
(function() {

__citryRuntime.registerTypeOptions.bind(null, "DataGridSortingSelection_ebb6c2", "e42c2f94851c4ec2f5a187fec139da27e1cffaca99a026ac20e04199016a0b27")({
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
__citryRuntime.finishScript("61029839ed89a517f3495d594fdb36e752e41725748edd0e7af37090d9b65f05");
} catch (error) {
__citryRuntime.finishScript("61029839ed89a517f3495d594fdb36e752e41725748edd0e7af37090d9b65f05", error);
}