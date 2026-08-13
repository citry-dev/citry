import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagsInputPasteAndIme(Component):
    template = """
      <section
        class="tags-input-paste"
        x-data="{
          last:'Paste or compose in the editor',
          composing:false,
        }"
      >
        <c-CField>
          <c-fill name="label">Survey regions</c-fill>
          <c-fill name="description">
            Comma, semicolon, and a pasted newline separate regions.
            At most five tags are accepted.
          </c-fill>
          <c-fill name="default">
            <c-CTagsInput
              name="regions"
              c-value="['alpine']"
              c-delimiters="[',', ';']"
              max_tags="5"
              c-input_attrs="{
                '@compositionstart':'composing=true;last=`Composition started`',
                '@compositionend':'composing=false;last=`Composition ended`',
                '@paste':'last=`Paste received`',
              }"
              $c-props="{
                onValueChange:(next,detail)=>
                  last=`${detail.source}: ${JSON.stringify(next)}`,
                onValueInvalid:(reason,detail)=>
                  last=`Rejected ${reason}: ${detail.candidate || 'batch'}`,
              }"
            />
          </c-fill>
        </c-CField>

        <div class="tags-input-paste__sample">
          <p>Try replacing selected draft text with:</p>
          <pre>coast,forest;wetland
harbor</pre>
        </div>

        <output aria-live="polite" x-text="last">
          Paste or compose in the editor
        </output>
        <p x-show="composing">The input method editor owns Enter and delimiters.</p>
      </section>
    """

    css = """
      :where(.tags-input-paste) {
        display: grid;
        gap: 1rem;
        max-inline-size: 38rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tags-input-paste__sample) {
        padding: 0.85rem;
        border-radius: 0.75rem;
        background: color-mix(in srgb, CanvasText 6%, Canvas);
      }

      :where(.tags-input-paste__sample p) {
        margin-block-start: 0;
      }

      :where(.tags-input-paste pre) {
        margin: 0;
        white-space: pre-wrap;
      }
    """


preview = TagsInputPasteAndIme()

preview  # noqa: B018
