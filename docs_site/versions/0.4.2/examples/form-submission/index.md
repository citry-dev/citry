---
title: Form submission
url: https://citry.dev/v/0.4.2/examples/form-submission/
description: "Handle a form submission entirely in the browser."
---
# Form submission

A form component that handles its own submission in the browser, with no
server.



### Component

````citry
"""
A contact form that handles its own submission, used as a live docs example.

The component ships its own JS: it intercepts the form submit so the "thank you"
response appears with no server (the docs site is static). This mirrors the
django-components form-submission example, whose server POST is simulated here by
intercepting the submit in the browser.
"""

from citry import Component


class ContactForm(Component):
    """A styled contact form; submitting it shows a thank-you message, all client-side."""

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <form class="contact-form">
        <label class="contact-form__label">
          Name
          <input
            name="name"
            class="contact-form__input"
            type="text"
            placeholder="Ada Lovelace"
          />
        </label>
        <button class="contact-form__button" type="submit">Submit</button>
        <div
          class="contact-form__result"
          role="status"
          aria-live="polite"
        ></div>
      </form>
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
        padding: 0.65rem 0.85rem;
        border: 1px solid #2da44e;
        border-radius: 6px;
        background: #effef1;
        color: #1a7f37;
      }
    """

    js = """
      $component(({ els }) => {
        const root = els[0];
        const form = root.matches("form") ? root : root.querySelector("form");
        const result = root.querySelector(".contact-form__result");
        form.addEventListener("submit", (event) => {
          // No server on a static site: intercept the submit and show the
          // response in the browser, built from the entered name.
          event.preventDefault();
          const entered = (new FormData(form).get("name") || "").toString().trim();
          const name = entered || "stranger";
          result.textContent = "";
          const box = document.createElement("div");
          box.className = "contact-form__thanks";
          box.textContent = `Thank you for your submission, ${name}!`;
          result.appendChild(box);
        });
      });
    """
````

### Page

````citry
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
````

[Open the live result](/v/0.4.2/examples/form-submission/demo/)

