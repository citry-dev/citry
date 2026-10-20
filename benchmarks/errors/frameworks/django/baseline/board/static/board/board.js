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
  // board's, so its markup reads the board's `open` directly. Its Close
  // button leaves `open` to the board and asks it to close with an event.
  Alpine.data('status', () => ({
    close() {
      this.$dispatch('close');
    },
  }));
});
