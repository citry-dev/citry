import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagsInputKeyboardAndFocus(Component):
    template = """
      <section
        class="tags-input-keyboard"
        x-data="{last:'Focus an editor to begin'}"
      >
        <article>
          <h3>Left-to-right navigation</h3>
          <p>
            At an empty start position, Backspace selects the last tag.
            Press it again to remove. Arrow keys, Home, End, Delete, and Escape
            operate while focus stays in the editor.
          </p>
          <c-CTagsInput
            c-value="['alpine', 'forest', 'harbor']"
            c-input_attrs="{
              'aria-label':'Keyboard labels',
              '@focus':'last=`LTR editor focused`',
            }"
            $c-props="{
              onValueChange:(next,detail)=>
                last=`${detail.source}: ${JSON.stringify(next)}`,
            }"
          />
        </article>

        <article dir="rtl">
          <h3>Right-to-left navigation</h3>
          <p>Physical arrows follow the visual row while value order stays stable.</p>
          <c-CTagsInput
            c-value="['جبال', 'غابة', 'ميناء']"
            c-input_attrs="{
              'aria-label':'وسوم لوحة المفاتيح',
              '@focus':'last=`RTL editor focused`',
            }"
          />
        </article>

        <output aria-live="polite" x-text="last">
          Focus an editor to begin
        </output>
      </section>
    """

    css = """
      :where(.tags-input-keyboard) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 19rem), 1fr));
        gap: 1rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tags-input-keyboard article) {
        display: grid;
        gap: 0.75rem;
        align-content: start;
        padding: 1rem;
        border: 1px solid color-mix(in srgb, CanvasText 20%, transparent);
        border-radius: 0.75rem;
      }

      :where(.tags-input-keyboard h3, .tags-input-keyboard p) {
        margin: 0;
      }

      :where(.tags-input-keyboard output) {
        grid-column: 1 / -1;
      }
    """


preview = TagsInputKeyboardAndFocus()

preview  # noqa: B018
