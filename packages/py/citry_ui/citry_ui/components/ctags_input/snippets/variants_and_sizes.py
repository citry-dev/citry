import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class TagsInputVariantsAndSizes(Component):
    def template_data(self, kwargs, slots) -> dict[str, object]:  # noqa: ANN001, ARG002
        return {
            "variants": ("outline", "filled", "plain"),
            "sizes": ("sm", "md", "lg"),
        }

    template = """
      <section class="tags-input-variants">
        <div class="tags-input-variants__grid">
          <c-for each="variant in variants">
            <c-for each="size in sizes">
              <article>
                <code>{{ variant }} / {{ size }}</code>
                <c-CTagsInput
                  #c-key="f'{variant}-{size}'"
                  c-variant="variant"
                  c-size="size"
                  c-value="['alpine', 'coastal']"
                  c-input_attrs="{
                    'aria-label':f'{variant} {size} labels',
                  }"
                />
              </article>
            </c-for>
          </c-for>
        </div>

        <div class="tags-input-variants__boundaries">
          <article>
            <h3>Empty and required</h3>
            <c-CTagsInput
              required
              placeholder="Add a required label"
              c-input_attrs="{'aria-label':'Required empty labels'}"
            />
          </article>
          <article>
            <h3>At maximum</h3>
            <c-CTagsInput
              max_tags="2"
              c-value="['one', 'two']"
              c-input_attrs="{'aria-label':'Maximum labels'}"
            />
          </article>
          <article style="color-scheme:dark">
            <h3>Dark and narrow</h3>
            <c-CTagsInput
              invalid
              c-value="[
                'a-very-long-unbroken-routing-label-that-stays-contained',
              ]"
              c-input_attrs="{'aria-label':'Long invalid labels'}"
            />
          </article>
        </div>
      </section>
    """

    css = """
      :where(.tags-input-variants) {
        display: grid;
        gap: 1.25rem;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.tags-input-variants__grid) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 16rem), 1fr));
        gap: 0.75rem;
      }

      :where(.tags-input-variants article) {
        display: grid;
        gap: 0.5rem;
        min-inline-size: 0;
      }

      :where(.tags-input-variants__boundaries) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
        gap: 0.75rem;
      }

      :where(.tags-input-variants__boundaries article) {
        inline-size: min(100%, 20rem);
        padding: 0.85rem;
        border-radius: 0.75rem;
        background: Canvas;
        color: CanvasText;
      }

      :where(.tags-input-variants h3) {
        margin: 0;
      }
    """


preview = TagsInputVariantsAndSizes()

preview  # noqa: B018
