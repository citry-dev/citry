from app.citry_app import citry_app
from citry import Component, SlotInput


class Card(Component):
    citry = citry_app

    class Kwargs:
        title: str
        count: int

    class Slots:
        footer: SlotInput

    def template_data(self, kwargs: Kwargs, slots: Slots):
        return {"title": kwargs.title, "count": kwargs.count}

    def js_data(self, kwargs: Kwargs, slots: Slots):
        # The Hide button tells the page which card to hide.
        return {"title": kwargs.title}

    template = """
      <article class="card" v-show="!hiddenTitles.includes(title)">
        <h2>{{ title }}: {{ count }} tasks</h2>
        <footer class="card__footer">
          <c-slot name="footer" />
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
