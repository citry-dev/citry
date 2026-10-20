document.addEventListener('alpine:init', () => {
  Alpine.data('board', () => ({
    // page.html writes the public API base into a json_script tag with id api-base.
    api: JSON.parse(document.getElementById('api-base').textContent),
    open: false,

    toggle() {
      this.open = !this.open;
    },
  }));

  // The status line inside Details. Alpine nests its scope inside the
  // board's, so it reads the board's `open` directly; its Close button asks
  // the board to close by dispatching an event.
  Alpine.data('status', () => ({
    get label() {
      return this.open ? 'Status: open' : 'Status: closed';
    },
  }));
});
