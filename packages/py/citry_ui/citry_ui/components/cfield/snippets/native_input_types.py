import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class NativeInputTypes(Component):
    template = """
      <section class="shore-native-grid">
        <c-CField>
          <c-fill name="label">
            Observer email
          </c-fill>
          <c-fill name="default">
            <c-CInput name="email" type="email" autocomplete="email" />
          </c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">
            Ranger telephone
          </c-fill>
          <c-fill name="default">
            <c-CInput name="telephone" type="tel" inputmode="tel" />
          </c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">
            Field guide URL
          </c-fill>
          <c-fill name="default">
            <c-CInput name="guide" type="url" inputmode="url" />
          </c-fill>
        </c-CField>
        <c-CField>
          <c-fill name="label">
            Survey passphrase
          </c-fill>
          <c-fill name="default">
            <c-CInput name="passphrase" type="password" autocomplete="current-password" />
          </c-fill>
        </c-CField>
        <label class="shore-native-grid__standalone">
          Filter observations
          <c-CInput
            type="search"
            placeholder="Search species"
            c-attrs="{'aria-label': 'Filter observations'}"
          />
        </label>
      </section>
    """

    css = """
      :where(.shore-native-grid) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 17rem), 1fr));
        gap: 1.25rem;
        max-width: 62rem;
        padding: 1.25rem;
        border: 1px solid light-dark(#b9d8df, #315967);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.shore-native-grid__standalone) {
        display: grid;
        gap: 0.5rem;
        font-weight: 600;
      }
    """


preview = NativeInputTypes()

preview  # noqa: B018
