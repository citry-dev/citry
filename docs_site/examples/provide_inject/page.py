"""Standalone page showing buttons styled by an ancestor theme."""

from citry import Component


class ProvideInjectPage(Component):
    """A full page wrapping ThemedButtons in provided themes.

    The buttons inject their theme and never receive it as a prop.
    """

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Provide / inject example</title>
          <c-css />
          <style>
            body {
              margin: 0;
              padding: 1.5rem;
              font-family: system-ui, sans-serif;
            }
          </style>
        </head>
        <body>
          <c-provide
            key="theme"
            accent="#2563eb"
            label="Ocean"
          >
            <p style="margin: 0 0 0.5rem; color: #57606a;">
              These buttons read the outer theme:
            </p>
            <c-ThemedButton text="Save" />
            <c-ThemedButton text="Share" />

            <c-provide
              key="theme"
              accent="#16a34a"
              label="Forest"
            >
              <p style="margin: 1rem 0 0.5rem; color: #57606a;">
                Nested provide wins for buttons inside it:
              </p>
              <c-ThemedButton text="Publish" />
            </c-provide>
          </c-provide>
          <c-js />
        </body>
      </html>
    """
