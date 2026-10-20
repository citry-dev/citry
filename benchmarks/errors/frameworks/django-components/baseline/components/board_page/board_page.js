// django-components runs this callback with what get_js_data() returned.
$onComponent(({ api_base }) => {
  // Alpine loads after this script, so the board's data is registered for
  // it to pick up when it starts.
  document.addEventListener('alpine:init', () => {
    Alpine.data('board', () => ({
      api: api_base,
      open: false,

      toggle() {
        this.open = !this.open;
      },
    }));
  });
});
