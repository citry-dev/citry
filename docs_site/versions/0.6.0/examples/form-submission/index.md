---
title: Form submission
url: https://citry.dev/v/0.6.0/examples/form-submission/
description: "Handle a form submission entirely in the browser."
---
# Form submission

Use this pattern when a form should respond in the page instead of
loading a new one. The contact form handles the submit with Vue and
shows a thank-you message under the button.



### Component

````citry
"""
A contact form that handles its own submission, used as a live docs
example.

The docs site is static, so the form has no server to post to. Vue
handles the submit in the browser and shows the "thank you" response
from the entered name, standing in for the server response a real form
would show.
"""

from typing import Any

from citry import Component


class ContactForm(Component):
    """A styled contact form that thanks the sender on submit."""

    class Kwargs:
        pass

    class Slots:
        pass

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        # Python sends the empty starting state, so the server render
        # already knows there is no message and leaves the box out of
        # the first paint, before Vue loads.
        return {"name": "", "thanks": ""}

    template = """
      <form class="contact-form" @submit.prevent="submit">
        <label class="contact-form__label">
          Name
          <input
            v-model="name"
            name="name"
            class="contact-form__input"
            type="text"
            placeholder="Ada Lovelace"
          />
        </label>
        <button class="contact-form__button" type="submit">
          Submit
        </button>
        <div role="status" aria-live="polite">
          <p
            v-if="thanks"
            class="contact-form__thanks"
            v-text="thanks"
          ></p>
        </div>
      </form>
    """

    js = """
      $component({
        methods: {
          async submit() {
            // Clear the message first, so a screen reader announces
            // it again when the same name is submitted twice.
            this.thanks = "";
            await this.$nextTick();
            // A real form would post to the server and show its
            // reply. This one builds the reply from the entered name.
            const name = this.name.trim() || "stranger";
            this.thanks = `Thank you for your submission, ${name}!`;
          },
        },
      });
    """

    css = """
      .contact-form {
        max-width: 22rem;
        display: grid;
        gap: 0.75rem;
        font-family: system-ui, sans-serif;
      }
      .contact-form__label {
        display: grid;
        gap: 0.35rem;
        font-size: 0.9rem;
        color: #24292f;
      }
      .contact-form__input {
        padding: 0.5rem 0.65rem;
        border: 1px solid #d0d7de;
        border-radius: 6px;
        font: inherit;
      }
      .contact-form__button {
        padding: 0.5rem 1rem;
        border: none;
        border-radius: 6px;
        background: #4f46e5;
        color: #ffffff;
        font: inherit;
        cursor: pointer;
      }
      .contact-form__button:hover {
        background: #4338ca;
      }
      .contact-form__thanks {
        margin: 0;
        padding: 0.65rem 0.85rem;
        border: 1px solid #2da44e;
        border-radius: 6px;
        background: #effef1;
        color: #1a7f37;
      }
    """
````

### Page

````citry
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
````

[Open the live result](/v/0.6.0/examples/form-submission/demo/)



The lines to notice:

- `@submit.prevent="submit"` stops the browser from posting the form and
  calls the `submit` method from the component's JavaScript.
- `v-model="name"` keeps the input and the `name` value in step.
- `js_data()` sets the starting values from Python, so the first render
  already leaves out the empty message box.

This docs site has no server, so the example builds the reply in the
browser. To send the form to Python and validate it there, see
[Handle and validate forms](/v/0.6.0/events/forms/).