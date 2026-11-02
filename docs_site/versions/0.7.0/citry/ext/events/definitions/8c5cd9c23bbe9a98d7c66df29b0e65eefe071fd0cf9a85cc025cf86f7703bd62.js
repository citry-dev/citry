(function() {

__citryRuntime.registerTypeOptions.bind(null, "MenuItemContent_ccd3ff", "63931ed8c518ff36d4fe3c8b55ebde685c385609c22b6521fa668de7312a8959")({
  data() {
    return {
      lastAction: 'none',
      shortcuts: {F: 'search', P: 'bookmark'},
    };
  },
  methods: {
    // The menu shows the hints but never listens for the keys, so
    // the page handles them and records the same action as
    // choosing each item. Few browsers use Alt+Shift+letter. On
    // macOS, Option+Shift types a character such as Ø, so the
    // code falls back to the key's position.
    handleShortcut(event) {
      const target = event.target;
      const letter = /^[a-z]$/i.test(event.key)
        ? event.key.toUpperCase()
        : event.code.replace(/^Key/, '');
      const value = this.shortcuts[letter];
      // Leave text fields alone (input, textarea, select and
      // contenteditable). A checkbox takes no typing, so the keys
      // still work while one is focused.
      const typing = target.matches(
        'textarea, select, input:not([type=checkbox])'
      ) || target.isContentEditable;
      if (
        !value
        || !event.altKey || !event.shiftKey
        || event.ctrlKey || event.metaKey
        || event.isComposing
        || typing
      ) return;
      event.preventDefault();
      this.lastAction = value;
    },
  },
  mounted() {
    window.addEventListener("keydown", this.handleShortcut);
  },
  beforeUnmount() {
    window.removeEventListener("keydown", this.handleShortcut);
  },
});

})();