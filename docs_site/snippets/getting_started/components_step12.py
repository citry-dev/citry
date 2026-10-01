from citry_setup import citry_app

from citry import Component
from citry.ext.events import EventError, actions


# New in this step: show the accepted address.
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
          v-text="'Confirmation ready for ' + email"
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

    # New in this step: Python passes the accepted address
    # when it renders this form again.
    class Kwargs:
        email: str | None = None

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
            # New in this step: render this component again,
            # now with the accepted address.
            return actions.Render(SignupForm(email=email))

    template = """
      <section class="signup-form">
        {# New in this step: show the form until Python #}
        {# accepts an address. #}
        <form
          c-if="email is None"
          @c-submit.prevent="submit"
        >
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
              v-show="$error('submit')?.fieldErrors?.email"
              v-text="$error('submit')?.fieldErrors?.email || ''"
            ></span>
          </label>
          <button
            type="submit"
            :disabled="$loading('submit')"
            v-text="$loading('submit') ? 'Sending' : 'Send request'"
          >
            Send request
          </button>
        </form>
        {# New in this step: the live region stays on the page #}
        {# in both renders, so screen readers announce the #}
        {# confirmation that appears inside it. #}
        <div aria-live="polite">
          <c-Confirmation
            c-if="email is not None"
            c-email="email"
          />
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
