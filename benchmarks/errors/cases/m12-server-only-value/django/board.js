document.addEventListener('alpine:init', () => {
  Alpine.data('board', () => ({
    // page.html writes the public API base into a json_script tag with id api-base.
    api: JSON.parse(document.getElementById('secret-token').textContent),
    open: false,

    toggle() {
      this.open = !this.open;
    },
  }));
});
