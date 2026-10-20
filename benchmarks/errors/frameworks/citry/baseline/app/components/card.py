from typing import Literal

from app.citry_app import citry_app
from citry import Component, SlotInput


class FooterData:
    title: str
    count: int


class Card(Component):
    citry = citry_app

    class Kwargs:
        title: str
        count: int
        tone: Literal["plain", "accent"]

    class Slots:
        # The card hands its title and count to the page's footer fill.
        footer: SlotInput[FooterData]

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {"title": kwargs.title, "count": kwargs.count, "tone": kwargs.tone}

    def js_data(self, kwargs: Kwargs, slots: Slots):
        # The Hide button tells the page which card to hide.
        return {"title": kwargs.title}

    template = """
      <article
        c-class="['card', 'card--' + tone]"
        v-show="!hiddenTitles.includes(title)"
      >
        <h2>{{ title }}: {{ count }} tasks</h2>
        <footer class="card__footer">
          <c-slot
            name="footer"
            c-title="title"
            c-count="count"
          />
        </footer>
        <button type="button" @click="$emit('hide', title)">Hide</button>
      </article>
    """

    js = """
      $component({
        props: {
          hiddenTitles: { type: Array, required: true },
        },
        emits: ['hide'],
      });
    """

    css = """
      .card--accent {
        border: 2px solid rgb(0, 0, 255);
      }
    """
