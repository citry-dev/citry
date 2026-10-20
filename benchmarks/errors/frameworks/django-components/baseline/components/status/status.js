// The status line is an Alpine component nested inside the board's, so its
// markup reads the board's `open` through the scope Alpine shares with it.
// Its Close button leaves `open` to the board and asks it to close with an
// event. Alpine loads after this script, so the data is registered for it to
// pick up when it starts.
document.addEventListener('alpine:init', () => {
  Alpine.data('status', () => ({
    close() {
      this.$dispatch('close');
    },
  }));
});
