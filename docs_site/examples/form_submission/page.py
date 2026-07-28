"""Standalone page that renders the contact-form example (the live demo)."""

from citry import Component


class FormSubmissionPage(Component):
    """A full page showing the ContactForm handling its own submission client-side."""

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Form submission example</title>
          <c-css />
        </head>
        <body
          style="margin: 0; padding: 1.5rem; font-family: system-ui, sans-serif;"
        >
          <c-ContactForm />
          <c-js />
        </body>
      </html>
    """
