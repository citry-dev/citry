import citry_ui
from citry import Component, citry

citry.register_library(citry_ui)


class FieldThemeCustomization(Component):
    template = """
      <section class="shore-themes">
        <article class="shore-theme shore-theme--sunlit">
          <p>Sunlit survey</p>
          <c-CField required>
            <c-fill name="label">
              Water clarity
            </c-fill>
            <c-fill name="default">
              <c-CInput name="day_clarity" value="Clear" />
            </c-fill>
          </c-CField>
        </article>

        <article class="shore-theme shore-theme--moonlit">
          <p>Moonlit survey</p>
          <c-CField invalid>
            <c-fill name="label">
              Lantern marker
            </c-fill>
            <c-fill name="default">
              <c-CInput name="night_marker" value="Missing" variant="filled" />
            </c-fill>
            <c-fill name="error">
              Mark the nearest visible lantern.
            </c-fill>
          </c-CField>
        </article>
      </section>
    """

    css = """
      :where(.shore-themes) {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(min(100%, 18rem), 1fr));
        gap: 1rem;
        max-width: 62rem;
        font-family: ui-sans-serif, system-ui, sans-serif;
      }

      :where(.shore-theme) {
        min-width: 0;
        padding: 1.25rem;
        border: 1px solid var(--shore-border);
        border-radius: 0.875rem;
        background: Canvas;
        color: CanvasText;
      }

      :where(.shore-theme > p) {
        margin-block: 0 1rem;
        color: var(--shore-accent);
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.07em;
        text-transform: uppercase;
      }

      :where(.shore-theme--sunlit) {
        --shore-border: #91c7d2;
        --shore-accent: #086b7d;
        --cui-field-label-color: #164e63;
        --cui-input-focus-color: #0891b2;
        --cui-input-radius: 0.8rem;

        color-scheme: light;
      }

      :where(.shore-theme--moonlit) {
        --shore-border: #475569;
        --shore-accent: #67e8f9;
        --cui-field-label-color: #cffafe;
        --cui-field-error-color: #fda4af;
        --cui-input-background: #0f172a;
        --cui-input-foreground: #e2e8f0;
        --cui-input-border-color: #64748b;
        --cui-input-focus-color: #22d3ee;
        --cui-input-placeholder-color: #94a3b8;

        color-scheme: dark;
      }

      :where(.shore-theme [data-citry-ui-part="description"]) {
        max-inline-size: 38ch;
      }
    """


preview = FieldThemeCustomization()

preview  # noqa: B018
