"""A widget that can fail on demand, used to demonstrate error boundaries."""

from typing import Any

from citry import Component


class FlakyWidget(Component):
    """Renders normal content, or raises during render when ``fail`` is true."""

    class Kwargs:
        label: str
        fail: bool = False

    class Slots:
        pass

    template = """
      <div class="flaky">
        <strong>{{ label }}</strong>
        <p class="flaky__ok">Loaded cleanly.</p>
      </div>
    """

    css = """
      .flaky {
        padding: 0.75rem 1rem;
        border: 1px solid #2da44e;
        border-radius: 8px;
        background: #effef1;
      }
      .flaky__ok {
        margin: 0.35rem 0 0;
        color: #1a7f37;
      }
    """

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, Any]:
        if kwargs.fail:
            # Raised during render so the surrounding <c-error-fallback> catches it.
            raise ValueError("FlakyWidget was told to fail")
        return {"label": kwargs.label}
