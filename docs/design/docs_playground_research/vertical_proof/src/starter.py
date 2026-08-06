from citry import Component


class WelcomeCard(Component):
    class Kwargs:
        name: str
        accent: str

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, str]:
        return {"name": kwargs.name.strip().title()}

    def css_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, str]:
        return {"accent": kwargs.accent}

    template = """
      <article class="welcome-card">
        <p>Welcome, <strong>{{ name }}</strong>.</p>
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
    """


WelcomeCard(name="ada lovelace", accent="#6f42c1")
