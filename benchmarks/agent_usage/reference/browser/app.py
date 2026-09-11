"""Reference implementation of the browser counter task."""

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from citry import Citry, Component
from citry.contrib.fastapi import mount

citry_app = Citry(autodiscover=False)
app = FastAPI()
mount(app, citry_app)


class Counter(Component):
    citry = citry_app

    class Kwargs:
        identifier: str
        initial: int

    class Slots:
        pass

    def template_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, object]:
        return {"identifier": kwargs.identifier, "initial": kwargs.initial}

    def js_data(self, kwargs: Kwargs, slots: Slots) -> dict[str, int]:
        # Each rendered instance gets its own mutable browser state.
        return {"count": kwargs.initial, "initial": kwargs.initial}

    template = """
      <section c-id="identifier">
        <h2>{{ identifier }}</h2>
        <output data-role="value" x-text="count">{{ initial }}</output>
        <button
          type="button"
          data-action="increment"
          @click="count += 1"
        >Increment</button>
        <button
          type="button"
          data-action="decrement"
          @click="count -= 1"
        >Decrement</button>
        <button
          type="button"
          data-action="reset"
          @click="count = initial"
        >Reset</button>
      </section>
    """

    css = """
      section {
        margin: 1rem;
        padding: 1rem;
        border: 1px solid #b0b0b0;
      }
      button {
        margin: 0.25rem;
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
          <title>Independent counters</title>
          <c-css />
        </head>
        <body>
          <c-Counter identifier="counter-a" c-initial="2" />
          <c-Counter identifier="counter-b" c-initial="10" />
          <c-js />
        </body>
      </html>
    """


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    return str(Page())
