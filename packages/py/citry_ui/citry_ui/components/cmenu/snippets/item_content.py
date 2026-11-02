import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class MenuItemContent(Component):
    template = """
      <section class="archive-content-demo">
        <c-CMenu
          v-bind="{
            onAction: (value) => lastAction = value,
          }"
        >
          <c-fill name="activator" data="{ activator_attrs, activator_disabled }">
            <c-CButton c-disabled="activator_disabled" c-attrs="activator_attrs">Catalog tools</c-CButton>
          </c-fill>
          <c-fill name="default">
            <c-CMenuItem value="search">
              <c-fill name="start"><c-CIcon name="search" /></c-fill>
              <c-fill name="default">Search illuminated texts</c-fill>
              <c-fill name="description">Find titles, scribes, and sigils.</c-fill>
              <c-fill name="end"><kbd>Alt Shift F</kbd></c-fill>
            </c-CMenuItem>
            <c-CMenuItem value="bookmark">
              <c-fill name="start"><c-CIcon name="star" /></c-fill>
              <c-fill name="default">Mark this passage</c-fill>
              <c-fill name="end"><kbd>Alt Shift P</kbd></c-fill>
            </c-CMenuItem>
          </c-fill>
        </c-CMenu>
        <output v-text="`Last command: ${lastAction}`">Last command: none</output>
      </section>
    """

    js = """
      $component({
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
    """

    css = """
      :where(.archive-content-demo) {
        min-block-size: 15rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.archive-content-demo output) {
        display: block;
        margin-block-start: 1rem;
        color: light-dark(#66451f, #dec08f);
      }

      :where(.archive-content-demo kbd) {
        padding: 0.1rem 0.35rem;
        border: 1px solid color-mix(in srgb, CanvasText 20%, transparent);
        border-radius: 0.3rem;
        font: inherit;
        font-size: 0.75rem;
      }
    """


preview = MenuItemContent()

preview  # noqa: B018
