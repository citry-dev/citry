"""A button that reads its look from a provided theme, used as a live docs example."""

from typing import Any

from citry import Component


class ThemedButton(Component):
    """A button with no theme prop: it injects the nearest provided theme instead."""

    class Kwargs:
        text: str

    class Slots:
        pass

    template = """
      <button class="themed-btn" c-style="style">
        {{ label }}: {{ text }}
      </button>
    """

    css = """
      .themed-btn {
        padding: 0.5rem 1rem;
        margin: 0.25rem;
        border: none;
        border-radius: 6px;
        color: #ffffff;
        font-family: system-ui, sans-serif;
        font-size: 0.95rem;
        cursor: pointer;
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        theme = self.inject("theme")
        return {
            "text": kwargs.text,
            "label": theme.label,
            "style": "background: " + theme.accent + ";",
        }
