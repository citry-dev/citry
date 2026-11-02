(function() {

__citryRuntime.registerTypeOptions.bind(null, "DisabledAndShortcuts_fe5b18", "d11dd1cfe4db184aae3b062a39f9e0ec76e076b619a8fe6e13ea4f57cdb3c351")({
  data() {
    return {
      open:true,disabled:false,loop:true,last:'none',
      // Alt+Shift+D is left out on purpose: "Deploy production" is
      // disabled, so its hint must not run anything.
      shortcuts:{V:'view-logs',X:'delete-environment'}
    };
  },
  methods: {
    // The palette shows the hints but never listens for the keys,
    // so the page handles them and records the same action as
    // choosing each command. Few browsers use Alt+Shift+letter.
    // On macOS, Option+Shift types a character such as Ø, so the
    // code falls back to the key's position. In the search box
    // this also stops macOS Option+Shift from typing that
    // character, so an application should pick keys its users do
    // not need to type there.
    handleShortcut(event) {
      const target = event.target;
      const letter = /^[a-z]$/i.test(event.key)
        ? event.key.toUpperCase()
        : event.code.replace(/^Key/, '');
      const value = this.shortcuts[letter];
      // Leave text fields alone (input, textarea, select and
      // contenteditable), except a combobox such as the palette's
      // search box, which has focus whenever the hints are on
      // screen. A checkbox takes no typing and keeps focus after a
      // click, so the keys still work while one is focused.
      const typing = target.matches(
        'textarea, select, input:not([type=checkbox])'
      ) || target.isContentEditable;
      if (
        !value
        // A disabled palette's commands are unavailable, so their
        // keys do nothing too.
        || this.disabled
        || !event.altKey || !event.shiftKey
        || event.ctrlKey || event.metaKey
        || event.isComposing
        || (typing && target.getAttribute('role') !== 'combobox')
      ) return;
      event.preventDefault();
      this.last = value;
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