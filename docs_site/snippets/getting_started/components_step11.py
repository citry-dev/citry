from citry import Component
from citry.ext.events import EventError, actions

from citry_setup import citry_app


# New in this step: describe the named values sent by the form.
class SignupIn:
    email: str


# New in this step: Sign up form with server-side validation
class SignupForm(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    class Events:
        # Validate the form and return field errors
        def submit(self, data: SignupIn):
            email = data.email.strip()
            if not email.endswith("@example.com"):
                raise EventError(
                    "Please fix the email address.",
                    fields={"email": "Use an @example.com address."},
                )
            return actions.Dispatch(
                "signup:sent",
                {"email": email},
            )

    template = """
      <section
        class="signup-form"
        x-data="{ acceptedEmail: '' }"
        @signup:sent="acceptedEmail = $event.detail.email"
      >
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
        <p role="status" x-show="acceptedEmail">
          Accepted <output x-text="acceptedEmail"></output>.
        </p>
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
        </head>
        <body>
          <main>
            <h1>Join the reading room</h1>
            {# New in this step: place the form on the page. #}
            <c-SignupForm />
          </main>
        </body>
      </html>
    """
