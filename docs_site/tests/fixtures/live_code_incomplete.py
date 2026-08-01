"""A syntactically valid live-code source without a preview value."""

from citry import Component


class DraftCard(Component):
    class Kwargs:
        text: str

    class Slots:
        pass

    template = """
      <article class="draft-card">
        {{ text }}
      </article>
    """
