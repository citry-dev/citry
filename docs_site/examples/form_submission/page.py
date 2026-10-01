"""Standalone page that renders the contact-form example."""

from citry import Component


class FormSubmissionPage(Component):
    """A full page where ContactForm handles its own submission."""

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
          <style>
            body {
              margin: 0;
              padding: 1.5rem;
              font-family: system-ui, sans-serif;
            }
          </style>
        </head>
        <body>
          <c-ContactForm />
          <c-js />
        </body>
      </html>
    """
