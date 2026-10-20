from app.citry_app import citry_app
from citry import Component


class Details(Component):
    citry = citry_app

    class Kwargs:
        pass

    class Slots:
        pass

    def js_data(self, kwargs: Kwargs, slots: Slots):
        return {"open": False}

    template = """
      <section class="details">
        <button type="button" @click="toggle()">Details</button>
        <p v-iff="open">Details are visible</p>
      </section>
    """

    js = """
      $component({
        methods: {
          toggle() {
            this.open = !this.open;
          },
        },
      });
    """
