---
title: Form submission
description: Handle a form submission entirely in the browser.
---

# Form submission

Use this pattern when a form should respond in the page instead of
loading a new one. The contact form handles the submit with Vue and
shows a thank-you message under the button.

<c-example name="form_submission" />

The lines to notice:

- `@submit.prevent="submit"` stops the browser from posting the form and
  calls the `submit` method from the component's JavaScript.
- `v-model="name"` keeps the input and the `name` value in step.
- `js_data()` sets the starting values from Python, so the first render
  already leaves out the empty message box.

This docs site has no server, so the example builds the reply in the
browser. To send the form to Python and validate it there, see
[Handle and validate forms](/events/forms/).
