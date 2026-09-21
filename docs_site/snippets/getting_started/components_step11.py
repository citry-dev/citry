from citry_setup import citry_app

from citry import Component
from citry.ext.events import EventError, actions


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
        <p role="status" v-show="acceptedEmail">
          Accepted <output v-text="acceptedEmail"></output>.
        </p>
      </section>
    """

    js = """
      $component({
        data() {
          return { acceptedEmail: '' };
        },
        onServerRender({ component }) {
          const receiveSignup = (event) => {
            component.acceptedEmail = event.detail.email;
          };
          component.$el.addEventListener('signup:sent', receiveSignup);
          return () => component.$el.removeEventListener('signup:sent', receiveSignup);
        },
      });
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
