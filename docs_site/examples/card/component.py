"""A card with a colored top border and content of your choice."""

from __future__ import annotations

from citry import Component, SlotInput


class Card(Component):
    """Display any content inside a bordered card."""

    class Kwargs:
        accent: str

    class Slots:
        default: SlotInput

    def css_data(self, kwargs: Kwargs, slots: Slots):
        return { "accent": kwargs.accent }

    template = """
      <article class="demo-card">
        <c-slot />
      </article>
    """

    css = """
      .demo-card {
        max-width: 24rem;
        padding: 1rem 1.25rem;
        border: 1px solid color-mix(in srgb, currentColor 20%, transparent);
        border-top: 0.25rem solid var(--accent);
        border-radius: 8px;
        background: Canvas;
        color: CanvasText;
        font-family: system-ui, sans-serif;
      }

      .demo-card__title {
        margin: 0 0 0.25rem;
        font-size: 1.1rem;
      }

      .demo-card__body {
        margin: 0;
      }
    """
