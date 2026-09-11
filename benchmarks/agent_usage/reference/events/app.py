"""Reference implementation of the server plan chooser task."""

from dataclasses import dataclass

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from citry import Citry, Component
from citry.contrib.fastapi import mount
from citry.ext.events import EventError

PLANS = {
    "starter": ("Starter", 12),
    "team": ("Team", 29),
    "scale": ("Scale", 79),
}
citry_app = Citry(autodiscover=False, secret="benchmark-local-development-secret")  # noqa: S106 - local benchmark only
app = FastAPI()
mount(app, citry_app)


@dataclass
class ChoosePlan:
    plan: str


class PlanChooser(Component):
    citry = citry_app

    class Kwargs:
        selected: str = "starter"

    class Slots:
        pass

    class Events:
        def choose(self, data: ChoosePlan) -> "PlanChooser":
            # The browser supplies an identifier; prices remain server-owned.
            if data.plan not in PLANS:
                raise EventError("Choose an available plan.")
            return PlanChooser(selected=data.plan)

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
        label, price = PLANS[kwargs.selected]
        return {"selected": kwargs.selected, "label": label, "price": price, "plans": PLANS}

    template = """
      <section>
        <h1>Choose a plan</h1>
        <c-for each="key, plan in plans.items()">
          <button
            type="button"
            c-data-plan="key"
            c-aria-pressed="'true' if key == selected else 'false'"
            @c-click="choose({plan: $el.dataset.plan})"
          >{{ plan[0] }}</button>
        </c-for>
        <p id="selected-plan">{{ label }}</p>
        <p id="selected-price">${{ price }} / month</p>
      </section>
    """

    css = """
      section {
        margin: 2rem;
        font-family: sans-serif;
      }
      button[aria-pressed="true"] {
        font-weight: bold;
      }
    """


class Page(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    template = """
      <!DOCTYPE html>
      <html lang="en">
        <head>
          <title>Choose a plan</title>
          <c-css />
        </head>
        <body>
          <c-PlanChooser />
          <c-js />
        </body>
      </html>
    """


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return str(Page())
