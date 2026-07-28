"""Self-contained starter modules evaluated by the Stage 3 runner proof."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StarterCandidate:
    name: str
    source: str
    expected_text: str
    next_link: str


MINIMAL = StarterCandidate(
    name="Minimal visible component",
    source='''from citry import Component


class Hello(Component):
    template = """
      <h1>Hello from Citry!</h1>
    """


Hello()
''',
    expected_text="Hello from Citry!",
    next_link="/getting-started/your-first-component/",
)


CARD = StarterCandidate(
    name="Typed welcome card",
    source='''from citry import Component


class WelcomeCard(Component):
    class Kwargs:
        name: str
        accent: str

    def template_data(self, kwargs: Kwargs, slots):
        return {"name": kwargs.name.strip().title()}

    def css_data(self, kwargs: Kwargs, slots):
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
      }
    """


WelcomeCard(name="ada lovelace", accent="#6f42c1")
''',
    expected_text="Welcome, <strong>Ada Lovelace</strong>",
    next_link="/getting-started/your-first-component/",
)


COMPOSITION = StarterCandidate(
    name="Two-component feature list",
    source='''from citry import Component


class Feature(Component):
    class Kwargs:
        label: str

    def template_data(self, kwargs: Kwargs, slots):
        return {"label": kwargs.label}

    template = """
      <li class="feature">{{ label }}</li>
    """


class FeatureList(Component):
    template = """
      <section>
        <h1>Why Citry?</h1>
        <ul>
          <c-Feature label="Plain Python" />
          <c-Feature label="Reusable HTML" />
        </ul>
      </section>
    """

    css = """
      .feature {
        margin-block: 0.5rem;
        color: #6f42c1;
      }
    """


FeatureList()
''',
    expected_text="Reusable HTML",
    next_link="/getting-started/build-page/",
)


ALL_STARTERS = (MINIMAL, CARD, COMPOSITION)
