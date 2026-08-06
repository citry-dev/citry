from typing import Any

from citry import Component


class Welcome(Component):
    class Kwargs:
        title: str
        messages: list[str]

    class Slots:
        pass

    def template_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, Any]:
        return {
            "title": kwargs.title,
            "count": len(kwargs.messages),
        }

    template = """
      <div class="card">
        <h1>{{ title }}</h1>
        <p>You have {{ count }} new messages.</p>
      </div>
    """

    # js_data values reach the script as `data.*`.
    def js_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, Any]:
        return {"count": len(kwargs.messages)}

    js = """
      $component(({ els, data }) => {
        els[0].title = `${data.count} new messages`;
      });
    """

    # css_data values reach the styles as `var(--*)`.
    def css_data(
        self,
        kwargs: Kwargs,
        slots: Slots,
    ) -> dict[str, Any]:
        return {"accent": "tomato"}

    css = """
      .card {
        border-top: 3px solid var(--accent);
      }
    """


component = Welcome(
    title="Welcome back",
    messages=["a", "b", "c"],
)

if __name__ == "__main__":
    print(component)

component
