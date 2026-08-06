from citry import Component
from citry.ext.events import actions


class WelcomeCard(Component):
    class Kwargs:
        name: str
        accent: str
        greetings: int = 0

    class Slots:
        pass

    class State:
        greetings: int = 0

    class Events:
        def welcome(self, state):
            state.greetings += 1
            return actions.Dispatch(
                "welcome-card:welcomed",
                {"greetings": state.greetings},
            )

    def state_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, int]:
        return {"greetings": kwargs.greetings}

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, str | int]:
        return {
            "greetings": kwargs.greetings,
            "name": kwargs.name.strip().title(),
        }

    def css_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, str]:
        return {"accent": kwargs.accent}

    template = """
      <article
        class="welcome-card"
        c-x-data="{ 'greetings': greetings }"
        @welcome-card:welcomed="greetings = $event.detail.greetings"
      >
        <p>Welcome, <strong>{{ name }}</strong>.</p>
        <button
          type="button"
          :disabled="$loading('welcome')"
          @c-click="welcome"
        >
          Say hello from Python
        </button>
        <p>
          Replies from Python:
          <output x-text="greetings">{{ greetings }}</output>
        </p>
      </article>
    """

    css = """
      .welcome-card {
        padding: 1rem;
        border-top: 0.25rem solid var(--accent);
        border-radius: 0.5rem;
        background: #f6f3ff;
        color: #221b2f;
      }

      .welcome-card button {
        padding: 0.5rem 0.75rem;
        border: 0;
        border-radius: 0.35rem;
        background: var(--accent);
        color: white;
        cursor: pointer;
      }

      .welcome-card button:disabled {
        cursor: wait;
        opacity: 0.65;
      }
    """


WelcomeCard(name="ada lovelace", accent="#6f42c1")
