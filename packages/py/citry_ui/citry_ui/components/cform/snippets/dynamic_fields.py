import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class DynamicFields(Component):
    template = """
      <section
        class="filter-sequence"
        x-data="{
          rows: [
            { id: 1, value: 'Luminance' },
            { id: 2, value: 'Hydrogen-alpha' },
            { id: 3, value: 'Oxygen III' },
          ],
          nextId: 4,
          result: '',
        }"
      >
        <header>
          <p>Filter wheel</p>
          <h2>Build an exposure sequence</h2>
        </header>

        <c-CForm @submit.prevent="result = JSON.stringify(new FormData($el).getAll('filter'))">
          <div class="filter-sequence__rows">
            <template x-for="(row, index) in rows" :key="row.id">
              <div class="filter-sequence__row">
                <label
                  :for="`filter-${row.id}`"
                  x-text="`Exposure ${index + 1}`"
                ></label>
                <input
                  :id="`filter-${row.id}`"
                  name="filter"
                  x-model="row.value"
                />
                <button type="button" @click="rows.splice(index, 1)">Remove</button>
              </div>
            </template>
          </div>
          <div class="filter-sequence__actions">
            <c-CButton
              type="button"
              variant="outline"
              intent="neutral"
              @click="rows.push({ id: nextId++, value: 'New filter' })"
            >
              Add exposure
            </c-CButton>
            <c-CButton
              type="button"
              variant="ghost"
              intent="neutral"
              @click="rows.length > 1 && rows.unshift(rows.pop())"
            >
              Rotate order
            </c-CButton>
            <c-CButton type="submit">
              Read FormData
            </c-CButton>
          </div>
        </c-CForm>

        <output
          aria-live="polite"
          x-show="result"
          x-text="result"
        ></output>
      </section>
    """

    css = """
      :where(.filter-sequence) {
        max-width: 48rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#c7c9e8, #45486f);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.filter-sequence header) {
        margin-block-end: 1rem;
      }

      :where(.filter-sequence h2, .filter-sequence p) {
        margin-block: 0;
      }

      :where(.filter-sequence header p) {
        color: light-dark(#5b4bc4, #a9a2ff);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.filter-sequence__rows) {
        display: grid;
        gap: 0.625rem;
      }

      :where(.filter-sequence__row) {
        display: grid;
        grid-template-columns: minmax(6rem, 0.45fr) minmax(0, 1fr) auto;
        align-items: center;
        gap: 0.625rem;
      }

      :where(.filter-sequence__row input) {
        min-width: 0;
        padding: 0.55rem 0.7rem;
        border: 1px solid light-dark(#9498bd, #686c96);
        border-radius: 0.45rem;
        background: Canvas;
        color: CanvasText;
        font: inherit;
      }

      :where(.filter-sequence__row button) {
        border: 0;
        background: transparent;
        color: light-dark(#9b2c24, #ff9d94);
        cursor: pointer;
      }

      :where(.filter-sequence__actions) {
        display: flex;
        flex-wrap: wrap;
        gap: 0.625rem;
      }

      :where(.filter-sequence output) {
        display: block;
        margin-block-start: 1rem;
        overflow-wrap: anywhere;
      }

      @media (max-width: 34rem) {
        :where(.filter-sequence__row) {
          grid-template-columns: minmax(0, 1fr) auto;
        }

        :where(.filter-sequence__row label) {
          grid-column: 1 / -1;
        }
      }
    """


preview = DynamicFields()

preview  # noqa: B018
