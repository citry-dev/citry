from citry import Component
from citry.ext.events import EventError, actions

from citry_setup import citry_app


# New in this step: render this component after a valid form.
class Confirmation(Component):
    citry = citry_app

    class Kwargs:
        email: str

    class Slots:
        pass

    def js_data(self, kwargs: Kwargs, slots: Slots):
        return {"email": kwargs.email}

    template = """
      <section class="confirmation">
        <strong>Request received</strong>
        <p>We will write to {{ email }}.</p>
        <p
          class="confirmation__status"
          x-text="'Confirmation ready for ' + email"
        >
          Preparing confirmation...
        </p>
      </section>
    """

    css = """
      .confirmation {
        border: 2px solid #2f855a;
        border-radius: 0.5rem;
        padding: 1rem;
      }
    """


class SignupIn:
    email: str


class SignupForm(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    class Events:
        def submit(self, data: SignupIn):
            email = data.email.strip()
            if not email.endswith("@example.com"):
                raise EventError(
                    "Please fix the email address.",
                    fields={"email": "Use an @example.com address."},
                )
            # New in this step: replace the result area's contents.
            return actions.Render(
                Confirmation(email=email),
                target="#signup-result",
                swap="inner",
            )

    template = """
      <section class="signup-form">
        <form @c-submit.prevent="submit">
          <label>
            Work email
            <input
              name="email"
              type="email"
              autocomplete="email"
              required
            />
            <span
              class="signup-form__error"
              role="alert"
              x-show="$error('submit')?.fieldErrors?.email"
              x-text="$error('submit')?.fieldErrors?.email || ''"
            ></span>
          </label>
          <button
            type="submit"
            :disabled="$loading('submit')"
            x-text="$loading('submit') ? 'Sending' : 'Send request'"
          >
            Send request
          </button>
        </form>
        {# New in this step: give Render a stable target. #}
        <div id="signup-result" aria-live="polite">
          <p>Your confirmation will appear here.</p>
        </div>
      </section>
    """


class TutorialPage(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <meta charset="utf-8" />
          <title>Join the reading room</title>
          {# New in this step: place collected component CSS. #}
          <c-css />
        </head>
        <body>
          <main>
            <h1>Join the reading room</h1>
            <c-SignupForm />
          </main>
          {# New in this step: place collected component JS. #}
          <c-js />
        </body>
      </html>
    """
